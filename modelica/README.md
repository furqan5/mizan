# Modelica models

Dynamics the steady-state engine cannot express, run on **OpenModelica
1.27.0** against **Modelica Standard Library 4.1.0**.

```bash
omc modelica/run_basin.mos     # -> results/basin_res.csv
omc modelica/run_silica.mos    # -> results/silica_res.csv
```

Both are held by agreement gates in `tests/test_basin_dynamics.py`: the
numerical integration is scored against a closed-form solution, and the
silica margin is scored against the analytic version in `chemistry.py`.
Where two implementations disagree, the disagreement is the finding.

## TowerBasin.mo — how slowly a tower changes its mind

Salt balance on the basin, exact, no correlation:

```
V dc/dt = (E + B + D) c_m - (B + D) c        tau = V / (B + D)
```

`tau` is the turnover on the **non-evaporative** losses only, because
evaporation removes water and leaves the salt behind. On a 50 m³ basin at
five cycles that is **13.2 h**, so 95 % settling takes **39.5 h**.

A Gulf diurnal half-cycle is 12 h, over which the basin completes about
**60 %** of a commanded step. That is an independent second reason the
diurnal cycle-floating idea was dead — the steady-state work had already
shown the prograde and retrograde limits cancel, and this shows the basin
could not follow even if they did not.

**Control-architecture consequence: fan speed is a fast variable and cycles
is a slow one. Cycles belong on a seasonal schedule, not a diurnal one.**

## TowerSilicaDynamics.mo — the limit moves faster than the state

Amorphous silica is **prograde**, so its solubility falls as the basin cools:

| basin | solubility |
|---|---|
| 18 °C | 101 mg/L |
| 26 °C | 120 mg/L |
| 34 °C | 140 mg/L |

A basin swinging 25–35 °C sees the **limit** move 117.2 → 142.6 mg/L, by
25.5 mg/L, every day. The **concentration** cannot follow: with blowdown
fixed at the value that holds saturation at the mean temperature, it moves
0.01 mg/L. A ratio of about **2,400 to one**.

Measured over a periodic steady state, on measured makeup silica of 18 mg/L
(NACE Paper 577, Riyadh Refinery):

| | |
|---|---|
| saturation ratio over a day | 0.908 → 1.105 |
| maximum excursion above the setpoint | **10.5 %** |
| hours per day supersaturated | **11.8 of 24** |

**A conductivity setpoint placed at the steady-state ceiling is supersaturated
for half of every day**, and no blowdown policy fixes it — following a
twelve-hour forcing needs a time constant well under twelve hours, and the
basin has thirteen.

So the steady ceiling must be discounted. `chemistry.diurnal_silica_margin()`
returns that discount, and agrees with this simulation to better than half a
percentage point. **The product is a margin, not a setpoint.**
