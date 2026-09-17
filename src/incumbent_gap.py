"""
FURQAN / MIZAN :: the incumbent-gap study.
==========================================

How far are the cycles that incumbent practice permits from Mizan's
location-correct, multi-mineral ceiling, in which direction, and what is the
gap worth?

PRE-REGISTERED in docs/staged/incumbent_gap_preregistration.md, committed
before this file existed. Every parameter below is named there along with its
source. This module decides nothing on its own authority: it computes the
registered quantities and applies the registered verdict rules, and a failed
verdict is written to results/incumbent_gap.json as a failure.

It is deterministic and reads only repository data: the water analyses in
chemistry.py, the V5 ambients and tariffs in run_controller.py, and the fill
law in results/calibration.json.

    python src/incumbent_gap.py        -> results/incumbent_gap.json

It edits no behaviour in chemistry.py or controller.py. It imports them.
"""
from __future__ import annotations

import json
import math
import pathlib
import statistics
import sys
import warnings

import numpy as np
from scipy.optimize import brentq

warnings.filterwarnings("ignore")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import chemistry as chem       # noqa: E402
import controller as ctl       # noqa: E402
import corrosion               # noqa: E402
import sidestream as ss        # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUT = RESULTS / "incumbent_gap.json"
PREREG = "docs/staged/incumbent_gap_preregistration.md"

# ---- registered parameters (section 4 of the pre-registration) ------------
LO, HI = 1.0, 30.0                    # chemistry.max_cycles search range
ACID_PH = 7.8                         # [J] V5 incumbent baseline setpoint
ACID_PH_SWEEP = (7.5, 8.0, 8.25)      # 8.0 [C NACE 577]; 8.25 report example
DIURNAL_AMPLITUDE_K = 5.0             # scripts/ceiling_report.analyse default
P0_CYCLES = 3.0                       # [C] run_controller.V7_BASELINE_CYCLES
LSI_MAX = 2.5                         # [C] IWC-11-77, high-sulfate water
LSI_SWEEP = (0.5, 1.0, 1.4, 2.0, 2.5, 2.8)
RSI_MIN = 6.0                         # [C] UFC 3-230-13 S5-3.4.1
RSI_SWEEP = (4.0, 4.5, 5.1, 5.5, 6.0)
DEMADIS = {"pH>7.5": (100.0, 20_000.0), "pH<=7.5": (200.0, 40_000.0)}  # [C]
S_SWEEP = (100.0, 150.0, 200.0)
PI_SWEEP = (20_000.0, 25_000.0, 35_000.0, 40_000.0)
MG_BASES = ("CaCO3", "Mg")
CALCITE_ONLY_SI = chem.OPERATING_LIMITS["SI_calcite"]
H4_CYCLES = (3.0, 5.0, 7.0, 10.0)     # the review's grid
H4_PH = (7.5, 8.0, 8.5)
TOWER_KW = 4200.0                     # Badruzzaman (2022) tower
HOURS = 8760.0

# verdict thresholds (section 6)
H1_GAP, H1_SHARE = 1.0, 0.5
H2_GAP = 0.5
H3_GAP, H3_SHARE = 0.5, 0.5

PROVENANCE = {
    "ARAMCO_FIELD_VALIDATED": {
        "source": "Badruzzaman et al., Water Technology (2021) field analysis; "
                  "K, NO3 from WRI 28:100188 Table 1; Na-balanced",
        "silica": "ASSUMED 26.8 mg/L, imported from Salbukh brackish "
                  "groundwater (Al-Mutaz & Al-Anezi 2004)",
        "phosphate": "measured, 8.0 mg/L"},
    "ARAMCO_RIYADH_REFINERY_TSE": {
        "source": "AlMajnouni & Jaffer, NACE Paper 577, Table 1",
        "silica": "measured, 18.0 mg/L",
        "phosphate": "measured, 1.0 mg/L total"},
}


