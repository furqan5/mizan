"""Generate reproduction notes from accepted artifacts; no new model thresholds."""
from pathlib import Path
import importlib.metadata,json
ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'results/cdu_hybrid_verified/run.json').read_text())
v=json.loads((ROOT/'results/cdu_hybrid_verification.json').read_text())
c=json.loads((ROOT/'results/cdu_dry_cycles.json').read_text())
text=f'''# Reproducing the one-CDU research extension

8 Sep 2026. This is an internal engineering scenario and falsification study.
The full scope is recorded in `cdu_hybrid_research.md`; source links are in that
report and `research/claim-source-ledger.json`. Original files and historical
gates have not been changed. The scientific experiment was registered on
7 Sep 2026. The report and installation verification were completed subsequently.

## Outcome and remaining requirements

| Requirement | Current evidence | Status |
| --- | --- | --- |
| Add exactly one CDU; stop at GPU inlet water | `src/cdu_hybrid.py`, accepted state records | Implemented |
| H1 condenser-water sign | {r['verdicts']['H1a']['pairs']} matched pairs, fixed facility-water setpoint | FAIL; retain negative result |
| H1 cycles-to-gypsum sign | {r['verdicts']['H1b']['pairs']} matched pairs | PASS |
| H2 chemistry before equipment limits | Cycles witnesses in {r['verdicts']['H2_cycles']['weather_bins_with_witness']} bins; temperature witnesses in {r['verdicts']['H2_temperature']['weather_bins_with_witness']} bins | Cycles bind, maximum sampled FWS does not fall |
| H3 actual chip-optimum shortfall by cycles | Per-cycles water limits and required chip-to-water rise in JSON | NOT IDENTIFIABLE without measured same-device temperature relation |
| H4 annual ITD cost and lost cycles | Independent FWS comparison priced, both annual aggregations | ITD quantity NOT IDENTIFIABLE; independent reset costs zero cycles in this grid |
| A dry/wet crossover by tariff, weather, cycles | `cdu_dry_cycles.json`: {len(c['rows'])} combinations, {sum(x['status'].startswith('IN_CURVE') for x in c['rows'])} supported | Conditional crossover computed; full-year dry ROI requires a hot-hour machine map |
| B resolve and close defect 17 | Primary sulfate confirmed; two published analyses disagree | OPEN; no defensible correction, strict xfail retained |
| C scan closest full manuscript | Metadata/preview only after legitimate access searches | UNAVAILABLE/UNSCORED; full manuscript needed |
| Protect prior work and original gates | Byte hashes and before/after logs in installation record | Verified separately from model success |

The source ASHRAE water class applies to facility supply water. Actual site
class and GPU/OEM liquid-inlet limits remain unspecified. The Xeon curve is a
chip-temperature curve, not a GPU-water response. No semiconductor model or
temperature-dependent IT saving has been added. No external message, pitch,
publication, training run or repository commit is part of this change.

## Environment and commands

The run used the bundled Python runtime and workspace-isolated dependencies.
Exact scientific/PDF package versions are pinned in
`research/cdu_hybrid_requirements.txt`; that file is separate from the original
requirements. Use a suitable Python environment and install those packages if
needed. The full steady-state sweep took approximately
{r['elapsed_seconds']/60:.1f} minutes here; wall time is hardware-dependent.
It uses CPU calculations, not GPU training.

Run from the MIZAN repository root. Always pass a **fresh** result directory;
the main script's default directory contains the preserved failed experiment.
Completed experiments must not be overwritten. Example PowerShell commands:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
python -m pytest -p no:cacheprovider
python src/audit.py
python src/cdu_hybrid.py --repo . --self-test
python src/cdu_hybrid.py --repo . --output results/cdu_hybrid_rerun_01
python src/itd_source_lookup.py --pdf "C:/Users/Nouman/Desktop/sources/2606.11163v1.pdf" --out results/itd_lookup_rerun_01.json
python src/cdu_hybrid_diagnostics.py --repo . --run results/cdu_hybrid_rerun_01/run.json --lookup results/itd_lookup_rerun_01.json --out results/cdu_diagnostics_rerun_01.json
python src/cdu_dry_cycles.py --repo . --run results/cdu_hybrid_rerun_01/run.json --diagnostics results/cdu_diagnostics_rerun_01.json --out results/cdu_dry_rerun_01.json
python -m pytest -p no:cacheprovider
python src/audit.py
```

`research/verify_results.py --repo . --pdf "C:/Users/Nouman/Desktop/sources/2606.11163v1.pdf" --out results/cdu_verification_rerun_01.json`
checks the **delivered frozen experiment**, including its input hashes and
source PDF hash. It does not automatically verify a differently named rerun.
`research/build_report.py` builds the report from those delivered result paths
using ReportLab and the Windows Times New Roman fonts. It expects existing
`docs`, `research` and `output/pdf` folders. A rerun report must deliberately
point at the new experiment instead of silently mixing outputs.

The desktop source PDFs were relocated to `C:/Users/Nouman/Desktop/sources`
during this task. The source PDF hash, rather than its historical path, identifies
the ITD evidence; the final verifier accepts an explicit `--pdf` location and
requires that hash. The package includes
mechanical scan manifests and hashes, not copies of the papers. Both layout
and plain text extractions produced the recorded literal counts. To repeat
the scan, run `research/extract_sources.py` followed by `research/extract_plain.py`
with the supplied desktop PDFs available. The extraction paths are specific
to the discovery workspace; update their input directory for the relocated
files or another machine. Historical scan manifests retain discovery-time paths.

## Evidence and numerical verification

The main source docstring contains the pre-registration. Each completed run
contains a registration JSON, the exact docstring, input/source SHA256 values,
bin records, annual results and all {v['thermal_state_count']} accepted thermal
states. Both annual percentage conventions are stored for energy, makeup
water and operating cost. Weather bins represent the full year; centroid
feasibility is not proof of feasibility at every original hourly record.

The first inverse-root experiment failed the registered forward replay guard.
`results/cdu_hybrid/` retains its registration and partial bins;
`results/cdu_hybrid_replay_failure.json` records the offending state and
residual probes. The obsolete first solver source was not retained as a
separate snapshot, so that folder is not a complete executable version.
The bad state itself is reproducible through the unchanged tower routine:
the independent verifier confirms the failure again. Thresholds were not
changed; the accepted solver additionally replays every accepted inverse root.

The independent verifier records {v['check_count']} successful checks, including
all main fault injections, extraction faults, exact hashes, independent annual
sums, every stored envelope/heat/water balance, and the original bad root.
The first verifier attempt failed because `ast.get_docstring` stripped whitespace
before hashing. Using its uncleaned literal fixed that verifier implementation;
the registered docstring and all acceptance thresholds stayed unchanged.
The cycles crossover checks its cost intersection and injects false cost,
zero makeup and inconsistent fan assumptions to demonstrate rejection.

The first accepted source and results are retained in
`research/accepted_v1_snapshot/`. A final source cleanup reads the chiller's
reference temperatures directly from the original function defaults, removing
duplicated machine constants. The whole new sweep and its dependent diagnostics
were rerun with identical preregistration. The canonical result files contain
that final run; the archived version is evidence, not the recommended entry point.

Annual engineering estimates retain the inherited sodium-balancing assumption,
skin-temperature chemistry treatment and unvalidated operating scenarios.
Checking the maximum gypsum SI over each basin-to-skin temperature interval
produced no additional violations among the accepted chemistry states in this
grid; this does not establish global conservatism of the skin approximation.
Equipment sizing, pump deltas, transients, redundancy, condensation control,
corrosion programme, precipitation kinetics and actual tariff eligibility need
independent project data before implementation or client reliance.
'''
(ROOT/'docs/cdu_hybrid_readme.md').write_text(text,encoding='utf-8')
packages=['numpy','scipy','pandas','pytest','pypdf','pdfplumber','reportlab']
(ROOT/'research/cdu_hybrid_requirements.txt').write_text('\n'.join(
    name+'=='+importlib.metadata.version(name) for name in packages)+'\n',encoding='utf-8')
print('Wrote reproduction notes and isolated package version pins.')
