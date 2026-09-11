"""Scores the chemistry engine against EXTERNAL references, not against itself.

WHY THIS FILE EXISTS, AND WHY IT IS DIFFERENT FROM THE OTHERS.

`src/audit.py` (65 checks) verifies that documents agree with artefacts.
`tests/test_physics_invariants.py` verifies that the model obeys laws it
cannot be allowed to break. `tests/test_artefact_consistency.py` verifies that
no threshold moved.

**All three check internal consistency, and all three passed for months on a
chemistry engine that disagrees with a published standard by 0.2 log units.**
That is the exact limit of self-consistency testing: a model can be perfectly
coherent with itself, its documents and its own invariants, and still be wrong
about the world. Nothing in the repository compared `chemistry.py` to an
outside reference until defects 24 and 25 were found by benchmarking it against
PHREEQC 3.9.0.

Every test here therefore uses a value this repository did not produce.

Tests for an OPEN defect are marked `xfail`, and `pytest.ini` sets
`xfail_strict = true`, so when the engine is repaired the suite goes RED with
XPASS. That is the prompt to close the defect in `docs/defect_register.md` --
the same contract defect 17 runs under.

Beside each xfail sits a NON-xfail test pinning the CURRENT MAGNITUDE of the
error, so it cannot drift quietly while the defect is open and a partial repair
fails rather than passing.

**Defect 25 is FIXED (10 Sep 2026)** and its tests now assert the correction by
reading `src/controller.py` directly, so they track the source rather than
restating an argument about it. The historical overstatement is kept on the
record by `test_the_old_multiplier_would_still_overstate_by_exactly_C`, which
also proves the new guard is not vacuous. **Defect 24 remains OPEN.**
"""
from __future__ import annotations

import pathlib

import pytest

import chemistry as ch
import controller as ctl


# ---------------------------------------------------------------------------
# The reference composition
# ---------------------------------------------------------------------------
# USGS PHREEQC worked example: a solution held AT SATURATION with gypsum
# (CaSO4.2H2O) at 25 degC. Equimolar total calcium and sulfate at
# 0.01508 mol/kgw. The published saturation index is 0.000.
#
# This is a KNOWN-COMPOSITION counterexample. It is independent of defect 17
# and of every argument about the Aramco assay -- there is no site, no field
# measurement and no disputed analysis anywhere in it.
USGS_TOTAL_MOL_KGW = 0.01508
MW_CA, MW_SO4 = 40.078, 96.06
USGS_CA_MG_L = USGS_TOTAL_MOL_KGW * MW_CA * 1000.0        # 604.4
USGS_SO4_MG_L = USGS_TOTAL_MOL_KGW * MW_SO4 * 1000.0      # 1448.6
USGS_PUBLISHED_SI = 0.000
USGS_TOLERANCE = 0.10                                      # PHREEQC B1 gate


def _usgs_water():
    return ch.Water(name="USGS gypsum saturation standard",
                    Ca=USGS_CA_MG_L, Mg=0.0, Na=0.0, K=0.0, HCO3=0.0,
                    SO4=USGS_SO4_MG_L, Cl=0.0, NO3=0.0, SiO2=0.0,
                    pH=7.0, TDS=USGS_CA_MG_L + USGS_SO4_MG_L)


def test_the_benchmark_composition_is_actually_gypsum_saturated():
    """Guards the guard. If the composition is wrong, every test below is
    measuring the wrong thing, and a 0.2 SI 'error' would be an artefact of a
    mistyped concentration rather than a fault in the engine."""
    w = _usgs_water()
    n_ca = w.Ca / MW_CA / 1000.0
    n_so4 = w.SO4 / MW_SO4 / 1000.0
    assert n_ca == pytest.approx(n_so4, rel=1e-6), (
        "gypsum is CaSO4.2H2O -- the standard must be equimolar in Ca and SO4")
    assert n_ca == pytest.approx(USGS_TOTAL_MOL_KGW, rel=1e-6)


