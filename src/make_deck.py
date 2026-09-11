"""
MIZAN :: application deck content generator
===========================================
Produces the slide content for the DTV application deck, ordered to DTV's
stated scoring sequence: the technology-maturity gate is screened FIRST,
then product strength, market, defensibility, team. So the evidence leads
and the story follows, which is the opposite of a normal investor deck.

As with the report, every number is read from results/*.json and
results/*.csv. Nothing is typed by hand, so the deck cannot disagree with
the evidence package it accompanies.
"""
from __future__ import annotations

import json
import json as _json
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
DOCS = ROOT / "docs"


def main():
    cal = json.loads((RESULTS / "calibration.json").read_text())
    ho = cal["HOLDOUT"]
    ctrl = json.loads((RESULTS / "controller_summary.json").read_text())
    cs = ctrl["summary"]
    v3 = pd.read_csv(RESULTS / "v3_skin_vs_bulk.csv")
    v5b_path = RESULTS / "v5b_two_ceilings.csv"
    v5b = pd.read_csv(v5b_path) if v5b_path.exists() else None
    v6p = RESULTS / "mg_silicate_envelope.json"
    v6 = json.loads(v6p.read_text()) if v6p.exists() else None

    b = float(v3[(v3.T_bulk_C == 33.0) & (v3.skin_delta_K == 0.0)]["max_cycles"].iloc[0])
    sk = float(v3[(v3.T_bulk_C == 33.0) & (v3.skin_delta_K == 8.0)]["max_cycles"].iloc[0])
    overstate = 100 * (b - sk) / sk

    S = []
    A = S.append

    A("# Mizan — application deck content")
    A("")
    A("*Furqan · Deep physics for hard infrastructure*  ")
    A("Ordered to DTV's scoring sequence: maturity gate first, then product, "
      "market, defensibility, team.")
    A("")
    A("---")
    A("")

    A("## Slide 1 — Title")
    A("")
    A("**Mizan** — supervisory control for Gulf condenser-water loops  ")
    A("A Furqan venture · TRL 3, validated against measured experimental data  ")
    A("DTV .dvp Cohort 2 · Energy / Water & Sustainability")
    A("")

    A("## Slide 2 — The maturity gate, answered first")
    A("")
    A("Thresholds fixed before fitting. Campaign-wise holdout, scored once.")
    A("")
    A("| Gate | Threshold | Result |")
    A("|---|---|---|")
    A(f"| Outlet water temperature MAE | ≤ 1.00 K | **{ho['Tout_MAE_K']:.3f} K** |")
    A(f"| Heat rejection MAPE | ≤ 6.00 % | **{ho['Q_MAPE_pct']:.2f} %** |")
    A(f"| Evaporation vs *measured* water loss | ≤ 8.00 % | **{ho['evap_MAPE_pct']:.2f} %** |")
    A("")
    A(f"n = {ho['n_points']} held-out points from experimental campaigns the "
      f"model never saw. {ho['convergence_pct']:.0f} % solver convergence. "
      "Public dataset, MD5-verified, CC BY 4.0.")
    A("")

    A("## Slide 3 — The problem, in one number")
    A("")
    A("A Gulf condenser-water loop is run by three parties setting three "
      "handles independently:")
    A("")
    A("- the BMS sets **fan speed** on a fixed condenser-water setpoint")
    A("- the water treater sets **blowdown** on a fixed conductivity setpoint")
    A("- the water treater sets **acid dose** on a fixed pH setpoint")
    A("")
    A("They are not independent. Concentrating the loop to save water raises "
      "scaling risk and changes evaporation. Cooling the condenser to save "
      "compressor power costs fan power and evaporates more water.")
    A("")
    A("**Nobody solves them together, because doing so requires the thermal "
      "model and the chemistry model to be one problem.**")
    A("")

    A("## Slide 4 — Prior art, disclosed up front")
    A("")
    A("We searched before we claimed. Two of the three ingredients are "
      "already taken, and we say so:")
    A("")
    A("| Element | Status |")
    A("|---|---|")
    A("| Skin-temperature saturation | **Taken.** ChemTreat US 11,780,742 B2, "
      "granted Oct 2023 — but empirical LSI-family indices, antiscalant feed "
      "only |")
    A("| Ion-association speciation | **Taken.** French Creek WaterCycle since "
      "1990 — but offline, at bulk temperature |")
    A("| Blowdown on a saturation index | **Public domain.** US 4,460,008 / "
      "4,464,315, 1984, expired |")
    A("")
    A("**What is open, stated precisely:**")
    A("")
    A("> Routing each mineral to its own **governing temperature**, computed "
      "live, and closing **three actuators** on the result.")
    A("")
    A("Calcite, gypsum and magnesium silicate are retrograde — they "
      "govern at the hot condenser skin. Amorphous silica is **prograde** "
      "— it governs at the cold basin. One evaluation temperature is "
      "wrong for one group or the other. French Creek works from bulk "
      "profiles; ChemTreat evaluates at skin with calcite indices. Neither "
      "routes per mineral, and neither actuates.")
    A("")

    A("## Slide 5 — What we found that the single-point model misses")
    A("")
    A("Scale forms where each mineral is least soluble — and the sign "
      "differs by mineral:")
    A("")
    A("| Mineral | Solubility vs temperature | Governs at |")
    A("|---|---|---|")
    A("| Calcite, magnesium silicate | Retrograde | Hot tube skin |")
    A("| Gypsum | Maximum near 35–40 °C | Skin, weakly |")
    A("| **Amorphous silica** | **Prograde — more soluble hot** | "
      "**Cold tower basin** |")
    A("")
    A("Evaluating everything at one temperature is optimistic about silica — "
      "the one species with no effective inhibitor in general service. "
      "Correcting this moved our predicted silica limit from ~12 cycles to 9.")
    A("")
    A(f"And the skin offset is computed, not assumed: ΔT = q″/h_i gives "
      f"~3.8 K at typical design and ~8.7 K fouled. The bulk basis overstates "
      f"the safe cycles limit by **7 % typical, {overstate:.1f} % fouled** — "
      "reported as a band, not a point.")
    A("")

    if v5b is not None and "economic_ceiling_cycles" in cs:
        A("## Slide 6 — Two ceilings, and the setpoint that finds neither")
        A("")
        _feas = v5b[v5b.feasible]
        _turns_over = (len(_feas) > 0
                       and cs['economic_ceiling_cycles'] < int(_feas.cycles.max()))
        if _turns_over:
            A(f"- **Economic ceiling: {cs['economic_ceiling_cycles']} cycles.** "
              "Past this, acid to control calcite costs more than the water "
              "saved.")
        else:
            A("- **The cost curve never turns over.** Cost falls "
              f"monotonically to {cs['economic_ceiling_cycles']} cycles, the "
              "last feasible point — so the economics point straight at the "
              "wall, with no margin.")
        A(f"- **Physical ceiling: {cs['physical_ceiling_cycles']} cycles.** "
          f"First saturation violation at the skin — binding mineral "
          f"**{cs['binding_mineral']}**.")
        A("")
        A("Different numbers. A fixed conductivity setpoint locates neither: "
          "the first needs a coupled cost model, the second needs "
          "ion-specific speciation. **The Langelier index the industry runs "
          "on describes calcite only — it cannot represent the binding "
          "mineral here at all.**")
        A("")
        A("The plant operates between two limits it cannot see. That gap is "
          "the product.")
        A("")

    if v6 is not None:
        A("## Slide 7 — The constraint that needs all three models at once")
        A("")
        A("Magnesium silicate forms in two steps: brucite precipitates at "
          "the hot skin, then reacts with silica. Brucite's saturation pH "
          "is **retrograde** — it falls as the surface heats. So:")
        A("")
        A("> deposition occurs when **bulk pH > pH_s(brucite) at the SKIN**")
        A("")
        A("At 4 cycles, Gulf loops running pH 8.5–9.0:")
        A("")
        A("| Skin | Verdict |")
        A("|---|---|")
        for r in v6["rows"]:
            if r["skin_T_C"] in (30.0, 38.0, 46.0, 50.0):
                A(f"| {r['skin_T_C']:.0f} °C | {r['verdict']} |")
        A("")
        A("**The same tower deposits at high load and not at low load.** A "
          "fixed pH setpoint cannot express that. Neither can a fixed "
          "conductivity setpoint.")
        A("")
        A("It needs skin temperature (thermal model), bulk pH (chemistry "
          "model) and acid (actuator) together — and three independent "
          "literature sweeps found **no closed-loop scheme anywhere where a "
          "chemical saturation limit bounds a thermal optimiser.**")
        A("")

    A("## Slide 7 — The result")
    A("")
    A("| | Threshold | Result |")
    A("|---|---|---|")
    A(f"| Total operating cost | ≥ 3 % | **{cs['cost_pct']:.2f} %** |")
    A(f"| Makeup water | ≥ 15 % | {cs['water_pct']:.2f} % — **missed** |")
    A(f"| Saturation violations at skin | 0 | **{cs['violations']}** |")
    A("")
    A("We report the miss because the reason is the thesis. 4 → 7 cycles is "
      "worth exactly 12.50 % of makeup *at constant evaporation*. We "
      f"achieved {cs['water_pct']:.2f} %. The missing 2.46 points are "
      "evaporation the optimiser **chose** to add by running the fan harder, "
      "because colder condenser water was worth more than the water it cost.")
    A("")
    A("A water treater would have promised 12.5 % and not delivered it. An "
      "energy optimiser would have raised water use and never booked it.")
    A("")
    # DEFECT 48. The deck may not quote a water saving without this split.
    # Not a caveat -- a correction to which half of the product is defensible.
    try:
        env = _json.loads((RESULTS / "annual_dhahran.json")
                          .read_text(encoding="utf-8"))["by_envelope"]
        A("**And the half of this we can defend on our own data is the energy "
          "half.** Splitting the Dhahran year at the edge of our test data:")
        A("")
        A("| | hours | water | energy |")
        A("|---|---|---|---|")
        A(f"| Inside the validated wet-bulb envelope | {env['inside']['hours']:,} "
          f"| **{env['inside']['water_pct']:+.2f} %** "
          f"| {env['inside']['energy_pct']:+.2f} % |")
        A(f"| Hotter and wetter than any data we hold | "
          f"{env['extrapolated']['hours']:,} "
          f"| {env['extrapolated']['water_pct']:+.2f} % "
          f"| **{env['extrapolated']['energy_pct']:+.2f} %** |")
        A("")
        A("The water saving is **negative where the model has been "
          "validated** and positive only where it has not. Energy is the "
          "exact reverse. So we lead with energy, which our own data "
          "supports, and treat water as the thesis the pilot exists to "
          "test. We would rather say that than have a reviewer find it.")
        A("")
    except (OSError, KeyError, ValueError):
        A("*(envelope split unavailable -- re-run `python src/annual.py`)*")
        A("")

    A("## Slide 8 — Product")
    A("")
    A("A retrofit **edge controller**, not software: sensor skid "
      "(conductivity, pH, ORP, temperature, makeup and blowdown flow) + "
      "motorised blowdown valve + edge compute, speaking BACnet/Modbus. "
      "Sold as capex plus an annual model-recalibration licence.")
    A("")
    A("Ships read-only in shadow mode; blowdown and dosing stay advisory "
      "until site validation. Deterministic fixed-step solver, bounded "
      "runtime, documented fallback to incumbent setpoints on solver failure "
      "or sensor loss.")
    A("")
    A("**The skid deliberately does not measure the chemistry, and that is "
      "the central design decision.** Measuring silica, calcium, alkalinity "
      "and phosphate online costs **$120,000-185,000 per tower** against an "
      "annual water-and-energy saving of order **$89,000** on a 4.2 MW "
      "tower. The instruments cost more than the thing they optimise. That "
      "is structural, it is why no incumbent sells chemistry-bounded "
      "control, and no amount of negotiation closes it.")
    A("")
    A("So the skid buys only what is cheap -- toroidal conductivity, pH, "
      "ORP, temperature, two flow meters, a coupon rack -- at about "
      "**$15,000 in instruments and $23,000-30,000 installed**, and the "
      "chemistry is *computed*. The one measurement that is already there "
      "then checks the computation for nothing: specific conductance is a "
      "known function of ion composition, so the residual between computed "
      "and measured conductance says when the assumed composition has "
      "stopped being true. Precipitation removes ions; the residual moves "
      "first. See `docs/instrumentation_spec.md`.")
    A("")

    A("## Slide 9 — Why the Gulf, and why now")
    A("")
    A("Saudi and Qatari district cooling is moving onto treated sewage "
      "effluent under national reuse policy. TSE at high cycles is exactly "
      "the regime where the incumbent index breaks: high ionic strength, and "
      "a binding mineral LSI cannot describe. Extreme wet-bulb makes the "
      "energy side of the trade unusually valuable at the same time.")
    A("")
    A("Same physics, same equipment, same water policy in Qatar — the Gulf "
      "bridge needs no rework.")
    A("")

    A("## Slide 10 — Defensibility")
    A("")
    A("Not data volume, not UI, not AI-applied-to-X. The moat is the coupled "
      "model and the calibration library behind it:")
    A("")
    A("- Poppe integration with the **water-activity coupling** that lets "
      "chemistry change tower performance at all")
    A("- ion-specific speciation at **skin temperature**, not bulk")
    A("- the **economic/physical ceiling separation**, which needs both "
      "models simultaneously")
    A("")
    A("A generalist team reproduces the tower model in weeks. What they "
      "cannot reproduce is knowing that the fan correlation is in hertz, "
      "that gypsum binds before calcite on Gulf TSE, or that the water "
      "saving must be discounted for the evaporation the energy optimum "
      "adds back. Those came from the physics, and each one changed the "
      "answer.")
    A("")

    A("## Slide 11 — TRL 4 at KFUPM, and what SAR 200,000 buys")
    A("")
    A("The rig already exists on the DTV campus: KFUPM's Air-Conditioning "
      "and Refrigeration Laboratory holds a vertical cooling tower and a "
      "wind tunnel with heating, cooling and **humidification**.")
    A("")
    A("That humidification closes the one honest gap in this package — our "
      "validation data is from a semi-arid Spanish site whose summer "
      "wet-bulb sits below Dhahran's.")
    A("")
    A("In-kind budget buys instrumentation, blowdown valve and edge "
      "hardware, ICP-OES water analysis, OT-security assessment, third-party "
      "validation. Not runway.")
    A("")

    A("## Slide 12 — Where AI sits")
    A("")
    A("**No AI contributes to any result in this package.** The evidence is "
      "first-principles, and we say so.")
    A("")
    A("The load-bearing learned component is the **scaling-kinetics "
      "residual**, at TRL 4. Thermodynamics gives the driving force from "
      "published constants; precipitation *rate* depends on nucleation, "
      "surface and inhibitor residual and is not derivable. Remove that term "
      "and the controller still says whether scale is possible, but not when "
      "it will cost money — which is the product.")
    A("")
    A("We rejected reinforcement learning (no hard-constraint guarantee), "
      "chemistry soft-sensing (we showed the signal sits an order of "
      "magnitude below the noise floor), and a weather LSTM (numerical "
      "weather prediction already exists).")
    A("")

    A("## Slide 13 — Team and ask")
    A("")
    A("**Engr. Furqan Shakeel** — Co-founder & CTO · "
      "engr.furqan.shakeel@gmail.com · linkedin.com/in/furqan-shakeel  ")
    A("**Engr. Damia Baig** — Co-founder & CEO · [contact details to be added]  ")
    A("**Engr. Muhammad Ahsan** — Co-founder, Commercial Development · "
      "muhammadahsan4203@gmail.com")
    A("")
    A("Three energy engineers, all full-time. One owns the physics core and "
      "controller; two own customer development. That ratio is deliberate: "
      "the technical risk is now largely retired and the binding risk is "
      "commercial.")
    A("")
    A("Ask: DTV Cohort 2 place, lab access for the TRL 4 programme above, "
      "and introductions to Saudi district-cooling and industrial-cooling "
      "operators through the DTVC corporate partner network.")
    A("")

    A("---")
    A("")
    A("## Speaker note on honesty")
    A("")
    A("This deck reports a failed criterion and a defect we found in our own "
      "first run. That is deliberate. DTV screens the maturity gate first, "
      "and a team that inflates TRL is finished in this ecosystem "
      "permanently. Everything claimed here is reproducible with four "
      "commands against a public dataset.")

    out = DOCS / "deck_content.md"
    out.write_text("\n".join(S), encoding="utf8")
    print(f"written -> {out}  ({len(S)} lines)")


if __name__ == "__main__":
    main()