# ---------------------------------------------------------------------------
# root finding, identical in convention to chemistry.max_cycles
# ---------------------------------------------------------------------------
def _root(margin, lo=LO, hi=HI, tol=1e-3):
    """Highest cycles with margin >= 0, assuming margin falls with cycles."""
    if margin(lo) < 0:
        return float(lo)
    if margin(hi) > 0:
        return float(hi)
    return float(brentq(margin, lo, hi, xtol=tol))


def _ph(water, T_c, pH):
    """Regime pH: None means no acid, i.e. atmospheric CO2 equilibrium."""
    return chem.ph_atmospheric_equilibrium(water, T_c) if pH is None else float(pH)


# ---------------------------------------------------------------------------
# incumbent policies
# ---------------------------------------------------------------------------
def p1_lsi_ceiling(water, T_bulk, pH=ACID_PH, lsi_max=LSI_MAX):
    """P1: LSI at bulk temperature <= lsi_max."""
    def margin(cy):
        w = water.concentrate(cy)
        return lsi_max - chem.langelier_index(w, T_bulk, pH=_ph(w, T_bulk, pH))
    return _root(margin)


def p2_rsi_ceiling(water, T_bulk, pH=ACID_PH, rsi_min=RSI_MIN):
    """P2: Ryznar index at bulk temperature >= rsi_min."""
    def margin(cy):
        w = water.concentrate(cy)
        return corrosion.ryznar_index(w, T_bulk, pH=_ph(w, T_bulk, pH)) - rsi_min
    return _root(margin)


def demadis_row(water, T_bulk, pH):
    """Which row of the Demadis guideline applies. With no acid the free pH
    is lowest at one cycle and rises with concentration, so the makeup's free
    pH decides."""
    ph_eval = _ph(water, T_bulk, pH)
    return "pH>7.5" if ph_eval > 7.5 else "pH<=7.5"


def silica_rule_cycles(water, s_max):
    return HI if water.SiO2 <= 0 else min(HI, s_max / water.SiO2)


def mg_silica_rule_cycles(water, pi_max, mg_basis="CaCO3"):
    return min(HI, chem.max_cycles_mg_silicate(water, limit=pi_max,
                                               mg_basis=mg_basis))


def p3_ceiling(water, T_bulk, pH=ACID_PH, lsi_max=LSI_MAX, s_max=None,
               pi_max=None, mg_basis="CaCO3", c_p1=None):
    """P3: LSI bound AND silica rule of thumb AND Mg x SiO2 product rule."""
    row = demadis_row(water, T_bulk, pH)
    s_max = DEMADIS[row][0] if s_max is None else s_max
    pi_max = DEMADIS[row][1] if pi_max is None else pi_max
    c1 = p1_lsi_ceiling(water, T_bulk, pH, lsi_max) if c_p1 is None else c_p1
    parts = {"LSI": c1, "SiO2": silica_rule_cycles(water, s_max),
             "MgxSiO2": mg_silica_rule_cycles(water, pi_max, mg_basis)}
    binding = min(parts, key=parts.get)
    return {"cycles": parts[binding], "binding": binding, "row": row,
            "parts": parts, "s_max": s_max, "pi_max": pi_max,
            "mg_basis": mg_basis}