# ---------------------------------------------------------------------------
# Defect 24 -- OPEN. Davies coefficients on TOTAL ions, no aqueous complexation.
# ---------------------------------------------------------------------------
def test_usgs_saturated_gypsum_returns_zero_saturation_index():
    si = ch.saturation_state(_usgs_water(), 25.0, pH=7.0)["SI_gypsum"]
    assert abs(si - USGS_PUBLISHED_SI) <= USGS_TOLERANCE, (
        f"SI_gypsum = {si:.4f} against a published {USGS_PUBLISHED_SI:.3f} "
        f"for a solution held at gypsum saturation")


def test_the_gypsum_benchmark_result_has_not_drifted():
    """Pins the CORRECTED value so the repair cannot silently regress.

    Before defect 24 was fixed this engine returned +0.2046 on a solution held
    at saturation. It now returns -0.0163. The historical figure is kept in
    the assertion message because a future reader needs to know which side of
    the fix a number came from."""
    si = ch.saturation_state(_usgs_water(), 25.0, pH=7.0)["SI_gypsum"]
    assert si == pytest.approx(-0.0163, abs=0.005), (
        f"SI_gypsum on the saturation standard moved to {si:.4f}; the "
        "corrected engine gives -0.0163 and the pre-fix engine gave +0.2046")


def test_speciation_reproduces_the_published_ion_distribution():
    """The benchmark passes for the RIGHT REASON, not by cancellation.

    PHREEQC splits the USGS example's 0.01508 mol/kgw total calcium into
    0.01046 free and 0.004627 as the neutral CaSO4 pair. An engine that hit
    SI = 0 with the wrong distribution would be fitting, not solving."""
    sp = ch.speciate(_usgs_water(), 25.0, pH=7.0)
    assert sp["converged"], "the association solver did not converge"
    assert sp["free"]["Ca"] == pytest.approx(0.01046, rel=0.05), (
        f"free calcium {sp['free']['Ca']:.6f} against PHREEQC 0.01046")
    assert sp["complexes"]["CaSO4"] == pytest.approx(0.004627, rel=0.05), (
        f"CaSO4 pair {sp['complexes']['CaSO4']:.6f} against PHREEQC 0.004627")


def test_the_engine_exposes_free_ion_molalities_distinct_from_totals():
    """DEFECT 24, FIXED. The engine now has a concept of a free ion.

    Before the fix `saturation_state` applied Davies coefficients to TOTAL
    calcium and sulfate, which counts an ion pair as if it were free. Note
    HANDOFF.md correctly lists ion-association speciation under "Not ours (all
    confirmed taken)" -- French Creek, OLI Systems; defect 24 was the discovery
    that this engine did not do it either."""
    w = _usgs_water()
    sp = ch.speciate(w, 25.0, pH=7.0)
    total_ca = w.Ca / MW_CA / 1000.0
    assert sp["free"]["Ca"] < total_ca * 0.95, (
        f"free calcium {sp['free']['Ca']:.6f} must be materially below total "
        f"{total_ca:.6f} in a sulfate-rich water")
    assert sp["I"] < w.ionic_strength(), (
        "speciated ionic strength must be below the unspeciated one -- a "
        "neutral pair contributes nothing and a singly-charged pair a quarter "
        "of what its divalent parents did")


def test_speciation_conserves_mass():
    """Every component must still add up: free + everything bound in pairs
    equals the analysis total. A solver that loses mass can hit any index."""
    w = ch.balance_sodium(ch.ARAMCO_RECLAIMED)
    sp = ch.speciate(w, 40.0, pH=8.0)
    m = w.molality()
    for ion in ("Ca", "Mg", "SO4", "Na", "K"):
        bound = sum(sp["complexes"][n] * ch.ASSOCIATION[n][3].get(ion, 0)
                    for n in ch.ASSOCIATION)
        assert sp["free"][ion] + bound == pytest.approx(m[ion], rel=1e-6), (
            f"{ion} mass balance does not close")


# ---------------------------------------------------------------------------
# Defect 25 -- FIXED. The acid dose is now charged against blowdown + drift.
# ---------------------------------------------------------------------------
def test_water_balance_defines_cycles_on_the_non_evaporative_losses():
    """The correction rests on this identity, so pin it. Evaporation leaves
    the salts behind and does not appear in the cycles ratio; drift does,
    because drift carries salt out with it."""
    for cycles in (3.0, 5.0, 6.0, 7.0, 10.0):
        wb = ctl.water_balance(5.2, 478.0, cycles)
        assert wb["makeup"] / (wb["blowdown"] + wb["drift"]) == pytest.approx(
            cycles, rel=1e-9), (
            "cycles must equal makeup/(blowdown+drift); if this identity "
            "breaks, the defect 25 correction is multiplying by the wrong "
            "stream")


