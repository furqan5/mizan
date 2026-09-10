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
PAIRS: dict[str, str] = {}
ROUNDED: set[str] = set()

# The documents are full of the characters engineering prose needs -- >=, x,
# degree signs, arrows. On a Windows console stdout defaults to cp1252 and
# printing one of them raises. A PASSING audit prints only ASCII, so this
# crashed ONLY when there was something to report: the failure path was the
# untested path, and an audit that dies while listing problems is worse than
# no audit. Errors are replaced rather than raised.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):  # pragma: no cover - non-reconfigurable
    pass


def check(ok: bool, what: str, detail: str = ""):
    global CHECKS
    CHECKS += 1
    if not ok:
        PROBLEMS.append(f"{what}" + (f"  --  {detail}" if detail else ""))


def superseded_from_register() -> dict[str, str]:
    """Read the set of superseded headline figures OUT OF the defect register.

    This used to be four literals typed into section 5. That is the defect-12
    shape one level up: a hand-maintained record of what the numbers USED to
    be, which has to be edited by hand every time they move, and which
    therefore goes stale at exactly the moment a fix has made it matter.

    It did. Defect 11 superseded six headline figures on 3 September and not
    one was added to that list, so the scan went on passing documents that
    quote them -- including the draft of a post that was actually published.

    The register's before/after table is already the supersession record and
    is already required to be accurate. So it is read rather than copied.
    Any future fix that moves a headline number updates this scan for free,
    because writing that table is part of recording the defect.
    """
    reg = (DOCS / "defect_register.md").read_text(encoding="utf-8")
    out: dict[str, str] = {}
    # value -> the value that replaced it, so the scan can recognise a
    # paragraph that shows BOTH as a supersession record rather than a stale
    # quote. Without this the register's own table fails the check it feeds.
    PAIRS.clear()
    ROUNDED.clear()
    rows = re.findall(r"^\|([^|\n]*)\|([^|\n]*)\|([^|\n]*)\|\s*$",
                      reg, re.MULTILINE)
    for label, before, after in rows:
        label = label.strip()
        if not label or "---" in before:
            continue
        # only percentages: a bare "5 -> 3" count would match half the prose
        b = re.fullmatch(r"\**\s*([0-9]+\.[0-9]+)\s*%\s*\**", before.strip())
        a = re.search(r"([0-9]+\.[0-9]+)\s*%", after)
        if not (b and a):
            continue
        out[f"{b.group(1)} %"] = f"the pre-fix {label.lower()}"
        PAIRS[f"{b.group(1)} %"] = a.group(1)
        # Also the ROUNDED form. Documents quote two decimals internally and one
        # decimal to the outside world, so "12.57 %" leaves the repository as
        # "12.6 %" -- and it was the one-decimal form that reached LinkedIn, the
        # Sanabil website spec and three outreach templates while the audit
        # watched only for the two-decimal one.
        # Rounding is applied ONLY to supersessions recorded in this table, never
        # to the four legacy prose entries below: 12.51 and 6.48 round onto 12.5
        # and 6.5, which are a live cycles-arithmetic constant and a live cost
        # figure respectively. A stale-number scan that cries wolf gets silenced.
        rb, ra = f"{float(b.group(1)):.1f} %", f"{float(a.group(1)):.1f}"
        if rb != f"{b.group(1)} %":
            ROUNDED.add(rb)
            out[rb] = f"the pre-fix {label.lower()}, as rounded for publication"
            PAIRS[rb] = ra
    # Four supersessions predate the table convention and are recorded in the
    # register as prose only. They stay declared here, and they are the reason
    # the convention exists.
    out.update({
        "7.11 %": "the pre-drift-fix evaporation MAPE",
        "12.51 %": "the pre-chiller-fix water saving",
        "6.48 %": "the pre-chiller-fix cost saving",
        "14.64 %": "the unconverged-solver water saving",
        # Found 4 Sep in docs/outreach_targets.md, the file the outreach is sent
        # FROM, still telling the founder to quote these to prospects. They are
        # the pre-defect-11 hours-weighted MEAN-OF-RATIOS figures, superseded
        # twice, and they predate the before/after table convention so nothing
        # derived them. Nothing had been sent, so no prospect received them.
        "11.5 %": "the pre-defect-11 annual water, mean of ratios",
        "8.3 %": "the pre-defect-11 annual cost, mean of ratios",
        "6.7 %": "the pre-defect-11 annual electrical power, mean of ratios",
    })
    # A ROUNDED stale form that collides with a number the artefacts hold RIGHT
    # NOW is not evidence of staleness, it is a coincidence of one decimal
    # place -- and flagging it is how a check earns the reputation that gets it
    # ignored. The docstring above already warned about this class: 6.48 rounds
    # onto a live 6.5. Defects 15 and 16 made it bite for real, because the
    # pre-fix V5 cost of 6.37 % and the CURRENT annual cost of 6.44 % both
    # round to "6.4 %". So the live set is computed from the artefacts and
    # subtracted, rather than the collisions being listed by hand -- which is
    # the whole lesson of defects 12 and 13.
    for tok in _live_rounded_forms():
        if tok in ROUNDED:
            ROUNDED.discard(tok)
            out.pop(tok, None)
            PAIRS.pop(tok, None)
    # The hand-declared exact figures above never enter ROUNDED, so the loop
    # just run cannot reach them, and that is how the data centre run broke this
    # audit: its annual energy saving is 6.4779 %, prints as "6.48 %", and
    # collides exactly with the cost saving the chiller fix retired. So they get
    # their own pass -- against HEADLINE values only. Scope is the whole point.
    # Clearing them against per-bin values as well would retire the declared
    # "11.5 %" and "8.3 %" on nothing more than bin 0 saving 11.52 % energy and
    # bin 5 saving 8.33 % water, and those two were declared precisely because
    # they were found live in the file the outreach is sent from.
    for tok in _live_rounded_forms(headline_only=True):
        out.pop(tok, None)
        PAIRS.pop(tok, None)
    return out