# ---------------------------------------------------------------------------
# Mizan
# ---------------------------------------------------------------------------
def mizan_ceiling(water, T_skin, T_basin, pH=ACID_PH, programme=None,
                  amplitude_k=DIURNAL_AMPLITUDE_K, report=True):
    """C_M exactly as registered: diurnal-margin saturation ceiling at the
    skin and the basin, brucite at the skin, Davies validity. The discharge
    ceiling, phosphate screen and silica validity are reported, not imposed."""
    lim = chem.limits_with_diurnal_margin(T_basin, amplitude_k,
                                          programme=programme)
    c_scale, b_scale = ss.ceiling_with(water, T_skin, T_basin, limits=lim,
                                       pH=pH, lo=LO, hi=HI)

    def brucite_margin(cy):
        w = water.concentrate(cy)
        if w.Mg <= 0 or w.SiO2 <= 0:
            return 1.0
        return chem.ph_saturation_brucite(T_skin, w) - _ph(w, T_skin, pH)

    c_bru = _root(brucite_margin)
    c_dav = ss.davies_validity_cycles(water, lo=LO, hi=HI)
    parts = {b_scale: c_scale, "brucite_mg_silicate": c_bru,
             "davies_range": c_dav}
    c_m = min(parts.values())
    binding = b_scale if c_scale <= c_m else min(parts, key=parts.get)
    out = {"cycles": c_m, "binding": binding, "scaling_cycles": c_scale,
           "scaling_binding": b_scale, "brucite_cycles": c_bru,
           "davies_cycles": c_dav,
           "davies_binds": bool(c_dav <= c_m and binding == "davies_range")}
    if not report:
        return out
    cy = max(c_m, 1.01)
    w = water.concentrate(cy)
    ph_hot, ph_cold = _ph(w, T_skin, pH), _ph(w, T_basin, pH)
    ph_free = chem.ph_atmospheric_equilibrium(w, T_skin)
    verdict, si_tcp = chem.phosphate_screen(w, T_skin, pH=ph_hot)
    out.update({
        "ph_free_at_skin": ph_free,
        "acid_unphysical": bool(pH is not None and ph_free < float(pH)),
        "silica_index_valid": chem.silica_index_valid_at_ph(ph_cold),
        "phosphate_screen": verdict, "SI_tcp": si_tcp,
        "phosphate_flagged": verdict.startswith("PHOSPHATE"),
        "SI_calcite_bulk_basin": chem.saturation_state(
            w, T_basin, pH=ph_cold)["SI_calcite"],
    })
    try:
        import discharge as dis
        d = dis.binding_ceiling(water, T_skin, T_basin,
                                pH=pH if pH is not None else 8.25,
                                basis="monthly_avg", limits=lim)
        out["discharge"] = {"cycles": d["discharge_cycles"],
                            "parameter": d["parameter"] if d["binding"] ==
                            "DISCHARGE" else None,
                            "would_bind": d["binding"] == "DISCHARGE",
                            "imposed": False}
    except Exception as exc:                        # reported, never fatal
        out["discharge"] = {"error": str(exc)}
    return out


def single_point_ceiling(water, T_c, pH, limits):
    """All listed minerals at one temperature and a fixed pH. Used by the
    tests to reproduce the calcite-only / gypsum-wall result through this
    harness rather than through chemistry.max_cycles."""
    def margin(cy):
        s = chem.saturation_state(water.concentrate(cy), T_c, pH=pH)
        return min(limits[k] - s[k] for k in limits)
    return _root(margin)


# ---------------------------------------------------------------------------
# H4: the review's grids
# ---------------------------------------------------------------------------
def grid_permits(policy, water, cond, cycles, pH):
    w = water.concentrate(cycles)
    T_ret, T_skin, T_basin = cond["T_return"], cond["T_skin"], cond["T_basin"]
    if policy == "P1":
        return chem.langelier_index(w, T_ret, pH=pH) <= LSI_MAX
    if policy == "calcite_only":
        return chem.saturation_state(w, T_skin, pH=pH)["SI_calcite"] <= CALCITE_ONLY_SI
    if policy == "bulk_only":
        s = chem.saturation_state(w, T_ret, pH=pH)
        return all(s[k] <= v for k, v in chem.OPERATING_LIMITS.items())
    if policy == "M":
        lim = chem.limits_with_diurnal_margin(T_basin, DIURNAL_AMPLITUDE_K)
        s = chem.saturation_state_split(w, T_skin, T_basin, pH_hot=pH, pH_cold=pH)
        if any(s[k] > v for k, v in lim.items()):
            return False
        if w.Mg > 0 and w.SiO2 > 0 and pH > chem.ph_saturation_brucite(T_skin, w):
            return False
        return not w.pitzer_required()
    raise ValueError(policy)