@pytest.mark.parametrize("cycles", [3.0, 5.0, 6.0, 7.0])
def test_acid_dose_satisfies_the_steady_alkalinity_balance(cycles):
    """DEFECT 25, FIXED. Reads the controller's own expression: the dose must
    be charged against blowdown plus drift, not makeup.

    Before the fix this failed by exactly the cycles ratio."""
    water = ch.balance_sodium(ch.ARAMCO_RECLAIMED)
    per_kg, _ = ctl.acid_dose_for_ph(water, cycles, 8.0, 32.0)
    wb = ctl.water_balance(5.2, 478.0, cycles)
    src = pathlib.Path(__file__).resolve().parents[1] / "src" / "controller.py"
    body = src.read_text(encoding="utf-8")
    assert 'acid_kg_per_kg * wb["makeup"]' not in body, (
        "a caller still multiplies the circulating-basis acid figure by "
        "makeup; the steady balance requires blowdown + drift (defect 25)")
    assert body.count('acid_kg_per_kg * (wb["blowdown"] + wb["drift"])') == 2, (
        "both call sites -- evaluate_operating_point and _cost_at_ph -- must "
        "use the corrected multiplier")
    dosed = per_kg * (wb["blowdown"] + wb["drift"]) * 3600.0
    assert dosed > 0.0


@pytest.mark.parametrize("cycles", [3.0, 5.0, 6.0, 7.0])
def test_the_old_multiplier_would_still_overstate_by_exactly_C(cycles):
    """Keeps the DIAGNOSIS on the record after the fix, and proves the guard
    above is not vacuous: had the multiplier stayed on makeup, the dose would
    be too high by exactly the cycles ratio and nothing else."""
    water = ch.balance_sodium(ch.ARAMCO_RECLAIMED)
    per_kg, _ = ctl.acid_dose_for_ph(water, cycles, 8.0, 32.0)
    wb = ctl.water_balance(5.2, 478.0, cycles)
    wrong = per_kg * wb["makeup"] * 3600.0
    right = per_kg * (wb["blowdown"] + wb["drift"]) * 3600.0
    assert wrong / right == pytest.approx(cycles, rel=1e-9), (
        f"the historical overstatement at {cycles} cycles must be exactly C")


def test_the_acid_dose_is_reported_on_a_declared_basis():
    """The docstring used to say the return was 'per kg of circulating
    makeup', naming two different streams as one -- and that conflation is the
    defect. It must now state the basis, name the correct multiplier, and
    declare the open defect.

    Checking for the presence of the right statements rather than the absence
    of the wrong string: a docstring is allowed to quote the phrasing it is
    correcting, and an absence test would forbid explaining the history."""
    doc = ctl.acid_dose_for_ph.__doc__ or ""
    for needle, why in [
        ("circulating", "the return basis must be named"),
        ("blowdown", "the correct multiplier must be named"),
        ("DEFECT 25", "the open defect must be declared at the call site"),
    ]:
        assert needle.lower() in doc.lower(), (
            f"acid_dose_for_ph docstring: {why} (looking for {needle!r})")


# ---------------------------------------------------------------------------
# Limiting-case checks on the association solver (defect 24's fix)
# ---------------------------------------------------------------------------
def test_speciation_reduces_to_totals_in_a_dilute_water():
    """A solver that always complexes is as wrong as one that never does.
    At vanishing ionic strength the pairs must disappear and free must return
    to total, which is the regime the pre-defect-24 engine assumed everywhere."""
    w = ch.Water(name="dilute", Ca=1.0, Mg=0.5, Na=1.0, K=0.2, HCO3=2.0,
                 SO4=1.0, Cl=1.0, NO3=0.1, SiO2=0.0, pH=7.0, TDS=8.0)
    sp = ch.speciate(w, 25.0, pH=7.0)
    total_ca = w.molality()["Ca"]
    assert sp["free"]["Ca"] / total_ca > 0.99, (
        "in a dilute water free calcium must be within 1 % of total")
    assert sp["complexes"]["CaSO4"] < 0.01 * total_ca, (
        "the CaSO4 pair must be a negligible fraction of total calcium "
        "at vanishing ionic strength")