def _live_rounded_forms(headline_only: bool = False) -> set[str]:
    """Current artefact figures, as "N.N %" and "N.NN %".

    Two scopes, because the two callers need different ones. The default
    includes the per-bin arrays, since documents legitimately quote bin ranges
    ("6.0 to 8.6 % across the cooler half"). `headline_only` stops at the
    scalars, because a coincidence between one hourly bin and an annual total
    is not grounds for retiring a figure the register declared stale.

    A number a live artefact still generates cannot be a stale quote, whatever
    it once meant. The data centre run makes that concrete: its annual energy
    saving is 6.4779 %, which prints as "6.48 %" and collides exactly with the
    cost saving retired by the chiller capacity fix. Documents quote figures at
    one decimal and at two, so both forms have to be cleared, and every artefact
    that carries a headline has to be listed here or the audit starts demanding
    that current numbers be labelled superseded.
    """
    live: set[str] = set()
    for name in ("controller_summary.json", "annual_dhahran.json",
                 "annual_datacentre.json", "calibration.json"):
        path = RESULTS / name
        if not path.exists():
            continue
        def walk(node):
            if isinstance(node, dict):
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                if headline_only:
                    return
                for v in node:
                    walk(v)
            elif isinstance(node, float):
                live.add(f"{node:.1f} %")
                live.add(f"{node:.2f} %")
        walk(json.loads(path.read_text(encoding="utf-8")))
    return live


