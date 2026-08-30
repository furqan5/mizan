"""
FURQAN :: OpenModelica driver for the condenser-loop plant model
===============================================================
Detects whether OpenModelica and the LBNL Buildings library are present,
and says plainly what is missing rather than failing obscurely.

The reason this leg exists at all: the Buildings library ships the SAME
CoolTools chiller performance data the Python core reads its coefficients
from, so the Modelica plant and the Python reference are driven by one
dataset rather than two that have to be kept in step by hand. That was the
deciding argument over Simscape Fluids, which would have meant two.

Nothing in the evidence package depends on this file. It is the destination,
not a result.

Run:  python src/run_modelica.py
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODELICA = ROOT / "modelica"
RESULTS = ROOT / "results"


def find_omc() -> str | None:
    """Locate the OpenModelica compiler."""
    exe = shutil.which("omc")
    if exe:
        return exe
    for guess in (r"C:\Program Files\OpenModelica\bin\omc.exe",
                  r"C:\OpenModelica\bin\omc.exe",
                  "/usr/bin/omc"):
        if pathlib.Path(guess).exists():
            return guess
    return None


def have_ompython() -> bool:
    try:
        import OMPython           # noqa: F401
        return True
    except ImportError:
        return False


def main() -> int:
    print("=" * 74)
    print("FURQAN / MIZAN :: OpenModelica plant model")
    print("=" * 74)

    omc = find_omc()
    ompy = have_ompython()
    model = MODELICA / "MizanLoop.mo"

    print(f"\n  model file            {'found' if model.exists() else 'MISSING'}"
          f"  ({model.relative_to(ROOT)})")
    print(f"  omc compiler          {omc or 'NOT FOUND'}")
    print(f"  OMPython binding      {'installed' if ompy else 'NOT INSTALLED'}")

    if omc is None or not ompy:
        print("\n  OpenModelica is not available on this machine, so the")
        print("  Modelica leg cannot run here. That is a statement of fact,")
        print("  not a failure: nothing in the evidence package depends on")
        print("  it. The Python core is the reference and the MATLAB twin")
        print("  reproduces it to 1.4e-5 K.")
        print("\n  To enable it:")
        print("    1. install OpenModelica   https://openmodelica.org/download/")
        print("    2. install the Buildings library, in OMEdit:")
        print("         Tools -> Library Browser -> Manage Libraries -> Buildings")
        print("    3. pip install OMPython")
        print("\n  Then re-run this script. See modelica/README.md.")
        return 0                       # not an error, just not available

    # ---- OpenModelica is present: load, check, and simulate -------------
    from OMPython import OMCSessionZMQ            # noqa: E402

    om = OMCSessionZMQ()
    print("\n  loading the Modelica Standard Library ...")
    if not om.sendExpression("loadModel(Modelica)"):
        print("  FAILED to load the Modelica Standard Library")
        return 1
    print("  loading the LBNL Buildings library ...")
    if not om.sendExpression("loadModel(Buildings)"):
        print("  FAILED to load Buildings. Install it in OMEdit first:")
        print("    Tools -> Library Browser -> Manage Libraries -> Buildings")
        return 1
    print(f"  loading {model.name} ...")
    if not om.sendExpression(f'loadFile("{model.as_posix()}")'):
        print("  FAILED to load the model:")
        print(" ", om.sendExpression("getErrorString()"))
        return 1

    print("  checking the model ...")
    print(" ", om.sendExpression("checkModel(MizanLoop.CondenserLoop)"))

    print("\n  simulating one day ...")
    res = om.sendExpression(
        'simulate(MizanLoop.CondenserLoop, stopTime=86400, '
        'numberOfIntervals=1440, outputFormat="csv", '
        'fileNamePrefix="mizan_modelica")')
    print(" ", res.get("messages", "") if isinstance(res, dict) else res)

    out = {"omc": omc, "ran": True,
           "note": ("A third implementation makes no claim until it is scored "
                    "against the Python reference on results/matlab_cases.json, "
                    "to the same 0.010 K gate matlab/mizan_verify.m uses.")}
    (RESULTS / "modelica_run.json").write_text(json.dumps(out, indent=1))
    print(f"\n  written -> {(RESULTS / 'modelica_run.json').relative_to(ROOT)}")
    print("\n  NOT YET VALIDATED. Score it against the Python core before")
    print("  using any number it produces.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