def grid_max(policy, water, cond):
    ok = [c for c in H4_CYCLES for p in H4_PH
          if grid_permits(policy, water, cond, c, p)]
    return max(ok) if ok else None


# ---------------------------------------------------------------------------
# conditions and money
# ---------------------------------------------------------------------------
def reference_conditions():
    """The V5 ambients, with temperatures taken from the incumbent baseline's
    own operating point (fixed 3.0 cycles, pH 7.8, 32 C setpoint)."""
    import run_controller as rc
    cal = json.loads((RESULTS / "calibration.json").read_text(encoding="utf-8"))
    fill_c, fill_n = cal["fill_c"], cal["fill_n"]
    out = []
    for name, T_db, rh_pct in rc.AMBIENTS:
        rh = rh_pct / 100.0
        T_wb = float(rc.ps.wetbulb_from_rh(T_db, rh))
        cond = dict(rc.PLANT)
        cond.update({"T_db": T_db, "rh": rh, "T_wi": T_wb + 12.0})
        seed = ctl._thermal_solve(70.0, 4.0, cond, rc.TSE, fill_c, fill_n)
        if seed is not None:
            cond["T_wo_guess"] = seed[2]
        b = ctl.baseline(cond, rc.TSE, rc.TARIFFS, fill_c, fill_n,
                         fixed_cycles=P0_CYCLES, fixed_ph=ACID_PH,
                         cw_setpoint_c=32.0, fan_grid=np.arange(30, 101, 10.0))
        out.append({"name": name, "T_db": T_db, "RH_pct": rh_pct, "T_wb": T_wb,
                    "fan_pct": float(b["fan_pct"]),
                    "T_return": float(b["T_wi"]), "T_basin": float(b["T_basin"]),
                    "T_skin": float(b["T_skin"]),
                    "m_evap_kg_s": float(b["m_evap_kg_s"]),
                    "Q_cond_kW": float(b["Q_cond_kW"]), "m_w_kg_s": float(cond["m_w"])})
    return out, rc.TARIFFS


def annual_water_cost(cond, cycles, tariffs):
    """USD/yr, makeup + discharge, 4.2 MW tower scaled from the V5 solve."""
    k = TOWER_KW / cond["Q_cond_kW"]
    wb = ctl.water_balance(cond["m_evap_kg_s"] * k, cond["m_w_kg_s"] * k,
                           max(float(cycles), 1.001))
    return ctl._water_cost_per_h(wb, tariffs) * HOURS


def money(cond, c_p, c_m, tariffs):
    d = annual_water_cost(cond, c_p, tariffs) - annual_water_cost(cond, c_m, tariffs)
    if c_p < c_m:
        return {"direction": "under", "under_cycling_value_usd_yr": d}
    return {"direction": "over", "break_even_usd_yr": -d}


# ---------------------------------------------------------------------------
# panel
# ---------------------------------------------------------------------------
def enumerate_panel():
    rows = []
    for attr in sorted(vars(chem)):
        w = getattr(chem, attr)
        if not isinstance(w, chem.Water):
            continue
        checks = chem.validate_analysis(w)
        failed = sorted(k for k, (ok, _d) in checks.items() if not ok)
        cb = w.charge_balance_pct()
        strict = not failed
        extended = strict or (failed == ["charge_balance"] and abs(cb) -
                              chem.ANALYSIS_TOLERANCES["charge_balance_pct"] <= 1.0)
        rows.append({"attr": attr, "name": w.name, "failed_checks": failed,
                     "charge_balance_pct": cb, "strict_panel": strict,
                     "extended_panel": extended,
                     **PROVENANCE.get(attr, {})})
    return rows