def artefact_value(spec: str):
    """Resolve `file.json -> a.b.c` against the results directory.

    Documents cite a key the way a reader would say it -- `binding_mineral`,
    not `summary.binding_mineral`. An exact path is tried first; failing
    that, a key that occurs exactly ONCE anywhere in the file resolves to it.
    A key occurring more than once does not resolve, because then the
    citation really is ambiguous and the document should say which one.
    """
    fname, _, keypath = spec.partition("|")
    fp = RESULTS / fname
    if not fp.exists():
        return None
    doc = json.loads(fp.read_text())

    node = doc
    for part in keypath.split("."):
        if not isinstance(node, dict) or part not in node:
            node = None
            break
        node = node[part]
    if node is not None:
        return node

    if "." in keypath:
        return None
    found = []

    def walk(n):
        if isinstance(n, dict):
            for k, v in n.items():
                if k == keypath:
                    found.append(v)
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(doc)
    return found[0] if len(found) == 1 else None


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

        # --- the TOTAL count, across every document that states it -------
        #
        # The check above guards the OPEN count. Nothing guarded the TOTAL,
        # and the total is the number that moves every single time a defect
        # is found -- so it went stale in four documents at once, including
        # the co-founder-facing one, which claimed "none open" while the
        # register declared one. Defects 12, 13 and 21 are all the same
        # shape: a figure maintained by hand, in a file nobody re-reads.
        #
        # Derive it from the register's own table rather than declaring it.
        # Numerals are BUILT, not listed. A hand-maintained dict goes blind
        # the moment the count passes its last entry -- which is exactly
        # defect 21, a staleness guard that could not reach part of what it
        # was meant to police. It happened here too: the dict stopped at
        # twenty-five and "twenty-eight" silently matched "twenty".
        _UNITS = ["", "one", "two", "three", "four", "five", "six", "seven",
                  "eight", "nine"]
        _TEENS = {"ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
                  "fourteen": 14, "fifteen": 15, "sixteen": 16,
                  "seventeen": 17, "eighteen": 18, "nineteen": 19}
        _TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
                 "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
        _NUM = dict(_TEENS)
        for _w, _v in _TENS.items():
            _NUM[_w] = _v
            for _i, _u in enumerate(_UNITS[1:], start=1):
                _NUM[f"{_w}-{_u}"] = _v + _i
                _NUM[f"{_w} {_u}"] = _v + _i

        rows = [m.group(1) for m in
                re.finditer(r"^\|\s*(\d+)\s*\|.*?\*\*(?:Fixed|OPEN)\*\*",
                            reg, re.M)]
        n_defects = len({int(r) for r in rows})
        check(n_defects > 0,
              "could not count defect rows in the register's own table; the "
              "table format changed and this guard is now blind")

        # Longest-first, or "twenty" matches inside "twenty-one" and silently
        # reports 20 for a document that says twenty-one.
        _alts = "|".join(sorted(_NUM, key=len, reverse=True))
        _pat = re.compile(
            r"\b(" + _alts + r")\b[^.|\n]{0,40}?\bdefects?\b"
            r"[^.|\n]{0,40}?\bfound\b", re.I)
        _pat2 = re.compile(r"\b(" + _alts + r")\b\s+found\b", re.I)
        # A document whose job is to QUOTE the disagreement is not asserting
        # a count of its own.
        _quoting = {"datacentre_strategy.md"}
        disagree = []
        for md in list(DOCS.glob("*.md")) + [ROOT / "HANDOFF.md"]:
            if not md.exists() or md.name in _quoting:
                continue
            for ln, line in enumerate(
                    md.read_text(encoding="utf-8",
                                 errors="replace").splitlines(), 1):
                if line.lstrip().startswith("|"):
                    continue
                for mm in list(_pat.finditer(line)) + list(_pat2.finditer(line)):
                    said = _NUM[mm.group(1).lower()]
                    if said != n_defects:
                        disagree.append(f"{md.name}:{ln} says {said}")
        check(not disagree,
              "a document states a defect count that disagrees with the "
              "register's own table",
              f"table shows {n_defects}; " + "; ".join(disagree[:6]))

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
    stale = superseded_from_register()
    SCANNED = sorted(list(DOCS.glob("*.md")) + list(DOCS.glob("*.txt"))
                     + [ROOT / "HANDOFF.md"])
    # A superseded number may appear ONLY where the surrounding paragraph
    # says so. The label is often a sentence or two above the figure, so the
    # whole paragraph is the unit of context, not the line.
    LABELS = ("as sent", "earlier", "was later", "superseded", "withdrawn",
              "turned out", "artefact", "no longer", "previously",
              "used to", "corrected to")
    # .txt is in scope too. `docs/linkedin_correction_post.txt` is the text of
    # a post that was actually published and it was outside the glob, so the
    # one document in here with real-world consequences was the one document
    # the scan could not see. HANDOFF.md is in scope for the same reason from
    # the other direction: it is the first thing the next session reads, so a
    # superseded number in it propagates into everything written afterwards.
    # Documents written by make_report.py / make_deck.py from the artefacts.
    GENERATED = {"poc_report.md", "deck_content.md"}
    for md in SCANNED:
        generated = md.name in GENERATED
        text = md.read_text(encoding="utf-8")
        paras = text.split("\n\n")
        pos = 0
        for para in paras:
            start = text.find(para, pos)
            pos = start + len(para)
            low = para.lower()
            labelled = any(k in low for k in LABELS)
            for tok, why in stale.items():
                # A ROUNDED stale form is only meaningful in a HAND-WRITTEN
                # document. Generated reports recompute every number at build
                # time, so they cannot carry a figure someone forgot to update
                # -- but they CAN legitimately print a current value that
                # happens to round onto a superseded one. Not hypothetical:
                # poc_report.md prints Doha summer humid's water saving of
                # 12.64 % as "+12.6 %", colliding exactly with the pre-fix
                # annual water figure of 12.57 %. Flagging a freshly computed
                # number as stale is the fastest way to teach someone to ignore
                # this check. Exact forms still apply everywhere: if a GENERATED
                # file ever prints "12.57 %" the generator is broken, and that
                # must still fail.
                if generated and tok in ROUNDED:
                    continue
                # A paragraph carrying BOTH the old value and the one that
                # replaced it is a supersession record, not a stale quote --
                # otherwise the register's own before/after table, which is
                # where this list comes from, would fail the check it feeds.
                if PAIRS.get(tok) and PAIRS[tok] in para:
                    continue
                # Match on a NUMBER boundary, not a substring. Plain `in` finds
                # "6.0 %" inside "66.0 %" and reports a cost split as a stale
                # energy figure -- a false positive in a check whose only value
                # is that people believe it.
                if re.search(r"(?<![\d.])" + re.escape(tok), para) and not labelled:
                    line = text[:start].count("\n") + 1
                    check(False, f"{md.name}:~{line} quotes {tok} ({why}) "
                                 f"with nothing marking it as superseded",
                          para.strip().replace("\n", " ")[:90])

    # --- 5b. a stated provenance must actually hold ----------------------
    # Several documents carry a "Numbers used, and why these ones" table
    # whose rows name the artefact and the key each figure was taken from.
    # That is the strongest claim a document makes and nothing checked it.
    # `linkedin_post_draft.md` asserted
    #     | Annual makeup water | 12.6 % | annual_dhahran.json -> annual_water_pct_ratio_of_totals |
    # while that key held 9.23, and the draft was published in that state.
    # A cited number is WORSE than an uncited one when the citation is wrong:
    # it spends the reader's trust to carry the error.
    #
    # This check needs no list of figures. The document states where its
    # number came from; the artefact is opened and asked.
    ROW = re.compile(
        r"^\|(?P<label>[^|\n]*)\|(?P<value>[^|\n]*)\|(?P<prov>[^|\n]*)\|\s*$",
        re.MULTILINE)
    CITE = re.compile(r"`([A-Za-z0-9_]+\.json)`\s*(?:→|->)\s*`([A-Za-z0-9_.]+)`")
    for md in SCANNED:
        text = md.read_text(encoding="utf-8")
        for m in ROW.finditer(text):
            cite = CITE.search(m.group("prov"))
            if not cite:
                continue
            # A row may record what a document ONCE said, provided it says so.
            # A markdown table is a single block, and the sentence introducing
            # it is the block before -- so both are searched for a label, the
            # same allowance section 5 makes for prose.
            blk_start = text.rfind("\n\n", 0, m.start()) + 1
            ctx_start = max(0, text.rfind("\n\n", 0, blk_start - 2))
            blk_end = text.find("\n\n", m.end())
            ctx = text[ctx_start:blk_end if blk_end > 0 else len(text)].lower()
            if any(k in ctx for k in LABELS):
                continue
            fname, keypath = cite.group(1), cite.group(2)
            actual = artefact_value(f"{fname}|{keypath}")
            if actual is None:
                line = text[:m.start()].count("\n") + 1
                check(False, f"{md.name}:{line} cites {fname} -> {keypath}, "
                             f"which does not exist in the artefact")
                continue
            # the quoted figure may sit in the value cell or beside the key
            claimed = m.group("value") + " " + m.group("prov")
            if isinstance(actual, (int, float)) and not isinstance(actual, bool):
                nums = re.findall(r"[0-9]+(?:\.[0-9]+)?", claimed)
                if not nums:
                    continue
                # compare at whatever precision the document chose to quote
                ok = any(
                    abs(float(n) - round(float(actual), len(n.split(".")[1])
                                         if "." in n else 0)) < 1e-9
                    for n in nums)
                line = text[:m.start()].count("\n") + 1
                check(ok, f"{md.name}:{line} quotes {nums} for "
                          f"{fname} -> {keypath}, which holds {actual:.4g}",
                      m.group("label").strip()[:60])
            else:
                line = text[:m.start()].count("\n") + 1
                check(str(actual) in claimed,
                      f"{md.name}:{line} cites {fname} -> {keypath} = "
                      f"{actual!r}, which the row does not carry",
                      m.group("label").strip()[:60])

    # --- 5b2. a figure a document tells you to attach must exist ----------
    # `linkedin_outreach.md` and `linkedin_post_draft.md` both said
    # "Attach: figs/two_ceilings.png" for weeks. There is no such file -- the
    # figure is written by fig_water_ceiling as water_ceiling.png. A document
    # that instructs an action which cannot be performed is a defect, and it is
    # the kind nobody notices until someone is mid-post.
    # A block naming BOTH a missing figure and a real one is a record of the
    # correction, not an instruction to attach the missing file -- the same
    # allowance the supersession scan makes for the register's before/after
    # table. Without it, writing defect 18 down fails the check defect 18
    # created.
    for md in SCANNED:
        text = md.read_text(encoding="utf-8")
        for block in text.split("\n\n"):
            refs = set(re.findall(r"`figs/([A-Za-z0-9_]+\.png)`", block))
            if not refs:
                continue
            missing = {r for r in refs if not (ROOT / "figs" / r).exists()}
            if missing and (refs - missing):
                continue
            for figref in missing:
                check(False, f"{md.name} references figs/{figref}, "
                             f"which does not exist")

    # --- 5c. a run transcript must not be older than what the run wrote ---
    # `results/` holds the JSON artefacts AND the captured stdout of the
    # scripts that write them. The JSON was regenerated when defects 7 and 11
    # were fixed; the transcripts were not, because nothing regenerates them
    # and no check looked. So `calib_out.txt` sat in the results directory
    # recording
    #     V2 water  evap MAPE  7.11 <= 8.00 %  PASS
    # while `calibration.json` beside it held 9.90 -- a FAIL. A file shaped
    # like an artefact, stored with the artefacts, asserting a pass on a gate
    # that fails is the most dangerous single object in this repository, and
    # the audit that exists to prevent exactly that was only reading docs/.
    TRANSCRIPTS = {
        "calib_out.txt": "calibration.json",
        "controller_out.txt": "controller_summary.json",
        "annual_rerun.log": "annual_dhahran.json",
        "fill_law_out.txt": "fill_law_decision.json",
        "drift_out.txt": "drift.json",
        "uncertainty_out.txt": "uncertainty.json",
    }
    for txt, js in TRANSCRIPTS.items():
        tp, jp = RESULTS / txt, RESULTS / js
        if not (tp.exists() and jp.exists()):
            continue
        check(tp.stat().st_mtime >= jp.stat().st_mtime - 2,
              f"results/{txt} is older than results/{js}, so it is the "
              f"transcript of a run that has since been superseded",
              "re-run the script and capture its output again")

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
    # The counter is ASSERTIONS EVALUATED, not coverage, and the two differ:
    # several call sites live inside `if violation:` branches, so they only
    # execute when they have something to report. A FAILING run therefore
    # reports MORE "checks" than a passing one -- 78 while twenty documents
    # carried stale figures, 58 once they were tagged. Comparing those two
    # numbers as if they measured the same thing is exactly the kind of quiet
    # nonsense this audit exists to catch, so it now says which it is.
    print(f"\n{CHECKS} assertions evaluated, {len(PROBLEMS)} raised.")
    print("Not a coverage figure: failure-path assertions only execute when "
          "they fire, so a failing run reports MORE than a passing one.")
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
