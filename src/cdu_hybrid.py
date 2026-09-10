"""MIZAN: one-CDU extension and falsification study (7 Sep 2026).

PRE-REGISTRATION, recorded before the first model execution.
Original H1-H4 remain hypotheses, not retrospective success criteria.

H1a (original): increasing condenser inlet water at fixed IT duty must increase
GPU inlet WATER temperature. Test matched states at fixed FWS and CDU approach;
strict positive change >1e-6 K is required for every pair. A regulated evaporator
is expected to refute this assertion; report FAIL, do not replace its verdict.
H1b: increasing cycles at fixed temperatures/pH must increase skin gypsum SI;
all adjacent tested pairs must increase >1e-8 SI, otherwise FAIL.
H2-cycles: at least one thermally feasible state becomes chemistry-infeasible
at the next cycles count while both condenser-temperature slack >0.1 K and PLR
slack >0.01 remain. This tests a cycles constraint, not an IT-temperature claim.
H2-temperature (the hybrid kill test): for at least one weather/cycles group,
chemistry must reduce the maximum feasible FWS temperature by >=0.1 K, compared
with the same grid without chemistry. No feasible chemistry state is reported
as exclusion, not an arbitrarily large temperature loss. Zero qualifying groups
means FAIL in this sampled domain, not proof outside it.
H3: actual chip-optimum shortfall requires a measured chip-to-water map for the
same part/workload. If absent, return NOT_IDENTIFIABLE and null, never subtract
water from chip temperature and label that a delivery shortfall. Report the
required chip-to-water rise separately, as an algebraic diagnostic.
H4: reaching the ITD-optimal point requires the H3 map. If absent return
NOT_IDENTIFIABLE. Price the independent 7 C -> allowed FWS optimisation as a
conditional engineering estimate, never as ITD savings. Report both annual
mean-of-ratios and ratio-of-totals; never omit unsolved hours from an annual total.

Study inputs [A]: fixed IT duty = 0.90 * reference plant load, all captured by
liquid; one equivalent aggregate CDU, approach = 5 K (sensitivity 3/5/7 K),
equal FWS/TCS capacity rates derived for 5 K loop rise, no heat leak or pump heat.
The approach abstraction is local, not a rated CDU selection or hydraulic model.
FWS grid = native chilled-water lower limit, 7 C, native upper limit. ECWT grid
= 9 equally spaced points over native bounds plus 32 C baseline setpoint.
Cycles = integers 2..10, pH = 7..9 by 0.25 plus baseline 7.8. Fan admissible
range =30..100%, located by 10%-point brackets then continuous Brent root.
Nameplate is selected ONCE at design reference load, FWS7, ECWT upper limit.
Skin rise = 8 K, inherited scenario; 3 K is a cheap chemistry-only sensitivity.
Chemistry/price coefficients come from the repository, never duplicated.

Numerical acceptance [J]: root xtol1e-7 fan percentage points; residual Me
relative/absolute tolerance 1e-6 * max(1, Me_fill); energy balance error <=1e-7
of duty; water balance <=1e-9 kg/s; independent tower forward replay <=1e-3 K
at one selected point per weather bin. No accepted point may violate any
chiller fitted range (T_FWS, T_ECWT, PLR) or require a curve clamp. Raw PLR is
used through the source's upper bound. Coefficient/reference normalisation
follows legacy MIZAN; legacy files and their historical gates remain unchanged.
Fault injection: negative CDU approach/flow, reversed heat balance, each
envelope edge, nonfinite input, solver residual, water balance, stale source hash,
ITD extrapolation and wrong temperature boundary must all be rejected.

The direct inverse tower solve uses the SAME Poppe integrator and fill law:
Qcond=Qit+Pchiller, Twi=ECWT+Qcond/(m*cp), and solves
Me_Poppe(ECWT,Twi,fan)-Me_fill(fan)=0. This is an algebraic reparameterisation
of the converged duty fixed point, not a shortened iteration or surrogate.
No semiconductor, DVFS, transient CDU or flow-allocation model is introduced.

Run: python src/cdu_hybrid.py --repo <MIZAN-root> --output <new-results-directory>
     python src/cdu_hybrid.py --repo <MIZAN-root> --self-test
"""
from __future__ import annotations
import argparse
import dataclasses
import hashlib
import inspect
import json
import math
import pathlib
import sys
import time
from collections import Counter

