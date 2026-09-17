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


CAMPAIGNS = ("Exp1", "Exp2", "Exp3")

# Every variable the netCDF files carry. A duplicate is equal in ALL of them.
MEASURED_CHANNELS = ("Tin", "Tout", "Tamb", "HR", "q", "w_fan", "q_w_lost")


def load_all(deduplicate=True):
    """Load the three campaigns as one frame, one row per distinct measurement.

    DEFECT 51 (staged, 17 Sep 2026). The published files load as 165 rows but
    only 147 are distinct: all 17 rows of Exp3.nc are copies of Exp1 rows
    0-16, and Exp1 row 16 is also Exp2 row 113. The dataset README describes
    Exp3 as a different full-factorial campaign; the file does not contain
    it. Concatenating the files counted 18 measurements twice and put one
    training row in the holdout.

    With `deduplicate` (the default) each distinct measurement appears once.
    `campaign` is the first campaign it appears in (load order Exp1, Exp2,
    Exp3) and `campaigns` is the '+'-joined list of EVERY campaign it appears
    in, so a split can refuse to hold out a row it trained on. Use
    `split_holdout` for that rather than filtering on `campaign`.
    `deduplicate=False` returns the raw concatenation, for inspection only.
    """
    raw = pd.concat([load_campaign(n) for n in CAMPAIGNS], ignore_index=True)
    if not deduplicate:
        return raw
    cols = [c for c in MEASURED_CHANNELS if c in raw.columns]
    membership = {}
    for key, name in zip(raw[cols].itertuples(index=False, name=None),
                         raw["campaign"]):
        membership.setdefault(key, [])
        if name not in membership[key]:
            membership[key].append(name)
    out = raw.drop_duplicates(subset=cols, keep="first").reset_index(drop=True)
    out["campaigns"] = ["+".join(membership[k]) for k in
                        out[cols].itertuples(index=False, name=None)]
    return out


def in_campaigns(df, names):
    """Boolean mask: rows that appear in ANY of `names` (membership, not label)."""
    names = set(names)
    col = df["campaigns"] if "campaigns" in df else df["campaign"]
    return col.map(lambda s: bool(names & set(str(s).split("+"))))


def split_holdout(df, train_campaigns, test_campaigns):
    """Campaign-wise split that cannot leak.

    train   = every row appearing in a training campaign
    holdout = every row appearing in a test campaign AND in no training one
    """
    tr = in_campaigns(df, train_campaigns)
    te = in_campaigns(df, test_campaigns) & ~tr
    return df[tr].reset_index(drop=True), df[te].reset_index(drop=True)


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
    print("concatenated rows:", len(load_all(deduplicate=False)))
    a = derive(load_all())
    print("distinct rows:", len(a))
    print(a.describe().T.to_string(float_format=lambda x: f"{x:9.3f}"))
    print("\nnull counts:\n", a.isna().sum().to_string())
