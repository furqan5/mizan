"""Side-stream treatment: does removing the binding species pay?

The module turns a chemistry result into a procurement question. These tests
fix the physics it must not get wrong, and one published claim it must refuse
to reproduce.
"""

from __future__ import annotations

import pytest

import chemistry as ch
import sidestream as ss

T_HOT, T_COLD, PH = 45.0, 32.0, 8.25
EVAP = 4.2                      # kg/s, the archetype plant's evaporation


@pytest.fixture(scope="module")
def water():
    import run_controller as rc
    return rc.TSE


@pytest.fixture(scope="module")
def tariffs():
    import run_controller as rc
    return rc.TARIFFS


# ---------------------------------------------------------------------------
# the refusal that matters most
# ---------------------------------------------------------------------------

def test_a_sand_filter_cannot_move_a_saturation_ceiling(water, tariffs):
    """Granular media removes SUSPENDED solids. Dissolved silica, calcium and
    alkalinity pass straight through, so the ceiling cannot move.

    This is a test rather than a comment because a 2026 Water-Energy Nexus
    paper reports a sand filter cutting conductivity from 1700 to 700 uS/cm
    and evaporation by 20.5 %. Conductivity measures dissolved ions and
    evaporation is set by duty; neither can be caused by media filtration.
    The model must not be able to reproduce that result.
    """
    r = ss.break_even_cost(water, "sand_filtration", EVAP, tariffs,
                           T_HOT, T_COLD, pH=PH)
    assert r["raises_ceiling"] is False
    assert r["ceiling_after"] == pytest.approx(r["ceiling_before"])
    assert r["break_even_per_m3"] is None

    treated = ss.treat(water, "sand_filtration")
    for s in ch.SPECIES:
        assert getattr(treated, s) == pytest.approx(getattr(water, s)), s


# ---------------------------------------------------------------------------
# treat()
# ---------------------------------------------------------------------------

def test_treatment_removes_what_it_claims_and_nothing_else(water):
    treated = ss.treat(water, "lime_softening")
    spec = ss.TECHNOLOGIES["lime_softening"]["removes"]
    for s in ch.SPECIES:
        before, after = getattr(water, s), getattr(treated, s)
        expected = before * (1.0 - spec.get(s, 0.0))
        assert after == pytest.approx(expected), s
        if s not in spec:
            assert after == pytest.approx(before), f"{s} moved and should not"


def test_partial_treatment_is_monotone_and_bracketed(water):
    """Treating a fraction of the makeup must land between doing nothing and
    treating all of it, and must move monotonically in between."""
    prev = getattr(water, "SiO2")
    for f in (0.0, 0.25, 0.5, 0.75, 1.0):
        si = getattr(ss.treat(water, "lime_softening", f), "SiO2")
        assert si <= prev + 1e-12
        prev = si
    full = getattr(ss.treat(water, "lime_softening", 1.0), "SiO2")
    none = getattr(ss.treat(water, "lime_softening", 0.0), "SiO2")
    assert none == pytest.approx(water.SiO2)
    assert full == pytest.approx(water.SiO2 * 0.5)


def test_bad_inputs_are_refused_by_name(water):
    with pytest.raises(ValueError, match="unknown technology"):
        ss.treat(water, "magic")
    with pytest.raises(ValueError, match="fraction_treated"):
        ss.treat(water, "lime_softening", 1.5)
    with pytest.raises(ValueError, match="fraction_treated"):
        ss.treat(water, "lime_softening", -0.1)


# ---------------------------------------------------------------------------
# the ceiling, and the acid that cannot buy it
# ---------------------------------------------------------------------------

def test_removing_silica_raises_the_ceiling(water):
    """The whole thesis of the module, reduced to a monotonicity check."""
    prev, _ = ss.ceiling_with(water, T_HOT, T_COLD, pH=PH)
    for f in (0.25, 0.5, 1.0):
        c, _ = ss.ceiling_with(ss.treat(water, "lime_softening", f),
                               T_HOT, T_COLD, pH=PH)
        assert c > prev, f"fraction {f}: {c} not above {prev}"
        prev = c


def test_the_untreated_ceiling_agrees_with_the_v5b_sweep(water):
    """Guards the handoff. V5b reports 5 economic and 6 physical cycles on
    this water bound by amorphous silica; this module must not quietly
    disagree with the gate it is built on top of."""
    c, mineral = ss.ceiling_with(water, T_HOT, T_COLD, pH=PH)
    assert 4.5 < c < 6.5, c
    assert mineral == "SI_silica_am"


