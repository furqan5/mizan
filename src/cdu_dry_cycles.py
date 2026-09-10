"""Dry/wet price crossover by achievable cycles, preregistered 7 Sep 2026.

Reuse accepted thermal states; do not rerun or rescore the main experiment.
For every weather bin, fix FWS to that bin's selected FWS (equal delivered
water temperature for both alternatives). For each tested cycles count,
use every chemistry-feasible saved ECWT/fan state at that FWS. Its saved pH
minimises chemical cost for that state independently of the makeup price.
Dry approach assumptions, fan power and discharge price are read from the
completed diagnostic artifact, not retyped. All main chiller bounds apply.
Compute pM* = max_s[(pE*Pdry - other_wet_cost_s)/makeup_s]. This is the
intersection of dry cost and the lower envelope of the sampled wet-cost
lines, allowing wet ECWT/fan choice to change with price at fixed cycles.
Below pM*, at least one wet state is cheaper; above it, dry is cheaper under
the stated assumptions. Negative values mean no nonnegative makeup price
favours wet at that cycles count. Unsupported dry bins stay null and prohibit
annual dry ROI. Excluded cycles remain explicit rather than silently removed.

Numerical verification, before first run: minimum wet cost at crossover must
equal dry cost within 1e-8 USD/h. Add 1 USD/h to the dry comparator to prove
that this guard fails. All makeup rates must be positive; inject zero makeup
to prove rejection. Source and upstream diagnostic hashes must match exactly.
This is a steady-state scenario, with no equipment selection, CAPEX or new
engineering performance gate. No historical file or threshold is modified.
"""
from pathlib import Path
import argparse,json
import cdu_hybrid as h

def positive_makeup(value):
    h.require(value>0,'positive makeup required')
    return value

def check_crossover(dry_cost,wet_cost):
    h.require(abs(dry_cost-wet_cost)<=1e-8,'crossover cost closure')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,default=h.DEFAULT_REPO)
    ap.add_argument('--run',type=Path,default=h.ROOT/'results/cdu_hybrid_verified/run.json')
    ap.add_argument('--diagnostics',type=Path,default=h.ROOT/'results/cdu_hybrid_diagnostics.json')
    ap.add_argument('--out',type=Path,default=h.ROOT/'results/cdu_dry_cycles.json')
    args=ap.parse_args();h.setup(args.repo)
    h.require(not args.out.exists(),'refuse to overwrite completed study')
    run=json.loads(args.run.read_text());d=json.loads(args.diagnostics.read_text())
    h.require(h.source_hash(args.run)==d['run_sha256'],'diagnostic run source hash')
    for p,digest in run['input_sha256'].items():
        h.require(h.source_hash(args.repo/p)==digest,'stale model input: '+p)
    states=json.loads((args.run.parent/'states.json').read_text())
    tariff=next(x for x in d['water_tariff_policy_repricing'] if x['label']=='process_and_industrial_discharge')
    pm=tariff['makeup_USD_m3'];pb=tariff['discharge_USD_m3'];tar=run['tariffs']
    approaches=sorted(set(x['dry_approach_K'] for x in d['dry_counterparts']))
    fans=set(x['dry_fan_assumed_kW'] for x in d['dry_counterparts'] if x['status'].startswith('IN_CURVE'))
    h.require(len(fans)==1,'inconsistent dry fan assumption');dryfan=fans.pop()
    rows=[];closures=[]
    for weather in run['bins']:
        fws=weather['coupled_optimum']['T_fws_C']
        for cy in run['grids']['cycles']:
            wet=[s for s in states if s['bin']==weather['bin'] and s['T_fws_C']==fws
                 and s['cycles']==cy and s['chemistry_ok']]
            for approach in approaches:
                row=dict(bin=weather['bin'],hours=weather['hours'],T_db_C=weather['T_db_C'],
                         T_wb_C=weather['T_wb_C'],cycles=cy,FWS_C=fws,dry_approach_K=approach,
                         wet_candidate_count=len(wet))
                if not wet:
                    row.update(status='NO_CHEMISTRY_FEASIBLE_WET_STATE',crossover_USD_m3=None)
                    rows.append(row);continue
                try:
                    power=h.chiller(h.QIT,weather['T_db_C']+approach,fws)['P_chiller_kW']+dryfan
                except h.InvalidState as ex:
                    row.update(status='DRY_OUTSIDE_CURVE',reason=str(ex),crossover_USD_m3=None)
                    rows.append(row);continue
                drycost=tar['elec_per_kwh']*power
                def other(s):
                    return tar['elec_per_kwh']*s['P_total_kW']+pb*s['blowdown_m3_h']+tar['acid_per_kg']*s['acid_kg_h']+tar['antiscalant_per_m3']*s['makeup_m3_h']
                cross,limiting=max([((drycost-other(s))/positive_makeup(s['makeup_m3_h']),s)
                                   for s in wet], key=lambda item:item[0])
                at_cross=min(other(s)+cross*s['makeup_m3_h'] for s in wet)
                check_crossover(drycost,at_cross);closures.append(abs(drycost-at_cross))
                at_price=min(wet,key=lambda s:other(s)+pm*s['makeup_m3_h'])
                row.update(status='IN_CURVE_CONDITIONAL_ESTIMATE',crossover_USD_m3=cross,
                           dry_total_kW=power,dry_cost_USD_h=drycost,
                           crossover_ECWT_C=limiting['T_ecwt_C'],crossover_fan_pct=limiting['fan_pct'],
                           wet_cost_at_process_tariff_USD_h=other(at_price)+pm*at_price['makeup_m3_h'],
                           wet_ECWT_at_process_tariff_C=at_price['T_ecwt_C'],
                           wet_fan_at_process_tariff_pct=at_price['fan_pct'],
                           closure_error_USD_h=abs(drycost-at_cross))
                rows.append(row)
    faults=[]
    for name,fn in [('bad crossover closure',lambda:check_crossover(drycost+1,drycost)),
                    ('zero makeup',lambda:positive_makeup(0)),
                    ('inconsistent dry fan',lambda:h.require(len({dryfan,dryfan+1})==1,'inconsistent dry fan assumption'))]:
        try:fn()
        except h.InvalidState:faults.append(dict(name=name,rejected=True));continue
        raise AssertionError('unrejected fault: '+name)
    output=dict(preregistration=__doc__,script_sha256=h.source_hash(Path(__file__)),
                run_sha256=h.source_hash(args.run),diagnostics_sha256=h.source_hash(args.diagnostics),
                rows=rows,makeup_USD_m3=pm,discharge_USD_m3=pb,dry_fan_assumption_kW=dryfan,
                maximum_cost_closure_error_USD_h=max(closures),fault_injections=faults,
                annual_dry_ROI=None,limits='Only sampled wet schedules at each bin optimum FWS; hot dry hours unsupported.')
    args.out.write_text(json.dumps(output,indent=2),encoding='utf-8')
    print(json.dumps(dict(rows=len(rows),feasible_rows=sum(x['status'].startswith('IN_CURVE') for x in rows),
                         maximum_cost_closure_error_USD_h=max(closures)),indent=2))

if __name__=='__main__':main()
