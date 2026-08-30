"""
MIZAN :: PSA wet cooling tower dataset loader
=============================================
Source : Palenzuela, Roca & Serrano Rodriguez,
         "Steady-state operation dataset of an experimental Wet Cooling
         Tower pilot plant located at Plataforma Solar de Almeria",
         Zenodo record 10806201. Licensed CC BY 4.0.
Verified: sha/md5 ac94e0076a9217b58e032a2545bf9fc4 (matches Zenodo record).

Channels (dataset name -> meaning, units):
    Tamb      ambient dry-bulb temperature            [degC]
    HR        ambient relative humidity               [%]
    Tin       inlet (hot) cooling water temperature   [degC]
    Tout      outlet (cold) cooling water temperature [degC]
    q         cooling water volumetric flow rate      [m3/h]
    w_fan     fan feed frequency                      [% of 50 Hz]
    q_w_lost  water consumed by the cooling tower     [l/h]

`q_w_lost` is the channel that makes this dataset unusual and is why it was
chosen: it is a MEASURED water-consumption signal on the same rig and the
same operating points as the thermal measurements, so the evaporation model
and the thermal model are validated against one consistent experiment.
"""
from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd
from netCDF4 import Dataset

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "extracted" / "wct_pilot_plant_dataset" / "data"

RHO_W = 995.0        # density of water near 30 degC [kg/m3]


def load_campaign(name):
    """Load one campaign ('Exp1' | 'Exp2' | 'Exp3' | 'Complete')."""
    path = DATA / f"{name}.nc"
    with Dataset(path, "r") as nc:
        df = pd.DataFrame({v: np.asarray(nc.variables[v][:]).ravel()
                           for v in nc.variables})
    df["campaign"] = name
    return df


def load_all():
    """Load the three campaigns, tagged, as one frame."""
    return pd.concat([load_campaign(n) for n in ("Exp1", "Exp2", "Exp3")],
                     ignore_index=True)


def derive(df):
    """Add the engineering quantities the model needs."""
    out = df.copy()
    out["m_w"] = out["q"] * RHO_W / 3600.0                  # kg/s
    out["rh"] = out["HR"] / 100.0                           # fraction
    out["range_K"] = out["Tin"] - out["Tout"]               # K
    out["Q_kW"] = out["m_w"] * 4.186 * out["range_K"]       # kW
    if "q_w_lost" in out:
        out["m_evap_meas"] = out["q_w_lost"] / 3600.0       # l/h -> kg/s (rho~1)
    return out


if __name__ == "__main__":
    for n in ("Exp1", "Exp2", "Exp3", "Complete"):
        d = load_campaign(n)
        print(f"--- {n}: {len(d)} rows, cols={list(d.columns)}")
    print()
    a = derive(load_all())
    print("combined rows:", len(a))
    print(a.describe().T.to_string(float_format=lambda x: f"{x:9.3f}"))
    print("\nnull counts:\n", a.isna().sum().to_string())
