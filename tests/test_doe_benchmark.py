"""DEFECT 29 -- the US DOE pilot study, scored against the engine.

Vidic, Dzombak & Landis (2012), "Use of Treated Municipal Wastewater as Power
Plant Cooling System Makeup Water: Tertiary Treatment versus Expanded Chemical
Regimen for Recirculating Water Quality Management", US DOE / NETL Cooperative
Agreement DE-NT0006550, 415 pp. doi:10.2172/1063876

WHY THIS FILE IS THE MOST IMPORTANT BENCHMARK IN THE PACKAGE.

It is the definitive study of exactly the application Mizan addresses: treated
municipal wastewater as recirculating cooling makeup. Bench and pilot scale,
three tertiary treatments, real cooling towers, three summers of weekly
sampling. It is public domain, it is not ours, and NOTHING in `chemistry.py`
was fitted to it -- the engine was complete before the report was read.

It supplies three things nothing else in the repository has:

  1. A water analysis with MEASURED PHOSPHATE and no silica at all. The report
     measures four anions weekly -- Cl, PO4, NO3, SO4 -- and four cations --
     Ca, Mg, Fe, Cu. The word "silica" does not appear once in 415 pages.
     That is the strongest available evidence that carrying an unmeasured
     silica while omitting a measured phosphate had the priority backwards.

  2. A DIRECT OBSERVATION OF WHICH MINERAL FORMED, by XRD, on a heated
     surface. Section 4.2.5: "Hydroxyapatite (Ca5(PO4)3(OH)) was the only
     crystalline material identified by XRD analysis in the deposits formed
     on the heater."

  3. THE INCUMBENT INDEX POINTING AT THE WRONG MINERAL. Section 3.2.4
     computes LSI, RSI and PSI -- "widely used to estimate the scaling
     potential of calcium carbonate" -- and then concludes: "Water quality
     analysis suggests that calcium phosphate is the primary mineral scale
     when pH of the recirculating water is adjusted at 7.8".

     CORRECTED 11 Sep 2026, AND THE CORRECTION COST US THE STRONGER VERSION
     OF THIS CLAIM. This file originally ran on Table 2.3.2 and asserted that
     LSI reads NEGATIVE on the water that scaled. On the correct chapter 4
     recipe -- Table 4.2.1, four times the alkalinity -- it does not: LSI is
     -0.01 at 40 C and +0.25 at the skin. So the honest claim is not that the
     index is silent. It is that the index is UNINFORMATIVE ABOUT SPECIES:
     it reads a mild carbonate number on a water whose calcium phosphate
     index is four log units higher, and calcium phosphate is what the XRD
     actually found. An operator reading +0.25 would dose for carbonate.

Until now the claim "LSI is definitionally a calcium-carbonate index and
cannot represent the mineral that actually binds" was an argument from the
definition of the index plus our own model. It is now an observation on
somebody else's pilot hardware.

WHAT THIS BENCHMARK DOES **NOT** SHOW, WHICH MATTERS AS MUCH.

It would be easy, and wrong, to read the report as "LSI said no scale and
scale happened, everywhere". In the PILOT TOWERS it did not: the report's own
Phase 2 reading is that when make-up alkalinity fell, pH fell, LSI fell AND
calcium phosphate formation fell together -- "negligible mass gain was
observed in all the three towers ... phosphate concentrations in the
recirculating water increased ... indicating lower calcium phosphate
formation potential. Besides, much lower LSI meaning less CaCO3 scaling
potential was also observed" (section 5.2, p. 5-17/5-18).

That is a real correlation, and working out its cause sharpened the claim
rather than weakening it. The obvious reading -- "alkalinity drives both" --
is WRONG, and the model says so: at fixed pH, raising alkalinity RAISES LSI
while slightly LOWERING SI_tcp, because the extra bicarbonate ties up free
calcium in CaHCO3(+) and CaCO3(0) pairs and calcium phosphate is third order
in free calcium. Measured on the DOE water at 55 C, an eightfold alkalinity
range moves LSI by +0.90 and SI_tcp by -0.02.

The variable that genuinely moves both is **pH**. It raises carbonate
saturation, and it raises the HPO4(2-) fraction of total phosphate steeply
through the pKa2 of phosphoric acid at 7.20. In the DOE pilot, make-up
alkalinity changes moved the recirculating pH -- the report links them
explicitly -- and pH is what carried the apparent correlation.

The defensible claim is therefore narrower and sharper than "LSI is blind":

    LSI is a proxy for calcium phosphate only while pH is what varies. It
    decouples on the other two axes an operator actually controls: raising
    CALCIUM moves phosphate saturation far more than it moves LSI, and
    raising ALKALINITY moves them in opposite directions. In the decoupled
    region -- low alkalinity, adequate calcium and phosphate, hot surface --
    LSI reads negative and calcium phosphate deposits anyway.

The bench heated-surface test is exactly that decoupled case, which is why it
is the benchmark and the pilot towers are not. MWW_NF is a nitrified, filtered
water: alkalinity 25.1 mg/L as CaCO3 and pH 6.65, i.e. carbonate stripped out,
while calcium is the HIGHEST of the three waters at 46.7 mg/L and phosphate is
still 7.16 mg/L. Tertiary treatment removed the thing LSI can see and left the
thing it cannot.
"""