def _median(xs):
    return float(statistics.median(xs))


def analyse_water(water, conds, tariffs):
    per = []
    for c in conds:
        Tr, Ts, Tb = c["T_return"], c["T_skin"], c["T_basin"]
        row = {"condition": c["name"], "acid": {}, "no_acid": {}}
        for regime, pH in (("acid", ACID_PH), ("no_acid", None)):
            m = mizan_ceiling(water, Ts, Tb, pH=pH)
            c1 = p1_lsi_ceiling(water, Tr, pH)
            c2 = p2_rsi_ceiling(water, Tr, pH)
            p3 = p3_ceiling(water, Tr, pH, c_p1=c1)
            pol = {"P0": P0_CYCLES, "P1": c1, "P2": c2, "P3": p3["cycles"]}
            row[regime] = {
                "M": m, "P3_detail": p3,
                "cycles": {**pol, "M": m["cycles"]},
                "gap": {k: v - m["cycles"] for k, v in pol.items()},
                "at_bound": {k: bool(v >= HI - 1e-6 or m["cycles"] >= HI - 1e-6)
                             for k, v in pol.items()},
                "P1_at_basin": p1_lsi_ceiling(water, Tb, pH),
            }
            if regime == "acid":
                row[regime]["money"] = {k: money(c, v, m["cycles"], tariffs)
                                        for k, v in pol.items()}
                row[regime]["M_programme_standard"] = mizan_ceiling(
                    water, Ts, Tb, pH=pH, programme="standard",
                    report=False)["cycles"]
                row[regime]["P1_lsi_sweep"] = {
                    str(x): p1_lsi_ceiling(water, Tr, pH, x) for x in LSI_SWEEP}
                row[regime]["P2_rsi_sweep"] = {
                    str(x): p2_rsi_ceiling(water, Tr, pH, x) for x in RSI_SWEEP}
                row[regime]["P3_sweep"] = {
                    f"S{int(s)}_P{int(pi)}_{b}": p3_ceiling(
                        water, Tr, pH, s_max=s, pi_max=pi, mg_basis=b,
                        c_p1=c1)["cycles"]
                    for s in S_SWEEP for pi in PI_SWEEP for b in MG_BASES}
                sweep = {}
                for ph2 in ACID_PH_SWEEP:
                    m2 = mizan_ceiling(water, Ts, Tb, pH=ph2, report=False)
                    c12 = p1_lsi_ceiling(water, Tr, ph2)
                    sweep[str(ph2)] = {
                        "M": m2["cycles"], "M_binding": m2["binding"],
                        "P1": c12,
                        "P3": p3_ceiling(water, Tr, ph2, c_p1=c12)["cycles"]}
                row[regime]["pH_sweep"] = sweep
        per.append(row)

    acid = [r["acid"] for r in per]
    bindings = [a["M"]["binding"] for a in acid]
    mode = statistics.mode(bindings)
    cls = {"SI_silica_am": "silica-bound", "SI_calcite": "calcite-bound",
           "SI_gypsum": "gypsum-bound"}.get(mode, "other")
    summary = {
        "class": cls, "M_binding_by_condition": bindings,
        "phosphate_flagged": any(a["M"]["phosphate_flagged"] for a in acid),
        "median_gap_acid": {k: _median([a["gap"][k] for a in acid])
                            for k in ("P0", "P1", "P2", "P3")},
        "median_gap_no_acid": {k: _median([r["no_acid"]["gap"][k] for r in per])
                               for k in ("P0", "P1", "P2", "P3")},
        "median_cycles_acid": {k: _median([a["cycles"][k] for a in acid])
                               for k in ("P0", "P1", "P2", "P3", "M")},
        "median_cycles_no_acid": {k: _median([r["no_acid"]["cycles"][k] for r in per])
                                  for k in ("P0", "P1", "P2", "P3", "M")},
        "any_gap_at_bound_acid": {k: any(a["at_bound"][k] for a in acid)
                                  for k in ("P0", "P1", "P2", "P3")},
        "P3_variants_within_0_5": sorted(
            name for name in acid[0]["P3_sweep"]
            if abs(_median([a["P3_sweep"][name] - a["M"]["cycles"]
                            for a in acid])) <= H3_GAP),
        "money_median": {},
    }
    for k in ("P0", "P1", "P2", "P3"):
        ms = [a["money"][k] for a in acid]
        under = [x["under_cycling_value_usd_yr"] for x in ms if x["direction"] == "under"]
        over = [x["break_even_usd_yr"] for x in ms if x["direction"] == "over"]
        summary["money_median"][k] = {
            "conditions_under": len(under), "conditions_over": len(over),
            "under_value_median_usd_yr": _median(under) if under else None,
            "under_value_range_usd_yr": [min(under), max(under)] if under else None,
            "break_even_median_usd_yr": _median(over) if over else None,
            "break_even_range_usd_yr": [min(over), max(over)] if over else None}
    return {"per_condition": per, "summary": summary}


