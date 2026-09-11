"""MILESTONE 2 -- the CDU subsystem and the chemically-bounded economizer.

THE CLAIM UNDER TEST.

A thermal-only free-cooling controller minimises facility water temperature,
because colder water is compressor work avoided. Amorphous silica is prograde
-- least soluble COLD -- so on a silica-bearing makeup water that controller
drives the plant toward precipitation, at the tower basin and on the CDU
plate. Neither surface is visible to any thermal model.

The tests below fix the physics that makes the claim true, and the behaviour
that acts on it. They do not assert a saving.
"""

from __future__ import annotations

import json
import pathlib

import pytest

import chemistry as ch
from models import cdu_model as cdu

RESULTS = pathlib.Path(__file__).resolve().parent.parent / "results"


@pytest.fixture(scope="module")
def water():
    import run_controller as rc
    return rc.TSE


@pytest.fixture(scope="module")
def unit():
    return cdu.sized_for(9000.0, delta_t_k=10.0)


# ---------------------------------------------------------------------------
# the CDU itself
# ---------------------------------------------------------------------------

def test_pump_power_is_cubic_in_flow(unit):
    """The affinity law is why the hydraulic compensation is expensive and
    why it has to be computed rather than assumed cheap. Doubling flow is
    eight times the power, not two."""
    base = cdu.CDUSubsystem(q_it_kw=1000.0, m_dot_sec_kg_s=10.0,
                            m_dot_sec_nom_kg_s=10.0, p_pump_sec_nom_kw=20.0)
    assert base.pump_power_kw() == pytest.approx(20.0)
    for ratio in (0.5, 1.5, 2.0):
        u = cdu.CDUSubsystem(q_it_kw=1000.0, m_dot_sec_kg_s=10.0 * ratio,
                             m_dot_sec_nom_kg_s=10.0, p_pump_sec_nom_kw=20.0)
        assert u.pump_power_kw() == pytest.approx(20.0 * ratio ** 3)


def test_the_cold_plate_return_limit_is_an_invariant(unit):
    """T_ret = T_sup + Q/(m*cp), and 42 C is the limit. The model must report
    the breach rather than clamp it -- a clamped constraint is the shape of
    defect 11, computed and enforced by nothing."""
    for t_fws in (20.0, 27.0, 32.0, 40.0):
        st = unit.solve(t_fws, m_dot_pri_kg_s=250.0)
        expected = (t_fws + unit.approach_k
                    + unit.q_it_kw * 1000.0
                    / (unit.m_dot_sec_kg_s * unit.cp_sec))
        assert st["t_sec_return_c"] == pytest.approx(expected)
        assert st["return_ok"] == (st["t_sec_return_c"]
                                   <= cdu.COLD_PLATE_RETURN_MAX_C)
        assert st["return_margin_k"] == pytest.approx(
            cdu.COLD_PLATE_RETURN_MAX_C - st["t_sec_return_c"])


def test_the_plate_wall_sits_between_its_two_streams(unit):
    """A wall temperature outside the two bulk temperatures is a sign error,
    and it would feed straight into the saturation index."""
    for t_fws in (18.0, 25.0, 33.0):
        st = unit.solve(t_fws, m_dot_pri_kg_s=250.0)
        lo, hi = st["t_fwr_c"], st["t_sec_return_c"]
        assert lo <= st["t_wall_primary_c"] <= hi, (
            f"wall {st['t_wall_primary_c']:.2f} outside [{lo:.2f}, {hi:.2f}]")
    # and the wall must be HOTTER than the primary bulk, since heat flows
    # secondary -> primary. This is what makes it a scaling surface at all.
    st = unit.solve(25.0, m_dot_pri_kg_s=250.0)
    assert st["t_wall_primary_c"] > st["t_fwr_c"]


def test_required_secondary_flow_lands_exactly_on_the_limit(unit):
    """The hydraulic compensation: given a supply temperature, the flow that
    holds the return at 42 C. Rebuilding the unit at that flow must return
    exactly the limit."""
    for t_fws in (24.0, 28.0, 31.0):
        import hybrid_supervisor as hs
        m = hs.required_secondary_flow(unit, t_fws)
        assert m is not None and m > 0
        u = cdu.CDUSubsystem(
            q_it_kw=unit.q_it_kw, m_dot_sec_kg_s=m,
            m_dot_sec_nom_kg_s=unit.m_dot_sec_nom_kg_s,
            p_pump_sec_nom_kw=unit.p_pump_sec_nom_kw,
            approach_k=unit.approach_k)
        st = u.solve(t_fws, m_dot_pri_kg_s=250.0)
        assert st["t_sec_return_c"] == pytest.approx(
            cdu.COLD_PLATE_RETURN_MAX_C, abs=1e-6)


