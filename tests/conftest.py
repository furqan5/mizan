"""Shared fixtures and path setup for the Mizan regression suite.

The package is a flat `src/` layout with no installable package, which is
deliberate (an edge controller ships without a third-party scientific
runtime). Tests therefore put `src/` on the path rather than importing an
installed distribution.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
RESULTS = ROOT / "results"
DOCS = ROOT / "docs"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _load(name: str):
    p = RESULTS / name
    if not p.exists():
        pytest.skip(f"results/{name} not present -- run the pipeline first")
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def controller_summary():
    return _load("controller_summary.json")


@pytest.fixture(scope="session")
def annual_dhahran():
    return _load("annual_dhahran.json")


@pytest.fixture(scope="session")
def field_validation():
    return _load("field_validation.json")


@pytest.fixture(scope="session")
def corrosion_floor():
    return _load("corrosion_floor.json")


@pytest.fixture(scope="session")
def aramco():
    import chemistry as ch
    return ch.ARAMCO_RECLAIMED


# Molar masses and charges, written here independently of src/chemistry.py so
# that a charge-balance test cannot be satisfied by the same table it is
# checking. [C: IUPAC 2021 standard atomic weights]
MW = {"Ca": 40.078, "Mg": 24.305, "Na": 22.990, "K": 39.098,
      "HCO3": 61.016, "SO4": 96.06, "Cl": 35.453, "NO3": 62.004}
Z = {"Ca": 2, "Mg": 2, "Na": 1, "K": 1,
     "HCO3": -1, "SO4": -2, "Cl": -1, "NO3": -1}
CATIONS = ("Ca", "Mg", "Na", "K")
ANIONS = ("HCO3", "SO4", "Cl", "NO3")


def charge_balance_pct(water) -> float:
    """Signed charge imbalance [%] on the meq/L convention used by every
    water-analysis laboratory: (cations - anions) / mean(cations, anions)."""
    cat = sum(getattr(water, k) / MW[k] * Z[k] for k in CATIONS)
    an = sum(getattr(water, k) / MW[k] * abs(Z[k]) for k in ANIONS)
    return 100.0 * (cat - an) / ((cat + an) / 2.0)


def ion_sum_mg_l(water) -> float:
    return sum(getattr(water, k) for k in MW) + getattr(water, "SiO2", 0.0)
