"""Pre-registration integrity, and agreement between documents and artefacts.

`src/audit.py` already checks that headline numbers in the documents match the
artefacts they are generated from. These tests guard the thing an audit cannot
guard against, because the audit reads the same file: that a **threshold** is
never quietly moved to turn a failure into a pass.

The single most important test in this repository is
`test_pre_registered_thresholds_have_never_moved`. Everything else is a number;
that one is the method.
"""
from __future__ import annotations

import json
import pathlib

import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

# The thresholds as registered BEFORE any fitting, transcribed here from
# docs/defect_register.md Part 2. Changing a number in this dict is changing
# the experiment after seeing the answer.
REGISTERED = {
    "makeup_water_reduction_pct_min": 15.0,
    "total_cost_reduction_pct_min": 3.0,
    "skin_SI_violations_allowed": 0,
}


def test_pre_registered_thresholds_have_never_moved(controller_summary):
    """The water gate fails at 10.83 % against 15 %. It must STAY failed.

    The threshold was mis-specified -- makeup = evaporation x C/(C-1) means
    15 % needs 8.5 cycles while gypsum saturates at 7, so no control strategy
    of any kind reaches it -- but a mis-specified pre-registration is reported,
    not rewritten. Lowering this number to 10 would turn the package's most
    honest result into its most dishonest one."""
    live = controller_summary["criteria"]
    for key, value in REGISTERED.items():
        assert live[key] == value, (
            f"pre-registered threshold {key} has moved from {value} to "
            f"{live[key]}. If this was deliberate it is no longer a "
            f"pre-registration. See docs/threshold_revision_memo.md.")

    pre = controller_summary["summary"]["pre_registered"]
    for key, value in REGISTERED.items():
        assert pre[key] == value, (
            f"the summary's own copy of {key} disagrees with the criteria "
            f"block -- the artefact is internally inconsistent")


def test_the_water_gate_verdict_on_the_validated_analysis(controller_summary):
    """V5 water FAILS at 6.65 % on the validated water analysis.

    THE THRESHOLD HAS NEVER MOVED. It is 15.0 and
    `test_pre_registered_thresholds_have_never_moved` enforces that. The
    RESULT moved three times in one day, and the order matters:

        10.83 % FAIL   original engine, original analysis
        16.84 % PASS   after defects 24 and 25 -- but still run on an analysis
                       that fails TDS closure by 22.7 % with silica carried as
                       an unmeasured zero
         6.65 % FAIL   after defect 27, on an analysis that passes all four
                       objective self-consistency checks

    **The last one is the defensible number**, because it is the only one
    computed on a water this model is entitled to run on. A 16.84 % pass
    obtained from an analysis that cannot be right is worth less than a 6.65 %
    failure obtained from one that can."""
    s = controller_summary["summary"]
    assert s["pre_registered"]["makeup_water_reduction_pct_min"] == 15.0
    # DEFECT 30, 10 Sep 2026: 6.65 -> 4.38. The water tariff had been
    # charging the wastewater-discharge fee on evaporated water, which
    # overvalued a cubic metre of makeup by about 35 %. Correcting it makes
    # water genuinely worth less, so the optimiser correctly trades water
    # saving away for energy saving. The gate fails either way, and now
    # fails by a factor of 3.4 rather than 2.3.
    assert s["water_pct"] == pytest.approx(4.38, abs=0.05)
    assert s["water_pct"] < 15.0, "V5 water fails on the validated analysis"


def test_the_cost_gate_passes_and_violations_are_zero(controller_summary):
    """The cost gate passes at 3.70 % against a 3.0 % threshold -- a margin of
    0.70 points. That is thin, and it should be reported as thin."""
    s = controller_summary["summary"]
    assert s["cost_pct"] >= s["pre_registered"]["total_cost_reduction_pct_min"]
    # DEFECT 30, 10 Sep 2026: 3.69 -> 3.91. Cost is the gate that passes,
    # and pricing makeup and discharge on their own streams widened its
    # margin over the 3.0 threshold rather than narrowing it.
    assert s["cost_pct"] == pytest.approx(3.91, abs=0.05)
    assert s["violations"] == 0, (
        "zero skin saturation violations is a PASSED gate; a non-zero count "
        "means the controller is operating past the wall it exists to respect")


