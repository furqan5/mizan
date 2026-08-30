"""
MIZAN :: TRL-3 validation gates V1 and V2
=========================================
Thresholds are declared BEFORE any fit is run and printed before any result,
so the holdout cannot be tuned after the fact.

Split: calibrated on campaign Exp2 only, tested on Exp1 + Exp3 -- separate
experimental campaigns run in different seasons under different designs of
experiment. That is a harder and more honest test than a random row-wise
split, because it measures transfer across campaigns rather than
interpolation within one.

Method
------
The fill characteristic is identified the way cooling-tower practice
identifies it (CTI ATC-105), not by black-box search:

  1. For each measured point, integrate the Poppe equations from the
     MEASURED outlet temperature up to the measured inlet temperature. That
     yields the Merkel number the duty actually demanded, using measurements
     only -- no fitting, no free parameters.
  2. Regress log(Me) on log(m_w/m_a) over the training campaign. The fill
     law Me = c (m_w/m_a)^n is linear in these coordinates, so this is
     ordinary least squares with a closed-form answer.
  3. Predict outlet temperature FORWARD on the untouched holdout with the
     fitted law and score it.

Step 1 is one integration per row, so the whole identification costs
seconds. It is also more defensible than an optimiser: the fill law is
fitted to a physically-derived quantity rather than tuned to minimise the
score it is later graded on.

Gate V1  thermal   outlet water temperature MAE <= 1.0 K (target 0.5 K)
                   heat-rejection MAPE            <= 6 %
Gate V2  water     evaporation vs measured water loss MAPE <= 8 %
"""
from __future__ import annotations

import json
import pathlib
import sys
import time
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dataset as ds
import psychro as ps
import tower as tw

RESULTS = pathlib.Path(__file__).resolve().parents[1] / "results"
RESULTS.mkdir(exist_ok=True)

# ----- PRE-REGISTERED PASS/FAIL THRESHOLDS -------------------------------
THRESHOLDS = {
    "V1_Tout_MAE_K": 1.00,
    "V1_Tout_MAE_target_K": 0.50,
    "V1_Q_MAPE_pct": 6.00,
    "V2_evap_MAPE_pct": 8.00,
}
TRAIN_CAMPAIGNS = ["Exp2"]
TEST_CAMPAIGNS = ["Exp1", "Exp3"]


def demanded_merkel(df):
    """Merkel number demanded by each measured point (measurements only)."""
    Me, LG, evap, ok = [], [], [], []
    for r in df.itertuples():
        m_a = float(tw.air_mass_flow_from_fan(r.w_fan))
        w_in = float(ps.humidity_ratio_from_rh(r.Tamb, r.rh))
        res = tw.integrate_poppe(float(r.Tout), float(r.Tin), float(r.Tamb),
                                 w_in, float(r.m_w), m_a)
        if res is None or res["Me"] <= 0 or not np.isfinite(res["Me"]):
            Me.append(np.nan); LG.append(np.nan); evap.append(np.nan); ok.append(False)
        else:
            Me.append(res["Me"]); LG.append(r.m_w / m_a)
            evap.append(res["m_evap"] + tw.drift_loss(float(r.m_w)))
            ok.append(True)
    return np.array(Me), np.array(LG), np.array(evap), np.array(ok)


def fit_fill_law(Me, LG, ok):
    """OLS of log(Me) = log(c) + n log(L/G). Closed form, no search."""
    x = np.log(LG[ok])
    y = np.log(Me[ok])
    n, log_c = np.polyfit(x, y, 1)
    resid = y - (log_c + n * x)
    r2 = 1.0 - np.var(resid) / np.var(y)
    return float(np.exp(log_c)), float(n), float(r2)


def predict(df, c, n):
    """Forward-predict outlet temperature and evaporation."""
    T_out, evap, ok = [], [], []
    for r in df.itertuples():
        m_a = float(tw.air_mass_flow_from_fan(r.w_fan))
        t, info = tw.solve_outlet_temperature(float(r.Tin), float(r.Tamb),
                                              float(r.rh), float(r.m_w),
                                              m_a, c, n)
        if info is None:
            T_out.append(np.nan); evap.append(np.nan); ok.append(False)
        else:
            T_out.append(t)
            evap.append(info["m_evap"] + tw.drift_loss(float(r.m_w)))
            ok.append(True)
    return np.array(T_out), np.array(evap), np.array(ok)