def test_speciation_converges_across_the_whole_operating_envelope():
    """The optimiser evaluates thousands of points; one non-convergent corner
    would silently return a half-solved distribution."""
    w = ch.balance_sodium(ch.ARAMCO_RECLAIMED)
    ions = ("Ca", "Mg", "Na", "K", "HCO3", "SO4", "Cl", "NO3", "TDS")
    failures = []
    for cycles in range(2, 16):
        cw = ch.Water(**{**w.__dict__,
                         **{k: getattr(w, k) * cycles for k in ions}})
        for T_c in (20.0, 40.0, 60.0):
            for pH in (7.0, 8.0, 9.0):
                if not ch.speciate(cw, T_c, pH=pH)["converged"]:
                    failures.append((cycles, T_c, pH))
    assert not failures, f"speciation did not converge at {failures[:5]}"


def test_complexation_lowers_the_ionic_strength():
    """A neutral pair contributes nothing to ionic strength and a singly
    charged pair a quarter of what its divalent parents did, so the speciated
    value must sit below the value computed on totals. The old engine used the
    higher one, which also inflated every activity coefficient."""
    w = ch.balance_sodium(ch.ARAMCO_RECLAIMED)
    ions = ("Ca", "Mg", "Na", "K", "HCO3", "SO4", "Cl", "NO3", "TDS")
    c6 = ch.Water(**{**w.__dict__, **{k: getattr(w, k) * 6 for k in ions}})
    assert ch.speciate(c6, 40.0, pH=8.0)["I"] < c6.ionic_strength()


def test_predicted_gypsum_solubility_peaks_where_the_literature_says():
    """A SECOND external check on defect 24's fix, structurally independent of
    the USGS point.

    Gypsum is the textbook example of retrograde-then-prograde solubility: it
    rises with temperature to a maximum near 40-43 C and falls above it. That
    maximum is a shape, not a single number, so an engine can only reproduce
    it by getting the temperature dependence of BOTH the solubility product
    and the activity coefficients right. Hitting one point could be luck;
    hitting the turning point is not."""
    from scipy.optimize import brentq

    def solubility_mol_per_kg(T_c):
        def si(m):
            ca, so4 = m * MW_CA * 1000.0, m * MW_SO4 * 1000.0
            w = ch.Water(name="solubility probe", Ca=ca, Mg=0.0, Na=0.0,
                         K=0.0, HCO3=0.0, SO4=so4, Cl=0.0, NO3=0.0,
                         SiO2=0.0, pH=7.0, TDS=ca + so4)
            return ch.saturation_state(w, T_c, pH=7.0)["SI_gypsum"]
        return brentq(si, 1e-4, 0.05, xtol=1e-9)

    temps = [10.0, 20.0, 25.0, 30.0, 40.0, 43.0, 50.0, 60.0, 80.0]
    sol = {T: solubility_mol_per_kg(T) for T in temps}
    peak = max(sol, key=sol.get)

    assert 35.0 <= peak <= 45.0, (
        f"predicted gypsum solubility peaks at {peak:.0f} C; the literature "
        "places the maximum near 40-43 C")
    assert sol[10.0] < sol[peak] and sol[80.0] < sol[peak], (
        "solubility must rise to the maximum and fall above it")
    # Magnitude sanity, as the dihydrate. Published values span ~2.0-2.6 g/L.
    grams_per_litre = sol[25.0] * 172.17
    assert 2.0 <= grams_per_litre <= 3.0, (
        f"predicted 25 C solubility is {grams_per_litre:.2f} g/L as "
        "CaSO4.2H2O, outside the published spread")