def test_no_gate_revisions_have_been_recorded(controller_summary):
    assert controller_summary["summary"]["revisions"] == [], (
        "a recorded revision means a gate was re-scored; that must be a "
        "deliberate, documented act, not a silent one")


def test_energy_is_declared_a_diagnostic_not_a_gate(controller_summary):
    """Electrical power was always the first term of the objective but was
    never reported alone. Surfacing it after the fact is legitimate; attaching
    a threshold to it now would be scoring a criterion chosen once the answer
    was known."""
    status = controller_summary["summary"]["energy_pct_status"]
    assert "NOT A PRE-REGISTERED GATE" in status.upper()
    assert "energy_pct_min" not in controller_summary["criteria"], (
        "the energy figure must never acquire a threshold retroactively")


def test_the_two_ceilings_return_on_the_validated_analysis(controller_summary):
    """The two-ceilings STRUCTURE survives every correction; the numbers and
    the mineral do not.

        6 and 7, gypsum      original engine, original analysis
        12 and none          after defects 24-25, silica still carried as zero
        5 and 6, SILICA      after defect 27, on the validated analysis

    One cycle lower than the original pair, and about a different mineral.
    Amorphous silica is PROGRADE -- it binds at the COLD tower basin, not the
    hot condenser skin -- and it is pH-invariant in this model, so acid cannot
    move this wall either."""
    s = controller_summary["summary"]
    assert s["economic_ceiling_cycles"] == 5
    assert s["physical_ceiling_cycles"] == 6
    assert s["binding_mineral"] == "SI_silica_am", (
        "on a validated analysis the binding mineral is amorphous silica, not "
        "gypsum -- the product is about a different mineral than the "
        "documents were written around")


def test_annual_figures_store_both_aggregations(annual_dhahran):
    """The mean-of-ratios defect. Both must be present, and the ratio-of-totals
    figures are the ones to quote outside the repository."""
    for key in ("annual_water_pct", "annual_cost_pct", "annual_energy_pct"):
        assert key in annual_dhahran
    for key in ("annual_water_pct_ratio_of_totals",
                "annual_cost_pct_ratio_of_totals",
                "annual_energy_pct_ratio_of_totals"):
        assert key in annual_dhahran, (
            f"{key} missing -- storing only percentages makes the physically "
            "meaningful aggregation impossible to compute later")
    assert "weighting_note" in annual_dhahran


def test_the_energy_and_water_corrections_have_opposite_signs(annual_dhahran):
    """Documented in annual.py: the mean of ratios FLATTERS the energy number
    and UNDERSTATES the water one, because the percentage saving correlates
    negatively with load for energy and positively for water."""
    d = annual_dhahran
    e_corr = d["annual_energy_pct_ratio_of_totals"] - d["annual_energy_pct"]
    w_corr = d["annual_water_pct_ratio_of_totals"] - d["annual_water_pct"]
    assert e_corr * w_corr < 0.0, (
        f"corrections must have opposite signs; energy {e_corr:+.3f}, "
        f"water {w_corr:+.3f}")


def test_field_validation_is_labelled_a_retrodiction(field_validation):
    """The gate was written after the observation was found. It must never be
    quoted as a pre-registered prediction, and the artefact must say so."""
    assert "RETRODICTION" in field_validation["status"].upper()
    assert field_validation["n_passed"] < field_validation["n_total"], (
        "F2 failed and is reported as failed; a clean sweep here would mean "
        "the retrodiction had been tuned")


def test_field_validation_failure_is_not_rescored(field_validation):
    note = field_validation["reported_diagnostic"]["note"]
    assert "NOT rescored" in note or "not rescored" in note.lower()


def test_corrosion_floor_sweep_covers_observed_practice(corrosion_floor):
    """A plant chemist holds LSI 0.8-1.0 deliberately. The sweep must reach
    that far or it does not answer the objection."""
    floors = [r["floor"] for r in corrosion_floor["rows"] if r["floor"] is not None]
    assert max(floors) >= 1.0, (
        "the corrosion floor must be swept to at least LSI 1.0, the top of "
        "the band a real plant chemist holds")
    assert all(r["feasible"] for r in corrosion_floor["rows"]), (
        "if a floor inside observed practice makes the optimum infeasible, "
        "that is a finding and this test should be updated to record it")