from __future__ import annotations

import pytest

import chemistry as ch


def test_the_doe_study_finds_the_mineral_the_incumbent_index_cannot_rank():
    """THE BENCHMARK, on the chapter 4 recipe that actually governs the
    heated-surface test.

    What must hold: calcium phosphate is the dominant supersaturated phase by
    a wide margin, gypsum is far undersaturated, silica is absent, and the
    carbonate index -- whatever its sign -- carries no information about the
    species that deposited. The XRD found hydroxyapatite and nothing else.
    """
    w = ch.DOE_SYN_MWW_NF_COC4
    for T in (40.0, 55.0):
        s = ch.saturation_state(w, T)
        lsi = ch.langelier_index(w, T)

        # phosphate dominates, and by log units rather than by a hair
        assert s["SI_tcp"] > 3.0, f"SI_tcp {s['SI_tcp']:+.2f} at {T} C"
        assert s["SI_hydroxyapatite"] > 7.0, s["SI_hydroxyapatite"]
        assert s["SI_tcp"] - s["SI_calcite"] > 3.0, (
            f"at {T} C phosphate must dominate carbonate by >3 log units: "
            f"tcp {s['SI_tcp']:+.2f} vs calcite {s['SI_calcite']:+.2f}")

        # the other candidates are not in contention
        assert s["SI_gypsum"] < -0.5, f"gypsum {s['SI_gypsum']:+.2f} at {T} C"
        assert s["SI_silica_am"] < 0.0, "the report never measures silica"

        # and the carbonate index is small either way -- it neither warns of
        # the deposit that formed nor rules it out
        assert abs(lsi) < 0.5, (
            f"LSI {lsi:+.2f} at {T} C: the claim is that the carbonate index "
            f"is uninformative here, which requires it to be small while the "
            f"phosphate index is {s['SI_tcp']:+.2f}")
        assert abs(s["SI_calcite"]) < 0.5, s["SI_calcite"]


def test_the_two_doe_recipes_are_not_interchangeable():
    """Guards the correction itself. Table 2.3.2 is the general chapter 2/3
    recipe; Table 4.2.1 governs chapter 4 and carries four times the
    alkalinity. Substituting one for the other moves calcite by more than
    half a log unit and would make this benchmark pass for the wrong
    reason."""
    a = ch.DOE_SYN_MWW_NF_COC4                      # 4.2.1
    b = ch.DOE_SYN_MWW_NF_COC4_TABLE_2_3_2          # 2.3.2
    assert a.HCO3 == pytest.approx(1.60 * 61.017)
    assert b.HCO3 == pytest.approx(0.40 * 61.017)
    assert a.Na == pytest.approx(9.80 * 22.990)
    assert b.Na == pytest.approx(8.60 * 22.990)
    for T in (40.0, 55.0):
        d = (ch.saturation_state(a, T)["SI_calcite"]
             - ch.saturation_state(b, T)["SI_calcite"])
        assert d > 0.5, f"the two recipes differ by only {d:.2f} at {T} C"
    # but phosphate barely moves, which is why the headline finding survives
    for T in (40.0, 55.0):
        d = abs(ch.saturation_state(a, T)["SI_tcp"]
                - ch.saturation_state(b, T)["SI_tcp"])
        assert d < 0.1, d