def test_no_flow_can_rescue_a_supply_that_is_already_too_warm(unit):
    """Above 42 - approach there is no headroom left, and the honest answer
    is None rather than an enormous flow."""
    import hybrid_supervisor as hs
    assert hs.required_secondary_flow(unit, 42.0) is None
    assert hs.required_secondary_flow(
        unit, cdu.COLD_PLATE_RETURN_MAX_C - unit.approach_k + 0.1) is None


def test_free_cooling_availability_follows_the_ashrae_class(unit):
    """A warmer class buys free-cooling hours. That is the whole reason the
    industry is moving up the W classes, and it is also what pushes the
    facility water toward the silica floor from the other side."""
    prev = None
    for cls in ("W17", "W27", "W32", "W40", "W45"):
        ok, _ = cdu.free_cooling_available(24.0, 4.0, 5.0, cls)
        if prev is not None:
            assert ok >= prev, "a warmer class cannot lose free cooling"
        prev = ok
    assert cdu.free_cooling_available(10.0, 4.0, 5.0, "W27")[0]
    assert not cdu.free_cooling_available(30.0, 4.0, 5.0, "W27")[0]
    with pytest.raises(ValueError, match="unknown ASHRAE class"):
        cdu.free_cooling_available(20.0, 4.0, 5.0, "W99")


# ---------------------------------------------------------------------------
# THE CHEMICAL FREE-COOLING FLOOR
# ---------------------------------------------------------------------------

def test_the_silica_floor_rises_with_cycles(water):
    """The coupling this module exists to expose: every cycle of
    concentration won -- water saved -- costs free-cooling headroom, because
    concentrating the water raises the temperature below which its silica
    precipitates. Monotone, and steep."""
    floors = [ch.temperature_floor_for_silica(water, c)
              for c in (3.0, 4.0, 5.0, 6.0, 7.0)]
    for a, b in zip(floors, floors[1:]):
        assert b > a, f"floor did not rise: {floors}"
    # steepness is the point; a shallow floor would make the trade academic
    assert floors[-1] - floors[0] > 20.0, floors


def test_at_the_floor_silica_is_exactly_at_saturation(water):
    """Definition check. Above the floor the water is safe, below it is not."""
    for c in (4.0, 5.0, 6.0):
        f = ch.temperature_floor_for_silica(water, c)
        conc = water.concentrate(c)
        assert ch.saturation_state(conc, f)["SI_silica_am"] == pytest.approx(
            0.0, abs=1e-3)
        assert ch.saturation_state(conc, f - 3.0)["SI_silica_am"] > 0.0
        assert ch.saturation_state(conc, f + 3.0)["SI_silica_am"] < 0.0


def test_acid_cannot_buy_back_the_floor(water):
    """Every other limit in this package moves with pH, which is why acid is
    a control lever at all. Silica does not, so the floor is a hard thermal
    boundary. An operator who has always solved scaling with acid has no
    lever here, and will not know it."""
    conc = water.concentrate(5.0)
    at_25 = [ch.saturation_state(conc, 25.0, pH=p)["SI_silica_am"]
             for p in (7.0, 7.5, 8.0, 8.5, 9.0)]
    assert max(at_25) - min(at_25) < 1e-9, at_25


def test_a_silica_free_water_has_no_floor(water):
    """The floor is a property of the water, not of the model. Remove the
    silica and free cooling becomes chemically unbounded."""
    import run_controller as rc
    bare = ch.Water(name="no silica", Na=water.Na, K=water.K, Ca=water.Ca,
                    Mg=water.Mg, Cl=water.Cl, SO4=water.SO4, HCO3=water.HCO3,
                    NO3=water.NO3, SiO2=0.0, PO4=water.PO4, pH=water.pH,
                    TDS=water.TDS)
    assert ch.temperature_floor_for_silica(bare, 6.0) == pytest.approx(1.0)


