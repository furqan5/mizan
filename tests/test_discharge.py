"""The discharge ceiling, and the fact that it can bind harder than chemistry.

Until 11 September 2026 every ceiling in this package was a saturation limit.
A controller that recommends six cycles on a water whose blowdown breaches its
permit at one has not optimised anything. These tests fix the arithmetic of
the second ceiling and the one result that reorders the product.
"""

from __future__ import annotations

import pytest

import discharge as dis


@pytest.fixture(scope="module")
def water():
    import run_controller as rc
    return rc.TSE


# ---------------------------------------------------------------------------
# transcription
# ---------------------------------------------------------------------------

def test_the_rcer_limits_are_transcribed_as_published():
    """RCER-2015 Volume I, Table 3C pp. 63-64 and Table 3B p. 61, Jubail."""
    assert dis.RCER_TABLE_3C["P_as_P"]["max"] == 2.0
    assert dis.RCER_TABLE_3C["P_as_P"]["monthly_avg"] == 1.0
    assert dis.RCER_TABLE_3C["NO3"]["max"] == 10.0
    assert dis.RCER_TABLE_3C["NO3"]["monthly_avg"] == 1.0
    assert dis.RCER_TABLE_3C["pH"] == {"min": 6.0, "max": 9.0,
                                       "unit": "pH units"}
    assert dis.RCER_TABLE_3B_JUBAIL["TDS"]["max"] == 2000.0
    assert dis.RCER_TABLE_3B_JUBAIL["Cl"]["max"] == 1000.0


def test_the_phosphorus_conversion_is_elemental_not_molecular():
    """Table 3C limits 'Phosphorus, total as P'. The Aramco analysis reports
    'Phosphate total' by ASTM D515, which is as PO4. Confusing the two is a
    factor of 3.07 and would silently make the water look compliant."""
    assert dis.P_PER_PO4 == pytest.approx(30.974 / 94.971, rel=1e-9)
    assert dis.P_PER_PO4 == pytest.approx(0.3262, abs=1e-4)
    assert 8.0 * dis.P_PER_PO4 == pytest.approx(2.61, abs=0.01)


# ---------------------------------------------------------------------------
# the arithmetic
# ---------------------------------------------------------------------------

def test_blowdown_concentration_is_linear_in_cycles(water):
    for cy in (1.0, 2.0, 4.0):
        q = dis.blowdown_quality(water, cy)
        assert q["PO4"] == pytest.approx(water.PO4 * cy)
        assert q["Cl"] == pytest.approx(water.Cl * cy)
        assert q["TDS"] == pytest.approx(water.tds() * cy)
        assert q["P_as_P"] == pytest.approx(water.PO4 * cy * dis.P_PER_PO4)


def test_a_tighter_basis_can_only_lower_the_ceiling(water):
    c_max, _ = dis.max_cycles_for_discharge(water, basis="max")
    c_avg, _ = dis.max_cycles_for_discharge(water, basis="monthly_avg")
    assert c_avg <= c_max + 1e-9


def test_a_clean_water_is_not_capped(water):
    """The module must not report a ceiling where none exists, or it would be
    a constraint that always binds and therefore means nothing."""
    import chemistry as ch
    clean = ch.Water(name="clean", Ca=40.0, Mg=10.0, Na=30.0, Cl=50.0,
                     SO4=40.0, HCO3=60.0, NO3=0.2, PO4=0.1, SiO2=5.0,
                     pH=7.6, TDS=240.0)
    c, p = dis.max_cycles_for_discharge(clean, basis="monthly_avg")
    assert c > 2.0, (c, p)


# ---------------------------------------------------------------------------
# THE RESULT
# ---------------------------------------------------------------------------

def test_the_makeup_alone_breaches_the_phosphorus_limit(water):
    """The finding, stated as an assertion.

    Treated sewage effluent carrying 8 mg/L of total phosphate sits at
    2.61 mg/L as P BEFORE it is concentrated at all, against a Table 3C
    maximum of 2.0 and a monthly average of 1.0. Concentrating it is not the
    problem; using it is.
    """
    p_makeup = water.PO4 * dis.P_PER_PO4
    assert p_makeup > dis.RCER_TABLE_3C["P_as_P"]["max"], p_makeup
    assert p_makeup > dis.RCER_TABLE_3C["P_as_P"]["monthly_avg"]


def test_discharge_binds_harder_than_scaling_on_this_water(water):
    """The reordering. The engine computes a scaling ceiling near five cycles
    and the permit allows one. Every scaling number in this package is
    therefore MOOT for a Jubail site on this water, and saying so is the
    honest output.
    """
    b = dis.binding_ceiling(water, 45.0, 32.0, pH=8.25)
    assert b["binding"] == "DISCHARGE"
    assert b["discharge_cycles"] < b["scaling_cycles"]
    assert b["scaling_cycles"] > 4.0
    assert b["discharge_cycles"] <= 1.01
    # and the scaling answer must still be reported, not discarded
    assert b["scaling_mineral"] == "SI_silica_am"


def test_the_iwtp_route_is_capped_by_tds_not_by_nutrients(water):
    """The two routes bind on different parameters, which is the whole reason
    the operator has a choice to make."""
    c, p = dis.max_cycles_for_discharge(
        water, table=dis.RCER_TABLE_3B_JUBAIL, basis="max")
    assert p == "TDS"
    assert c == pytest.approx(2000.0 / water.tds(), rel=1e-3)


def test_the_module_declares_what_it_cannot_see(water):
    """A pass here is a pass on major ions. Table 3C also limits thirty-odd
    metals, organics and biological parameters that no major-ion analysis can
    produce. The result must carry that caveat rather than imply compliance.
    """
    b = dis.binding_ceiling(water, 45.0, 32.0, pH=8.25)
    assert "compliance statement" in b["caveat"]
    assert "Dhahran" in b["jurisdiction"], (
        "the result must state that RCER governs Jubail and Yanbu and not "
        "the city the makeup analysis actually came from")
