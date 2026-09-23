"""Review regressions; the historical tests and result files stay unchanged."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import chemistry as chem
import sidestream as ss


@pytest.mark.parametrize("pH, expected_si", [(9.0, 2.19737949955),
                                            (None, 2.30863604926)])
def test_already_supersaturated_lower_bound_is_not_a_ceiling(pH, expected_si):
    # Before the fix both calls returned (1.0, 'SI_calcite'), despite the
    # repository's unchanged SI_calcite <= 2.0 operating criterion.
    with pytest.raises(ss.InfeasibleCeilingError) as rejected:
        ss.ceiling_with(chem.DOE_SYN_MWW_COC4, 45.0, 30.0, pH=pH)
    reason = rejected.value
    assert reason.lower_bound_cycles == 1.0
    assert reason.binding_mineral == "SI_calcite"
    assert reason.limit == 2.0
    assert reason.saturation_index == pytest.approx(expected_si, abs=1e-9)
    assert reason.saturation_index > reason.limit
    assert "no numeric ceiling returned" in str(reason)


@pytest.mark.parametrize("pH, expected", [(8.25, 4.51710418235),
                                         (None, 1.55924665738)])
def test_admissible_search_keeps_existing_numeric_contract(pH, expected):
    cycles, mineral = ss.ceiling_with(
        chem.ARAMCO_RIYADH_REFINERY_TSE, 45.0, 30.0, pH=pH)
    assert isinstance(cycles, float)
    assert cycles == pytest.approx(expected, abs=1e-9)
    assert mineral == "SI_calcite"


def test_custom_lower_bound_is_not_mistaken_for_a_feasible_result():
    with pytest.raises(ss.InfeasibleCeilingError) as rejected:
        ss.ceiling_with(chem.ARAMCO_RIYADH_REFINERY_TSE, 45.0, 30.0,
                        pH=8.25, lo=5.0)
    assert rejected.value.lower_bound_cycles == 5.0
    assert rejected.value.saturation_index > rejected.value.limit
