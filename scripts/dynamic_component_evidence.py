"""Record the 21 Sep 2026 dynamic-component numerical probes.

Protocol: three synthetic tower cases RH=.3/.6/.85, hot38C, dry25C,
p101325Pa, hot100kg/s, air75kg/s, fill c1/n.6, aw1. Retain the old
temperature-coordinate energy residual; it is not rescored as a new field
gate. Compare conservative160/320steps at fixed cold flow100kg/s: outlet
change<=.01K, evaporation relative change<=.001, registered in tower.py
before its tests. Canonical chiller reference-point PLR1/1.03/1.06 records
old and strict power; no economic or field-performance assertion.
All input/source/output hashes are registered. Output directory must be new.
"""
from dataclasses import asdict
from pathlib import Path
import argparse
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from evidence_run import EvidenceRun, verify_run
import thermal_dynamics as td


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    tests = [ROOT/'review_tests'/f'test_{name}.py' for name in
             ('thermal_dynamics', 'inventory_ledger', 'solution_mass_bridge', 'control_timeline')]
    tests += [ROOT/'docs'/f'{name}_scope.md' for name in
              ('inventory_ledger', 'solution_mass_bridge', 'control_timeline')]
    run = EvidenceRun(ROOT, args.output, inputs=tests, configuration={
        'fixture_basis': 'synthetic mathematical probes, no plant dataset',
        'rh': [.3, .6, .85], 'convergence_temperature_k': .01,
        'convergence_evaporation_relative': .001,
        'water_mass_tolerance': {'absolute_kg_s': 1e-9, 'relative': 1e-8},
        'energy_tolerance': {'absolute_kw': 1e-6, 'relative': 1e-5}},
        method='Canonical thermal components and retained legacy balance comparison')
    rows = []
    for rh in [.3, .6, .85]:
        started = time.perf_counter()
        dynamic = td.tower_pass(38., 25., rh, 101325., 100., 75., 1., .6, 1.)
        duration = time.perf_counter()-started
        legacy_t, legacy = td.tower.solve_outlet_temperature(38., 25., rh, 100., 75., 1., .6)
        humidity = float(td.psychro.humidity_ratio_from_rh(25., rh, 101325.))
        legacy_air = 75.*(legacy['h_a_out']-td.psychro.h_scalar(25., humidity))
        legacy_liquid = td.tower.CPW*(legacy['m_w_top']*38.-100.*legacy_t)
        coarse_t, coarse = td.tower.solve_outlet_temperature(
            38., 25., rh, 100., 75., 1., .6, conservative_energy=True, n_steps=160)
        fine_t, fine = td.tower.solve_outlet_temperature(
            38., 25., rh, 100., 75., 1., .6, conservative_energy=True, n_steps=320)
        dt = abs(coarse_t-fine_t)
        de = abs(coarse['m_evap']/fine['m_evap']-1.)
        rows.append({'relative_humidity': rh, 'new_hot_flow_component': asdict(dynamic),
                     'observed_call_duration_s': duration,
                     'legacy_fixed_cold_flow_kg_s': 100.,
                     'legacy_energy_residual_kw': legacy_liquid-legacy_air,
                     'legacy_exceeds_new_numerical_tolerance': abs(legacy_liquid-legacy_air)>1e-6+1e-5*abs(legacy_liquid),
                     'step_refinement': {'temperature_change_k': dt,
                                         'evaporation_relative_change': de,
                                         'passed': dt <= .01 and de <= .001}})
    chillers = []
    for plr in [1., 1.03, 1.06]:
        legacy, _ = td.controller.chiller_power_biquad(1000.*plr, 29.44, 6.67, Q_ref_kw=1000.)
        strict = td.chiller_pass(1000.*plr, 29.44, 6.67, 1000., enabled=True)
        chillers.append({'plr': plr, 'legacy_power_kw': legacy, 'strict': asdict(strict)})
    passed = all(row['step_refinement']['passed'] for row in rows)
    result = {'numerical_probe_status': 'PASS' if passed else 'FAIL', 'tower': rows, 'chiller': chillers,
              'physical_accuracy_validated': False, 'full_mpc_implemented': False,
              'warm_fws_chiller_qualified': False, 'write_enabled': False,
              'limitations': ['Three synthetic component cases do not prove global solver robustness.',
                              'Old tower evaporation/heat-rejection/PINN/chemistry gates remain unchanged.',
                              'Solution mass and phase enthalpy require a speciation/property bridge.',
                              'No joint inventory/thermal/chemistry rollout or optimizer is certified.',
                              'Measured component runtime is not full-horizon or worst-case timing.']}
    (run.output/'component_probes.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    run.finish(model_status='NUMERICAL_PROBES_PASS_ONLY' if passed else 'NUMERICAL_PROBE_FAIL',
               result_summary={'tower_cases': len(rows), 'chiller_cases': len(chillers),
                               'field_qualified': False, 'full_mpc_complete': False})
    verification = verify_run(run.output)
    print(json.dumps(verification, indent=2))
    return 0 if passed and verification['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
