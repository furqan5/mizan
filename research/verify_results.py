"""Independent artifact verification, registered before its first execution.

This adds verification, not new scientific success thresholds. Source hashes
and preregistration must match exactly. Recompute annual totals/percentages
using Python math.fsum (relative tolerance 1e-12, absolute 1e-8 for numerical
roundoff); use the main study's unchanged 1e-3 K forward replay criterion.
All accepted states must respect each original chiller envelope, 30..100% fan,
the registered CDU balance and water-balance tolerances. Re-extracted ITD
points must equal the saved rounded points exactly. Inject one bad PDF page
state for every explicit extraction assertion: curve count, tick alignment,
axis calibration, power closure, ascending temperatures, interior minimum.
The recorded first-run spurious inverse root must fail the forward replay
guard again; never rerun its obsolete optimiser or overwrite its evidence.
Hash checks also cover every registered model input. Missing annual bins and
stale source records must be detected. The original pytest/audit suites remain
separate required checks; no protected test file is modified.
"""
from pathlib import Path
import argparse,ast,copy,hashlib,json,math,sys
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import cdu_hybrid as m
import itd_source_lookup as itd

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',type=Path,default=m.DEFAULT_REPO)
    ap.add_argument('--pdf',type=Path,help='Relocated source PDF; its exact recorded hash is still required')
    ap.add_argument('--out',type=Path,default=ROOT/'results/cdu_hybrid_verification.json')
    args=ap.parse_args()
    assert not args.out.exists(),'use a fresh verification output path'
    m.setup(args.repo)
    r=json.loads((ROOT/'results/cdu_hybrid_verified/run.json').read_text())
    d=json.loads((ROOT/'results/cdu_hybrid_diagnostics.json').read_text())
    l=json.loads((ROOT/'results/itd_source_lookup.json').read_text())
    pdf_path=args.pdf or Path(l['source'])
    states=json.loads((ROOT/'results/cdu_hybrid_verified/states.json').read_text())
    checks=[]
    def check(name,condition):
        assert condition,name
        checks.append(name)
    def reject(name,fn,exception,expected=None):
        try:fn()
        except exception as error:
            if expected is not None:assert str(error)==expected,(name,str(error))
            checks.append(name)
            return
        raise AssertionError('fault not rejected: '+name)
    check('main source hash',sha(ROOT/'src/cdu_hybrid.py')==r['script_sha256'])
    prereg=ast.get_docstring(ast.parse((ROOT/'src/cdu_hybrid.py').read_text()),clean=False)
    check('registered docstring hash',hashlib.sha256(prereg.encode()).hexdigest()==r['preregistration_sha256'])
    check('failed and accepted numerical preregistrations identical',
          (ROOT/'results/cdu_hybrid/preregistration.txt').read_bytes()==
          (ROOT/'results/cdu_hybrid_verified/preregistration.txt').read_bytes())
    check('diagnostic source hash',sha(ROOT/'src/cdu_hybrid_diagnostics.py')==d['script_sha256'])
    check('diagnostic run dependency',sha(ROOT/'results/cdu_hybrid_verified/run.json')==d['run_sha256'])
    check('diagnostic lookup dependency',sha(ROOT/'results/itd_source_lookup.json')==d['lookup_sha256'])
    for p,h in r['input_sha256'].items():check('model input '+p,sha(args.repo/p)==h)
    check('eight complete bins and all hours',len(r['bins'])==8 and sum(x['hours'] for x in r['bins'])==8760
          and all(x['baseline'] and x['fixed_fws_optimum'] and x['coupled_optimum'] for x in r['bins']))
    recomputed={}
    for base,opt,label in [('baseline','coupled_optimum','coupled_vs_baseline'),
                           ('fixed_fws_optimum','coupled_optimum','FWS_increment_only')]:
        recomputed[label]={}
        for key,name in [('P_total_kW','energy'),('makeup_m3_h','water'),('cost_per_h','cost')]:
            rows=r['bins'];hours=sum(x['hours'] for x in rows)
            bt=math.fsum(x['hours']*x[base][key] for x in rows)
            ot=math.fsum(x['hours']*x[opt][key] for x in rows)
            diff=math.fsum(x['hours']*(x[base][key]-x[opt][key]) for x in rows)
            values=dict(base_annual_total=bt,opt_annual_total=ot,annual_difference=diff,
                        ratio_of_totals_pct=100*diff/bt,
                        mean_of_ratios_pct=math.fsum(x['hours']*100*(x[base][key]-x[opt][key])/x[base][key] for x in rows)/hours)
            for k,v in values.items():check(label+'/'+name+'/'+k,
                math.isclose(v,r['annual'][label][name][k],rel_tol=1e-12,abs_tol=1e-8))
            recomputed[label][name]=values
    for s in states:
        for key,bounds in [('T_fws_C','FWS_C'),('T_ecwt_C','ECWT_C'),('plr_raw','PLR')]:
            assert r['limits'][bounds][0]<=s[key]<=r['limits'][bounds][1]
        assert 30<=s['fan_pct']<=100
        assert s['forward_replay_error_K']<=1e-3
        m.check_cdu_balance(s)
        m.check_water_balance(*(s[k]/3.6 for k in ['evaporation_m3_h','drift_m3_h','blowdown_m3_h','makeup_m3_h']))
        assert math.isclose(s['Q_cond_kW'],s['Q_cdu_kW']+s['P_chiller_kW'],rel_tol=1e-12)
    checks.append('all stored thermal states: envelopes, fan, heat, water, replay')
    main_faults=m.faults()
    check('all main registered fault injections',all(x['pass_'] for x in main_faults))
    missing=copy.deepcopy(r['bins']);missing[0]['baseline']=None
    reject('missing annual bin fault',lambda:m.aggregates(missing,'baseline','coupled_optimum'),m.InvalidState)
    failed=json.loads((ROOT/'results/cdu_hybrid_replay_failure.json').read_text())
    bad=failed['best'];w=failed['weather']
    actual,info=m.tw.solve_outlet_temperature(bad['T_cw_return_C'],w['T_db_C'],w['rh'],
        m.PLANT['m_w'],m.PLANT['m_a_rated']*bad['fan_pct']/100,m.FC,m.FN,aw=bad['aw'])
    reject('recorded spurious inverse root replay',lambda:m.check_replay(bad['T_ecwt_C'],actual,info),m.InvalidState)
    check('preserved failed replay numeric result',math.isclose(actual,failed['replay'],rel_tol=1e-12,abs_tol=1e-8))
    extracted=itd.extract(pdf_path)
    check('ITD re-extraction exact points',extracted['points']==l['points'])
    check('ITD source hash',sha(pdf_path)==l['source_sha256'])
    with itd.pdfplumber.open(pdf_path) as pdf:
        pg=pdf.pages[1]
        original=SimpleNamespace(curves=copy.deepcopy(pg.curves),lines=copy.deepcopy(pg.lines),words=copy.deepcopy(pg.extract_words()))
    def selected(page):
        return [c for c in page.curves if not c['fill'] and len(c['pts'])==10 and c['width']>100
                and c['x1']<285 and 300<c['top']<450 and c['bottom']<450]
    def run_fault(name,mutate,expected):
        page=copy.deepcopy(original);mutate(page)
        page.extract_words=lambda:page.words
        with patch.object(itd.pdfplumber,'open',return_value=SimpleNamespace(pages=[None,page])):
            reject(name,lambda:itd.extract(pdf_path),AssertionError,expected)
    run_fault('ITD wrong figure count',lambda p:selected(p)[0].update(fill=True),'wrong figure selection')
    def tick_fault(p):
        w=next(w for w in p.words if w['text'].isdigit() and 90<w['x0']<285 and 450<w['top']<460)
        w['x0']+=6;w['x1']+=6
    run_fault('ITD tick alignment',tick_fault,'tick mismatch')
    def axis_fault(p):
        w=next(w for w in p.words if w['text'].isdigit() and 90<w['x0']<285 and 450<w['top']<460)
        w['text']='999'
    run_fault('ITD axis calibration',axis_fault,'axis calibration')
    def closure_fault(p):
        c=selected(p)[0];x,y=c['pts'][0];c['pts'][0]=(x,y+10)
    run_fault('ITD power closure',closure_fault,'component closure')
    def monotonic_fault(p):
        for c in selected(p):c['pts'][0],c['pts'][1]=c['pts'][1],c['pts'][0]
    run_fault('ITD increasing temperature',monotonic_fault,'')
    def minimum_fault(p):
        for c in selected(p):
            red,green,blue=c['stroking_color']
            if not (green>red and green>blue):
                x,y=c['pts'][0];c['pts'][0]=(x,y+500)
    run_fault('ITD interior minimum',minimum_fault,'no interior minimum')
    output=dict(status='PASS',preregistration=__doc__,script_sha256=sha(Path(__file__)),source_pdf_verified_at=str(pdf_path),
                checks=checks,check_count=len(checks),main_fault_injections=main_faults,
                independently_recomputed_annual=recomputed,thermal_state_count=len(states),
                maximum_forward_replay_error_K=max(x['forward_replay_error_K'] for x in states),
                failed_root_forward_error_K=abs(actual-bad['T_ecwt_C']),
                unavailable_requirements=['same-device chip-to-water measurements','closest Applied Energy full manuscript',
                                          'reconciled primary makeup laboratory analysis','applicable hot-hour dry equipment map'])
    args.out.write_text(json.dumps(output,indent=2),encoding='utf-8')
    print(json.dumps(dict(status=output['status'],check_count=len(checks),thermal_states=len(states),
                         maximum_forward_replay_error_K=output['maximum_forward_replay_error_K']),indent=2))

if __name__=='__main__':main()
