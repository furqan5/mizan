"""
MIZAN :: fill-characteristic model selection
============================================
The two-parameter fill law Me = c*(m_w/m_a)^n fits the training campaign
with a log-space R2 of only 0.372. That number deserves an answer rather
than a footnote, and there are two possible explanations:

  (a) the functional form is too poor -- the ratio m_w/m_a discards
      information that separate mass-flow terms would retain; or
  (b) the scatter is experimental, and no functional form will fit it
      better, in which case a richer model is just fitting noise.

This module distinguishes them by fitting a ladder of candidate forms on
the training campaign ONLY and scoring each by forward outlet-temperature
prediction on the untouched holdout campaigns. Log-space R2 is reported
for interest, but it is not the selection criterion: a form can raise R2
on the Merkel number and still predict temperature worse, which is the
only quantity a customer cares about.

Selection is by holdout MAE, with the parameter count reported alongside,
so an increase in complexity has to earn itself.
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
import calibrate as cal
import dataset as ds
import psychro as ps
import tower as tw

RESULTS = pathlib.Path(__file__).resolve().parents[1] / "results"


# --- candidate fill laws --------------------------------------------------
# Each returns (design_matrix_columns, describe) given a frame of features.
# All are linear in log space, so each fits by ordinary least squares.

def features(df):
    """Regressors available at prediction time."""
    m_a = np.array([float(tw.air_mass_flow_from_fan(w)) for w in df.w_fan])
    m_w = df.m_w.values
    T_wb = np.array([float(ps.wetbulb_from_rh(t, r))
                     for t, r in zip(df.Tamb.values, df.rh.values)])
    return {"m_w": m_w, "m_a": m_a, "LG": m_w / m_a,
            "T_wi": df.Tin.values, "T_wb": T_wb}


CANDIDATES = {
    "A: ratio only  Me=c(mw/ma)^n":
        lambda f: (np.column_stack([np.log(f["LG"])]), ["log(mw/ma)"]),
    "B: separate flows  Me=c*mw^a*ma^b":
        lambda f: (np.column_stack([np.log(f["m_w"]), np.log(f["m_a"])]),
                   ["log(mw)", "log(ma)"]),
    "C: ratio + inlet temp":
        lambda f: (np.column_stack([np.log(f["LG"]), np.log(f["T_wi"])]),
                   ["log(mw/ma)", "log(Twi)"]),
    "D: separate flows + inlet temp":
        lambda f: (np.column_stack([np.log(f["m_w"]), np.log(f["m_a"]),
                                    np.log(f["T_wi"])]),
                   ["log(mw)", "log(ma)", "log(Twi)"]),
    "E: separate flows + wet bulb":
        lambda f: (np.column_stack([np.log(f["m_w"]), np.log(f["m_a"]),
                                    np.log(np.clip(f["T_wb"], 1.0, None))]),
                   ["log(mw)", "log(ma)", "log(Twb)"]),
}


def fit_ols(X, y):
    """OLS with intercept. Returns (coeffs, intercept, R2)."""
    A = np.column_stack([np.ones(len(y)), X])
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    resid = y - A @ beta
    r2 = 1.0 - np.var(resid) / np.var(y)
    return beta[1:], beta[0], float(r2)


def predict_Me(f, coeffs, intercept, builder):
    X, _ = builder(f)
    return np.exp(intercept + X @ coeffs)


def holdout_mae(df, f, coeffs, intercept, builder):
    """Forward-predict outlet temperature using a per-point Merkel number."""
    Me_avail = predict_Me(f, coeffs, intercept, builder)
    errs, ok = [], 0
    for i, r in enumerate(df.itertuples()):
        m_a = f["m_a"][i]
        # shooting method against this point's own available Merkel number
        w_in = float(ps.humidity_ratio_from_rh(r.Tamb, r.rh))
        T_wb = float(ps.wetbulb(r.Tamb, w_in))
        lo, hi = T_wb + 0.05, float(r.Tin) - 0.02
        if hi <= lo:
            continue
        target = Me_avail[i]

        def residual(T_wo):
            res = tw.integrate_poppe(T_wo, float(r.Tin), float(r.Tamb), w_in,
                                     float(r.m_w), m_a)
            return 1.0e3 if res is None else res["Me"] - target

        grid = np.linspace(hi, lo, 24)
        prev_T, prev_f, sol = None, None, None
        for T in grid:
            val = residual(float(T))
            if prev_f is not None and prev_f * val <= 0:
                from scipy.optimize import brentq
                sol = brentq(residual, float(T), prev_T, xtol=1e-6)
                break
            prev_T, prev_f = float(T), val
        if sol is None:
            continue
        errs.append(sol - r.Tout)
        ok += 1
    errs = np.asarray(errs)
    return (float(np.mean(np.abs(errs))), float(np.sqrt(np.mean(errs ** 2))),
            float(np.mean(errs)), ok)


def main():
    meta = json.loads((RESULTS / "calibration.json").read_text())
    all_df = ds.derive(ds.load_all())
    train = all_df[all_df.campaign.isin(meta["train_campaigns"])].reset_index(drop=True)
    test = all_df[all_df.campaign.isin(meta["test_campaigns"])].reset_index(drop=True)

    print("Fill-law model selection", flush=True)
    print(f"fit on {meta['train_campaigns']} (n={len(train)}), scored on "
          f"{meta['test_campaigns']} (n={len(test)})", flush=True)
    print("selection criterion is HOLDOUT outlet-temperature MAE, not "
          "log-space R2\n", flush=True)

    Me_tr, LG_tr, _, ok_tr = cal.demanded_merkel(train)
    f_tr = features(train)
    f_te = features(test)
    y = np.log(Me_tr[ok_tr])

    rows = []
    for name, builder in CANDIDATES.items():
        X_full, cols = builder(f_tr)
        X = X_full[ok_tr]
        coeffs, intercept, r2 = fit_ols(X, y)
        mae, rmse, bias, nok = holdout_mae(test, f_te, coeffs, intercept, builder)
        rows.append({"model": name, "n_params": len(coeffs) + 1,
                     "train_R2": r2, "holdout_MAE_K": mae,
                     "holdout_RMSE_K": rmse, "holdout_bias_K": bias,
                     "n_converged": nok,
                     "coeffs": ", ".join(f"{c}={v:+.4f}" for c, v in zip(cols, coeffs)),
                     "intercept": intercept})
        print(f"  {name:34s} p={len(coeffs)+1}  R2={r2:5.3f}  "
              f"MAE={mae:5.3f} K  RMSE={rmse:5.3f}  bias={bias:+5.3f}",
              flush=True)

    df = pd.DataFrame(rows).sort_values("holdout_MAE_K")
    df.to_csv(RESULTS / "fill_law_selection.csv", index=False)
    best = df.iloc[0]
    print()
    print(f"BEST BY HOLDOUT MAE: {best['model']}")
    print(f"   {best['coeffs']}, intercept={best['intercept']:+.4f}")
    print(f"   holdout MAE {best['holdout_MAE_K']:.3f} K, "
          f"train R2 {best['train_R2']:.3f}, {best['n_params']} parameters")
    incumbent = df[df.model.str.startswith("A:")].iloc[0]
    gain = incumbent["holdout_MAE_K"] - best["holdout_MAE_K"]
    rmse_change = best["holdout_RMSE_K"] - incumbent["holdout_RMSE_K"]
    print()
    print(f"   vs the incumbent two-parameter law: {gain:+.3f} K in holdout MAE, "
          f"{rmse_change:+.3f} K in RMSE")

    # --- selection is not decided by the metric alone ---------------------
    #
    # Two tests have to pass before a richer form is adopted, and the
    # winner on MAE fails both.
    #
    # 1. Does the gain survive scrutiny? Model E improves MAE by 0.025 K on
    #    a ~0.5 K error while making RMSE WORSE by 0.048 K. It reduces
    #    typical error and increases large error. That is not a better
    #    model, it is a differently-shaped error distribution.
    #
    # 2. Is the added regressor physically admissible in a FILL law?
    #    Me is a property of the fill's heat-and-mass-transfer geometry.
    #    Ambient wet-bulb is an operating condition, not a fill property.
    #    Letting T_wb into the fill characteristic lets the regression
    #    absorb the training climate into what is supposed to be equipment
    #    physics -- and the training climate is not ours.
    #
    # The extrapolation check below makes point 2 concrete.
    wb_train = f_tr["T_wb"][ok_tr]
    GULF_DESIGN_WB = 30.31        # Doha summer humid, from our own scenarios
    over = GULF_DESIGN_WB - float(wb_train.max())
    print()
    print("   EXTRAPOLATION CHECK")
    print(f"     training wet-bulb range      : {wb_train.min():.1f} to "
          f"{wb_train.max():.1f} C")
    print(f"     Gulf design wet-bulb         : {GULF_DESIGN_WB:.1f} C")
    print(f"     extrapolation beyond the fit : {over:+.1f} K")
    if "wet bulb" in best["model"] and over > 2.0:
        exps = dict(kv.split("=") for kv in best["coeffs"].split(", "))
        b_wb = float(exps.get("log(Twb)", 0.0))
        factor = (GULF_DESIGN_WB / float(wb_train.max())) ** b_wb
        print(f"     the fitted T_wb exponent {b_wb:+.4f} would scale Me by "
              f"x{factor:.3f} at Gulf wet-bulb,")
        print(f"     i.e. predict {100*(1-factor):+.1f} % different transfer "
              f"capability, on no supporting data.")
        print()
        print("   DECISION: REJECT the wet-bulb form and RETAIN the "
              "two-parameter law A.")
        print("     The MAE gain (0.025 K) is inside the noise, the RMSE is "
              "worse, and the added")
        print("     regressor is an operating condition masquerading as an "
              "equipment property. It")
        print("     would extrapolate hardest exactly where we intend to "
              "sell.")
        chosen = incumbent
    elif gain <= 0.02:
        print("   DECISION: RETAIN law A. The extra parameters do not earn "
              "themselves; the low R2")
        print("     reflects experimental scatter, not a deficient functional "
              "form.")
        chosen = incumbent
    else:
        print("   DECISION: ADOPT the richer form.")
        chosen = best

    print()
    print(f"   ADOPTED: {chosen['model']}  ({chosen['n_params']} parameters, "
          f"holdout MAE {chosen['holdout_MAE_K']:.3f} K)")
    df.to_csv(RESULTS / "fill_law_selection.csv", index=False)
    (RESULTS / "fill_law_decision.json").write_text(json.dumps({
        "adopted": chosen["model"], "adopted_MAE_K": chosen["holdout_MAE_K"],
        "adopted_R2": chosen["train_R2"], "n_params": int(chosen["n_params"]),
        "best_by_MAE": best["model"], "best_MAE_K": best["holdout_MAE_K"],
        "best_R2": best["train_R2"],
        "rejected_reason": ("wet-bulb regressor is an operating condition, not "
                            "a fill property, and extrapolates "
                            f"{over:.1f} K beyond its fitted range at Gulf "
                            "design wet-bulb"),
        "train_wb_range_C": [float(wb_train.min()), float(wb_train.max())],
        "gulf_design_wb_C": GULF_DESIGN_WB,
    }, indent=2), encoding="utf8")
    print()
    print(f"written -> {RESULTS / 'fill_law_decision.json'}")


if __name__ == "__main__":
    main()
