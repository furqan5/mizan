import dataclasses
import json
from pathlib import Path
import pytest
import chemistry as chem
import controller as ctl


def test_same_tds_assays_never_share_cached_chemistry_or_feasibility():
    cal = json.loads((Path(__file__).resolve().parents[1] / "results" / "calibration.json").read_text())
    a = dataclasses.replace(chem.ARAMCO_FIELD_VALIDATED, name="synthetic A")
    dca = 100.
    dmg = (-2*dca/40.078 + dca/22.990)/(2/24.305-1/22.990)
    b = dataclasses.replace(a, name="synthetic B", Ca=a.Ca+dca,
                            Mg=a.Mg+dmg, Na=a.Na-dca-dmg)
    assert a.tds() == b.tds()
    assert a.charge_balance_pct() == pytest.approx(b.charge_balance_pct())
    assert sum(getattr(a,s) for s in chem.SPECIES) == pytest.approx(
        sum(getattr(b,s) for s in chem.SPECIES))
    cond = dict(Q_evap_kw=10000., m_w=478., m_a_rated=400.,
                p_fan_rated_kw=110., Q_nominal_kw=None, T_db=33., rh=.4, T_wi=38.)
    tariffs = dict(elec_per_kwh=.074, water_per_m3=3.11,
                   water_makeup_per_m3=2.144, water_discharge_per_m3=.971,
                   acid_per_kg=.19, antiscalant_per_m3=.05)
    cache = {}
    ctl._thermal_solve(75.,4.,cond,a,cal['fill_c'],cal['fill_n'],_cache=cache)
    warm = ctl._thermal_solve(75.,4.,cond,b,cal['fill_c'],cal['fill_n'],_cache=cache)
    fresh = ctl._thermal_solve(75.,4.,cond,b,cal['fill_c'],cal['fill_n'],_cache={})
    assert warm[4].Ca == pytest.approx(b.Ca*4.)
    rw = ctl._cost_at_ph(warm,75.,4.,8.25,cond,b,tariffs,None)
    rf = ctl._cost_at_ph(fresh,75.,4.,8.25,cond,b,tariffs,None)
    assert rw['SI_calcite'] == pytest.approx(rf['SI_calcite'],abs=1e-12)
    assert rw['feasible'] == rf['feasible'] is False
    assert rw['violations']['SI_calcite'] > 0.