def test_the_doe_benchmark_magnitudes_have_not_drifted():
    """Pins the numbers, so a later change to the phosphate model cannot
    satisfy the qualitative test above while quietly moving the answer."""
    s = ch.saturation_state(ch.DOE_SYN_MWW_NF_COC4, 40.0)
    assert -0.30 < s["SI_calcite"] < 0.15, s["SI_calcite"]
    assert -1.15 < s["SI_gypsum"] < -0.90, s["SI_gypsum"]
    assert 3.05 < s["SI_tcp"] < 3.55, s["SI_tcp"]
    assert 7.30 < s["SI_hydroxyapatite"] < 8.05, s["SI_hydroxyapatite"]


def test_calcium_phosphate_deposits_hot_and_silica_deposits_cold():
    """The DOE deposit formed on a HEATER, so calcium phosphate must come out
    retrograde -- less soluble hot -- like calcite and unlike silica.

    This is a sign test the model could have failed. The enthalpies were
    transcribed from a thermodynamic database with no reference to this
    observation, so agreement is evidence rather than construction. It is
    also why phosphate is evaluated at the skin and silica at the basin.
    """
    w = ch.DOE_SYN_MWW_NF_COC4
    cold = ch.saturation_state(w, 30.0)
    hot = ch.saturation_state(w, 55.0)

    assert hot["SI_tcp"] > cold["SI_tcp"] + 0.3, (
        f"cold {cold['SI_tcp']:+.2f} -> hot {hot['SI_tcp']:+.2f}: calcium "
        f"phosphate must be retrograde")
    assert hot["SI_hydroxyapatite"] > cold["SI_hydroxyapatite"]
    assert hot["SI_calcite"] > cold["SI_calcite"], "calcite is retrograde too"
    assert ch.MINERAL_EVAL_POINT["SI_tcp"] == "hot"

    # the opposite sign, on a water that has silica, is what makes a single
    # evaluation temperature wrong
    sil = ch.ARAMCO_FIELD_VALIDATED.concentrate(5.0)
    assert (ch.saturation_state(sil, 55.0)["SI_silica_am"]
            < ch.saturation_state(sil, 30.0)["SI_silica_am"]), (
        "silica must remain prograde -- opposite sign to phosphate")


def test_the_phosphate_constants_reproduce_the_textbook_dissociation_steps():
    """An internal consistency check on a transcription, needing no database.

    The cumulative association constants of orthophosphate must differ by the
    successive pKa of phosphoric acid. A mistyped digit fails here.
    """
    a = ch.PHOSPHATE_ASSOCIATION
    pka3 = a["HPO4"][0]
    pka2 = a["H2PO4"][0] - a["HPO4"][0]
    pka1 = a["H3PO4"][0] - a["H2PO4"][0]

    assert abs(pka1 - 2.148) < 0.03, pka1
    assert abs(pka2 - 7.198) < 0.02, pka2
    assert abs(pka3 - 12.346) < 0.02, pka3
    assert ch.PHOSPHATE_PKA == pytest.approx((pka1, pka2, pka3), abs=0.03)

    # the Ca and Mg pairs are cumulative from PO4(3-), so each must sit the
    # published pair constant above the acid-base constant it was built on
    for pair, base, step in (("CaHPO4", "HPO4", 2.739),
                             ("CaH2PO4", "H2PO4", 1.408),
                             ("MgHPO4", "HPO4", 2.870),
                             ("MgH2PO4", "H2PO4", 1.513)):
        got = a[pair][0] - a[base][0]
        assert abs(got - step) < 0.01, f"{pair}: {got:.3f} vs {step}"


def test_phosphate_mean_charge_is_physical_and_monotonic():
    """Total phosphate cannot carry its formal -3 at cooling-tower pH."""
    assert ch.phosphate_mean_charge(7.8) == pytest.approx(-1.80, abs=0.03)
    prev = 0.0
    for pH in (4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0):
        z = ch.phosphate_mean_charge(pH)
        assert -3.0 <= z <= 0.0, f"pH {pH} gives charge {z}"
        assert z < prev + 1e-12, "charge must fall monotonically as pH rises"
        prev = z
    assert ch.phosphate_mean_charge(14.0) < -2.9, "approaches -3 only in alkali"


