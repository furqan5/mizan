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


def _rank(c):
    """INFEASIBLE sorts below every feasible cycle count."""
    return -1.0 if dis.is_infeasible(c) else c


def test_a_tighter_basis_can_only_lower_the_ceiling(water):
    import chemistry as ch
    for w in (water, ch.ARAMCO_RIYADH_REFINERY_TSE):
        c_max, _ = dis.max_cycles_for_discharge(w, basis="max")
        c_avg, _ = dis.max_cycles_for_discharge(w, basis="monthly_avg")
        assert _rank(c_avg) <= _rank(c_max) + 1e-9, (w.name, c_max, c_avg)


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
    assert b["scaling_cycles"] > 4.0
    # DEFECT 69: the makeup breaches before concentration, so no cycle count
    # complies. This used to read 1.00, as if one cycle did.
    assert dis.is_infeasible(b["discharge_cycles"])
    assert dis.is_infeasible(b["cycles"])
    assert b["discharge_feasible"] is False
    # both nitrate and phosphorus breach at one cycle on this makeup
    assert b["parameter"] in ("NO3", "P_as_P")
    # and the scaling answer must still be reported, not discarded
    assert b["scaling_mineral"] == "SI_silica_am"


def test_defect_69_the_rcer_nitrate_monthly_average_admits_no_cycles():
    """RCER-2015 Vol. I Table 3C, printed p.63 / PDF p.77: Nitrate, mg/l,
    maximum 10, monthly average 1. The Riyadh assay carries NO3 3.0 mg/L, so
    the MAXIMUM allows 10/3 = 3.33 cycles -- the package's headline -- and the
    monthly average, the operative limit for continuous operation, allows
    none: the makeup is at three times it before it is concentrated."""
    import chemistry as ch
    w = ch.ARAMCO_RIYADH_REFINERY_TSE
    c_max, p_max = dis.max_cycles_for_discharge(w, basis="max")
    assert p_max == "NO3"
    assert c_max == pytest.approx(10.0 / 3.0, rel=1e-9)
    c_avg, p_avg = dis.max_cycles_for_discharge(w, basis="monthly_avg")
    assert dis.is_infeasible(c_avg) and p_avg == "NO3"
    assert w.NO3 > dis.RCER_TABLE_3C["NO3"]["monthly_avg"]


def test_defect_69_an_infeasible_search_never_returns_its_lower_bound():
    """Whatever `lo` is, a constraint already breached there must come back
    INFEASIBLE, never as the bound; and INFEASIBLE must refuse arithmetic, so
    no caller can mistake it for a cycle count."""
    import chemistry as ch
    w = ch.Water(name="nitrate-rich", Ca=40.0, Na=30.0, Cl=50.0, HCO3=60.0,
                 NO3=12.0, PO4=0.1, SiO2=5.0, pH=7.6, TDS=240.0)
    for lo in (1.0, 1.5, 2.0):
        c, p = dis.max_cycles_for_discharge(w, basis="max", lo=lo)
        assert dis.is_infeasible(c) and p == "NO3", (lo, c, p)
    with pytest.raises(TypeError):
        _ = dis.INFEASIBLE < 3.0
    # and a water feasible at lo still gets a number at or above lo
    ok = ch.Water(name="clean", NO3=2.0, PO4=0.1, Cl=50.0, TDS=240.0)
    c, p = dis.max_cycles_for_discharge(ok, basis="max")
    assert not dis.is_infeasible(c)
    assert c == pytest.approx(5.0, rel=1e-6) and p == "NO3"


def test_the_nitrate_basis_is_read_as_printed():
    """Table 3C names the basis for ammonia ("as N") and phosphorus ("as P")
    and not for nitrate, so the limit is carried as the ion. The alternative
    reading is recorded, not adopted: as N, 1 mg/L would be 4.43 mg/L as NO3
    and the monthly average would admit cycles up to 1.48 on this assay --
    and still not the daily-maximum 3.33."""
    import chemistry as ch
    n_to_no3 = 62.004 / 14.007
    assert n_to_no3 == pytest.approx(4.4267, abs=1e-4)
    w = ch.ARAMCO_RIYADH_REFINERY_TSE
    as_n = {"NO3": {"max": 10.0 * n_to_no3, "monthly_avg": 1.0 * n_to_no3}}
    c_avg_n, _ = dis.max_cycles_for_discharge(w, table=as_n,
                                               basis="monthly_avg")
    assert c_avg_n == pytest.approx(n_to_no3 / 3.0, rel=1e-6)
    assert dis.RCER_TABLE_3C["NO3"] == {"max": 10.0, "monthly_avg": 1.0,
                                        "unit": "mg/L"}


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
