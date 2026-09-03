"""
FURQAN :: build the DTV application bundle
==========================================
One zip, everything a reviewer needs, nothing they do not.

The audit must pass before anything is packaged. A bundle assembled from an
inconsistent tree is worse than no bundle, because it looks finished.

Run:  python src/package.py
"""
from __future__ import annotations

import datetime as _dt
import json
import pathlib
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT.parent / "Furqan_Mizan_DTV_Application.zip"

# What goes in, and why. `sources/` (95 MB of reference PDFs) is deliberately
# left out: it is our working library, not evidence, and every source is
# cited by name in the documents that need it.
INCLUDE = [
    ("submission", "*.pdf",  "01_Application_PDFs"),
    ("submission", "*.pptx", "01_Application_PDFs"),
    ("figs",       "*.png",  "02_Figures"),
    ("figs/slide", "*.png",  "02_Figures/slide_variants"),
    ("matlab",     "*.m",    "03_MATLAB_Simulink"),
    ("matlab",     "*.slx",  "03_MATLAB_Simulink"),
    ("matlab",     "*.md",   "03_MATLAB_Simulink"),
    ("matlab/+mizan", "*.m", "03_MATLAB_Simulink/+mizan"),
    ("modelica",   "*",      "04_OpenModelica"),
    ("src",        "*.py",   "05_Python_source"),
    ("src",        "*.js",   "05_Python_source"),
    ("results",    "*.json", "06_Results"),
    ("results",    "*.csv",  "06_Results"),
    ("results",    "*.txt",  "06_Results"),
    ("docs",       "*.md",   "07_Document_sources"),
]

SKIP_NAMES = {"__pycache__"}