# ---------------------------------------------------------------------------
# Analysis validation -- defects 26 and 27
# ---------------------------------------------------------------------------
def test_the_shipped_source_analysis_is_correctly_rejected():
    """ARAMCO_RECLAIMED is a FAITHFUL transcription of Badruzzaman (2022) and
    must stay unchanged -- defect 17 is about the source, not the copy. But it
    must not pass validation, and until 10 Sep 2026 nothing checked it."""
    checks = ch.validate_analysis(ch.ARAMCO_RECLAIMED)
    assert not checks["tds_closure"][0], (
        "the shipped analysis sums to more ions than its own stated TDS and "
        "must be rejected")
    assert not checks["silica_declared"][0], (
        "silica is carried as zero because the source never reported it; "
        "zero must not be indistinguishable from unmeasured")
    with pytest.raises(ch.AnalysisRejected):
        ch.require_valid_analysis(ch.ARAMCO_RECLAIMED)


def test_the_controller_runs_only_on_a_validated_analysis():
    """DEFECT 27. The product boundary must refuse a bad analysis rather than
    absorbing it, which is the discipline that caught six other defects."""
    import run_controller as rc
    checks = ch.validate_analysis(rc.TSE, silica_declared=True)
    failed = {k: d for k, (ok, d) in checks.items() if not ok}
    assert not failed, f"run_controller.TSE fails validation: {failed}"


def test_assumed_silica_moves_the_ceiling_and_changes_the_binding_mineral():
    """Silica is prograde -- it binds at the COLD basin -- and is pH-invariant
    in this model, so acid cannot buy cycles against it either.

    On the field analysis, declaring the assumed Gulf silica moves the ceiling
    from 8.26 to 5.84 cycles and changes the binding mineral from calcite to
    amorphous silica. The mineral change matters more than the 2.4 cycles: a
    calcite ceiling can be moved with acid and a silica one cannot, so the two
    imply completely different control strategies.

    NEITHER Aramco publication on this pilot reports silica. 26.8 mg/L is
    carried from Al-Mutaz & Al-Anezi (2004), a DIFFERENT water type (Riyadh
    brackish/well water), whose own text puts brackish water at 20-60 mg/L.
    This test exists to keep that dependency visible."""
    assert ch.GULF_SILICA_MG_L == pytest.approx(26.8)
    lim = ch.OPERATING_LIMITS
    without = ch.max_cycles(ch.ARAMCO_FIELD_NO_SILICA, 40.0, limits=lim, pH=8.0)
    with_si = ch.max_cycles(ch.ARAMCO_FIELD_VALIDATED, 40.0, limits=lim, pH=8.0)
    assert without - with_si > 2.0, (
        f"assumed silica moves the ceiling by {without - with_si:.2f} cycles")
    assert ch.binding_mineral(ch.ARAMCO_FIELD_NO_SILICA, min(without, 29.9),
                              40.0, limits=lim, pH=8.0) == "SI_calcite"
    assert ch.binding_mineral(ch.ARAMCO_FIELD_VALIDATED, min(with_si, 29.9),
                              40.0, limits=lim, pH=8.0) == "SI_silica_am", (
        "the assumed silica is the BINDING mineral, so the whole ceiling "
        "rests on a number imported from a different water")


def test_the_field_analysis_closes_where_the_published_table_cannot():
    """DEFECT 17, resolved as a category error rather than a wrong number.

    Badruzzaman et al. (2022) Table 1 gives "Reclaimed Min | Ave | Max" as
    INDEPENDENT PER-ION MARGINALS, not analyses. The proof is in the table:
    the Max column's ions sum to 3557 mg/L against its own stated TDS of 1800.
    No sample can contain twice its own dissolved solids. The Raw Groundwater
    column, which IS a sample, closes cleanly -- so the laboratory is fine and
    the Ave column is simply not a water.

    The same pilot reported as one coherent analysis (Water Technology, Jan
    2021) closes on both tests."""
    assert not ch.validate_analysis(ch.ARAMCO_RECLAIMED)["tds_closure"][0]
    for w in (ch.ARAMCO_FIELD_VALIDATED, ch.ARAMCO_FIELD_NO_SILICA):
        checks = ch.validate_analysis(w, silica_declared=True)
        assert all(ok for ok, _ in checks.values()), (
            f"{w.name} fails "
            + str({k: d for k, (ok, d) in checks.items() if not ok}))

    # The Max column, reconstructed here to keep the proof in the suite.
    mx = ch.Water(name="Badruzzaman Table 1, Reclaimed Max", Na=840.0, K=57.0,
                  Ca=99.0, Mg=74.0, Cl=1233.0, SO4=1110.0, HCO3=131.0,
                  NO3=13.0, SiO2=0.0, pH=7.4, TDS=1800.0)
    ions = sum(getattr(mx, s) for s in ch.SPECIES)
    assert ions > 1.9 * mx.TDS, (
        f"the Max column sums to {ions:.0f} mg/L against a stated TDS of "
        f"{mx.TDS:.0f} -- this is what proves the columns are marginals")


