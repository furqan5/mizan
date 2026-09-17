"""MIZAN :: defect-corrected re-score of the registered one-CDU study (R2).

Pre-registered in docs/staged/cdu_joint_policy_preregistration.md, section 7,
committed before this ran.

`src/cdu_hybrid.py` is a registered experiment, so it is NOT edited. It carries
local re-implementations of three calculations that the package has since
corrected in the engine. This wrapper replaces its `chemistry_at` with a
version that differs in exactly those three places, then runs its unchanged
`main()`. The thresholds and verdict logic stay as registered.

  defect 25  acid is charged on blowdown + drift, not on makeup
  defect 30  water is charged through controller._water_cost_per_h
             (makeup price on makeup, discharge price on blowdown)
  defect 44  skin rise is controller.SKIN_DELTA_K_DEFAULT (derived), not 8 K

NOT corrected, and recorded as a dependency: the staged safety-branch
defect 54 (the sulfate the acid adds is missing from the gypsum index). H1b is a
gypsum hypothesis and inherits it.

Run: python src/cdu_hybrid_rescore.py --repo . --output results/cdu_hybrid_rescore_corrected_20260917
"""
from __future__ import annotations

import hashlib
import inspect
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import cdu_hybrid as ch  # noqa: E402


def corrected_chemistry_at(r, ph, water, skin_rise=None):
    ctl, chem, TAR = ch.ctl, ch.chem, ch.TAR
    skin_rise = float(ctl.SKIN_DELTA_K_DEFAULT) if skin_rise is None else skin_rise
    conc = water.concentrate(r['cycles'])
    skin = r['T_cw_return_C'] + skin_rise
    sat = chem.saturation_state_split(conc, skin, r['T_ecwt_C'], pH_hot=ph, pH_cold=ph)
    violations = {k: float(sat[k] - v) for k, v in chem.OPERATING_LIMITS.items() if sat[k] > v}
    bulk = chem.saturation_state(conc, r['T_ecwt_C'], pH=ph)
    if ctl.CORROSION_FLOOR_SI is not None and bulk['SI_calcite'] < ctl.CORROSION_FLOOR_SI:
        violations['corrosion_floor'] = float(ctl.CORROSION_FLOOR_SI - bulk['SI_calcite'])
    acid, _ = ctl.acid_dose_for_ph(water, r['cycles'], ph, skin)
    # defect 25: the alkalinity balance leaves on blowdown + drift
    acid_h = acid * ((r['blowdown_m3_h'] + r['drift_m3_h']) / 3.6) * 3600
    # defect 30: split tariff, blowdown carries the discharge fee
    wb = {'makeup': r['makeup_m3_h'] / 3.6, 'blowdown': r['blowdown_m3_h'] / 3.6}
    cost = (TAR['elec_per_kwh'] * r['P_total_kW'] + ctl._water_cost_per_h(wb, TAR)
            + TAR['acid_per_kg'] * acid_h + TAR['antiscalant_per_m3'] * r['makeup_m3_h'])
    out = dict(r, ph=float(ph), chemistry_ok=not violations, violations=violations,
               SI_calcite=float(sat['SI_calcite']), SI_gypsum=float(sat['SI_gypsum']),
               SI_gypsum_basin=float(bulk['SI_gypsum']), SI_silica_am=float(sat['SI_silica_am']),
               bulk_SI_calcite=float(bulk['SI_calcite']), acid_kg_h=float(acid_h),
               cost_per_h=float(cost), ionic_strength=float(conc.ionic_strength()),
               assumed_skin_rise_K=float(skin_rise))
    return out


def main():
    args = sys.argv[1:]
    out = pathlib.Path(args[args.index('--output') + 1]) if '--output' in args else None
    if out is None:
        raise SystemExit('--output <fresh directory> is required')
    if (out / 'run.json').exists():
        raise SystemExit('refuse to overwrite previous experiment')
    out.mkdir(parents=True, exist_ok=True)
    src = inspect.getsource(corrected_chemistry_at)
    (out / 'rescore_patch.json').write_text(json.dumps({
        'wrapper': 'src/cdu_hybrid_rescore.py',
        'wrapper_sha256': hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        'registered_script_sha256': hashlib.sha256((ROOT / 'src/cdu_hybrid.py').read_bytes()).hexdigest(),
        'patched_function': 'chemistry_at',
        'patch_source': src,
        'corrects': ['defect 25 acid on blowdown+drift', 'defect 30 split water tariff',
                     'defect 44 derived skin rise'],
        'not_corrected': ['staged defect 54 acid sulfate absent from gypsum index (H1b depends on gypsum)'],
        'preregistration': 'docs/staged/cdu_joint_policy_preregistration.md section 7',
    }, indent=2), encoding='utf-8')
    ch.chemistry_at = corrected_chemistry_at
    sys.argv = [str(ROOT / 'src/cdu_hybrid.py')] + args
    ch.main()


if __name__ == '__main__':
    main()
