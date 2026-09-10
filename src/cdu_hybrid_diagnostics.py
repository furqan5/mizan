"""Supporting diagnostics for the registered CDU study, 7 Sep 2026.

Pre-registration BEFORE this diagnostic run. No historical gates are rescored.
Use both annual aggregation conventions for every annual saving percentage.
Skin sensitivity: inherited 8 K versus assumed clean 3 K, exactly the same
thermal states and original operating SI limits. Diagnostic only, no pass gate.
SI temperature direction: 101 equally spaced temperatures between each basin
and skin; report hotter-vs-colder sign without asserting monotonicity.
Makeup data cases: unbalanced2022, sodium-balanced2022 (legacy assumption),
unbalanced2020 and sodium-balanced2020. 2020 values are read from the existing
makeup-analysis audit script, not typed into this second file.
Dry counterpart [A]: indirect water-cooled chiller with a dry cooler, assumed
ECWT=Tdb+approach; approach3/5/7 K, fixed dry fan110 kW from reference plant
fan nameplate (an explicit sensitivity assumption, NOT a dry-cooler rating).
No inferred dry power beyond original ECWT/FWS/PLR ranges. Unsupported hours
remain missing and prohibit a full-year dry/wet ROI claim. Evaluate per-bin
makeup tariff crossover only for in-envelope dry cases. No CAPEX, pump delta,
heat recovery, redundancy or discount rate invented.
Tariff alternative [C/A]: Marafiq industrial process water8.04 SAR/m3 and
industrial wastewater3.64 SAR/m3, converted at3.75 SAR/USD; applicability and
VAT unresolved. Keep legacy3.11 USD/m3 makeup objective exactly as requested,
and separately compute pM*M+pB*B. Coastal scenario pB=0 is conditional.
ITD: use only extracted Figure2 lookup. Report required chip-to-water rise
Tchip_opt - (Tfws+A) for A3/5/7 K. This is NOT an identified chip shortfall.
No thresholds in this script may be interpreted as new product success gates.
"""
from pathlib import Path
import argparse,ast,dataclasses,hashlib,json,sys
import cdu_hybrid as hybrid


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,default=hybrid.DEFAULT_REPO)
    ap.add_argument('--run',type=Path,default=hybrid.ROOT/'results/cdu_hybrid/run.json')
    ap.add_argument('--lookup',type=Path,default=hybrid.ROOT/'results/itd_source_lookup.json')
    ap.add_argument('--out',type=Path,default=hybrid.ROOT/'results/cdu_hybrid_diagnostics.json')
    args=ap.parse_args();hybrid.setup(args.repo)
    import numpy as np
    run=json.loads(args.run.read_text());lookup=json.loads(args.lookup.read_text())
    states=json.loads((args.run.parent/'states.json').read_text())
    rows=run['bins'];tar=run['tariffs'];optT=lookup['minimum_sample']['T_chip_C']
    H3=[];H4=[];dry=[];skin=[];wclass=[]
    for row in rows:
        base=row['fixed_fws_optimum'];warmer=row['coupled_optimum']
        for r in row['by_cycles']:
            if r['max_chemical_FWS_C'] is not None:
                for approach in [3.,5.,7.]:
                    water=r['max_chemical_FWS_C']+approach
                    H3.append(dict(bin=row['bin'],cycles=r['cycles'],CDU_approach_K=approach,
                                   delivered_max_GPU_water_C=water,
                                   required_chip_to_water_rise_K=optT-water,
                                   actual_chip_temperature_gap_K=None))
        if base and warmer:
            for name in ['W17','W27','W32','W40','W45']:
                wclass.append(dict(bin=row['bin'],class_name=name,
                    boundary='facility_supply_water',FWS_C=warmer['T_fws_C'],
                    margin_K=hybrid.fw_margin(float(name[1:]),warmer['T_fws_C'],'facility_supply_water'),
                    GPU_water_C=warmer['T_gpu_inlet_water_C'],GPU_OEM_limit_C=None,GPU_OEM_margin_K=None))
            H4.append(dict(bin=row['bin'],hours=row['hours'],FWS_before_C=base['T_fws_C'],FWS_after_C=warmer['T_fws_C'],
                           cycles_before=base['cycles'],cycles_after=warmer['cycles'],
                           cycles_cost_of_warming=base['cycles']-warmer['cycles'],
                           annual_cost_change_USD=row['hours']*(warmer['cost_per_h']-base['cost_per_h']),
                           ITD_attribution=False))
            for approach in [3.,5.,7.]:
                tcw=row['T_db_C']+approach
                d=dict(bin=row['bin'],hours=row['hours'],dry_approach_K=approach,dry_ECWT_C=tcw)
                try:
                    ch=hybrid.chiller(hybrid.QIT,tcw,warmer['T_fws_C'])
                    pdry=ch['P_chiller_kW']+hybrid.PLANT['p_fan_rated_kw']
                    chemical=tar['acid_per_kg']*warmer['acid_kg_h']+tar['antiscalant_per_m3']*warmer['makeup_m3_h']
                    # crossover makeup price with discharged-water tariff separated
                    pB=3.64/3.75
                    crossover=(tar['elec_per_kwh']*(pdry-warmer['P_total_kW'])-pB*warmer['blowdown_m3_h']-chemical)/warmer['makeup_m3_h']
                    d.update(status='IN_CURVE_CONDITIONAL_ESTIMATE',P_dry_total_kW=pdry,makeup_tariff_crossover_USD_m3=crossover,
                             dry_fan_assumed_kW=hybrid.PLANT['p_fan_rated_kw'])
                except hybrid.InvalidState as ex:
                    d.update(status='UNSUPPORTED',reason=str(ex),P_dry_total_kW=None,makeup_tariff_crossover_USD_m3=None)
                dry.append(d)
    for r in states:
        # Original pH policy is recomputed on this same state under each skin rise.
        versions=[]
        for rise in [3.,8.]:
            rr=[hybrid.chemistry_at(r,p,hybrid.rc.TSE,skin_rise=rise) for p in run['grids']['pH']]
            ok=[s for s in rr if s['chemistry_ok']]
            versions.append(dict(skin_rise_K=rise,any_ph_feasible=bool(ok)))
        ts=np.linspace(r['T_ecwt_C'],r['T_skin_C'],101)
        si=[hybrid.chem.saturation_state(hybrid.rc.TSE.concentrate(r['cycles']),float(t),pH=r['ph'])['SI_gypsum'] for t in ts]
        skin.append(dict(bin=r['bin'],cycles=r['cycles'],FWS_C=r['T_fws_C'],ECWT_C=r['T_ecwt_C'],versions=versions,
                         skin_minus_basin_gypsum_SI=r['SI_gypsum']-r['SI_gypsum_basin'],
                         highest_gypsum_along_temperature_span=float(max(si)),
                         temperature_at_highest_gypsum_C=float(ts[int(np.argmax(si))])))
    # Compare water charges on exactly the same precomputed schedules, never
    # claim the legacy-cost optimum is a new tariff-optimal operating policy.
    tariffs=[]
    for label,pm,pb in [('legacy_requested',tar['water_per_m3'],0),
                        ('process_and_industrial_discharge',8.04/3.75,3.64/3.75),
                        ('process_and_unbilled_outfall',8.04/3.75,0)]:
        pairs=[]
        for r in rows:
            if not r['baseline'] or not r['coupled_optimum']:continue
            def cost(s):return tar['elec_per_kwh']*s['P_total_kW']+pm*s['makeup_m3_h']+pb*s['blowdown_m3_h']+tar['acid_per_kg']*s['acid_kg_h']+tar['antiscalant_per_m3']*s['makeup_m3_h']
            pairs.append((r['hours'],cost(r['baseline']),cost(r['coupled_optimum'])))
        h,b,o=map(np.array,zip(*pairs))
        tariffs.append(dict(label=label,makeup_USD_m3=pm,discharge_USD_m3=pb,
                            hours=int(h.sum()),annual_saving_USD=float(np.sum(h*(b-o))),
                            mean_of_ratios_pct=float(np.average(100*(b-o)/b,weights=h)),
                            ratio_of_totals_pct=float(100*np.sum(h*(b-o))/np.sum(h*b)),
                            policy_reoptimized=False))
    # Per-bin maximum additional dry energy supported by avoided water/chemicals.
    break_even=[]
    for r in rows:
        s=r['coupled_optimum']
        if not s:continue
        pwater=8.04/3.75*s['makeup_m3_h']+3.64/3.75*s['blowdown_m3_h']
        chemical=tar['acid_per_kg']*s['acid_kg_h']+tar['antiscalant_per_m3']*s['makeup_m3_h']
        break_even.append(dict(bin=r['bin'],hours=r['hours'],wet_kW=s['P_total_kW'],
                               water_and_chemical_USD_h=pwater+chemical,
                               allowable_dry_extra_kW=(pwater+chemical)/tar['elec_per_kwh'],
                               dry_break_even_total_kW=s['P_total_kW']+(pwater+chemical)/tar['elec_per_kwh']))
    import makeup_analysis_audit as maa
    analyses=[]
    for label,source in [('published_2022',maa.AS_MODELLED),('field_2020',maa.AS_REPORTED)]:
        raw=hybrid.chem.Water(name=label,**source)
        for balanced in [False,True]:
            water=hybrid.chem.balance_sodium(raw) if balanced else raw
            cat=sum(getattr(water,k)/maa.EQW[k] for k in maa.CATIONS)
            an=sum(getattr(water,k)/maa.EQW[k] for k in maa.ANIONS)
            cy_limit=hybrid.brentq(lambda cy:hybrid.chem.saturation_state(water.concentrate(cy),40)['SI_gypsum']-hybrid.chem.OPERATING_LIMITS['SI_gypsum'],2,10)
            analyses.append(dict(source=label,sodium_balancing_assumption=balanced,ions=dataclasses.asdict(water),
                cations_meq_L=cat,anions_meq_L=an,imbalance_repo_pct=100*(cat-an)/((cat+an)/2),
                imbalance_sum_denominator_pct=100*(cat-an)/(cat+an),ion_sum_mg_L=sum(getattr(water,k) for k in maa.EQW),
                gypsum_operating_limit_cycles_at40C=float(cy_limit),source_is_resolved=False))
    result=dict(preregistration=__doc__,script_sha256=hybrid.source_hash(Path(__file__)),
                run_sha256=hybrid.source_hash(args.run),lookup_sha256=hybrid.source_hash(args.lookup),
                H3_required_rise_only=H3,H4_non_ITD_FWS_comparison=H4,dry_counterparts=dry,
                W_class_margins=wclass,makeup_analyses=analyses,
                dry_annual_ROI=None,dry_annual_status='NOT_IDENTIFIABLE_WITH_GULF_OUTSIDE_CURVE',
                water_tariff_policy_repricing=tariffs,dry_break_even_power=break_even,
                skin_sensitivity=skin,skin_gypsum_below_basin_count=sum(s['skin_minus_basin_gypsum_SI']<0 for s in skin),
                skin_sensitivity_feasibility_changes=sum(s['versions'][0]['any_ph_feasible']!=s['versions'][1]['any_ph_feasible'] for s in skin),
                H3_note='Required rise is an algebraic condition, not a device model or actual delivery shortfall.',
                H4_note='FWS comparison is cooling-plant operating cost only; IT draw fixed by assumption.')
    args.out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['preregistration','skin_sensitivity','H3_required_rise_only']},indent=2))


if __name__=='__main__':main()
