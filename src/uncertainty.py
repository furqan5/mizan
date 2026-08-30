"""
MIZAN :: measurement-uncertainty propagation
============================================
The question this answers is the one a reviewer should ask: **is our model
error large compared with the experiment's own uncertainty, or comparable
to it?**

A model that agrees with an experiment to within the experiment's
measurement uncertainty cannot be improved further by that experiment. It
is the strongest statement a validation against a given dataset can make,
and it is much stronger than quoting an error in isolation.

The PSA dataset publishes its instrument uncertainties (README, Table
"Characteristics of instrumentation"), reproduced here verbatim:

    Water temperature (Pt100)      0.03 + 0.005*T   [degC]
    Cooling water flow (vortex)    +/- 0.65 % of reading
    Ambient temperature (Pt1000)   +/- 0.4 degC @ 20 degC
    Relative humidity (capacitive) +/- 3 % of reading @ 20 degC
    Air velocity (anemometer)      +/- 0.1 m/s + 1.5 % of reading

Method: Monte Carlo propagation (GUM Supplement 1 approach). Each measured
input is perturbed by its stated uncertainty, treated as the half-width of
a rectangular distribution converted to an equivalent standard uncertainty
(divide by sqrt(3)), and the model is re-solved. The spread of predicted
outlet temperature is the model's input-driven uncertainty.

Two separate quantities are reported and must not be confused:

  u_pred   uncertainty in the PREDICTED outlet temperature, caused by
           uncertainty in the measured inputs fed to the model
  u_meas   uncertainty in the MEASURED outlet temperature itself

The comparison band is the quadrature sum of the two: no model, however
perfect, can be shown to agree better than that.
"""
from __future__ import annotations

import json
import pathlib
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dataset as ds
import tower as tw

RESULTS = pathlib.Path(__file__).resolve().parents[1] / "results"
SQRT3 = np.sqrt(3.0)


def u_water_temp(T):
    """Standard uncertainty of a Pt100 water temperature [K]."""
    return (0.03 + 0.005 * np.asarray(T, float)) / SQRT3


def u_ambient_temp():
    """Standard uncertainty of the Pt1000 ambient temperature [K]."""
    return 0.4 / SQRT3


def u_rh(rh_pct):
    """Standard uncertainty of relative humidity [% points], 3 % of reading."""
    return 0.03 * np.asarray(rh_pct, float) / SQRT3


def u_water_flow(q):
    """Standard uncertainty of the vortex water flow [m3/h], 0.65 % o.r."""
    return 0.0065 * np.asarray(q, float) / SQRT3


def u_air_flow_frac():
    """Standard uncertainty of derived air mass flow, as a fraction.

    Air mass flow is not measured directly at every point; it comes from
    the facility correlation m_a = f(fan speed), itself fitted to
    anemometer traverses carrying +/- 0.1 m/s + 1.5 % of reading over nine
    quadrants. A 3 % standard uncertainty on m_a is a deliberately
    conservative stand-in for that chain. [A]
    """
    return 0.03


def propagate(df, c, n, n_samples=160, seed=20260829):
    """Monte Carlo propagation of input uncertainty through the model."""
    rng = np.random.default_rng(seed)
    rows = []
    for r in df.itertuples():
        preds = []
        for _ in range(n_samples):
            T_in = r.Tin + rng.normal(0.0, u_water_temp(r.Tin))
            T_amb = r.Tamb + rng.normal(0.0, u_ambient_temp())
            rh = np.clip((r.HR + rng.normal(0.0, u_rh(r.HR))) / 100.0, 0.01, 0.995)
            q = r.q + rng.normal(0.0, u_water_flow(r.q))
            m_w = q * ds.RHO_W / 3600.0
            m_a = float(tw.air_mass_flow_from_fan(r.w_fan)) * \
                (1.0 + rng.normal(0.0, u_air_flow_frac()))
            if m_a <= 0.05 or m_w <= 0:
                continue
            t, info = tw.solve_outlet_temperature(T_in, T_amb, rh, m_w, m_a, c, n)
            if info is not None and np.isfinite(t):
                preds.append(t)
        if len(preds) < 0.5 * n_samples:
            continue
        preds = np.asarray(preds)
        u_pred = float(preds.std(ddof=1))
        u_meas = float(u_water_temp(r.Tout))
        rows.append({
            "Tout_meas": r.Tout,
            "Tout_pred_mean": float(preds.mean()),
            "u_pred_K": u_pred,
            "u_meas_K": u_meas,
            "u_combined_K": float(np.hypot(u_pred, u_meas)),
            "residual_K": float(preds.mean() - r.Tout),
            "n_ok": len(preds),
        })
    return pd.DataFrame(rows)


def main():
    cal = json.loads((RESULTS / "calibration.json").read_text())
    c, n = cal["fill_c"], cal["fill_n"]
    all_df = ds.derive(ds.load_all())
    test = all_df[all_df.campaign.isin(cal["test_campaigns"])].reset_index(drop=True)

    print("Monte Carlo measurement-uncertainty propagation", flush=True)
    print(f"holdout campaigns {cal['test_campaigns']}, n={len(test)}, "
          f"160 samples per point\n", flush=True)

    u = propagate(test, c, n)
    u.to_csv(RESULTS / "uncertainty.csv", index=False)

    up = u.u_pred_K.mean()
    um = u.u_meas_K.mean()
    uc = u.u_combined_K.mean()
    mae = u.residual_K.abs().mean()
    rms = float(np.sqrt((u.residual_K ** 2).mean()))
    within = float((u.residual_K.abs() <= 2 * u.u_combined_K).mean() * 100)
    ratio = mae / uc

    print(f"  mean u(predicted T_out) from input uncertainty : {up:.3f} K")
    print(f"  mean u(measured  T_out) from the Pt100         : {um:.3f} K")
    print(f"  mean combined standard uncertainty u_c         : {uc:.3f} K")
    print(f"  expanded uncertainty U = 2*u_c (k=2, ~95 %)    : {2*uc:.3f} K")
    print()
    print(f"  model MAE on the same points                   : {mae:.3f} K")
    print(f"  model RMSE                                     : {rms:.3f} K")
    print(f"  MAE / u_c                                      : {ratio:.2f}")
    print(f"  points agreeing within U (k=2)                 : {within:.1f} %")
    print()
    if ratio <= 1.0:
        verdict = ("Model error is BELOW the combined measurement uncertainty. "
                   "The dataset cannot distinguish this model from a perfect "
                   "one.")
    elif ratio <= 2.0:
        verdict = ("Model error is COMPARABLE to the combined measurement "
                   "uncertainty (within a factor of two). Most of the residual "
                   "is plausibly experimental, not model deficiency.")
    else:
        verdict = ("Model error EXCEEDS the measurement uncertainty by more "
                   "than 2x. There is real model deficiency to explain.")
    print("  VERDICT:", verdict)

    out = {"u_pred_K": up, "u_meas_K": um, "u_combined_K": uc,
           "U_k2_K": 2 * uc, "model_MAE_K": mae, "model_RMSE_K": rms,
           "MAE_over_uc": ratio, "pct_within_U_k2": within,
           "verdict": verdict, "n_points": int(len(u))}
    (RESULTS / "uncertainty.json").write_text(json.dumps(out, indent=2),
                                              encoding="utf8")
    print(f"\nwritten -> {RESULTS/'uncertainty.json'}")


if __name__ == "__main__":
    main()
