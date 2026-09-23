import dataclasses
import math
import pytest
import chemistry as chem
import discharge as dis


@pytest.mark.parametrize("table", [
    {}, {"nitrate": {"monthly_avg": 1.}},
    {"NO3": {"monthly_avg": math.nan}},
    {"NO3": {"monthly_avg": math.inf}},
    {"NO3": {"monthly_avg": -1.}},
    {"NO3": {}}, {"NO3": {"monthly_avrg": 1., "max": 10.}},
    {"NO3": {"monthly_avg": 1., "unit": "mg N/L"}},
    {"pH": {"min": 6., "max": 9.}},
])
def test_bad_permit_configuration_never_returns_a_ceiling(table):
    with pytest.raises(ValueError):
        dis.max_cycles_for_discharge(chem.ARAMCO_RIYADH_REFINERY_TSE, table=table)


@pytest.mark.parametrize("kw", [
    {"basis": "monthly_avrg"}, {"lo": 0.}, {"lo": math.nan},
    {"hi": math.inf}, {"lo": 5., "hi": 2.},
])
def test_bad_search_basis_and_range_are_rejected(kw):
    with pytest.raises(ValueError):
        dis.max_cycles_for_discharge(chem.ARAMCO_RIYADH_REFINERY_TSE, **kw)


@pytest.mark.parametrize("bad", [None, math.nan, math.inf, -1.])
def test_missing_or_invalid_assay_is_not_zero_concentration(bad):
    w = dataclasses.replace(chem.ARAMCO_RIYADH_REFINERY_TSE, NO3=bad)
    with pytest.raises(ValueError):
        dis.max_cycles_for_discharge(w)


def test_published_arithmetic_and_infeasibility_are_preserved():
    w = chem.ARAMCO_RIYADH_REFINERY_TSE
    maximum, parameter = dis.max_cycles_for_discharge(w, basis="max")
    assert maximum == pytest.approx(10./3.) and parameter == "NO3"
    assert dis.max_cycles_for_discharge(w)[0] == dis.INFEASIBLE
