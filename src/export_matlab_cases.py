"""
Export a case file so the MATLAB twin can be checked against this core.

Both implementations must answer identical questions, so the questions are
written once, here, from the validated Python side. `matlab/mizan_verify.m`
reads this file and scores the agreement against thresholds fixed before it
was first run.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import chemistry as chem       # noqa: E402
import controller as ctl       # noqa: E402
import tower as tw             # noqa: E402
import water_activity as wa    # noqa: E402


def main():
    cal = json.loads((RESULTS / "calibration.json").read_text())
    fc, fn = cal["fill_c"], cal["fill_n"]
    rng = np.random.default_rng(20260830)

    cases = []
    tries = 0
    while len(cases) < 40 and tries < 400:
        tries += 1
        T_db = float(rng.uniform(12.0, 46.0))
        rh = float(rng.uniform(0.12, 0.80))
        m_w = float(rng.uniform(1.0, 4.0))
        m_a = float(rng.uniform(0.8, 3.2))
        T_wb = float(__import__("psychro").wetbulb_from_rh(T_db, rh))
        T_wi = T_wb + float(rng.uniform(6.0, 20.0))
        aw = float(wa.water_activity_tds(1500.0 * rng.uniform(1.0, 8.0)))
        T_wo, info = tw.solve_outlet_temperature(T_wi, T_db, rh, m_w, m_a,
                                                 fc, fn, aw=aw)
        if info is None or not np.isfinite(T_wo):
            continue
        cases.append({"T_wi": T_wi, "T_db": T_db, "rh": rh, "m_w": m_w,
                      "m_a": m_a, "aw": aw, "T_wo": float(T_wo),
                      "m_evap": float(info["m_evap"])})

    chiller = []
    for T_cws in (18.0, 22.0, 26.0, 29.44, 32.0, 34.5):
        for plr in (0.5, 0.8, 1.0):
            Q_ref = 10_000.0
            Q = Q_ref * plr
            P, _cop = ctl.chiller_power_biquad(Q, T_cws, 7.0, Q_ref_kw=Q_ref)
            chiller.append({"Q_evap_kW": Q, "T_cws": T_cws, "T_chws": 7.0,
                            "Q_ref_kW": Q_ref, "P_kW": float(P)})

    brucite = []
    for cyc in (3.0, 4.0, 6.0):
        for T in (30.0, 38.0, 46.0, 52.0):
            w = chem.balance_sodium(chem.ARAMCO_RECLAIMED)
            w.SiO2 = 26.8
            conc = w.concentrate(cyc)
            brucite.append({"cycles": cyc, "SiO2": 26.8, "T_c": T,
                            "pH_s": float(chem.ph_saturation_brucite(T, conc))})

    out = {"fill_c": fc, "fill_n": fn, "cases": cases,
           "chiller": chiller, "brucite": brucite,
           "note": "Written by src/export_matlab_cases.py for matlab/mizan_verify.m"}
    (RESULTS / "matlab_cases.json").write_text(json.dumps(out, indent=1))
    print(f"written -> {RESULTS/'matlab_cases.json'}  "
          f"({len(cases)} tower, {len(chiller)} chiller, {len(brucite)} brucite)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
