"""MIZAN :: does holding cycles at 5 overstate what chemistry-awareness costs?

Pre-registered in docs/staged/cdu_joint_policy_preregistration.md, committed
before this script first ran. It runs once. Nothing in it scores a gate the
package already holds.

B0  blind free cooling, 5 cycles                     (the deck's baseline)
B1  chemically bounded at fixed 5 cycles             (the deck's policy)
B2  jointly choose cycles in 2..10 and the fan grid point, cheapest admissible
B1f B2 restricted to 5 cycles                         (decomposition only)

Plus S-OEM (the same three policies with the cold-plate return limit at 55 C),
the load-shape sensitivity L0-L3 on B0 silica scaling hours, the plausibility
checks and the defect-46 material boundary.

Everything the deck study sets is taken from the deck study's own code path.
`generate_pitch_artifacts.run_region` is executed unchanged, and the keyword
arguments it passes to `hybrid_supervisor.compare_blind_vs_bounded` are
captured, so the flow rates, CDU sizing and tariffs are never retyped.

Run: python src/cdu_joint_policy.py            (about 20-60 min, 4 processes)
     python src/cdu_joint_policy.py --smoke    (one hour of one region, no files)
"""
from __future__ import annotations

import csv
import dataclasses
import hashlib
import importlib.util
import json
import math
import pathlib
import sys
import time
from multiprocessing import Pool

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

OUT = ROOT / "results" / "cdu_joint_policy_20260917"
PREREG = ROOT / "docs" / "staged" / "cdu_joint_policy_preregistration.md"
NLR_CSV = pathlib.Path(r"C:\Users\Nouman\Desktop\Furqan's Docs\Startup Astra"
                       r"\results\nlr_power_20260917_v2\power_5min.csv")
CYCLES_GRID = list(range(2, 11))          # src/cdu_hybrid.py cygrid
TOL = 1e-3                                # defect 40
BASE_CYCLES = 5.0
OEM_RETURN_C = 55.0                       # [C] NVIDIA blog 21 Jun 2026: 45 C in, ~55 C out
L2_AMP, L3_AMP = 0.060, 0.155             # [C] PowerData2019 median / max diurnal amplitude
UPTIME_PUE_2025 = 1.54                    # [C] Uptime Institute survey 2025
FLOW_RATIO_FLAG = 1.5                     # [J]
H_FG_MJ_KG = 2.4                          # [J] physics bound
ALFA_LAVAL_FHE_316 = {25.0: {3: 80, 5: 300, 7: 1000, 9: 6000},     # [C] Table 1
                      50.0: {3: 15, 5: 80, 7: 300, 9: 1500},
                      80.0: {3: 8, 5: 30, 7: 100, 9: 600}}