def test_phosphate_cannot_bind_a_ceiling_on_the_field_water():
    """The honest negative result, pinned so it cannot be quietly reversed.

    Every cycle count of interest on the field analysis puts SI_tcp INSIDE
    the published inhibited band (3.18 typical, 5.10 stressed). Inside that
    band the outcome is decided by the treatment programme, not by the water,
    so phosphate selects a requirement rather than a ceiling.

    Anyone who later makes phosphate bind a ceiling has to delete this test
    and say why. The reason it must not is concrete: at a limit of 3.0 the
    field water's ceiling collapses to 1.0 cycle, which contradicts the pilot
    that ran that same TSE at 3.5 cycles with a clean condenser.
    """
    lo = ch.PHOSPHATE_SCREEN["typical_inhibited"]
    hi = ch.PHOSPHATE_SCREEN["stressed_inhibited"]
    for cycles in (3.5, 4.0, 5.0, 6.0, 7.0):
        _, si = ch.phosphate_screen(
            ch.ARAMCO_FIELD_VALIDATED.concentrate(cycles), 40.0)
        assert lo < si < hi, (
            f"at {cycles} cycles SI_tcp = {si:+.2f}, outside the band "
            f"{lo}-{hi} that the negative result rests on")

    assert "SI_tcp" not in ch.OPERATING_LIMITS
    assert "SI_tcp" not in ch.CHARACTERISED_LIMITS


def test_the_field_water_carries_its_measured_phosphate():
    """Silica on this analysis is ASSUMED, imported from Riyadh brackish
    groundwater. Phosphate is MEASURED on this water. The model must not
    treat the two the same way, and both must be declared."""
    w = ch.ARAMCO_FIELD_VALIDATED
    assert w.PO4 == pytest.approx(8.0), "the 2021 field account reports 8 mg/L"

    checks = ch.validate_analysis(w, silica_declared=True)
    assert checks["phosphate_declared"][0], checks["phosphate_declared"][1]
    assert all(ok for ok, _ in checks.values()), {
        k: d for k, (ok, d) in checks.items() if not ok}

    # and an unmeasured phosphate must still be refused, exactly as silica is
    bare = ch.Water(name="no phosphate", Ca=100.0, HCO3=100.0, SiO2=10.0)
    assert not ch.validate_analysis(bare)["phosphate_declared"][0]
    assert ch.validate_analysis(bare, phosphate_declared=True)[
        "phosphate_declared"][0]


def test_adding_phosphate_moved_nothing_on_a_water_that_has_none():
    """A new species must be inert where it is absent.

    Any water with PO4 = 0 must produce exactly the indices it produced
    before defect 29, and both phosphate minerals must be so far
    undersaturated that they can never accidentally bind.
    """
    w = ch.ARAMCO_FIELD_NO_SILICA
    zero = ch.Water(name="stripped", Na=w.Na, K=w.K, Ca=w.Ca, Mg=w.Mg,
                    Cl=w.Cl, SO4=w.SO4, HCO3=w.HCO3, NO3=w.NO3,
                    SiO2=w.SiO2, PO4=0.0, pH=w.pH, TDS=w.TDS)

    s = ch.saturation_state(zero.concentrate(5.0), 40.0)
    assert s["SI_tcp"] < -20.0, s["SI_tcp"]
    assert s["SI_hydroxyapatite"] < -20.0, s["SI_hydroxyapatite"]

    sp = ch.speciate(zero, 40.0)
    assert all(v == 0.0 for v in sp["phosphate"].values())
    assert sp["free"]["PO4"] == 0.0
    assert sp["converged"]


def test_hydroxyapatite_is_the_less_soluble_phase():
    """Hydroxyapatite is the thermodynamically stable calcium phosphate, so
    on any water carrying phosphate it must read MORE supersaturated than
    whitlockite. The DOE study saw exactly this ordering physically: it found
    hydroxyapatite by XRD, with a Ca:P ratio of 1.54 against the 1.67 of the
    pure phase, "indicating that amorphous calcium phosphate ... may also
    exist in the deposits" -- the metastable precursor alongside the stable
    product.
    """
    for w in (ch.DOE_SYN_MWW_NF_COC4, ch.DOE_SYN_MWW_COC4,
              ch.ARAMCO_FIELD_VALIDATED.concentrate(5.0)):
        for T in (30.0, 40.0, 55.0):
            s = ch.saturation_state(w, T)
            assert s["SI_hydroxyapatite"] > s["SI_tcp"], (
                f"{w.name} at {T} C: HAP {s['SI_hydroxyapatite']:+.2f} is not "
                f"above TCP {s['SI_tcp']:+.2f}")