def test_the_floor_is_what_separates_blind_from_bounded(water):
    """The behavioural test. At a supply temperature below the floor the
    blind policy is in violation and the bounded one is not -- which is the
    entire product claim, reduced to two saturation indices."""
    cycles = 5.0
    floor = ch.temperature_floor_for_silica(water, cycles)
    conc = water.concentrate(cycles)
    limits = ch.OPERATING_LIMITS

    blind_t = floor - 8.0            # what a thermal optimiser would take
    blind = ch.saturation_state(conc, blind_t)["SI_silica_am"]
    bounded = ch.saturation_state(conc, floor)["SI_silica_am"]

    assert blind > limits["SI_silica_am"], (
        f"the blind point must actually violate: SI {blind:+.3f} at "
        f"{blind_t:.1f} C")
    assert bounded <= limits["SI_silica_am"] + 1e-6


# ---------------------------------------------------------------------------
# the scaling handoff, which is the reason the CDU lives inside Mizan
# ---------------------------------------------------------------------------

def test_the_cdu_evaluates_silica_cold_and_calcite_hot(unit, water):
    """The per-mineral evaluation point has to survive the handoff from the
    data-centre side to the water side, or the CDU would inherit exactly the
    single-temperature error the Mizan core was corrected for."""
    st = unit.solve(26.0, m_dot_pri_kg_s=250.0)
    sc = unit.scaling_state(st, water, 5.0, 8.25)
    assert sc["eval_point"]["SI_calcite"] == "hot"
    assert sc["eval_point"]["SI_silica_am"] == "cold"
    assert sc["t_wall_primary_c"] == st["t_wall_primary_c"]
    assert set(sc["SI"]) == set(ch.OPERATING_LIMITS)


def test_colder_facility_water_makes_the_plate_worse_for_silica(unit, water):
    """Stated as a test because it is the counter-intuitive half. Every other
    surface in this package gets safer as it cools."""
    cold = unit.scaling_state(unit.solve(20.0, 250.0), water, 5.0, 8.25)
    warm = unit.scaling_state(unit.solve(32.0, 250.0), water, 5.0, 8.25)
    assert cold["SI"]["SI_silica_am"] > warm["SI"]["SI_silica_am"]
    # and the retrograde species go the other way, on the same plate
    assert cold["SI"]["SI_calcite"] < warm["SI"]["SI_calcite"]


def test_makeup_chemistry_constrains_cdu_design_delta_t():
    """The coupling nothing in the CDU literature evaluates.

    A CDU's warmest acceptable facility water at design flow is
    42 - approach - design_delta_T. The makeup chemistry sets a FLOOR on that
    same temperature. They meet, and the meeting point is a capital decision.
    """
    from models import cdu_model as cdu
    import chemistry as chem
    import run_controller as rc

    floor5 = chem.temperature_floor_for_silica(rc.TSE, 5.0)
    assert 31.0 < floor5 < 33.0, floor5

    # Google Deschutes: tight approach, but a large design delta-T
    d = cdu.design_is_compatible(approach_k=3.0, design_delta_t_k=18.0,
                                 floor_c=floor5)
    assert d["t_fws_max_c"] == pytest.approx(21.0, abs=0.01)
    assert not d["compatible"], (
        "a Deschutes-class CDU cannot run at design flow against a 5-cycle "
        "silica floor, and that is the finding")

    # and the rule it implies
    assert d["max_design_delta_t_k"] == pytest.approx(42.0 - 3.0 - floor5,
                                                      abs=0.01)
    assert d["max_design_delta_t_k"] < 8.0, (
        "at five cycles on this water the design delta-T must be under half "
        "the Deschutes figure")


def test_a_tighter_approach_does_not_rescue_a_large_design_delta_t():
    """The result that is the opposite of the intuition.

    Going 5 K -> 3 K on the approach buys 2 K. Going 10 K -> 18 K on the
    design delta-T costs 8 K. The spec that looked like good news is worse
    overall, and worse again on pump power because a larger design delta-T
    means a smaller nominal flow and pump power is cubic in the flow ratio.
    """
    from models import cdu_model as cdu
    arch = cdu.max_facility_water_at_nominal_flow(5.0, 10.0)
    desch = cdu.max_facility_water_at_nominal_flow(3.0, 18.0)
    assert arch == pytest.approx(27.0)
    assert desch == pytest.approx(21.0)
    assert desch < arch, "the tighter approach loses to the larger delta-T"

    # nominal flow falls with design delta-T, so the same absolute duty needs
    # a larger flow RATIO, and the cube makes that expensive
    q = 9000.0
    lo = cdu.sized_for(q, delta_t_k=10.0).m_dot_sec_kg_s
    hi = cdu.sized_for(q, delta_t_k=18.0).m_dot_sec_kg_s
    assert hi < lo
    assert (lo / hi) ** 3 > 5.0, "the cubic penalty must be material"