KEEP = ("cycles", "fan_pct", "T_fws_c", "T_wall_primary_c", "T_sec_return_c",
        "chemical_floor_c", "floor_unreachable", "cost_per_h", "makeup_m3_h",
        "blowdown_m3_h", "P_fan_kW", "P_pump_pri_kW", "P_pump_sec_kW",
        "P_facility_kW", "P_it_kW", "PUE", "WUE_L_per_kWh",
        "secondary_flow_ratio", "SI", "violations")


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def _load_gpa():
    spec = importlib.util.spec_from_file_location(
        "generate_pitch_artifacts", ROOT / "scripts" / "generate_pitch_artifacts.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _memoise(hs):
    orig = hs.solve_free_cooling
    if getattr(orig, "_memo", False):
        return
    cache = {}

    def memo(T_db, rh, m_w_pri, q_total_kw, fan_pct, m_a_rated, fill_c, fill_n,
             aw=1.0, **kw):
        key = tuple(float(x) for x in (T_db, rh, m_w_pri, q_total_kw, fan_pct,
                                       m_a_rated, fill_c, fill_n, aw)) + tuple(sorted(kw.items()))
        if key not in cache:
            cache[key] = orig(T_db, rh, m_w_pri, q_total_kw, fan_pct, m_a_rated,
                              fill_c, fill_n, aw=aw, **kw)
        return cache[key]
    memo._memo = True
    hs.solve_free_cooling = memo


def _slim(e):
    return None if e is None else {k: e[k] for k in KEEP}


def _admissible(e):
    return (e is not None and not e["floor_unreachable"]
            and all(v <= TOL for v in e["violations"].values()))


def _joint(hs, chem, kw, cycles_set):
    """Cheapest admissible (cycles, fan) state; None when nothing is admissible."""
    base = {k: v for k, v in kw.items() if k != "cycles"}
    q_guess = kw["q_it_kw"] * hs.LOOP_HEAT_FACTOR
    best, n_cand, n_adm = None, 0, 0
    for c in cycles_set:
        floor = chem.temperature_floor_for_silica(kw["makeup"], float(c))
        cands = [hs.evaluate(enforce_chemical_floor=True, cycles=float(c), **base)]
        for f in hs.fan_grid():
            st = hs.solve_free_cooling(kw["T_db"], kw["rh"], kw["m_w_pri"], q_guess, f,
                                       kw["m_a_rated"], kw["fill_c"], kw["fill_n"])
            if st is None or st["T_fws"] < floor:
                continue
            cands.append(hs.evaluate(enforce_chemical_floor=True, cycles=float(c),
                                     tower_state=(f, st), **base))
        for e in cands:
            n_cand += 1
            if _admissible(e):
                n_adm += 1
                if best is None or e["cost_per_h"] < best["cost_per_h"]:
                    best = e
    return best, n_cand, n_adm


def run_region(key, smoke=False):
    t0 = time.time()
    gpa = _load_gpa()
    import hybrid_supervisor as hs
    import chemistry as chem
    import run_controller as rc
    _memoise(hs)
    cal = json.loads((ROOT / "results" / "calibration.json").read_text())
    cfg = dict(gpa.REGIONS[key])
    captured = []
    orig_cmp = hs.compare_blind_vs_bounded

    def capture(**kw):
        captured.append(dict(kw))
        return orig_cmp(**kw)
    hs.compare_blind_vs_bounded = capture
    if smoke:
        full_profile = gpa.diurnal_profile
        gpa.diurnal_profile = lambda spec: (full_profile(spec)[0][14:15], full_profile(spec)[1])
    deck = gpa.run_region(key, cfg, rc.TSE, cal["fill_c"], cal["fill_n"])
    hs.compare_blind_vs_bounded = orig_cmp
    print(f"[{key}] deck path B0/B1 done {time.time()-t0:.0f}s", flush=True)

    hours = []
    for t, (kw, row) in enumerate(zip(captured, deck["rows"])):
        b0, b1 = row["blind"], row["bounded"]
        rec = {"hour": t, "T_db": kw["T_db"], "rh": kw["rh"], "B0": _slim(b0), "B1": _slim(b1)}
        b2, nc, na = _joint(hs, chem, kw, CYCLES_GRID)
        rec.update(B2=_slim(b2), B2_candidates=nc, B2_admissible=na)
        b1f, _, _ = _joint(hs, chem, kw, [int(BASE_CYCLES)])
        rec["B1f"] = _slim(b1f)
        # S-OEM: identical tower states, cold-plate return limit at the OEM point
        ko = dict(kw, unit=dataclasses.replace(kw["unit"], return_limit_c=OEM_RETURN_C))
        base_o = {k: v for k, v in ko.items() if k != "cycles"}
        rec["OEM_B0"] = _slim(hs.evaluate(enforce_chemical_floor=False, cycles=BASE_CYCLES, **base_o))
        rec["OEM_B1"] = _slim(hs.evaluate(enforce_chemical_floor=True, cycles=BASE_CYCLES, **base_o))
        ob2, _, _ = _joint(hs, chem, ko, CYCLES_GRID)
        rec["OEM_B2"] = _slim(ob2)
        hours.append(rec)
        print(f"[{key}] hour {t} {time.time()-t0:.0f}s", flush=True)

    # load shapes, B0 only; the plant (flows, CDU nominal) stays at nameplate
    temps = [kw["T_db"] for kw in captured]
    t_cold = temps.index(min(temps))
    fr_nlr = _nlr_fraction()
    shapes = {"L1_NLR_flat": [fr_nlr] * len(captured)}
    for name, amp in (("L2_PowerData_median", L2_AMP), ("L3_PowerData_max", L3_AMP)):
        shapes[name] = [1.0 - amp * (1.0 + math.cos(2 * math.pi * (t - t_cold) / 24.0)) / 2.0
                        for t in range(len(captured))]
    load = {}
    for name, fr in shapes.items():
        rows = []
        for kw, f in zip(captured, fr):
            k2 = dict(kw, q_it_kw=kw["q_it_kw"] * f,
                      unit=dataclasses.replace(kw["unit"], q_it_kw=kw["unit"].q_it_kw * f))
            base2 = {k: v for k, v in k2.items() if k != "cycles"}
            rows.append(_slim(hs.evaluate(enforce_chemical_floor=False, cycles=BASE_CYCLES, **base2)))
        load[name] = {"fractions": fr, "B0": rows}
    print(f"[{key}] done {time.time()-t0:.0f}s", flush=True)
    deck_fields = {k: v for k, v in deck.items() if k != "rows"}
    return key, {"deck_path_summary": deck_fields, "hours": hours, "load": load,
                 "t_cold_hour": t_cold, "elapsed_s": time.time() - t0}


def _nlr_fraction():
    with open(NLR_CSV, newline="", encoding="utf-8") as fh:
        vals = [float(r["combined_mean_kW"]) for r in csv.DictReader(fh)
                if float(r["coverage_fraction"]) >= 1.0]
    return (sum(vals) / len(vals)) / max(vals)


# ------------------------------------------------------------------ scoring
def _sil(e):
    return e["SI"]["SI_silica_am"] if e else None


def aggregate(hours, p0, pk, fallback=None):
    solved = [h for h in hours if h["B0"] and h["B1"]]
    n = len(solved)

    def st(h, p):
        e = h[p]
        if e is None and fallback:
            e = h[fallback]
        return e
    tot = lambda p, f: sum(st(h, p)[f] for h in solved)
    b0c, kc = tot(p0, "cost_per_h"), tot(pk, "cost_per_h")
    b0w, kw_ = tot(p0, "makeup_m3_h"), tot(pk, "makeup_m3_h")
    it, fac = tot(pk, "P_it_kW"), tot(pk, "P_facility_kW")
    return {
        "solved_hours": n,
        "cost_delta_vs_B0_usd_yr": (kc - b0c) * 365.0,
        "water_m3_day": kw_ * 24.0 / n, "water_delta_pct_vs_B0": 100.0 * (kw_ - b0w) / b0w,
        "silica_scaling_hours": sum(1 for h in solved if _sil(st(h, pk)) > TOL),
        "any_mineral_material_hours": sum(1 for h in solved
                                          if any(v > TOL for v in st(h, pk)["violations"].values())),
        "floor_unreachable_hours": sum(1 for h in solved if st(h, pk)["floor_unreachable"]),
        "infeasible_hours_fallback": sum(1 for h in solved if h[pk] is None) if fallback else 0,
        "PUE_mean_of_hours": sum(st(h, pk)["PUE"] for h in solved) / n,
        "PUE_ratio_of_totals": (it + fac) / it,
        "max_secondary_flow_ratio": max(st(h, pk)["secondary_flow_ratio"] for h in solved),
        "hours_flow_ratio_over_flag": sum(1 for h in solved
                                          if st(h, pk)["secondary_flow_ratio"] > FLOW_RATIO_FLAG),
        "hours_PUE_over_uptime_avg": sum(1 for h in solved if st(h, pk)["PUE"] > UPTIME_PUE_2025),
        "max_P_pump_sec_kW": max(st(h, pk)["P_pump_sec_kW"] for h in solved),
        "mean_P_fan_kW": tot(pk, "P_fan_kW") / n, "mean_P_pump_sec_kW": tot(pk, "P_pump_sec_kW") / n,
        "T_fws_range_c": [min(st(h, pk)["T_fws_c"] for h in solved), max(st(h, pk)["T_fws_c"] for h in solved)],
        "max_T_wall_primary_c": max(st(h, pk)["T_wall_primary_c"] for h in solved),
        "cycles_chosen": {str(c): sum(1 for h in solved if st(h, pk)["cycles"] == c)
                          for c in sorted({st(h, pk)["cycles"] for h in solved})},
        "WUE_max_L_kWh": max(st(h, pk)["WUE_L_per_kWh"] for h in solved),
    }


def score(results):
    import chemistry as chem
    import corrosion
    import run_controller as rc
    from models import cdu_model as cdu
    stored = json.loads((ROOT / "results" / "pitch_artifacts.json").read_text())["regions"]
    regions, verdict_rows = {}, []
    for key, r in results.items():
        H = r["hours"]
        agg = {"B0": aggregate(H, "B0", "B0"), "B1": aggregate(H, "B0", "B1"),
               "B2": aggregate(H, "B0", "B2", fallback="B1"),
               "B1f": aggregate(H, "B0", "B1f", fallback="B1")}
        oem = {"B0": aggregate(H, "OEM_B0", "OEM_B0"), "B1": aggregate(H, "OEM_B0", "OEM_B1"),
               "B2": aggregate(H, "OEM_B0", "OEM_B2", fallback="OEM_B1")}
        d1, d2 = agg["B1"]["cost_delta_vs_B0_usd_yr"], agg["B2"]["cost_delta_vs_B0_usd_yr"]
        supports = bool(d1 > 0 and d2 <= 0.5 * d1)
        verdict_rows.append(supports)
        s = stored.get(key, {})
        stale = {f: {"stored": s.get(f), "now": r["deck_path_summary"].get(f)}
                 for f in ("PUE_blind", "PUE_bounded", "WUE_blind", "WUE_bounded",
                           "cost_delta_per_year_usd", "hours_blind_materially_violating",
                           "hours_bounded_materially_violating", "hours_floor_unreachable",
                           "max_silica_SR_blind", "max_silica_SR_bounded", "solved_hours",
                           "chemical_floor_c", "max_secondary_flow_ratio")}
        # WUE ceiling, B0 and B1 each hour
        wue_viol = 0
        for h in H:
            for p in ("B0", "B1"):
                e = h[p]
                if not e:
                    continue
                c = e["cycles"]
                bound = (3.6 / H_FG_MJ_KG) * c / (c - 1.0) * (1.0 + e["P_facility_kW"] / e["P_it_kW"]) * 1.05
                wue_viol += e["WUE_L_per_kWh"] > bound
        L0 = agg["B0"]["silica_scaling_hours"]
        load = {"L0_flat_1.00": {"silica_scaling_hours": L0}}
        for name, v in r["load"].items():
            rows = [e for e in v["B0"] if e]
            load[name] = {"fraction_min": min(v["fractions"]), "fraction_max": max(v["fractions"]),
                          "solved": len(rows),
                          "silica_scaling_hours": sum(1 for e in rows if _sil(e) > TOL),
                          "delta_vs_L0": sum(1 for e in rows if _sil(e) > TOL) - L0}
        regions[key] = {"label": r["deck_path_summary"]["label"], "base": agg, "S_OEM_return_55C": oem,
                        "H_B2_region_supports": supports, "H_B2_scoreable": d1 > 0,
                        "deck_table_staleness": stale, "WUE_bound_violations": int(wue_viol),
                        "load_shape": load, "t_cold_hour": r["t_cold_hour"], "elapsed_s": r["elapsed_s"]}
    n_sup = sum(verdict_rows)
    counts = [v["load_shape"][k]["silica_scaling_hours"] for v in regions.values() for k in v["load_shape"]]
    moved = any(abs(v["load_shape"][k].get("delta_vs_L0", 0)) >= 3
                for v in regions.values() for k in v["load_shape"])
    lo_range = [min(counts), max(counts)]
    # materials, defect 46
    ph = 8.25
    max_wall = max(v["base"][p]["max_T_wall_primary_c"] for v in regions.values() for p in ("B0", "B1"))
    row_t = min(t for t in ALFA_LAVAL_FHE_316 if t >= max_wall) if max_wall <= 80 else None
    al = None
    if row_t is not None:
        tab = ALFA_LAVAL_FHE_316[row_t]
        al = tab[7] + (tab[9] - tab[7]) * (ph - 7.0) / 2.0
    mats = {"alfa_laval_fhe_316": {"wall_T_used_c": max_wall, "table_row_c": row_t, "pH": ph, "limit_mg_l": al}}
    for wname, w in (("ARAMCO_RIYADH_REFINERY_TSE", chem.ARAMCO_RIYADH_REFINERY_TSE),
                     ("run_controller.TSE", rc.TSE)):
        mats[wname] = {"Cl_mg_l": w.Cl,
                       "janikowski_304_max_cycles": corrosion.chloride_pitting_check(w, 1.0, "304_stainless")["max_cycles_on_chloride"],
                       "janikowski_316_max_cycles": corrosion.chloride_pitting_check(w, 1.0, "316_stainless")["max_cycles_on_chloride"],
                       "alfa_laval_fhe_316_max_cycles": (al / w.Cl) if al else None,
                       "silica_floor_5cy_c": chem.temperature_floor_for_silica(w, 5.0),
                       "silica_floor_4cy_c": chem.temperature_floor_for_silica(w, 4.0),
                       "duplex_2205": "no cited criterion held; not derived",
                       "titanium": "no cited criterion held; not derived",
                       "copper_nickel": "no cited criterion held (corrosion.py records none); not derived"}
    # cdu_hybrid temperatures (P-T)
    states = json.loads((ROOT / "results" / "cdu_hybrid_verified" / "states.json").read_text())
    ptc = {"cdu_hybrid_T_fws_range_c": [min(s["T_fws_C"] for s in states), max(s["T_fws_C"] for s in states)],
           "cdu_hybrid_T_gpu_inlet_water_range_c": [min(s["T_gpu_inlet_water_C"] for s in states),
                                                    max(s["T_gpu_inlet_water_C"] for s in states)],
           "cdu_hybrid_states_with_chiller": sum(1 for s in states if s.get("P_chiller_kW", 0) > 0),
           "cdu_hybrid_states": len(states),
           "supervisor_nominal_flow_T_fws_max_c_at_42C_return": cdu.max_facility_water_at_nominal_flow(5.0, 10.0),
           "supervisor_nominal_flow_T_fws_max_c_at_55C_return": cdu.max_facility_water_at_nominal_flow(5.0, 10.0, OEM_RETURN_C),
           "model_return_limit_c": cdu.COLD_PLATE_RETURN_MAX_C, "model_cdu_approach_k": 5.0,
           "deschutes_approach_k": cdu.DESCHUTES_SPEC["approach_k"], "model_heat_to_liquid": 1.0}
    return {"H_B2": {"regions_supporting": n_sup, "status": "PASS" if n_sup >= 3 else "FAIL",
                     "rule": "delta2 <= 0.5*delta1 in >= 3 of 4 regions; delta1 <= 0 counts against"},
            "load_shape_verdict": {"depends_on_load_shape": bool(moved or lo_range[0] < 12 or lo_range[1] > 24),
                                   "any_region_moved_3h_or_more": bool(moved), "count_range": lo_range,
                                   "nlr_fraction": _nlr_fraction()},
            "plausibility_temperatures": ptc, "materials": mats, "regions": regions}


def _print(summary):
    print("\nH-B2:", summary["H_B2"])
    print("load shape:", summary["load_shape_verdict"])
    print(f"\n{'region':<30}{'policy':<8}{'dCost $/yr':>14}{'water %':>9}{'m3/d':>9}{'sil h':>6}"
          f"{'unr h':>6}{'inf h':>6}{'PUE mh':>8}{'PUE rt':>8}{'maxflow':>8}  cycles")
    for k, v in summary["regions"].items():
        for scen, block in (("base", v["base"]), ("OEM55", v["S_OEM_return_55C"])):
            for p, a in block.items():
                print(f"{(k + ' ' + scen):<30}{p:<8}{a['cost_delta_vs_B0_usd_yr']:>14,.0f}"
                      f"{a['water_delta_pct_vs_B0']:>9.2f}{a['water_m3_day']:>9.0f}{a['silica_scaling_hours']:>6}"
                      f"{a['floor_unreachable_hours']:>6}{a['infeasible_hours_fallback']:>6}"
                      f"{a['PUE_mean_of_hours']:>8.3f}{a['PUE_ratio_of_totals']:>8.3f}"
                      f"{a['max_secondary_flow_ratio']:>8.2f}  {a['cycles_chosen']}")
        print("   load:", {n: (x["silica_scaling_hours"], x.get("delta_vs_L0")) for n, x in v["load_shape"].items()},
              "WUE bound violations:", v["WUE_bound_violations"])
        print("   staleness:", {f: (round(x['stored'], 3) if isinstance(x['stored'], float) else x['stored'],
                                    round(x['now'], 3) if isinstance(x['now'], float) else x['now'])
                                for f, x in v["deck_table_staleness"].items()})
    print("\nmaterials:", json.dumps(summary["materials"], indent=1))
    print("temperatures:", json.dumps(summary["plausibility_temperatures"], indent=1))


if __name__ == "__main__":
    smoke = "--smoke" in sys.argv
    if smoke:
        key, r = run_region("Europe_Frankfurt", smoke=True)
        h = r["hours"][0]
        for p in ("B0", "B1", "B2", "B1f", "OEM_B0", "OEM_B1", "OEM_B2"):
            e = h[p]
            print(p, None if e is None else (e["cycles"], round(e["fan_pct"], 1), round(e["T_fws_c"], 2),
                                             round(e["cost_per_h"], 1), round(e["PUE"], 3), e["violations"]))
        print("candidates", h["B2_candidates"], "admissible", h["B2_admissible"],
              {n: v["B0"][0] and round(_sil(v["B0"][0]), 4) for n, v in r["load"].items()})
        raise SystemExit(0)
    if (OUT / "run.json").exists():
        raise SystemExit("refuse to overwrite a completed run")
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = ["src/cdu_joint_policy.py", "src/hybrid_supervisor.py", "src/models/cdu_model.py",
              "src/chemistry.py", "src/controller.py", "src/tower.py", "src/corrosion.py",
              "scripts/generate_pitch_artifacts.py", "results/calibration.json",
              "results/tmy_hourly.npy", "results/pitch_artifacts.json",
              "docs/staged/cdu_joint_policy_preregistration.md"]
    reg = {"inputs_sha256": {p: sha(ROOT / p) for p in inputs}, "nlr_csv_sha256": sha(NLR_CSV),
           "python": sys.version, "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    (OUT / "registration.json").write_text(json.dumps(reg, indent=2), encoding="utf-8")
    gpa = _load_gpa()
    t0 = time.time()
    with Pool(len(gpa.REGIONS)) as pool:
        results = dict(pool.map(run_region, list(gpa.REGIONS)))
    changed = [p for p, h in reg["inputs_sha256"].items() if sha(ROOT / p) != h]
    if changed:
        raise SystemExit(f"inputs changed during the run: {changed}")
    summary = score(results)
    summary["elapsed_s"] = time.time() - t0
    (OUT / "hours.json").write_text(json.dumps(results, indent=1, default=float), encoding="utf-8")
    (OUT / "run.json").write_text(json.dumps(dict(registration=reg, **summary), indent=2, default=float),
                                  encoding="utf-8")
    _print(summary)