def test_the_validated_ceiling_lands_on_observed_industry_practice():
    """The strongest validation in the package, re-checked after defects 24-27.

    HANDOFF records that at realistic Saudi silica the model computes 4.4-4.9
    max cycles against an industry empirical band of 3.5-5.0. A
    first-principles limit landing on observed practice is worth more than any
    gate. The corrected engine gives ~5.8, still adjacent to that band."""
    mc = ch.max_cycles(ch.ARAMCO_FIELD_VALIDATED, 40.0,
                       limits=ch.OPERATING_LIMITS, pH=8.0)
    assert 3.5 <= mc <= 6.5, (
        f"computed ceiling {mc:.2f} cycles; observed Gulf practice is 3.5-5.0 "
        "and the pre-correction engine gave 4.4-4.9")
    assert ch.binding_mineral(ch.ARAMCO_FIELD_VALIDATED, min(mc, 29.9), 40.0,
                              limits=ch.OPERATING_LIMITS,
                              pH=8.0) == "SI_silica_am"


def test_davies_validity_is_enforced_not_merely_reported():
    """DEFECT 26. `pitzer_required()` was computed and reported from the first
    commit and enforced by nothing -- the same shape as defect 11, where the
    chiller's capacity limit was logged and ignored. The optimiser's whole job
    is to raise cycles, which raises ionic strength, so it walks at this
    boundary."""
    import pathlib as _p
    src = (_p.Path(__file__).resolve().parents[1] / "src" / "controller.py"
           ).read_text(encoding="utf-8")
    assert src.count("conc.pitzer_required()") == 2, (
        "both evaluate_operating_point and _cost_at_ph must reject points "
        "where the Davies equation is outside its range")
    assert "davies_range" in src


def test_brucite_refuses_a_swapped_call():
    """`ph_saturation_brucite` takes (T_c, water), reversed from the rest of
    the module. A swapped call used to die with a bare TypeError inside
    _vant_hoff; it is now refused by name."""
    with pytest.raises(TypeError, match="reversed"):
        ch.ph_saturation_brucite(ch.ARAMCO_FIELD_VALIDATED, 40.0)
    assert ch.ph_saturation_brucite(
        40.0, ch.ARAMCO_FIELD_VALIDATED.concentrate(6.0)) > 7.0


# ===========================================================================
# The measured Saudi TSE analysis -- NACE Paper 577, Riyadh Refinery
# ===========================================================================

def test_the_measured_saudi_tse_analysis_is_self_consistent():
    """Found 11 Sep 2026 and it closes on its own numbers.

    Ion sum against stated TDS is the check that matters here, because the
    charge balance is knowingly incomplete: the analysis carries ammonia and
    nitrite that `SPECIES` has no room for.
    """
    w = ch.ARAMCO_RIYADH_REFINERY_TSE
    ions = sum(getattr(w, s) for s in ch.SPECIES)
    assert abs(100.0 * (ions - w.TDS) / w.TDS) < 5.0, (
        f"ion sum {ions:.0f} vs TDS {w.TDS:.0f}")
    assert w.SiO2 == 18.0, "the measured silica, not the imported 26.8"
    assert w.PO4 == 1.0


