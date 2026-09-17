"""Is the modelled makeup water self-consistent, and is its sulfate right?

WHY THIS EXISTS
---------------
`ARAMCO_RECLAIMED` carries **SO4 = 566 mg/L**, and sulfate is the single most
load-bearing number in this package: it sets the gypsum wall, which is the
product's central claim, and `value_of_information.py` scores it as worth 10.2 %
of makeup water while being measured by nobody.

A field write-up of the same Saudi Aramco pilot -- same authors, same site,
same eight-month study -- reports the TSE as:

    TDS 1500, Ca 106, Mg 41, SO4 300, HCO3 105, Na 310, Cl 528, TOC 5, PO4 8

That is **300 mg/L sulfate, not 566**. Nearly a factor of two, on the one ion
the thesis rests on.

This does NOT silently replace the water. The two analyses are scored against
two objective tests that need no outside authority -- charge balance and
whether the ions sum to the stated TDS -- and then the gypsum wall is computed
under both so the consequence is visible either way.

Run:  python src/makeup_analysis_audit.py
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import chemistry as chem  # noqa: E402

EQW = {"Na": 22.990, "K": 39.098, "Ca": 40.078 / 2, "Mg": 24.305 / 2,
       "Cl": 35.453, "SO4": 96.06 / 2, "HCO3": 61.017, "NO3": 62.004}
CATIONS = ("Na", "K", "Ca", "Mg")
ANIONS = ("Cl", "SO4", "HCO3", "NO3")

# As modelled today.
AS_MODELLED = dict(Na=379.0, K=25.0, Ca=94.0, Mg=41.0,
                   Cl=565.0, SO4=566.0, HCO3=70.0, NO3=12.0, TDS=1500.0)

# As reported in the field write-up of the same pilot.
AS_REPORTED = dict(Na=310.0, K=0.0, Ca=106.0, Mg=41.0,
                   Cl=528.0, SO4=300.0, HCO3=105.0, NO3=0.0, TDS=1500.0)


def diagnose(name, w):
    cat = sum(w.get(k, 0.0) / EQW[k] for k in CATIONS)
    an = sum(w.get(k, 0.0) / EQW[k] for k in ANIONS)
    imbalance = (cat - an) / ((cat + an) / 2.0) * 100.0
    ion_sum = sum(w.get(k, 0.0) for k in CATIONS + ANIONS)
    tds_err = (ion_sum - w["TDS"]) / w["TDS"] * 100.0
    print(f"\n{name}")
    print(f"  cations {cat:6.2f} meq/L   anions {an:6.2f} meq/L")
    print(f"  charge imbalance      {imbalance:+7.1f} %   "
          f"({'FAIL, >5 %' if abs(imbalance) > 5 else 'ok'})")
    print(f"  ions sum to           {ion_sum:7.0f} mg/L vs stated TDS {w['TDS']:.0f}")
    print(f"  TDS closure           {tds_err:+7.1f} %   "
          f"({'FAIL, ions exceed TDS' if tds_err > 5 else 'ok'})")
    return imbalance, tds_err


def wall_for(w, label):
    water = chem.balance_sodium(chem.Water(
        name=label, Na=w["Na"], K=w.get("K", 0.0), Ca=w["Ca"], Mg=w["Mg"],
        Cl=w["Cl"], SO4=w["SO4"], HCO3=w["HCO3"], NO3=w.get("NO3", 0.0),
        SiO2=0.0, pH=7.4, TDS=w["TDS"]))
    print(f"\n  {label}: gypsum / calcite saturation at the skin (40 C), pH 8.0")
    wall = None
    for cy in range(3, 15):
        sat = chem.saturation_state(water.concentrate(float(cy)), T_c=40.0)
        gyp, cal = sat["SI_gypsum"], sat["SI_calcite"]
        over = gyp > chem.DEFAULT_LIMITS["SI_gypsum"]
        if over and wall is None:
            wall = cy
        print(f"    {cy:2d} cycles   SI_gypsum {gyp:+.3f}   SI_calcite {cal:+.3f}"
              + ("   <-- gypsum over limit" if over else ""))
        if wall is not None and cy > wall:
            break
    return wall


def main():
    print("=" * 74)
    print("MAKEUP ANALYSIS: is the modelled water self-consistent?")
    print("=" * 74)
    i1, t1 = diagnose("AS MODELLED  (ARAMCO_RECLAIMED, SO4 = 566)", AS_MODELLED)
    i2, t2 = diagnose("AS REPORTED  (field write-up, SO4 = 300)", AS_REPORTED)

    print("\n" + "=" * 74)
    print("CONSEQUENCE FOR THE GYPSUM WALL")
    print("=" * 74)
    w1 = wall_for(AS_MODELLED, "as modelled, SO4 566")
    w2 = wall_for(AS_REPORTED, "as reported, SO4 300")

    print("\n" + "-" * 74)
    print(f"  gypsum wall, SO4 566 : {w1} cycles")
    print(f"  gypsum wall, SO4 300 : {w2} cycles")
    print(f"  charge imbalance     : {i1:+.1f} % modelled vs {i2:+.1f} % reported")
    print(f"  TDS closure          : {t1:+.1f} % modelled vs {t2:+.1f} % reported")
    print("-" * 74)


# ---------------------------------------------------------------------------
# NACE 577 Table 1: is the -5.25 % charge imbalance the dropped nitrogen?
# ---------------------------------------------------------------------------
# A DIAGNOSTIC. It changes no threshold and no water, and
# `chemistry.validate_analysis` does not read it.
#
# The Riyadh assay prints "Ammonia 16" and "Nitrite 31" in mg/L and states no
# basis for either. A laboratory may report ammonia as N, as NH3 or as NH4+,
# and nitrite as N or as NO2-. `SPECIES` carries neither, so the engine's
# balance omits both. Crediting ammonium (a cation) while ignoring nitrite (an
# anion from the same table) is selective: this reports every combination.
#
# CRITERIA, written before the function was first run (17 Sep 2026):
#   * Charge is the engine's convention, 100 (cat - an) / ((cat + an) / 2),
#     on the engine's own molalities and charges for the carried species.
#     Ammonium carries +1 times its NH4+ fraction at the analysis pH
#     (pKa 9.245, 25 C); nitrite carries -1 (pKa 3.3, fully dissociated).
#   * Ion sum adds each nitrogen species as the mass of the ION (NH4+,
#     NO2-), converted from the stated basis.
#   * A combination is CONSISTENT when |charge balance| <= 5.0 % AND the ion
#     sum exceeds the stated TDS by <= 10.0 %: the two tolerances in
#     `chemistry.ANALYSIS_TOLERANCES`, unchanged.
#   * The omitted nitrogen EXPLAINS the imbalance only if at least one
#     combination that includes BOTH ammonia and nitrite is consistent. If
#     none is, the verdict is NOT EXPLAINED. If more than one basis pair is
#     consistent, the basis is UNDETERMINED by this analysis, and that is
#     reported rather than resolved. Rows that include only one of the two
#     are printed but cannot count as an explanation.
MW_N, MW_NH3, MW_NH4, MW_NO2 = 14.007, 17.031, 18.038, 46.005
PKA_NH4_25C = 9.245
NITROGEN_AMMONIA_BASES = ("omitted", "as N", "as NH3", "as NH4+")
NITROGEN_NITRITE_BASES = ("omitted", "as N", "as NO2-")


def nitrogen_basis_charge_balance(water=None, table=None, tolerances=None):
    """Charge balance and ion-sum closure under every reporting basis for the
    ammonia and nitrite the engine drops. Returns {"rows", "verdict", ...}."""
    water = chem.ARAMCO_RIYADH_REFINERY_TSE if water is None else water
    table = chem.NACE577_TABLE1_PRINTED if table is None else table
    tol = dict(chem.ANALYSIS_TOLERANCES if tolerances is None else tolerances)

    m = water.molality()
    z = {s: water._charge(s) for s in chem.SPECIES}
    cat0 = sum(m[s] * z[s] for s in chem.SPECIES if z[s] > 0)
    an0 = sum(-m[s] * z[s] for s in chem.SPECIES if z[s] < 0)
    ions0 = sum(getattr(water, s) for s in chem.SPECIES)
    tds = water.tds()
    f_nh4 = 1.0 / (1.0 + 10.0 ** (water.pH - PKA_NH4_25C))

    nh3, no2 = float(table["ammonia"]), float(table["nitrite"])
    # (mol/kg of the species, mg/L as the ion)
    ammonia = {"omitted": (0.0, 0.0),
               "as N": (nh3 * 1e-3 / MW_N, nh3 * MW_NH4 / MW_N),
               "as NH3": (nh3 * 1e-3 / MW_NH3, nh3 * MW_NH4 / MW_NH3),
               "as NH4+": (nh3 * 1e-3 / MW_NH4, nh3)}
    nitrite = {"omitted": (0.0, 0.0),
               "as N": (no2 * 1e-3 / MW_N, no2 * MW_NO2 / MW_N),
               "as NO2-": (no2 * 1e-3 / MW_NO2, no2)}

    rows = []
    for ka in NITROGEN_AMMONIA_BASES:
        mol_a, mg_a = ammonia[ka]
        for kn in NITROGEN_NITRITE_BASES:
            mol_n, mg_n = nitrite[kn]
            cat = cat0 + mol_a * f_nh4
            an = an0 + mol_n
            cb = 100.0 * (cat - an) / (0.5 * (cat + an))
            ion_sum = ions0 + mg_a + mg_n
            closure = 100.0 * (ion_sum - tds) / tds
            ok_cb = abs(cb) <= tol["charge_balance_pct"]
            ok_tds = closure <= tol["tds_closure_pct"]
            rows.append({
                "ammonia": ka, "nitrite": kn,
                "both_included": ka != "omitted" and kn != "omitted",
                "cations_meq": 1e3 * cat, "anions_meq": 1e3 * an,
                "charge_balance_pct": cb, "ion_sum_mg_L": ion_sum,
                "tds_closure_pct": closure,
                "charge_balance_ok": ok_cb, "tds_closure_ok": ok_tds,
                "consistent": ok_cb and ok_tds})

    both_ok = [r for r in rows if r["both_included"] and r["consistent"]]
    if not both_ok:
        verdict = "NOT EXPLAINED"
    elif len(both_ok) == 1:
        verdict = "EXPLAINED"
    else:
        verdict = "UNDETERMINED"
    return {"water": water.name, "nh4_fraction_at_pH": f_nh4,
            "tolerances": tol, "rows": rows, "verdict": verdict,
            "consistent_with_both": [(r["ammonia"], r["nitrite"])
                                     for r in both_ok]}


def nitrogen_report():
    import json
    res = nitrogen_basis_charge_balance()
    print("\n" + "=" * 74)
    print("NACE 577 TABLE 1: charge balance under every nitrogen basis")
    print("=" * 74)
    print(f"  NH4+ fraction at pH {chem.ARAMCO_RIYADH_REFINERY_TSE.pH}: "
          f"{res['nh4_fraction_at_pH']:.4f}")
    print(f"  {'ammonia':9s} {'nitrite':9s} {'cat meq':>8s} {'an meq':>8s} "
          f"{'CB %':>7s} {'ions':>6s} {'TDS %':>6s}  consistent")
    for r in res["rows"]:
        print(f"  {r['ammonia']:9s} {r['nitrite']:9s} {r['cations_meq']:8.3f} "
              f"{r['anions_meq']:8.3f} {r['charge_balance_pct']:+7.2f} "
              f"{r['ion_sum_mg_L']:6.0f} {r['tds_closure_pct']:+6.1f}  "
              f"{'yes' if r['consistent'] else 'no'}")
    print(f"  VERDICT: {res['verdict']}  (pairs with both species that pass: "
          f"{res['consistent_with_both']})")
    out = ROOT / "results" / "nace577_nitrogen_basis.json"
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"  written -> {out}")
    return res


if __name__ == "__main__":
    main()
    nitrogen_report()