def h4_block(water, conds):
    rows = []
    for c in conds:
        rows.append({"condition": c["name"],
                     **{p: grid_max(p, water, c)
                        for p in ("P1", "M", "calcite_only", "bulk_only")}})
    return {"water": water.name, "rows": rows,
            "P1_equals_M_all": all(r["P1"] == r["M"] for r in rows),
            "calcite_only_equals_M_all": all(r["calcite_only"] == r["M"] for r in rows),
            "bulk_only_equals_M_all": all(r["bulk_only"] == r["M"] for r in rows)}


def verdicts(panel_results, h4, h4b):
    def share(pred):
        n = len(panel_results)
        return (sum(1 for r in panel_results.values() if pred(r["summary"])) / n
                if n else None)

    out = {}
    s1 = share(lambda s: abs(s["median_gap_acid"]["P1"]) >= H1_GAP)
    out["H1"] = {"share": s1, "n_waters": len(panel_results),
                 "verdict": "NOT TESTABLE" if s1 is None else
                 ("HOLDS" if s1 >= H1_SHARE else "FAILS")}
    silica = {k: r for k, r in panel_results.items()
              if r["summary"]["class"] == "silica-bound"}
    if not silica:
        out["H2"] = {"verdict": "NOT TESTABLE", "silica_bound_waters": []}
    else:
        ok = {k: all(a["acid"]["gap"]["P1"] >= H2_GAP for a in r["per_condition"])
              for k, r in silica.items()}
        out["H2"] = {"verdict": "HOLDS" if all(ok.values()) else "FAILS",
                     "silica_bound_waters": sorted(silica), "per_water": ok,
                     "min_gap": {k: min(a["acid"]["gap"]["P1"]
                                        for a in r["per_condition"])
                                 for k, r in silica.items()}}
    s3 = share(lambda s: abs(s["median_gap_acid"]["P3"]) <= H3_GAP)
    out["H3"] = {"share": s3, "n_waters": len(panel_results),
                 "verdict": "NOT TESTABLE" if s3 is None else
                 ("HOLDS" if s3 >= H3_SHARE else "FAILS")}
    out["H4"] = {"verdict": "HOLDS" if h4["P1_equals_M_all"] else "FAILS"}
    out["H4b"] = {"verdict": "HOLDS" if h4b["P1_equals_M_all"] else "FAILS"}
    return out


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (bool, np.bool_)):
        return bool(o)
    if isinstance(o, (float, np.floating)):
        f = float(o)
        return None if not math.isfinite(f) else round(f, 4)
    if isinstance(o, np.integer):
        return int(o)
    return o