def test_the_doe_analyses_are_transcribed_not_invented():
    """Guards the transcription of Table 2.3.1 against silent edits, and
    records the two facts about it that carry the argument: phosphate is
    present in all three waters, silica in none of them."""
    for w, ca, po4 in ((ch.DOE_MWW, 33.3, 9.98),
                       (ch.DOE_MWW_NF, 46.7, 7.16),
                       (ch.DOE_MWW_NFG, 39.8, 8.46)):
        assert w.Ca == pytest.approx(ca)
        assert w.PO4 == pytest.approx(po4)
        assert w.SiO2 == 0.0, "the report never measures silica"
        assert w.Na == 0.0 and w.K == 0.0, "neither was measured"

    # Na and K unmeasured means these are not analyses a controller may run
    # on, and the product boundary must refuse them for that reason.
    with pytest.raises(ch.AnalysisRejected):
        ch.require_valid_analysis(ch.DOE_MWW_NF, silica_declared=True,
                                  phosphate_declared=True)


def test_lsi_is_a_proxy_for_phosphate_on_only_one_of_three_axes():
    """The honest boundary on the benchmark's claim, made mechanical.

    Three axes, three different answers -- and only the first is the one the
    DOE pilot happened to move:

      pH          both rise together      -> LSI looks like a usable proxy
      calcium     SI_tcp rises much more  -> LSI understates the risk
      alkalinity  they move OPPOSITE ways -> LSI is actively misleading

    The third is the sharpest and was found by this test failing: raising
    alkalinity at fixed pH ties free calcium up in carbonate pairs, and
    calcium phosphate is third order in free calcium.
    """
    base = ch.DOE_SYN_MWW_NF_COC4

    def state(hco3=None, ca=None, pH=None):
        w = ch.Water(name="probe", Ca=ca or base.Ca, Mg=base.Mg, Na=base.Na,
                     K=base.K, HCO3=hco3 or base.HCO3, SO4=base.SO4,
                     Cl=base.Cl, NO3=base.NO3, PO4=base.PO4,
                     pH=pH or base.pH)
        return (ch.langelier_index(w, 55.0),
                ch.saturation_state(w, 55.0)["SI_tcp"])

    # axis 1 -- pH. Both rise. This is the regime that made LSI look adequate.
    lo_lsi, lo_tcp = state(pH=7.0)
    hi_lsi, hi_tcp = state(pH=8.5)
    assert hi_lsi > lo_lsi + 1.0, (lo_lsi, hi_lsi)
    assert hi_tcp > lo_tcp + 1.0, (lo_tcp, hi_tcp)

    # axis 2 -- calcium at fixed pH. SI_tcp is third order in free calcium;
    # LSI is first order in its logarithm. The gap is the whole point.
    ca_lo_lsi, ca_lo_tcp = state(ca=base.Ca * 0.5)
    ca_hi_lsi, ca_hi_tcp = state(ca=base.Ca * 2.0)
    d_lsi = ca_hi_lsi - ca_lo_lsi
    d_tcp = ca_hi_tcp - ca_lo_tcp
    assert d_tcp > 2.0 * d_lsi, (
        f"calcium moves SI_tcp by {d_tcp:.2f} and LSI by {d_lsi:.2f}")

    # axis 3 -- alkalinity at fixed pH. OPPOSITE SIGNS. An operator raising
    # alkalinity sees LSI climb and would tighten a carbonate programme,
    # while the phosphate risk is quietly falling.
    a_lo_lsi, a_lo_tcp = state(hco3=base.HCO3 * 0.5)
    a_hi_lsi, a_hi_tcp = state(hco3=base.HCO3 * 4.0)
    assert a_hi_lsi > a_lo_lsi + 0.5, (a_lo_lsi, a_hi_lsi)
    assert a_hi_tcp < a_lo_tcp, (
        f"alkalinity must move SI_tcp the OTHER way: {a_lo_tcp:+.3f} -> "
        f"{a_hi_tcp:+.3f}. Free calcium is consumed by carbonate pairing")
