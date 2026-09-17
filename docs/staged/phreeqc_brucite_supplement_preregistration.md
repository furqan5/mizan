# SUPPLEMENTARY pre-registration, 17 September 2026: brucite temperature dependence against PHREEQC

**Separate from, and added after, `phreeqc_benchmark_preregistration.md`**,
whose grid had already been run and scored. Written and committed BEFORE
PHREEQC is run on brucite. Nothing in the main benchmark's criteria changes.

## 0. Why

Another branch staged a suspected defect (its staged **#57**, referenced here
rather than renumbered): `chemistry.ph_saturation_brucite` combines a
**hydroxide-form** log K (`Mg(OH)2 = Mg+2 + 2 OH-`, -11.18) with a
**proton-form** reaction enthalpy (-27.1 kcal, which belongs to
`Mg(OH)2 + 2 H+ = Mg+2 + 2 H2O`). The two forms share nothing at 25 °C that
would reveal it, so a 25 °C-only check cannot see it; it would make the
saturation pH fall far too fast with temperature.

## 1. What the database files say, read before any run

* `phreeqc.dat` (SHA-256 5745f0be…, the registered database) has **no
  Brucite phase**; `Mg(OH)2` appears only in its MEAN_GAMMAS block. So the
  main benchmark's database cannot test brucite.
* The same installer (`phreeqcx64.cab`, whose `phreeqc.dat` has the
  registered hash, so it is the same release) ships:
  * `wateq4f.dat`, SHA-256
    `8bec1e1ed3fc686444bd00ba386883b1ff6d4349f9346049a6bd359c981e9945`:
    `Brucite  Mg(OH)2 + 2 H+ = Mg+2 + 2 H2O  log_k 16.84  delta_h -27.1 kcal`
    -- the enthalpy the engine uses, written in proton form.
  * `llnl.dat`, SHA-256
    `b6e397c0294866dddc6aa0afb710a272051b5969716dffed5cbcc1aa6e03b744`:
    `Brucite  Mg(OH)2 + 2 H+ = Mg+2 + 2 H2O  log_k 16.298`, with an analytic
    temperature expression -- an independent temperature dependence.
* Arithmetic from those lines alone: converting proton form to hydroxide form
  adds 2 × (H2O = H+ + OH-, dH +13.362 kcal), so the hydroxide-form enthalpy
  is -27.1 + 26.724 = **-0.376 kcal**, not -27.1. The expected engine error in
  log K is then about 0.64 / 1.24 / 1.79 at 35 / 45 / 55 °C, i.e. saturation
  pH too low by about **0.32 / 0.62 / 0.90**. This is the a priori prediction.

## 2. Reference runs

* Same registered `phreeqc.exe` (SHA-256 51476790…). Databases extracted from
  the installer cab to a scratch directory outside the repository; their
  hashes above are checked before running. Neither file is committed.
* **Run B1 (gated)**, `wateq4f.dat`: the 128 points of the main grid
  (`grid.json`, unchanged). Each point is one SOLUTION with the same mol/kgw
  totals as the main benchmark, `C(4)` = the engine's HCO3 molality (the
  f = 1.00 convention), no charge keyword, and **pH adjusted by PHREEQC to
  Brucite saturation index 0**. Punched: pH, temperature, ionic strength,
  SI(Brucite), LK_PHASE(Brucite), LK_SPECIES(OH-), total and free Mg and
  log γ(Mg+2). wateq4f.dat uses the same WATEQ Debye-Hückel activity model
  family as phreeqc.dat.
* **Run B2 (constants only, reported)**, `llnl.dat`: one dilute solution per
  temperature (25, 35, 45, 55 °C) punching LK_PHASE(Brucite) and
  LK_SPECIES(OH-), for an independent hydroxide-form log K(T).
* Each run once. Setup or transport errors are execution errors, fixed,
  re-run and recorded as such, as in the main pre-registration.

## 3. Quantities and criterion

For each point, pH_sat(engine) = `ph_saturation_brucite(T, w.concentrate(C))`
and pH_sat(PHREEQC) from run B1.

The engine's brucite function does not speciate (total Mg, unspeciated ionic
strength), so its **absolute** pH_sat is expected to sit off PHREEQC's by a
composition-dependent amount from Mg pairing (MgSO4, MgCO3 at pH ~9-10).
That offset is reported, not gated. The suspected defect is in the
**temperature dependence**, and the offset largely cancels in it, so the gated
quantity is

    D(T) = [pH_sat,e(T) - pH_sat,e(25 C)] - [pH_sat,P(T) - pH_sat,P(25 C)]

for T = 35, 45, 55 °C at every composition and cycles count: 96 comparisons.

**Tolerance |D| ≤ 0.05 pH units**, justified without the run: between 25 and
55 °C the Davies vs Truesdell-Jones difference for a divalent ion changes by
well under 0.02 log units at I ≤ 0.2, the MgSO4 pair constant (dH 4.55 kcal)
moves free Mg by a few per cent, and the water-dissociation temperature
functions differ by under 0.04 log units -- each at most ~0.02 pH once
halved. A correct implementation should sit well inside 0.05; the predicted
defect is 6-18 times larger.

**PASS** iff at least 95 % of the 96 D values satisfy |D| ≤ 0.05.

**"PHREEQC confirms the suspected defect"** iff the criterion FAILS **and**
the median D at 45 °C is below -0.30 (engine saturation pH falling faster with
temperature than PHREEQC's, by the predicted order).

## 4. What follows from each outcome

* **Not confirmed:** the brucite code is not changed on this branch; the
  result is reported to the main session and the other branch.
* **Confirmed:** the smallest correction consistent with section 1 --
  keep log K(25 °C) = -11.18 and use the hydroxide-form enthalpy
  -27.1 + 2 × 13.362 kcal -- with a regression test. The SAME comparison is
  then re-scored against the STORED run B1 output (no new PHREEQC run), with
  the criterion unchanged, and reported as the post-fix result whichever way
  it goes. Every consumer of `ph_saturation_brucite` that writes a committed
  artefact the tests or audit read is re-run, and before/after reported.