def main():
    conds, tariffs = reference_conditions()
    panel = enumerate_panel()
    strict = [p["attr"] for p in panel if p["strict_panel"]]
    extended = [p["attr"] for p in panel if p["extended_panel"]]

    results = {a: analyse_water(getattr(chem, a), conds, tariffs) for a in extended}
    strict_res = {a: results[a] for a in strict}
    h4 = h4_block(chem.balance_sodium(chem.ARAMCO_RECLAIMED), conds)
    h4b = h4_block(chem.ARAMCO_FIELD_VALIDATED, conds)
    v = verdicts(strict_res, h4, h4b)
    v_ext = verdicts(results, h4, h4b)

    doc = {
        "preregistration": PREREG,
        "parameters": {
            "search_range": [LO, HI], "acid_pH": ACID_PH,
            "acid_pH_sweep": ACID_PH_SWEEP, "diurnal_amplitude_k": DIURNAL_AMPLITUDE_K,
            "P0_cycles": P0_CYCLES, "LSI_max": LSI_MAX, "RSI_min": RSI_MIN,
            "demadis_rows": DEMADIS, "skin_delta_k": ctl.SKIN_DELTA_K_DEFAULT,
            "tower_kW": TOWER_KW, "hours": HOURS,
            "tariffs": {k: tariffs[k] for k in ("water_makeup_per_m3",
                                                  "water_discharge_per_m3")}},
        "conditions": conds,
        "panel": panel, "strict_panel": strict, "extended_panel": extended,
        "waters": results,
        "H4_review_input": h4, "H4b_field_water": h4b,
        "verdicts": v, "verdicts_extended_panel": v_ext,
    }
    OUT.write_text(json.dumps(_clean(doc), indent=1), encoding="utf-8")

    print("INCUMBENT GAP -- pre-registered in", PREREG)
    for c in conds:
        print(f"  {c['name']:22s} T_return {c['T_return']:.2f}  T_skin "
              f"{c['T_skin']:.2f}  T_basin {c['T_basin']:.2f}  Q_cond "
              f"{c['Q_cond_kW']:.0f} kW")
    print("panel: strict", strict, "| extended", extended)
    for a, r in results.items():
        s = r["summary"]
        print(f"\n{a}  [{s['class']}; phosphate flagged {s['phosphate_flagged']}]")
        print("  M binding by condition:", s["M_binding_by_condition"])
        for reg in ("acid", "no_acid"):
            cy, gp = s[f"median_cycles_{reg}"], s[f"median_gap_{reg}"]
            print(f"  {reg:8s} median cycles " + "  ".join(
                f"{k} {cy[k]:.2f}" for k in cy) + " | gap " + "  ".join(
                f"{k} {gp[k]:+.2f}" for k in gp))
        for i, pc in enumerate(r["per_condition"]):
            a_ = pc["acid"]
            print(f"   {pc['condition']:22s} acid: M {a_['M']['cycles']:.2f} "
                  f"({a_['M']['binding']}) P1 {a_['cycles']['P1']:.2f} "
                  f"P2 {a_['cycles']['P2']:.2f} P3 {a_['cycles']['P3']:.2f} "
                  f"[{a_['P3_detail']['binding']}]  disc {a_['M'].get('discharge', {}).get('cycles')}"
                  f"  M_std {a_['M_programme_standard']:.2f}  pH sweep "
                  + " ".join(f"{k}:M{x['M']:.2f}/P1{x['P1']:.2f}/P3{x['P3']:.2f}"
                             for k, x in a_["pH_sweep"].items()))
        print("  P3 variants within 0.5:", s["P3_variants_within_0_5"])
        print("  money:", json.dumps(_clean(s["money_median"])))
    for tag, h in (("H4", h4), ("H4b", h4b)):
        print(f"\n{tag} {h['water']}")
        for row in h["rows"]:
            print("   ", row)
    print("\nVERDICTS (strict panel):", json.dumps(_clean(v)))
    print("VERDICTS (extended panel):", json.dumps(_clean(v_ext)))
    print("written ->", OUT)
    return doc


if __name__ == "__main__":
    main()