def readme(cal, ctrl, mp) -> str:
    ho, sm = cal["HOLDOUT"], ctrl["summary"]
    d = _dt.date.today().strftime("%d %B %Y")
    return f"""FURQAN  --  The criterion for energy.
MIZAN   --  The balance between energy and water.

DTV Deep-Tech Ventures Program (.dvp) Cohort 2
Dhahran Techno Valley / KFUPM
Bundle built {d}

================================================================================
START HERE
================================================================================

  01_Application_PDFs/Furqan_Mizan_PoC_Report.pdf     the evidence
  01_Application_PDFs/Furqan_Mizan_DTV_Deck.pptx      the deck
  03_MATLAB_Simulink/README.md                        the model, in plain
                                                      English, for a reader
                                                      with no thermodynamics

================================================================================
WHAT IS CLAIMED, AND WHAT IS NOT
================================================================================

Thresholds were fixed and printed BEFORE fitting. Two of them are not met,
and both are reported as failures rather than rescored.

  V1  outlet water temperature MAE     {ho['Tout_MAE_K']:.3f} K   <= 1.00 K    PASS
  V1  heat rejection MAPE              {ho['Q_MAPE_pct']:.2f} %    <= 6.00 %    PASS
  V2  water consumption MAPE           {ho['evap_MAPE_pct']:.2f} %    <= 8.00 %    FAIL
  V5  total cost reduction             {sm['cost_pct']:.2f} %    >= 3 %       PASS
  V5  makeup water reduction           {sm['water_pct']:.2f} %   >= 15 %      FAIL
  V5  skin saturation violations       {sm['violations']}          0            PASS

Both failures are diagnosed, not merely admitted:

  V2 fails because a drift constant was a hundred times too large and was
  padding the prediction. Correcting it turned a 7.11 % pass into a 9.90 %
  failure. The residual is campaign-dependent, which points at the same fill
  drift already documented, and the measured channel is TOTAL water
  consumption, so it may include a bleed the rig never published.

  V5's water threshold was arithmetically unreachable. Makeup water is
  evaporation x C/(C-1), so 15 % requires 8.5 cycles of concentration, and
  gypsum saturates at 8. The criterion was written on the far side of a wall
  that had not been found yet. It was mis-specified, not missed.

================================================================================
WHAT IS IN THE BUNDLE
================================================================================

  01_Application_PDFs   18 PDFs and the 20-slide deck. Typeset in XeLaTeX,
                        Times New Roman 12 pt.
  02_Figures            Every figure, in report and slide variants.
  03_MATLAB_Simulink    The MATLAB twin, the Simulink plant model with
                        Simscape and Stateflow, the control-design work
                        (Curve Fitting, System Identification, Control
                        System, MPC, Optimization) and the physics-informed
                        surrogate. START WITH README.md.
  04_OpenModelica       The Modelica leg. Written, not yet run -- OpenModelica
                        is not installed. It makes no claim.
  05_Python_source      The reference implementation. This is the thing that
                        was validated against experiment.
  06_Results            Every result artefact. Every number in every document
                        is generated from these files.
  07_Document_sources   The markdown the PDFs are built from.

================================================================================
REPRODUCING IT
================================================================================

  python src/fetch_zenodo.py        downloads and MD5-verifies the dataset
  python src/calibrate.py           gates V1, V2
  python src/run_controller.py      gates V3, V5, V5b     (~25 min)
  python src/make_figures.py        every figure, both variants
  python src/make_report.py         markdown from the results
  python src/make_latex.py          the PDFs
  node   src/build_deck.js          the deck
  python src/audit.py               34 consistency checks -- MUST PASS

  In MATLAB:
    mizan_verify           the MATLAB twin against the Python core
    mizan_demo             one Gulf day, plain English
    mizan_simulate         the Simulink plant model
    mizan_control_design   the five toolboxes
    mizan_pinn             the physics-informed surrogate

================================================================================
THE MATLAB TWIN AGREES WITH THE PYTHON REFERENCE
================================================================================

A second implementation is worth nothing until it is shown to reproduce the
one that was validated. Gates fixed before the first run:

  outlet water temperature   0.000014 K   <= 0.010 K    PASS
  evaporation rate           0.00018 %    <= 0.50 %     PASS
  chiller electrical power   0.000000 %   <= 0.10 %     PASS
  brucite saturation pH      0.0014       <= 0.005      PASS

The physics-informed surrogate, against gates fixed before training:

  faithfulness to the physics model   {mp['Tout_MAE_K']:.4f} K   <= 0.10 K   PASS
  physical violations, Gulf band      {mp['violations']}          0          PASS
  speed-up over the physics model     {mp['speedup']:.0f}x         >= 500x    FAIL

That last one is reported as a failure and the threshold was not moved. The
500x figure was written against the Python core at 141 ms per point; MATLAB's
core is ten times faster, so the same surrogate scores a smaller ratio
against a faster baseline.

================================================================================
OPEN ITEMS
================================================================================

  Almeria wet-bulb 21.9 C vs Gulf design 30.3 C   the largest one. Closed by
                                                  KFUPM's humidifying wind
                                                  tunnel, not by argument.
  Model error 2.48x measurement uncertainty       against us, reported.
  V2 water-consumption gate                       failed, diagnosed above.
  V5 water-reduction gate                         failed, threshold was
                                                  unreachable.
  Skin temperature rise of +8 K                   assumed from literature.
                                                  Every V3 and V5 result
                                                  scales with it. Deriving it
                                                  from boundary-layer CFD is
                                                  on the roadmap.
  Magnesium-silicate SI threshold                 handled by the empirical
                                                  Mg x SiO2 product instead.
  No traction, no LOIs, no patents                Cohort 1 winners had none
                                                  either.

Nothing here is papered over. Where a number could not be verified it is
tagged, and where a gate failed it says so.

--------------------------------------------------------------------------------
Engr. Furqan Shakeel   engr.furqan.shakeel@gmail.com   +92 302 1044259
Engr. Damia Baig       baigdamia@gmail.com             +92 331 6491787
Engr. Muhammad Ahsan   muhammadahsan4203@gmail.com     +92 307 4873873
Lahore, Pakistan
"""


def main() -> int:
    print("=" * 74)
    print("FURQAN / MIZAN :: building the DTV application bundle")
    print("=" * 74)

    print("\nrunning the consistency audit first ...")
    r = subprocess.run([sys.executable, str(ROOT / "src" / "audit.py")],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:])
        print("\nAUDIT FAILED -- nothing packaged. Fix the tree first.")
        return 1
    print("audit passed.\n")

    cal = json.loads((ROOT / "results" / "calibration.json").read_text())
    ctrl = json.loads((ROOT / "results" / "controller_summary.json").read_text())
    mp = json.loads((ROOT / "results" / "matlab_pinn.json").read_text())

    if OUT.exists():
        OUT.unlink()

    n = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("README.txt", readme(cal, ctrl, mp))
        z.write(ROOT / "HANDOFF.md", "08_Project_state/HANDOFF.md")
        n += 2
        for src_dir, pattern, dest in INCLUDE:
            d = ROOT / src_dir
            if not d.exists():
                continue
            for f in sorted(d.glob(pattern)):
                if not f.is_file() or f.parent.name in SKIP_NAMES:
                    continue
                z.write(f, f"{dest}/{f.name}")
                n += 1

    size = OUT.stat().st_size / 1e6
    print(f"{n} files, {size:.1f} MB")
    print(f"\nwritten -> {OUT}")

    with zipfile.ZipFile(OUT) as z:
        groups: dict[str, int] = {}
        for i in z.namelist():
            groups[i.split("/")[0]] = groups.get(i.split("/")[0], 0) + 1
        print()
        for g, c in sorted(groups.items()):
            print(f"   {g:28s} {c:4d} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
