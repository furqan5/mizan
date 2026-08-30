# The OpenModelica leg — what it is for and how to run it

**FURQAN** · *The criterion for energy.* · **MIZAN** · *The balance between energy and water.*

## Why a third implementation

There are already two: the Python core, which is the reference and the thing validated against experiment, and the MATLAB twin, which reproduces it to 1.4e-5 K and carries the Simulink demonstration. A third needs a reason.

The reason is specific. **The LBNL Modelica Buildings library ships the same CoolTools chiller performance data the Python core reads its coefficients from.** `Buildings.Fluid.Chillers.Data.ElectricEIR` contains named records of the form `ElectricEIRChiller_York_YT_1055kW_5_96COP_Vanes` — the same library, the same machines, the same numbers. A Modelica plant model and the Python reference would therefore be driven by **one** chiller dataset rather than two that have to be kept in step by hand.

That was the deciding argument over Simscape Fluids, which would have meant two.

## Status: not yet runnable here

Neither OpenModelica nor the Buildings library is installed on this machine, so `MizanLoop.mo` is **written but unrun**. It is included because it is the destination, not because it is finished. Nothing in the evidence package depends on it.

## Setup

```bash
# 1. OpenModelica (Windows installer, includes OMEdit and the omc compiler)
#    https://openmodelica.org/download/download-windows/

# 2. The Buildings library, inside OMEdit:
#      Tools -> Library Browser -> Manage Libraries -> Install "Buildings"
#    or clone it directly:
#      git clone https://github.com/lbl-srg/modelica-buildings

# 3. The Python binding
pip install OMPython

# 4. The MATLAB binding (preferred -- see below)
#    https://github.com/OpenModelica/OMMatlab
```

## Two coupling routes

**(a) OMMatlab — preferred.** MATLAB drives the OpenModelica model directly: build, set parameters, simulate, read results back as arrays. No FMU, no import block, nothing further to license. The supervisory controller stays in MATLAB and Simulink where the licensed toolboxes are; the plant lives in Modelica.

**(b) FMU — fallback.** Export FMI 2.0 Co-Simulation (`buildModelFMU`, or *File → Export → FMU* in OMEdit) and import into Simulink. Two cautions, both documented upstream:

1. Base Simulink on this machine has **no FMU Import block** — checked, it is not in `simulink/User-Defined Functions`. This route needs the free **FMI Kit for Simulink** (Modelon/Dassault).
2. OpenModelica-generated FMUs are known to fail to load in Simulink unless the OpenModelica `bin` directory is on the Windows `PATH` **before MATLAB starts**, because Simulink loads the FMU's main DLL in a way that does not find the auxiliary DLLs inside the archive.

## Running it

```bash
python ../src/run_modelica.py            # checks for OpenModelica, then runs
```

`run_modelica.py` detects whether OpenModelica is present and says plainly what is missing rather than failing obscurely.

## What it must be checked against

The same discipline as everything else here: a third implementation is worth nothing until it is shown to agree with the reference. The gate is the same one `matlab/mizan_verify.m` uses — outlet water temperature to 0.010 K against the Python core over the same case file, `results/matlab_cases.json`. Until that gate has been scored, this model makes no claim.