# ---------------------------------------------------------------------------
# Cross-document consistency the audit does not currently cover
# ---------------------------------------------------------------------------
# Extend this as defects are found. A count above the top of this dict is not
# matched at all, which makes the guard silently blind -- the exact failure
# mode of defect 21, where a staleness guard could not reach part of what it
# was meant to police.
# DEFECT 41. This table stopped at "thirty", so from defect 31 onward every
# document could disagree and the test SKIPPED instead of failing -- with a
# message, "no defect-count claims found to compare", that read like an
# absence of claims rather than a parser that had run out of vocabulary. The
# guard disabled itself precisely when the number it guards started moving.
#
# Same shape as defect 12 and as the register's own note on second-order
# staleness: a constant duplicated into files that other files are validated
# against. Generated to a hundred now, and `_declared_defect_counts` refuses
# to skip while the register plainly states a count.
_UNITS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
          "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
          "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
_TENS = {20: "twenty", 30: "thirty", 40: "forty", 50: "fifty", 60: "sixty",
         70: "seventy", 80: "eighty", 90: "ninety"}


def _spell(n):
    if n < 20:
        return _UNITS[n]
    tens, unit = divmod(n, 10)
    base = _TENS[tens * 10]
    return base if not unit else f"{base}-{_UNITS[unit]}"


WORDS = {_spell(n): n for n in range(10, 100)}


# Documents whose JOB is to quote the disagreement are not making a claim of
# their own. Excluding them by name, so the exclusion is visible rather than
# hidden in a heuristic.
_REPORTS_THE_PROBLEM = {"datacentre_strategy.md"}


def _declared_defect_counts():
    """Every 'N defects were found' claim across the documents, as (file, n).

    Alternatives are sorted longest-first: with 'twenty' ahead of 'twenty-one'
    the regex matches the prefix and silently reports 20 for a line that says
    twenty-one. That is the same class of bug this test exists to catch, so it
    is worth naming here.
    """
    import re
    alts = "|".join(sorted(WORDS, key=len, reverse=True))
    pat = re.compile(
        r"\b(" + alts + r")\b[^.|\n]{0,40}?\bdefects?\b"
        r"[^.|\n]{0,40}?\b(?:found|were found)\b", re.I)
    pat2 = re.compile(r"\b(" + alts + r")\b\s+found\b", re.I)
    out = []
    for p in sorted(DOCS.glob("*.md")) + [ROOT / "HANDOFF.md"]:
        if not p.exists() or p.name in _REPORTS_THE_PROBLEM:
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        for line_no, line in enumerate(txt.splitlines(), 1):
            if line.lstrip().startswith("|"):     # a table quoting others
                continue
            for m in list(pat.finditer(line)) + list(pat2.finditer(line)):
                out.append((f"{p.name}:{line_no}", WORDS[m.group(1).lower()]))
    return out


def test_every_document_agrees_on_how_many_defects_were_found():
    """audit.py checks that the register's declared OPEN count matches its OPEN
    rows, but nothing checks the TOTAL across documents -- and the total is the
    number that moves every time a defect is found.

    This is the same second-order staleness the register itself documents as
    defect 12: a constant duplicated into files that other files are validated
    against is a slow-acting fault."""
    counts = _declared_defect_counts()
    if not counts:
        # DEFECT 41. Skipping here is only honest if no document claims a
        # count. The register always does, so failing to parse one means the
        # PARSER is broken, not that the claims are absent -- and that is the
        # failure mode this test spent ten defects in.
        reg = (DOCS / "defect_register.md").read_text(encoding="utf-8",
                                                      errors="replace")
        assert not re.search(r"\bdefects?\b[^.\n]{0,40}\bfound\b", reg, re.I), (
            "docs/defect_register.md states a defect count that this test "
            "could not parse. The vocabulary in WORDS has run out again -- "
            "extend it rather than letting the check skip.")
        pytest.skip("no defect-count claims found to compare")
    distinct = sorted({n for _, n in counts})
    assert len(distinct) == 1, (
        "documents disagree on the number of defects found: "
        + "; ".join(f"{where} says {n}" for where, n in counts)
        + f"\n  distinct values: {distinct}")


