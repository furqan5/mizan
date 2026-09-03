"""
FURQAN :: consistency audit across code, results and documents
==============================================================
Every headline number in this package exists in exactly one place -- a
results artefact -- and everything else is supposed to be generated from
it. This checks that nothing has drifted, and it checks the things a
generator cannot: numbers typed into hand-written documents, constants
duplicated between modules, and claims that contradict a gate verdict.

It is written to FAIL LOUDLY. A quiet audit is worthless.

Run:  python src/audit.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
DOCS = ROOT / "docs"
sys.path.insert(0, str(pathlib.Path(__file__).parent))

PROBLEMS: list[str] = []
CHECKS = 0


def check(ok: bool, what: str, detail: str = ""):
    global CHECKS
    CHECKS += 1
    if not ok:
        PROBLEMS.append(f"{what}" + (f"  --  {detail}" if detail else ""))


def main():
    global CHECKS
    cal = json.loads((RESULTS / "calibration.json").read_text())
    ctrl = json.loads((RESULTS / "controller_summary.json").read_text())
    ho, sm, crit = cal["HOLDOUT"], ctrl["summary"], ctrl["criteria"]

    print("=" * 74)
    print("FURQAN / MIZAN :: consistency audit")
    print("=" * 74)

    # --- 1. the gate verdicts implied by the numbers ---------------------
    v1_t = ho["Tout_MAE_K"] <= 1.00
    v1_q = ho["Q_MAPE_pct"] <= 6.00
    v2 = ho["evap_MAPE_pct"] <= 8.00
    v5_c = sm["cost_pct"] >= crit["total_cost_reduction_pct_min"]
    v5_w = sm["water_pct"] >= crit["makeup_water_reduction_pct_min"]
    v5_s = sm["violations"] <= crit["skin_SI_violations_allowed"]

    print("\ngate verdicts, computed from the artefacts:")
    for name, val, unit, ok in (
        ("V1 outlet temperature MAE", ho["Tout_MAE_K"], "K", v1_t),
        ("V1 heat rejection MAPE", ho["Q_MAPE_pct"], "%", v1_q),
        ("V2 evaporation MAPE", ho["evap_MAPE_pct"], "%", v2),
        ("V5 cost reduction", sm["cost_pct"], "%", v5_c),
        ("V5 water reduction", sm["water_pct"], "%", v5_w),
        ("V5 skin SI violations", sm["violations"], "", v5_s),
    ):
        print(f"   {name:32s} {val:9.3f} {unit:2s}  "
              f"{'PASS' if ok else 'FAIL'}")

    # --- 2. constants that exist in more than one module -----------------
    import chemistry as chem
    import controller as ctlm
    import tower as tw

    check(tw.DRIFT_FRACTION == ctlm.DRIFT_FRACTION,
          "drift fraction differs between tower.py and controller.py",
          f"{tw.DRIFT_FRACTION} vs {ctlm.DRIFT_FRACTION}")
    check(abs(tw.DRIFT_FRACTION - 1.0e-5) < 1e-12,
          "drift fraction is not the documented 0.001 % of circulating flow",
          f"{tw.DRIFT_FRACTION}")
    check(tw.CPW == ctlm.CPW, "CPW differs between tower.py and controller.py")
    check(abs(ctlm.CHILLER_COP_REF - 6.28) < 1e-9,
          "chiller reference COP is not the York YT 1758 kW value 6.28")
    check(ctlm.CHILLER_TCWS_RANGE == (15.56, 35.00),
          "chiller entering-condenser range is not the fitted 15.56-35.00 C")
    check(chem.DISCHARGE_TDS_CAP_DEFAULT is None,
          "a blanket discharge TDS cap has been re-enabled; RCER-2015 makes it "
          "a property of the discharge route, not the loop")

    # --- 3. the MATLAB twin must carry the same chiller curve ------------
    mfile = (ROOT / "matlab" / "+mizan" / "chiller.m").read_text(encoding="utf-8")
    for v in ctlm.CHILLER_CAPFT + ctlm.CHILLER_EIRFT + ctlm.CHILLER_EIRFPLR:
        # match on the significant digits, formatting differs between languages
        token = f"{v:.7g}".lstrip("0") if abs(v) < 1 else f"{v:.7g}"
        check(token.lstrip("-").lstrip(".").split("e")[0][:6] in
              mfile.replace(" ", ""),
              f"chiller coefficient {v} not found in matlab/+mizan/chiller.m")
    check(str(ctlm.CHILLER_COP_REF) in mfile,
          "MATLAB chiller reference COP disagrees with controller.py")

    # --- 4. the MATLAB twin's agreement gates were actually scored -------
    mcases = RESULTS / "matlab_cases.json"
    check(mcases.exists(),
          "results/matlab_cases.json missing; run src/export_matlab_cases.py")
    if mcases.exists():
        mc = json.loads(mcases.read_text())
        check(abs(mc["fill_c"] - cal["fill_c"]) < 1e-12
              and abs(mc["fill_n"] - cal["fill_n"]) < 1e-12,
              "the MATLAB case file was generated against a different fill law",
              "regenerate with src/export_matlab_cases.py")

    # --- 4b. the MATLAB results must agree with the Python core ----------
    msim = RESULTS / "matlab_simulink.json"
    if msim.exists():
        ms = json.loads(msim.read_text())
        # The standalone MATLAB demo and the Simulink model are independent
        # paths through the same physics. They must land in the same place.
        check(38.0 <= ms["T_skin_min"] <= 41.0 and 45.0 <= ms["T_skin_max"] <= 47.5,
              "Simulink skin temperature is outside the range the standalone "
              "MATLAB demo produces (38-40 to 46 C)",
              f"{ms['T_skin_min']:.1f}-{ms['T_skin_max']:.1f} C")
        check(8.40 <= ms["pH_limit_min"] <= 8.50 and 8.75 <= ms["pH_limit_max"] <= 8.95,
              "Simulink brucite limit disagrees with the standalone demo "
              "(8.43 to 8.80-8.89)",
              f"{ms['pH_limit_min']:.2f}-{ms['pH_limit_max']:.2f}")
        check(bool(ms["in_envelope_all_day"]),
              "the Simulink run left the chiller's fitted envelope")
        check(9.0 <= ms["hours_depositing"] <= 13.0,
              "hours above the scaling limit disagree with the standalone "
              "demo (11 h)", f"{ms['hours_depositing']:.1f} h")

    mcd = RESULTS / "matlab_control_design.json"
    if mcd.exists():
        cd = json.loads(mcd.read_text())
        check(abs(cd["mpc_ecwt_max"] - ctlm.CHILLER_TCWS_RANGE[1]) < 1e-9,
              "the MPC output constraint does not match the chiller's fitted "
              "ceiling", f"{cd['mpc_ecwt_max']} vs {ctlm.CHILLER_TCWS_RANGE[1]}")
        check(300.0 <= cd["tau_s"] <= 900.0,
              "the identified loop time constant is not physical",
              f"{cd['tau_s']:.0f} s")
        check(abs(cd["fill_c"] - cal["fill_c"]) < 0.05,
              "the Curve Fitting result disagrees with the calibrated fill law",
              f"{cd['fill_c']:.4f} vs {cal['fill_c']:.4f}")

    # --- 4c. the V2 diagnosis must exist and must actually close --------
    v2 = RESULTS / "v2_diagnosis.json"
    check(v2.exists(), "results/v2_diagnosis.json missing -- the V2 failure "
                       "is undiagnosed")
    if v2.exists():
        dg = json.loads(v2.read_text())
        worst = max(dg[c]["evap_MAPE_pct"] for c in dg)
        check(worst <= 8.0,
              "per-campaign re-identification does NOT bring every campaign "
              "inside the 8 % gate, so the fill-drift explanation for V2 does "
              "not hold and the bleed hypothesis is back open",
              f"worst {worst:.2f} %")
        cs = [dg[c]["c"] for c in dg]
        spread = 100*(max(cs)-min(cs))/min(cs)
        check(15.0 <= spread <= 35.0,
              "the campaign-to-campaign fill drift is not in the range the "
              "documents describe", f"{spread:.1f} %")
        reg = (DOCS / "defect_register.md").read_text(encoding="utf-8")
        # The register must be INTERNALLY CONSISTENT about open defects, which
        # is a different and stricter test than requiring it to say "none".
        #
        # This previously asserted the literal string "Open defects: none". That
        # check passes for a register that is honest and empty, and fails for a
        # register that is honest and non-empty -- so it punished disclosure and
        # created pressure to either hide a defect or rush a fix to unblock
        # packaging. It also could not catch the case that actually matters: a
        # table listing an OPEN row while the summary line still claims none.
        #
        # Now: count the rows marked OPEN, read the declared count, require
        # they agree. Zero open defects still passes. One open and declared
        # passes. One open and undeclared fails, which is the real defect.
        _WORDS = {"none": 0, "one": 1, "two": 2, "three": 3, "four": 4,
                  "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9}
        n_open_rows = len(re.findall(r"\|\s*\*\*OPEN\*\*\s*\|", reg))
        m = re.search(r"\*\*Open defects:\s*([A-Za-z]+|\d+)", reg)
        if m is None:
            declared = None
        else:
            tok = m.group(1).lower()
            declared = int(tok) if tok.isdigit() else _WORDS.get(tok)
        check(declared is not None,
              "the defect register does not declare an open-defect count in "
              "the form '**Open defects: <n>'")
        check(declared == n_open_rows,
              "the defect register's declared open-defect count disagrees with "
              "the rows marked OPEN in its own table",
              f"declares {declared}, table shows {n_open_rows}")
        check(f"{spread:.1f}" in reg,
              "the defect register quotes a fill drift the artefact does not "
              "support", f"artefact says {spread:.1f} %")

    # --- 4d. no document may exist as two copies -------------------------
    # A duplicated document is a defect waiting to happen: identical today,
    # silently divergent the first time one copy is edited.
    seen: dict[str, pathlib.Path] = {}
    for md in list(DOCS.glob("*.md")) + [ROOT / "matlab" / "README.md",
                                         ROOT / "modelica" / "README.md",
                                         ROOT / "HANDOFF.md"]:
        if not md.exists():
            continue
        body = md.read_text(encoding="utf-8").strip()
        key = body[:400]
        if key in seen:
            check(False, f"{md.name} duplicates {seen[key].name}",
                  "one document, one source")
        seen[key] = md
    CHECKS += 1

    # --- 4e. the revision memo must still be a PROPOSAL -------------------
    # If a threshold is ever revised, it must be declared. This check exists
    # so that a revision cannot be applied quietly while the memo still
    # describes it as untaken.
    memo = DOCS / "threshold_revision_memo.md"
    if memo.exists():
        mt = memo.read_text(encoding="utf-8")
        check("Nothing here has been applied" in mt,
              "the revision memo no longer says the revisions are unapplied")
        check(abs(crit["makeup_water_reduction_pct_min"] - 15.0) < 1e-9,
              "the V5 water threshold has been changed from its "
              "pre-registered 15 % without the memo being updated",
              f"{crit['makeup_water_reduction_pct_min']}")

    # --- 4f. a revision must be DECLARED, never silent --------------------
    import run_controller as rcm
    for k, v in rcm.V5_PRE_REGISTERED.items():
        applied = rcm.V5_CRITERIA[k]
        if applied == v:
            continue
        # a threshold has moved: it must be a recorded revision, and the memo
        # and the report must both say so
        rev = [r for r in rcm.V5_REVISIONS if r["criterion"] == k]
        check(bool(rev),
              f"threshold {k} was changed from {v} to {applied} without a "
              f"recorded revision -- this is exactly the silent rescoring the "
              f"package exists to make impossible")
        if rev:
            r = rev[0]
            for field in ("was", "now", "date", "reason"):
                check(field in r and r[field] not in (None, ""),
                      f"the revision of {k} is missing its '{field}'")
            memo_t = (DOCS / "threshold_revision_memo.md").read_text(encoding="utf-8")
            check("has been applied" in memo_t or str(r["now"]) in memo_t,
                  "a threshold revision is applied but the decision memo still "
                  "presents it as an untaken proposal")
            poc = (DOCS / "poc_report.md").read_text(encoding="utf-8")
            check("revision" in poc.lower(),
                  "a threshold was revised but the PoC report does not record "
                  "the revision")

    # --- 4g. the TMY cross-check must still hold -------------------------
    tmy = RESULTS / "tmy_dhahran.json"
    if tmy.exists():
        t = json.loads(tmy.read_text())
        check(t["worst_design_disagreement_K"] <= 0.6,
              "our psychrometrics no longer agree with ASHRAE's published "
              "design conditions for Dhahran",
              f"worst {t['worst_design_disagreement_K']:.2f} K")
        check(35.0 <= t["pct_year_above_almeria"] <= 46.0,
              "the fraction of the Dhahran year above the validation ceiling "
              "is not what the documents state",
              f"{t['pct_year_above_almeria']:.1f} %")
        # every document that cites the extrapolation figure must cite THIS one
        want = f"{t['pct_year_above_almeria']:.1f} %"
        for f in ("poc_report.md", "defect_register.md", "ai_architecture.md"):
            fp = DOCS / f
            if fp.exists() and "of a Dhahran year" in fp.read_text(encoding="utf-8"):
                check(want in fp.read_text(encoding="utf-8"),
                      f"{f} cites an extrapolation figure the artefact does "
                      f"not support", f"artefact says {want}")

    # --- 4h. the annual figure must match the artefact --------------------
    ann = RESULTS / "annual_dhahran.json"
    if ann.exists():
        an = json.loads(ann.read_text())
        check(abs(an["v5_gate_unweighted_mean_water_pct"] - sm["water_pct"]) < 0.02,
              "the annual comparison quotes a V5 figure that no longer matches "
              "the controller result",
              f"{an['v5_gate_unweighted_mean_water_pct']} vs {sm['water_pct']:.2f}")
        check(an["annual_water_pct"] < sm["water_pct"],
              "the hours-weighted annual figure is no longer BELOW the "
              "five-condition mean; the documents say it is lower and explain "
              "why, so one of them is now wrong")
        want = f"{an['annual_water_pct']:.2f} %"
        poc_t = (DOCS / "poc_report.md").read_text(encoding="utf-8")
        check(want in poc_t or f"{an['annual_water_pct']:.1f} %" in poc_t,
              "the PoC report does not carry the hours-weighted annual figure",
              f"artefact says {want}")

    # --- 5. no document may quote a superseded headline number -----------
    stale = {
        "7.11 %": "the pre-drift-fix evaporation MAPE",
        "12.51 %": "the pre-chiller-fix water saving",
        "6.48 %": "the pre-chiller-fix cost saving",
        "14.64 %": "the unconverged-solver water saving",
    }
    # A superseded number may appear ONLY where the surrounding paragraph
    # says so. The label is often a sentence or two above the figure, so the
    # whole paragraph is the unit of context, not the line.
    LABELS = ("as sent", "earlier", "was later", "superseded", "withdrawn",
              "turned out", "artefact", "no longer", "previously",
              "used to", "corrected to")
    for md in sorted(DOCS.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        paras = text.split("\n\n")
        pos = 0
        for para in paras:
            start = text.find(para, pos)
            pos = start + len(para)
            low = para.lower()
            labelled = any(k in low for k in LABELS)
            for tok, why in stale.items():
                if tok in para and not labelled:
                    line = text[:start].count("\n") + 1
                    check(False, f"{md.name}:~{line} quotes {tok} ({why}) "
                                 f"with nothing marking it as superseded",
                          para.strip().replace("\n", " ")[:90])

    # --- 6. a document must not claim a pass the artefacts do not support -
    poc = (DOCS / "poc_report.md").read_text(encoding="utf-8")
    check(("9.90 % | **FAIL**" in poc) or ("9.90 %" in poc and "FAIL" in poc),
          "the PoC report does not record the V2 failure")
    # READ THE FIGURES FROM THE ARTEFACT. These were the literals "14.83" and
    # "8.55" -- the values as of the day the check was written. When defect 11
    # was fixed and the controller re-ran, the artefact moved to 10.02 and 6.37
    # and these checks began demanding that the report quote SUPERSEDED
    # numbers: an audit enforcing staleness. Same failure as the
    # "Open defects: none" literal fixed above, and as the 14.83 hardcoded four
    # times in annual.py and once in make_report.py.
    _sm = json.loads((RESULTS / "controller_summary.json").read_text())["summary"]
    _w, _c = _sm["water_pct"], _sm["cost_pct"]
    check(f"{_w:.2f}" in poc,
          "the PoC report does not carry the current water figure",
          f"artefact says {_w:.2f} %")
    check(f"{_c:.2f}" in poc,
          "the PoC report does not carry the current cost figure",
          f"artefact says {_c:.2f} %")

    # --- report ----------------------------------------------------------
    print(f"\n{CHECKS} checks run.")
    if PROBLEMS:
        print(f"\n{len(PROBLEMS)} PROBLEM(S):\n")
        for p in PROBLEMS:
            print(f"   x  {p}")
        print("\nAUDIT FAILED")
        return 1
    print("\nNo contradictions found. Every headline number in the documents\n"
          "matches the artefact it is generated from, every duplicated\n"
          "constant agrees, and no superseded figure is quoted unlabelled.")
    print("\nAUDIT PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
