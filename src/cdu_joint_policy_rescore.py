"""MIZAN :: the registered joint-policy study, run again on the current fill law.

Pre-registered in docs/staged/plant_scale_site_pressure_preregistration.md,
section 3, written before this ran. Defect 79 moved the fill law to the
Almeria site pressure, and the 17 September run was built on the sea-level one.

`src/cdu_joint_policy.py` is a registered experiment, so it is NOT edited. This
wrapper runs its unchanged functions with two declared deviations:

  OUT  a fresh directory, because the 17 September run refuses to be
       overwritten and should not be.
  NLR  the NLR power file the study reads is a path on the old laptop and is
       not on this one. The only thing the study takes from it is one scalar,
       mean / max of the fully covered 5-minute rows, used as the L1 flat load
       fraction. That scalar is read from the 17 September run's stored
       hours.json, not typed, and the run refuses to start if the four regions
       disagree on it.

The overrides sit at module level, not under the main guard, because the pool
spawns its workers and each worker re-imports this file.

Run: python src/cdu_joint_policy_rescore.py --output results/cdu_joint_policy_20261021
"""
from __future__ import annotations

import json
import pathlib
import sys
import time
from multiprocessing import Pool

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import cdu_joint_policy as jp  # noqa: E402

STORED_RUN = ROOT / "results" / "cdu_joint_policy_20260917"
PREREG = ROOT / "docs" / "staged" / "plant_scale_site_pressure_preregistration.md"


def _stored_nlr_fraction():
    hours = json.loads((STORED_RUN / "hours.json").read_text(encoding="utf-8"))
    vals = {f for r in hours.values() for f in r["load"]["L1_NLR_flat"]["fractions"]}
    if len(vals) != 1:
        raise SystemExit(f"the stored L1 fractions disagree: {sorted(vals)}")
    return vals.pop()


NLR_FRACTION = _stored_nlr_fraction()
jp._nlr_fraction = lambda: NLR_FRACTION


def main():
    args = sys.argv[1:]
    if "--output" not in args:
        raise SystemExit("--output <fresh directory> is required")
    out = pathlib.Path(args[args.index("--output") + 1])
    if not out.is_absolute():
        out = ROOT / out
    if (out / "run.json").exists():
        raise SystemExit("refuse to overwrite a completed run")
    out.mkdir(parents=True, exist_ok=True)
    inputs = ["src/cdu_joint_policy.py", "src/cdu_joint_policy_rescore.py",
              "src/hybrid_supervisor.py", "src/models/cdu_model.py",
              "src/chemistry.py", "src/controller.py", "src/tower.py", "src/corrosion.py",
              "scripts/generate_pitch_artifacts.py", "results/calibration.json",
              "results/tmy_hourly.npy", "results/pitch_artifacts.json",
              "docs/staged/cdu_joint_policy_preregistration.md",
              "docs/staged/plant_scale_site_pressure_preregistration.md"]
    reg = {"inputs_sha256": {p: jp.sha(ROOT / p) for p in inputs},
           "nlr_fraction": NLR_FRACTION,
           "nlr_fraction_source": "results/cdu_joint_policy_20260917/hours.json",
           "nlr_fraction_source_sha256": jp.sha(STORED_RUN / "hours.json"),
           "deviations": ["output directory", "NLR scalar read from the stored run"],
           "python": sys.version, "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    (out / "registration.json").write_text(json.dumps(reg, indent=2), encoding="utf-8")
    gpa = jp._load_gpa()
    t0 = time.time()
    with Pool(len(gpa.REGIONS)) as pool:
        results = dict(pool.map(jp.run_region, list(gpa.REGIONS)))
    changed = [p for p, h in reg["inputs_sha256"].items() if jp.sha(ROOT / p) != h]
    if changed:
        raise SystemExit(f"inputs changed during the run: {changed}")
    summary = jp.score(results)
    summary["elapsed_s"] = time.time() - t0
    (out / "hours.json").write_text(json.dumps(results, indent=1, default=float), encoding="utf-8")
    (out / "run.json").write_text(json.dumps(dict(registration=reg, **summary), indent=2, default=float),
                                  encoding="utf-8")
    jp._print(summary)


if __name__ == "__main__":
    main()