def test_the_cofounder_facing_document_does_not_claim_zero_open_defects():
    """docs/ENGINEERING_IN_PLAIN_ENGLISH.md is what the two non-technical
    co-founders read before speaking to a customer. If defect 17 is open, that
    document must not say otherwise -- the open one is the sulfate number the
    entire gypsum wall rests on."""
    p = DOCS / "ENGINEERING_IN_PLAIN_ENGLISH.md"
    if not p.exists():
        pytest.skip("plain-English document not present")
    txt = p.read_text(encoding="utf-8", errors="replace").lower()
    reg = (DOCS / "defect_register.md").read_text(encoding="utf-8",
                                                  errors="replace")
    register_has_open = "**OPEN**" in reg or "| **OPEN**" in reg
    if register_has_open:
        assert "none open" not in txt, (
            "the register declares an open defect but the co-founder-facing "
            "document says 'none open'")


# ---------------------------------------------------------------------------
# The physics-informed surrogate: its own pre-registered gates
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def pinn():
    p = ROOT / "results" / "pinn.json"
    if not p.exists():
        pytest.skip("results/pinn.json not present -- run src/pinn.py")
    return json.loads(p.read_text(encoding="utf-8"))


def test_pinn_gate_thresholds_have_not_moved(pinn):
    """Thresholds fixed and printed before training. Three defects were found
    during that training -- a contradictory collocation sampler, an untrained
    evaporation head, and an output range that could not represent 60 % of its
    own data -- and NO threshold was moved for any of them. Each failure was
    traced to a defect, the defect was fixed, and the run was re-scored."""
    assert pinn["gates"] == {
        "P1_core_Tout_MAE_K_max": 0.1,
        "P1_core_evap_MAPE_pct_max": 1.0,
        "P2_holdout_Tout_MAE_K_max": 0.6,
        "P3_extrap_violations_max": 0,
        "P4_speedup_min": 500.0,
    }, "a surrogate gate threshold has moved"


def test_pinn_gates_all_pass(pinn):
    g, r = pinn["gates"], pinn["results"]
    assert r["P1_core_Tout_MAE_K"] <= g["P1_core_Tout_MAE_K_max"]
    assert r["P1_core_evap_MAPE_pct"] <= g["P1_core_evap_MAPE_pct_max"]
    assert r["P3_extrap_violations"] <= g["P3_extrap_violations_max"]
    assert r["P4_speedup"] >= g["P4_speedup_min"]


def test_the_surrogate_violates_no_physical_constraint_when_extrapolating(pinn):
    """P3 is the gate that matters for control: at Gulf wet-bulbs the training
    data never reached, every individual admissibility constraint must be
    clean, not merely the total."""
    for name, n in pinn["results"]["P3_breakdown"].items():
        assert n == 0, f"surrogate violates {name} in {n} of 5,000 samples"


def test_the_surrogate_is_declared_subordinate_to_the_core(pinn):
    """It is scored against the physics core, not against experiment, so it
    inherits every limitation of the core and adds its own. The artefact must
    keep saying so -- a surrogate that quietly becomes the authority on a
    saturation limit is the failure mode this note exists to prevent."""
    note = pinn["note"].lower()
    assert "never the authority on a safety constraint" in note


def test_corrosion_floor_is_swept_across_every_scored_condition():
    """The one-condition sweep in results/corrosion_floor.json found the
    optimum completely insensitive to the floor. That is a strong claim from
    thin evidence, so src/corrosion_floor_conditions.py repeats it at all five
    conditions the V5 gate scores.

    If the floor BINDS anywhere, it has a price, and that price belongs in
    commercialisation.md rather than in a footnote."""
    p = ROOT / "results" / "corrosion_floor_conditions.json"
    if not p.exists():
        pytest.skip("run src/corrosion_floor_conditions.py")
    d = json.loads(p.read_text(encoding="utf-8"))

    scored = {c["condition"] for c in d["conditions"]}
    assert len(scored) == 5, (
        f"the sweep must cover all five V5 conditions, got {sorted(scored)}")

    binding = d.get("binding_conditions", [])
    assert d["C1_floor_never_binds"] == (not binding)
    if binding:
        pytest.fail(
            "the corrosion floor BINDS at " + ", ".join(binding) +
            " -- this is a finding, not a test bug. Price it in "
            "commercialisation.md, then update this test to record the "
            "expected binding set.")