DEFAULT_REPO = pathlib.Path(r"C:\Users\Nouman\Desktop\Furqan's Docs\Startup\mizan")
ROOT = pathlib.Path(__file__).resolve().parents[1]


class InvalidState(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise InvalidState(message)


def finite(*values):
    require(all(math.isfinite(float(v)) for v in values), 'nonfinite input')


def cdu(fws_c, q_kw, approach_k, capacity_rate_kw_k):
    finite(fws_c, q_kw, approach_k, capacity_rate_kw_k)
    require(q_kw > 0 and approach_k > 0 and capacity_rate_kw_k > 0,
            'CDU needs positive heat, approach and capacity rate')
    dt = q_kw/capacity_rate_kw_k
    r = dict(T_fws_C=float(fws_c), T_fws_return_C=float(fws_c+dt),
             T_gpu_inlet_water_C=float(fws_c+approach_k),
             T_tcs_return_C=float(fws_c+approach_k+dt),
             approach_K=float(approach_k), Q_cdu_kW=float(q_kw),
             capacity_rate_kW_K=float(capacity_rate_kw_k))
    # Both terminal temperature differences are positive for equal rates.
    require(r['T_tcs_return_C'] > r['T_fws_return_C'], 'CDU terminal cross')
    check_cdu_balance(r)
    return r


def check_cdu_balance(r):
    for hot,cold in [('T_fws_return_C','T_fws_C'),
                     ('T_tcs_return_C','T_gpu_inlet_water_C')]:
        q = r['capacity_rate_kW_K']*(r[hot]-r[cold])
        require(abs(q-r['Q_cdu_kW']) <= 1e-7*r['Q_cdu_kW'], 'CDU heat balance')


def check_water_balance(evap, drift, blowdown, makeup):
    finite(evap, drift, blowdown, makeup)
    require(min(evap, drift, blowdown, makeup) >= 0, 'negative water flow')
    require(abs(makeup-evap-drift-blowdown) <= 1e-9, 'water balance')


def check_tower_residual(residual, me_fill):
    finite(residual, me_fill)
    require(abs(residual) <= 1e-6*max(1,abs(me_fill)), 'tower residual')


def check_replay(target, actual, info):
    require(info is not None and math.isfinite(actual) and abs(actual-target)<=1e-3,
            'inverse/forward tower mismatch')


def source_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def setup(repo):
    global np, brentq, ctl, chem, tw, ps, wa, rc, TAR, QNOM, QIT, PLANT, FC, FN, CHILLER_REFERENCE
    sys.path.insert(0,str(repo/'src'))
    import numpy as np
    from scipy.optimize import brentq
    import controller as ctl
    import chemistry as chem
    import tower as tw
    import psychro as ps
    import water_activity as wa
    import run_controller as rc
    ref=json.loads((repo/'results/controller_summary.json').read_text())
    cal=json.loads((repo/'results/calibration.json').read_text())
    TAR=ref['tariffs']; PLANT=ref['plant']; FC=cal['fill_c']; FN=cal['fill_n']
    QNOM=ctl.nominal_capacity(dict(PLANT,T_chws_c=7.0))
    QIT=0.9*PLANT['Q_evap_kw']
    params=inspect.signature(ctl.chiller_power_biquad).parameters
    CHILLER_REFERENCE=tuple(float(params[name].default) for name in ['T_chws_ref','T_cws_ref'])


def chiller(q_kw, tcw, tfws, qnom= None):
    qnom=QNOM if qnom is None else qnom
    finite(q_kw,tcw,tfws,qnom)
    require(q_kw>0 and qnom>0,'positive chiller duty/nameplate required')
    require(ctl.CHILLER_TCHWS_RANGE[0] <= tfws <= ctl.CHILLER_TCHWS_RANGE[1], 'FWS outside curve')
    require(ctl.CHILLER_TCWS_RANGE[0] <= tcw <= ctl.CHILLER_TCWS_RANGE[1], 'ECWT outside curve')
    cap=ctl._biquad(ctl.CHILLER_CAPFT,tfws,tcw)/ctl._biquad(ctl.CHILLER_CAPFT,*CHILLER_REFERENCE)
    eir=ctl._biquad(ctl.CHILLER_EIRFT,tfws,tcw)/ctl._biquad(ctl.CHILLER_EIRFT,*CHILLER_REFERENCE)
    require(cap>0 and eir>0,'nonpositive chiller curve')
    plr=q_kw/(qnom*cap)
    require(ctl.CHILLER_PLR_RANGE[0] <= plr <= ctl.CHILLER_PLR_RANGE[1], 'PLR outside curve')
    a,b,c=ctl.CHILLER_EIRFPLR
    eirplr=(a+b*plr+c*plr*plr)/(a+b+c)
    power=qnom/ctl.CHILLER_COP_REF*cap*eir*eirplr
    require(power>0,'nonpositive compressor power')
    return dict(P_chiller_kW=float(power),cop=float(q_kw/power),plr_raw=float(plr),
                capacity_kW=float(qnom*cap))


def solve_tower(tcw, tfws, cycles, weather, water):
    ch=chiller(QIT,tcw,tfws)
    qcond=QIT+ch['P_chiller_kW']
    twin=tcw+qcond/(PLANT['m_w']*ctl.CPW)
    conc=water.concentrate(cycles)
    aw=float(wa.water_activity_tds(conc.tds()))
    win=float(ps.humidity_ratio_from_rh(weather['T_db_C'],weather['rh']))
    wb=float(ps.wetbulb(weather['T_db_C'],win))
    if tcw <= wb:
        return None,'below_wetbulb'
    cache={}
    def at(fan):
        if fan not in cache:
            ma=PLANT['m_a_rated']*fan/100
            z=tw.integrate_poppe(tcw,twin,weather['T_db_C'],win,PLANT['m_w'],ma,aw)
            me=tw.fill_merkel_number(PLANT['m_w'],ma,FC,FN)
            cache[fan]=(None if z is None else z['Me']-me,z,me)
        return cache[fan]
    previous=None
    root=None
    # Start on the high-airflow physical branch. A cold-end singularity can
    # manufacture residual roots with apparently small Me error. Every root
    # must reproduce in the unchanged forward solver before it can be priced.
    # The initial ascending scan failed the registered replay check; that
    # failed experiment is retained in results/cdu_hybrid_replay_failure.json.
    replay_error=None
    for f in np.arange(100.,29.,-10.):
        v,info,me=at(float(f))
        if v is None:
            previous=None
            continue
        candidate=None
        if abs(v) <= 1e-6*max(1,abs(me)):
            candidate=float(f)
        if previous is not None and previous[1]*v < 0:
            def residual(x):
                value=at(float(x))[0]
                require(value is not None,'undefined residual inside bracket')
                return value
            try:
                candidate=float(brentq(residual,float(f),previous[0],xtol=1e-7))
            except InvalidState:
                return None,'discontinuous_tower_bracket'
        if candidate is not None:
            replay,replay_info=tw.solve_outlet_temperature(twin,weather['T_db_C'],weather['rh'],
                PLANT['m_w'],PLANT['m_a_rated']*candidate/100,FC,FN,aw=aw)
            try:
                check_replay(tcw,replay,replay_info)
            except InvalidState:
                previous=(float(f),v)
                continue
            root=candidate
            replay_error=abs(replay-tcw)
            break
        previous=(float(f),v)
    if root is None:
        return None,'no_fan_root_in_admissible_range'
    residual,info,me=at(root)
    check_tower_residual(residual,me)
    ma=PLANT['m_a_rated']*root/100
    pfan=float(ctl.fan_power(ma,PLANT['m_a_rated'],PLANT['p_fan_rated_kw']))
    waterflows=ctl.water_balance(info['m_evap'],PLANT['m_w'],cycles)
    check_water_balance(info['m_evap'],waterflows['drift'],waterflows['blowdown'],waterflows['makeup'])
    r=dict(ch, T_ecwt_C=float(tcw),T_cw_return_C=float(twin),T_skin_C=float(twin+8),
           T_wb_actual_C=wb,cycles=float(cycles),fan_pct=root,aw=aw,
           P_fan_kW=pfan,P_total_kW=pfan+ch['P_chiller_kW'],Q_cond_kW=qcond,
           makeup_m3_h=waterflows['makeup']*3.6,blowdown_m3_h=waterflows['blowdown']*3.6,
           evaporation_m3_h=info['m_evap']*3.6,drift_m3_h=waterflows['drift']*3.6,
           tower_residual=float(residual),Me_fill=float(me),forward_replay_error_K=float(replay_error))
    r.update(cdu(tfws,QIT,5,QIT/5))
    return r,None


def chemistry_at(r,ph,water,skin_rise=8):
    conc=water.concentrate(r['cycles'])
    skin=r['T_cw_return_C']+skin_rise
    sat=chem.saturation_state_split(conc,skin,r['T_ecwt_C'],pH_hot=ph,pH_cold=ph)
    violations={k:float(sat[k]-v) for k,v in chem.OPERATING_LIMITS.items() if sat[k]>v}
    bulk=chem.saturation_state(conc,r['T_ecwt_C'],pH=ph)
    if ctl.CORROSION_FLOOR_SI is not None and bulk['SI_calcite']<ctl.CORROSION_FLOOR_SI:
        violations['corrosion_floor']=float(ctl.CORROSION_FLOOR_SI-bulk['SI_calcite'])
    acid,_=ctl.acid_dose_for_ph(water,r['cycles'],ph,skin)
    acid_h=acid*(r['makeup_m3_h']/3.6)*3600
    cost=TAR['elec_per_kwh']*r['P_total_kW']+TAR['water_per_m3']*r['makeup_m3_h']+TAR['acid_per_kg']*acid_h+TAR['antiscalant_per_m3']*r['makeup_m3_h']
    # Diagnostic: no global monotonic-temperature assumption for gypsum.
    gypsum_bulk=bulk['SI_gypsum']
    out=dict(r,ph=float(ph),chemistry_ok=not violations,violations=violations,
             SI_calcite=float(sat['SI_calcite']),SI_gypsum=float(sat['SI_gypsum']),
             SI_gypsum_basin=float(gypsum_bulk),SI_silica_am=float(sat['SI_silica_am']),
             bulk_SI_calcite=float(bulk['SI_calcite']),acid_kg_h=float(acid_h),
             cost_per_h=float(cost),ionic_strength=float(conc.ionic_strength()),
             assumed_skin_rise_K=float(skin_rise))
    return out


def fw_margin(wclass_max_c, value_c, boundary):
    require(boundary=='facility_supply_water', 'W-class is an FWS boundary')
    finite(wclass_max_c,value_c)
    return wclass_max_c-value_c


def lookup_itd(curve, temperature):
    xx=[r['T_chip_C'] for r in curve['points']]
    yy=[r['P_total_W'] for r in curve['points']]
    require(min(xx)<=temperature<=max(xx),'ITD lookup extrapolation prohibited')
    return float(np.interp(temperature,xx,yy))


def faults():
    checks=[]
    def rejects(name,fn):
        try: fn()
        except InvalidState: checks.append(dict(name=name,pass_=True)); return
        raise AssertionError('guard did not reject injected fault: '+name)
    rejects('negative CDU approach',lambda:cdu(7,QIT,-5,QIT/5))
    rejects('zero CDU flow',lambda:cdu(7,QIT,5,0))
    rejects('nonfinite input',lambda:cdu(float('nan'),QIT,5,QIT/5))
    bad=cdu(7,QIT,5,QIT/5); bad['T_fws_return_C']=bad['T_fws_C']-5
    rejects('reversed heat transfer',lambda:check_cdu_balance(bad))
    for j,name in [(0,'lower'),(1,'upper')]:
        direction=-1 if j==0 else 1
        rejects('FWS '+name,lambda j=j,direction=direction:chiller(QIT,30,ctl.CHILLER_TCHWS_RANGE[j]+direction))
        rejects('ECWT '+name,lambda j=j,direction=direction:chiller(QIT,ctl.CHILLER_TCWS_RANGE[j]+direction,7))
    for factor in [0.01,10]:
        rejects('PLR range '+str(factor),lambda factor=factor:chiller(QIT*factor,30,7))
    rejects('tower nonconvergence',lambda:check_tower_residual(0.01,1))
    rejects('spurious inverse root',lambda:check_replay(25.,26.,{}))
    rejects('mass balance',lambda:check_water_balance(1,0.1,0.2,9))
    rejects('wrong W-class boundary',lambda:fw_margin(27,30,'gpu_inlet_water'))
    rejects('stale file hash',lambda:require(source_hash(pathlib.Path(__file__))=='wrong','source hash'))
    dummy={'points':[{'T_chip_C':10,'P_total_W':3},{'T_chip_C':20,'P_total_W':2}]}
    rejects('lookup extrapolation',lambda:lookup_itd(dummy,5))
    good=cdu(7,QIT,5,QIT/5)
    require(good['T_gpu_inlet_water_C']>good['T_fws_C'],'CDU sign')
    return checks


def aggregates(rows,base_key,opt_key):
    require(all(r.get(base_key) and r.get(opt_key) for r in rows),'annual comparison missing bin')
    result={}
    hours=np.array([r['hours'] for r in rows],float)
    for key,name in [('P_total_kW','energy'),('makeup_m3_h','water'),('cost_per_h','cost')]:
        b=np.array([r[base_key][key] for r in rows]);o=np.array([r[opt_key][key] for r in rows])
        result[name]={'mean_of_ratios_pct':float(np.average(100*(b-o)/b,weights=hours)),
                      'ratio_of_totals_pct':float(100*np.sum(hours*(b-o))/np.sum(hours*b)),
                      'base_annual_total':float(np.sum(hours*b)),
                      'opt_annual_total':float(np.sum(hours*o)),
                      'annual_difference':float(np.sum(hours*(b-o)))}
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=pathlib.Path,default=DEFAULT_REPO)
    ap.add_argument('--output',type=pathlib.Path,default=ROOT/'results/cdu_hybrid')
    ap.add_argument('--self-test',action='store_true');args=ap.parse_args()
    setup(args.repo)
    checked=faults()
    if args.self_test:
        print(json.dumps(checked,indent=2));return
    out=args.output;out.mkdir(parents=True,exist_ok=True)
    require(not (out/'run.json').exists(),'refuse to overwrite previous experiment')
    prereg=__doc__
    (out/'preregistration.txt').write_text(prereg,encoding='utf-8')
    inputs=['src/controller.py','src/chemistry.py','src/tower.py','src/psychro.py',
            'src/water_activity.py','src/run_controller.py','results/calibration.json',
            'results/controller_summary.json','results/annual_datacentre.json','results/tmy_hourly.npy']
    hashes={p:source_hash(args.repo/p) for p in inputs}
    start=time.time()
    metadata=dict(script_sha256=source_hash(pathlib.Path(__file__)),input_sha256=hashes,
                  preregistration_sha256=hashlib.sha256(prereg.encode()).hexdigest(),
                  python=sys.version,repo=str(args.repo),Q_nominal_kW=QNOM,Q_IT_kW=QIT,tariffs=TAR)
    (out/'registration.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    old=json.loads((args.repo/'results/annual_datacentre.json').read_text())
    # Weather reconstructed from original hours, with the identical binning rule.
    h=np.load(args.repo/'results/tmy_hourly.npy')
    groups=np.array_split(np.argsort(h[:,5]),len(old['bins']))
    fwgrid=[ctl.CHILLER_TCHWS_RANGE[0],7.,ctl.CHILLER_TCHWS_RANGE[1]]
    cwgrid=sorted(set(np.linspace(*ctl.CHILLER_TCWS_RANGE,9).tolist()+[32.]))
    cygrid=list(range(2,11));phgrid=sorted(set(np.arange(7,9.01,0.25).tolist()+[7.8]))
    rows=[];reject=Counter();allstates=[]
    print('PRE-REGISTERED; strict envelope; fixed nameplate; one CDU; NO device model',flush=True)
    for i,idx in enumerate(groups):
        weather={'bin':i,'hours':int(len(idx)),'T_db_C':float(h[idx,3].mean()),
                 'rh':float(h[idx,4].mean()),'T_wb_C':float(h[idx,5].mean()),
                 'hours_above_validation':int(np.sum(h[idx,5]>21.9))}
        thermal=[]; candidates=[]; baseline_candidates=[]
        for tfw in fwgrid:
            for tcw in cwgrid:
                for cy in cygrid:
                    try: r,reason=solve_tower(tcw,tfw,cy,weather,rc.TSE)
                    except InvalidState as ex:
                        reject[str(ex)]+=1;continue
                    if r is None:
                        reject[reason]+=1;continue
                    r['bin']=i
                    versions=[chemistry_at(r,ph,rc.TSE) for ph in phgrid]
                    feasible=[x for x in versions if x['chemistry_ok']]
                    chosen=min(feasible or versions,key=lambda x:x['cost_per_h'])
                    thermal.append(chosen);allstates.append(chosen)
                    candidates.extend(feasible)
                    if tfw==7. and cy==4:
                        base=chemistry_at(r,7.8,rc.TSE)
                        if base['chemistry_ok']:baseline_candidates.append(base)
        base=min(baseline_candidates,key=lambda x:abs(x['T_ecwt_C']-32.)) if baseline_candidates else None
        fixed=[r for r in candidates if r['T_fws_C']==7]
        fixed=min(fixed,key=lambda x:x['cost_per_h']) if fixed else None
        best=min(candidates,key=lambda x:x['cost_per_h']) if candidates else None
        row=dict(weather,baseline=base,fixed_fws_optimum=fixed,coupled_optimum=best,
                 thermally_feasible_candidates=len(thermal),chemically_feasible_ph_candidates=len(candidates))
        h2c=[];h2t=[];percycles=[]
        for r in thermal:
            if r['chemistry_ok']:
                following=[x for x in thermal if x['cycles']==r['cycles']+1 and x['T_fws_C']==r['T_fws_C'] and x['T_ecwt_C']==r['T_ecwt_C']]
                for s in following:
                    if not s['chemistry_ok'] and ctl.CHILLER_TCWS_RANGE[1]-s['T_ecwt_C']>0.1 and ctl.CHILLER_PLR_RANGE[1]-s['plr_raw']>0.01:
                        h2c.append(dict(cycles_before=r['cycles'],cycles_after=s['cycles'],T_fws_C=s['T_fws_C'],T_ecwt_C=s['T_ecwt_C'],violations=s['violations']))
        for cy in cygrid:
            therm=[x for x in thermal if x['cycles']==cy]
            safe=[x for x in therm if x['chemistry_ok']]
            max_t=max((x['T_fws_C'] for x in therm),default=None)
            max_c=max((x['T_fws_C'] for x in safe),default=None)
            gap=max_t-max_c if max_t is not None and max_c is not None else None
            if gap is not None and gap>=0.1:h2t.append({'cycles':cy,'lost_FWS_K':gap})
            percycles.append(dict(cycles=cy,max_thermal_FWS_C=max_t,max_chemical_FWS_C=max_c,
                                  temperature_loss_K=gap,excluded_by_chemistry=bool(therm and not safe),
                                  actual_chip_optimum_shortfall_K=None,
                                  gpu_water_at_max_fws_C=None if max_c is None else max_c+5))
        row.update(H2_cycles_witnesses=h2c,H2_temperature_witnesses=h2t,by_cycles=percycles)
        if best:
            # Forward-solve comparison with the unchanged original tower routine.
            replay,info=tw.solve_outlet_temperature(best['T_cw_return_C'],weather['T_db_C'],weather['rh'],PLANT['m_w'],PLANT['m_a_rated']*best['fan_pct']/100,FC,FN,aw=best['aw'])
            check_replay(best['T_ecwt_C'],replay,info)
            row['forward_replay_error_K']=float(abs(replay-best['T_ecwt_C']))
        rows.append(row)
        (out/f'bin_{i}.json').write_text(json.dumps(row,indent=2),encoding='utf-8')
        print(f"bin {i}: thermal={len(thermal)}, H2cycles={len(h2c)}, H2temperature={len(h2t)}, elapsed={time.time()-start:.1f}s",flush=True)
    # H1 sign checks across matched states; retain the original expected sign.
    lookup={(r['bin'],r['cycles'],r['T_fws_C'],r['T_ecwt_C']):r for r in allstates}
    h1a=[];h1b=[]
    for r in allstates:
        for tcw in cwgrid:
            if tcw<=r['T_ecwt_C']:continue
            s=lookup.get((r['bin'],r['cycles'],r['T_fws_C'],tcw))
            if s:h1a.append(s['T_gpu_inlet_water_C']-r['T_gpu_inlet_water_C'])
        s=lookup.get((r['bin'],r['cycles']+1,r['T_fws_C'],r['T_ecwt_C']))
        if s:h1b.append(s['SI_gypsum']-r['SI_gypsum'])
    verdicts={'H1a':dict(status='PASS' if h1a and min(h1a)>1e-6 else 'FAIL',pairs=len(h1a),min_change_K=min(h1a,default=None),max_change_K=max(h1a,default=None)),
              'H1b':dict(status='PASS' if h1b and min(h1b)>1e-8 else 'FAIL',pairs=len(h1b),minimum_SI_increase=min(h1b,default=None)),
              'H2_cycles':dict(status='PASS' if any(r['H2_cycles_witnesses'] for r in rows) else 'FAIL',weather_bins_with_witness=sum(bool(r['H2_cycles_witnesses']) for r in rows)),
              'H2_temperature':dict(status='PASS' if any(r['H2_temperature_witnesses'] for r in rows) else 'FAIL',weather_bins_with_witness=sum(bool(r['H2_temperature_witnesses']) for r in rows)),
              'H3':dict(status='NOT_IDENTIFIABLE',actual_chip_optimum_shortfall_K=None,reason='No measured chip-to-water map; CPU paper is not a GPU water response'),
              'H4':dict(status='NOT_IDENTIFIABLE',annual_ITD_cost_USD=None,reason='H3 map is absent; independent FWS economics are reported separately')}
    annual={}
    for a,b,name in [('baseline','coupled_optimum','coupled_vs_baseline'),('fixed_fws_optimum','coupled_optimum','FWS_increment_only')]:
        if all(r.get(a) and r.get(b) for r in rows):annual[name]=aggregates(rows,a,b)
        else:annual[name]={'status':'NOT_COMPUTED_MISSING_BINS'}
    changed=[p for p,v in hashes.items() if source_hash(args.repo/p)!=v]
    require(not changed,'source changed during experiment: '+str(changed))
    result=dict(metadata,verdicts=verdicts,bins=rows,annual=annual,rejected_candidates=dict(reject),
                fault_injections=checked,elapsed_seconds=time.time()-start,
                limits=dict(FWS_C=ctl.CHILLER_TCHWS_RANGE,ECWT_C=ctl.CHILLER_TCWS_RANGE,PLR=ctl.CHILLER_PLR_RANGE),
                grids=dict(FWS_C=fwgrid,ECWT_C=cwgrid,cycles=cygrid,pH=phgrid),
                confidence='Engineering scenario, inherited makeup defect17, no site validation; grid maximum only',
                external_full_text_C='UNAVAILABLE_UNSCORED')
    (out/'states.json').write_text(json.dumps(allstates,indent=2),encoding='utf-8')
    (out/'run.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(verdicts=verdicts,annual=annual),indent=2),flush=True)


if __name__=='__main__':main()