def test_the_ph_argument_is_not_cosmetic(water):
    """Passing a pH must give a different, higher ceiling than atmospheric
    equilibrium, because that is what dosing acid buys. If these two agreed,
    the pH argument would be doing nothing and every treatment comparison
    would be answering the wrong question."""
    atm, _ = ss.ceiling_with(water, T_HOT, T_COLD, pH=None)
    dosed, _ = ss.ceiling_with(water, T_HOT, T_COLD, pH=PH)
    assert dosed > atm + 1.0, (atm, dosed)


# ---------------------------------------------------------------------------
# DEFECT 26, one module over
# ---------------------------------------------------------------------------

def test_a_ceiling_past_the_davies_limit_is_capped_and_declared(water,
                                                                tariffs):
    """Removing the binding species raises the ceiling, and a raised ceiling
    walks straight at the Davies validity boundary. A treated water reading
    thirty cycles is the model being asked a question it cannot answer.

    Defect 26 was exactly this quantity computed and enforced by nothing.
    """
    r = ss.break_even_cost(water, "lime_softening_with_magnesia", EVAP,
                           tariffs, T_HOT, T_COLD, pH=PH)
    assert r["ceiling_after"] <= r["davies_validity_cycles"] + 1e-6
    if r["model_limited"]:
        assert r["ceiling_after_unlimited"] > r["ceiling_after"]
        assert r["binding_after"] == "MODEL VALIDITY (Davies)", (
            "a model-limited ceiling must say so rather than name a mineral "
            "it did not actually reach")


def test_the_davies_limit_is_where_ionic_strength_crosses(water):
    c = ss.davies_validity_cycles(water)
    I_max = ch.ANALYSIS_TOLERANCES["ionic_strength_max"]
    assert water.concentrate(c).ionic_strength() == pytest.approx(I_max,
                                                                  rel=1e-3)
    assert water.concentrate(c * 1.1).ionic_strength() > I_max
    assert water.concentrate(c * 0.9).ionic_strength() < I_max


# ---------------------------------------------------------------------------
# the economics
# ---------------------------------------------------------------------------

def test_break_even_is_positive_where_the_ceiling_rises(water, tariffs):
    for tech in ("lime_softening", "lime_softening_with_magnesia",
                 "reverse_osmosis", "electrocoagulation"):
        r = ss.break_even_cost(water, tech, EVAP, tariffs, T_HOT, T_COLD,
                               pH=PH)
        if not r["raises_ceiling"]:
            continue
        assert r["break_even_per_m3"] > 0.0, tech
        assert r["saving_per_h"] > 0.0, tech
        assert r["water_saved_vs_baseline_pct"] > 0.0, tech


def test_reverse_osmosis_is_charged_for_its_own_reject(water, tariffs):
    """RO recovers 75 %, so the volume treated exceeds the volume delivered
    and the concentrate has to go somewhere. A model that ignored the reject
    would make RO look better than it is."""
    r = ss.break_even_cost(water, "reverse_osmosis", EVAP, tariffs,
                           T_HOT, T_COLD, pH=PH)
    assert r["reject_m3_h"] > 0.0
    recovery = ss.TECHNOLOGIES["reverse_osmosis"]["recovery"]
    assert r["treated_m3_h"] == pytest.approx(
        r["makeup_after_m3_h"] / recovery, rel=1e-6)
    # lime softening has no reject stream at all
    lime = ss.break_even_cost(water, "lime_softening", EVAP, tariffs,
                              T_HOT, T_COLD, pH=PH)
    assert lime["reject_m3_h"] == pytest.approx(0.0)


def test_water_saving_matches_the_cycles_arithmetic(water, tariffs):
    """M = E*C/(C-1). The saving reported against the baseline has to be the
    arithmetic one, or the water balance and the economics have drifted
    apart."""
    r = ss.break_even_cost(water, "lime_softening", EVAP, tariffs,
                           T_HOT, T_COLD, baseline_cycles=3.0, pH=PH)
    c0, c1 = r["baseline_cycles"], r["cycles_run_after"]
    expected = 100.0 * (1.0 - (c1 / (c1 - 1.0)) / (c0 / (c0 - 1.0)))
    assert r["water_saved_vs_baseline_pct"] == pytest.approx(expected,
                                                             abs=0.6)


def test_survey_ranks_by_ceiling_and_covers_every_technology(water, tariffs):
    rows = ss.survey(water, EVAP, tariffs, T_HOT, T_COLD, pH=PH)
    assert len(rows) == len(ss.TECHNOLOGIES)
    ceilings = [r["ceiling_after"] for r in rows]
    assert ceilings == sorted(ceilings, reverse=True)
    assert rows[-1]["technology"] == "sand_filtration", (
        "the technology that removes nothing must rank last")