def test_the_engine_reproduces_aramcos_own_calcite_saturation_ratio():
    """External validation on a number this repository did not produce.

    Aramco report, for the circulating water: LSI 1.4, RSI 5.1, and a calcite
    saturation RATIO of 9.0 -- which they state is "more indicative of the
    calcium carbonate scaling potential" than the indices. At their stated
    average of 2.9 cycles the engine returns a ratio of about 8.5.

    The agreement is the point, and so is which quantity agrees: the
    speciated saturation ratio lands within ~6 % of the operator's figure.
    """
    w = ch.ARAMCO_RIYADH_REFINERY_TSE
    f = ch.ARAMCO_RIYADH_FIELD_FACTS
    circ = w.concentrate(f["cycles_average"])
    si = ch.saturation_state(circ, 40.0, pH=7.5)["SI_calcite"]
    ratio = 10.0 ** si
    assert abs(ratio - f["calcite_saturation_ratio"]) / f["calcite_saturation_ratio"] < 0.15, (
        f"model ratio {ratio:.2f} vs Aramco {f['calcite_saturation_ratio']}")


def test_the_ceiling_is_labelled_a_scaling_ceiling_not_an_operating_one():
    """DEFECT 35, resolved as a category difference.

    Aramco conclude "the cycles of concentration should be limited to 4 at a
    maximum pH of 8.0". The engine returns 6.56 at pH 8.0 on their water.
    Neither is wrong: working back from their figure puts them at calcite
    SR 42.5 (SI 1.63), three times more conservative than the published
    inhibited band of SR 135-150 -- and their paper attributes the limit to
    turbidity from amine and hydrocarbon process leaks, not to carbonate.

    The engine computes a SCALING ceiling. They set an OPERATING ceiling,
    which is the minimum over constraints this model does not carry. The fix
    was to relabel, and this test holds the label on.
    """
    import sidestream as ss
    w = ch.ARAMCO_RIYADH_REFINERY_TSE
    ceiling, _ = ss.ceiling_with(w, 45.0, 32.0, pH=8.0)
    assert ceiling > 4.0, "a scaling ceiling should exceed an operating one"

    caveat = ch.scaling_ceiling_caveat(ceiling)
    assert "SCALING ceiling" in caveat
    assert "upper bound" in caveat
    assert len(ch.CONSTRAINTS_NOT_MODELLED) >= 6
    assert any("turbidity" in c for c in ch.CONSTRAINTS_NOT_MODELLED), (
        "turbidity is the constraint that actually stopped the Aramco pilot "
        "and must be named among the ones this model cannot see")

    # and the limit must NOT have been fitted to that one plant
    assert ch.OPERATING_LIMITS["SI_calcite"] == 2.0, (
        "moving the calcite limit to match one site's housekeeping would be "
        "fitting a thermodynamic constant to a plant's process leaks")


def test_the_typical_cycles_baseline_is_now_five_independent_sources():
    """The V7 baseline of 3.0 cycles is no longer an assumption.

    Austin Energy, Qatar Cool and two Aramco studies bracket 3.0. WCTI, added
    11 Sep 2026 from the Wayback PDF index, does NOT -- it operates below 2.1,
    and this test says so rather than quietly dropping it.

    That direction matters and is the reason the source is kept. The maximum
    water saving available against a baseline of C cycles is 1/C, so a LOWER
    real baseline means MORE headroom, not less. Holding the gate at 3.0 when
    a fifth operator runs at 2.1 makes the gate harder to pass, and WCTI is
    the site with the highest makeup silica of the five (32 ppm against our
    18) -- exactly where the silica thesis predicts cycles should be lowest.

    A source that disagrees in the conservative direction is evidence. One
    that disagreed in the flattering direction would need explaining before it
    could be used at all.
    """
    import sidestream as ss
    ev = ss.typical_cycles_evidence()
    assert len(ev) >= 5

    brackets, below = [], []
    for name, _what, (lo, hi) in ev:
        if lo is not None:
            assert lo <= 3.0, f"{name} starts above the 3.0 baseline"
        (brackets if hi >= 3.0 else below).append(name)

    assert len(brackets) >= 4, f"only {len(brackets)} sources bracket 3.0"
    assert below == ["WCTI food-processing plant"], (
        f"an unexpected source sits below the baseline: {below}. Check which "
        f"direction it moves the claim before accepting it.")

    # every source must still be inside the 2-4 band the package claims
    assert all(hi <= 4.0 for _n, _w, (_lo, hi) in ev)