def metrics(df, T_out, evap, ok):
    m = {"n_points": int(len(df)), "n_converged": int(ok.sum()),
         "convergence_pct": 100.0 * ok.sum() / len(df)}
    y = df["Tout"].values
    e = T_out[ok] - y[ok]
    m["Tout_MAE_K"] = float(np.mean(np.abs(e)))
    m["Tout_RMSE_K"] = float(np.sqrt(np.mean(e ** 2)))
    m["Tout_bias_K"] = float(np.mean(e))
    m["Tout_p95_abs_err_K"] = float(np.percentile(np.abs(e), 95))
    m["Tout_max_abs_err_K"] = float(np.max(np.abs(e)))
    Qm = df["Q_kW"].values[ok]
    Qp = df["m_w"].values[ok] * 4.186 * (df["Tin"].values[ok] - T_out[ok])
    m["Q_MAPE_pct"] = float(np.mean(np.abs((Qp - Qm) / Qm)) * 100)
    em, ep = df["m_evap_meas"].values[ok], evap[ok]
    g = np.isfinite(ep) & (em > 0)
    m["evap_MAPE_pct"] = float(np.mean(np.abs((ep[g] - em[g]) / em[g])) * 100)
    m["evap_bias_pct"] = float(np.mean((ep[g] - em[g]) / em[g]) * 100)
    return m


def main():
    print("=" * 74, flush=True)
    print("PRE-REGISTERED THRESHOLDS (declared before fitting):", flush=True)
    for k, v in THRESHOLDS.items():
        print(f"   {k:26s} {v}", flush=True)
    print(f"   train {TRAIN_CAMPAIGNS}   holdout {TEST_CAMPAIGNS}", flush=True)
    print("=" * 74, flush=True)

    all_df = ds.derive(ds.load_all())
    train = all_df[all_df.campaign.isin(TRAIN_CAMPAIGNS)].reset_index(drop=True)
    test = all_df[all_df.campaign.isin(TEST_CAMPAIGNS)].reset_index(drop=True)
    print(f"train n={len(train)}   holdout n={len(test)} (never seen during fit)\n",
          flush=True)

    t0 = time.time()
    Me, LG, _, ok = demanded_merkel(train)
    c, n, r2 = fit_fill_law(Me, LG, ok)
    print(f"identified fill law   Me = {c:.4f} * (m_w/m_a)^({n:.4f})", flush=True)
    print(f"   fitted on {ok.sum()}/{len(train)} training points, "
          f"log-space R2 = {r2:.4f}   [{time.time()-t0:.1f}s]\n", flush=True)

    out = {"fill_c": c, "fill_n": n, "fit_r2": r2, "thresholds": THRESHOLDS,
           "train_campaigns": TRAIN_CAMPAIGNS, "test_campaigns": TEST_CAMPAIGNS}

    for label, d in (("TRAIN", train), ("HOLDOUT", test)):
        T_out, evap, okp = predict(d, c, n)
        m = metrics(d, T_out, evap, okp)
        out[label] = m
        print(f"--- {label}  (n={m['n_points']}, converged {m['convergence_pct']:.1f}%)",
              flush=True)
        print(f"    Tout  MAE {m['Tout_MAE_K']:.3f} K   RMSE {m['Tout_RMSE_K']:.3f}   "
              f"bias {m['Tout_bias_K']:+.3f}   p95 {m['Tout_p95_abs_err_K']:.3f}",
              flush=True)
        print(f"    Q     MAPE {m['Q_MAPE_pct']:.2f} %", flush=True)
        print(f"    evap  MAPE {m['evap_MAPE_pct']:.2f} %  (bias {m['evap_bias_pct']:+.2f} %)\n",
              flush=True)

    m = out["HOLDOUT"]
    v1a = m["Tout_MAE_K"] <= THRESHOLDS["V1_Tout_MAE_K"]
    v1b = m["Q_MAPE_pct"] <= THRESHOLDS["V1_Q_MAPE_pct"]
    v2 = m["evap_MAPE_pct"] <= THRESHOLDS["V2_evap_MAPE_pct"]
    print("VERDICT on the untouched holdout, vs thresholds fixed in advance:",
          flush=True)
    print(f"   V1 thermal  Tout MAE  {m['Tout_MAE_K']:6.3f} <= 1.00 K   "
          f"{'PASS' if v1a else 'FAIL'}", flush=True)
    print(f"   V1 thermal  Q MAPE    {m['Q_MAPE_pct']:6.2f} <= 6.00 %   "
          f"{'PASS' if v1b else 'FAIL'}", flush=True)
    print(f"   V2 water    evap MAPE {m['evap_MAPE_pct']:6.2f} <= 8.00 %   "
          f"{'PASS' if v2 else 'FAIL'}", flush=True)
    out["verdict"] = {"V1_Tout": bool(v1a), "V1_Q": bool(v1b), "V2_evap": bool(v2)}

    (RESULTS / "calibration.json").write_text(json.dumps(out, indent=2), encoding="utf8")
    print(f"\nwritten -> {RESULTS / 'calibration.json'}", flush=True)


if __name__ == "__main__":
    main()