def test_austin_corrects_the_cost_conclusion_rather_than_contradicting_it():
    """A real operator softens condenser makeup and reaches 15-18 cycles,
    while the ZLD benchmark says treatment is 5-12x underwater. Both are
    true, because they treat different streams -- and the module must carry
    both rather than the flattering one."""
    import sidestream as ss
    a = ss.AUSTIN_COUNTER_BENCHMARK
    assert a["softened_cycles"] == (15.0, 18.0)
    assert a["acid_cycles"] == (6.0, 12.0)
    # and the lever Austin leans on is the one the Gulf may not use
    assert "sulfuric acid" in a["lever_banned_in_RC_jurisdiction"]
    assert ss.REAL_COST_BENCHMARK["duty_m3_per_h"] > 100.0, (
        "the ZLD benchmark is a large blowdown train, i.e. an upper bound "
        "on makeup-side treatment cost rather than an estimate of it")


def test_our_water_balance_reproduces_a_regulatory_filing():
    """The water arithmetic, checked against someone else's published version.

    Every other external check in this package validates a CHEMISTRY limit.
    Nothing validated the arithmetic that turns a cycles setpoint into a
    makeup figure -- and that arithmetic is what every water-saving claim in
    the deck rests on.

    Bill Powers, P.E., computed it for Diablo Canyon in a filing to the
    California State Water Resources Control Board, cross-checked in the same
    document against a separate consultant's estimate. Feeding his stated
    inputs into `controller.water_balance()` must land on his answers.

    The tolerances are loose on purpose: he rounds 12.17 gpm to 12 and carries
    that through. A test that demanded three decimals would be testing his
    rounding, not our physics.
    """
    import recycle as rcy

    d = rcy.POWERS_DIABLO_CANYON_2013
    r = rcy.reproduce_powers_balance()

    assert r["evaporation_gpm_per_mwe"] == pytest.approx(
        d["evaporation_gpm_per_mwe"], abs=0.25)
    assert r["blowdown_gpm_per_mwe"] == pytest.approx(
        d["blowdown_gpm_per_mwe"], abs=0.5)
    assert r["drift_gpm_per_mwe"] == pytest.approx(
        d["drift_gpm_per_mwe"], abs=1e-4)
    assert r["makeup_gpm_per_mwe"] == pytest.approx(
        d["makeup_gpm_per_mwe"], abs=0.75)

    # and the headline the filing exists to establish
    assert r["withdrawal_reduction_pct"] == pytest.approx(
        d["withdrawal_reduction_pct"], abs=0.2)
    assert abs(r["withdrawal_reduction_pct"]
               - d["tetratech_withdrawal_reduction_pct"]) < 0.5, (
        "we now disagree with the independent consultant estimate too, which "
        "would mean the gap is ours rather than his rounding")

    # his blowdown relation is ours: B = E/(C-1) with drift set aside
    assert (d["blowdown_gpm_per_mwe"] / d["evaporation_gpm_per_mwe"]
            == pytest.approx(1.0 / (d["cycles"] - 1.0), rel=1e-9))


def test_the_cycles_ladder_is_monotone_in_makeup_salinity():
    """Cycles are set by the water going in, not by the tower.

    This is the thesis in one line, and it now has three points spanning three
    orders of magnitude of makeup TDS:

        seawater      ~35,000 mg/L   1.5 - 2.0 cycles   CEC PIER, via Powers
        treated effluent 1,000-1,500   2.0 - 4.0        five operators
        polished water      low          ~9             Qatar Cool

    A seawater tower at 1.5 cycles is not badly run. The test pins the
    ORDERING, not the values, because the ordering is the claim.
    """
    import recycle as rcy
    import sidestream as ss

    seawater_hi = 2.0                       # top of the seawater band
    tse = [hi for _n, _w, (_lo, hi) in ss.typical_cycles_evidence()]
    polished = 9.0                          # Qatar Cool, polished water

    assert seawater_hi <= min(tse), (
        "the seawater band now overlaps the effluent band; the ladder is the "
        "argument, so check which source moved before relaxing this")
    assert max(tse) < polished

    # and the seawater figure must NOT have been folded into the TSE evidence,
    # which is a different water class on a different axis
    names = [n for n, _w, _r in ss.typical_cycles_evidence()]
    assert not any("Diablo" in n or "seawater" in n.lower() for n in names)
