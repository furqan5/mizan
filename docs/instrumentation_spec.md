# Instrumentation, hardware, and what Mizan actually is

**12 September 2026.** Written to answer three questions in order: is this software or hardware; if hardware, what exactly; and what does it cost against what it saves.

Every price below came off a manufacturer datasheet or a distributor page that publishes list prices. Anything quote-only is marked **`[U]`** and no number was guessed in its place.

---

## 1. The answer, first

**Mizan is software sold with a small, deliberately cheap instrument package.** Not a SaaS, not an analyser skid.

That is not a positioning preference. It is forced by an arithmetic result:

| | per tower |
|---|---|
| Annual water + discharge saving, 4.2 MW tower at Saudi tariffs | **$89,000** |
| Instrument package that would *measure* the chemistry the model computes | **$120,000 – $185,000** |
| Recurring consumables and service on that package | **$20,000 – $30,000 / yr** |

**The instruments cost more than the thing they optimise.** No negotiation closes a gap of that shape — it is the structure of the market, and it is the reason no incumbent sells chemistry-bounded control. Anyone who proposes to measure their way to this product has not costed it.

So the deliverable is the **inference engine**, and the skid exists to feed it the two or three signals that are cheap.

> **Tagline:** **Mizan — the limit, computed.**
>
> Runners-up, kept because each says something the winner does not: *"Know the ceiling before you hit it."* · *"Every tower has a limit. Most are guessing where."* · *"The balance between energy and water."* (the existing brand line, which stays as the parent descriptor)

---

## 2. Can you design the enclosure in SOLIDWORKS?

**Yes — and for this product, SOLIDWORKS is more tool than the job needs.**

What actually has to be designed is small: a wall-mounted enclosure, a sample panel with isolation valves and a flow cell, cable glands, a sunshade, and a DIN-rail backplate. That is sheet metal, a few brackets, and a hole pattern.

| Tool | Use it for | Cost |
|---|---|---|
| **SOLIDWORKS** | If you already have a licence or a university seat. Sheet-metal and weldment tools are genuinely good, and Gulf fabricators accept its files without asking | Commercial licence, expensive |
| **FreeCAD** *(recommended)* | Free, scriptable in Python — which matters here, because the skid is *parametric*: two flow sizes, three sensor counts, a Gulf variant with a sunshade. Exports STEP and STL. Already the plan of record in `HANDOFF.md` for the CFD path | Free |
| **Onshape** | Free for public documents. Browser-based, good for sharing with a fabricator | Free (public) |
| **KiCad** | The edge board, if you ever build one rather than buying a Moxa | Free |

**The recommendation is FreeCAD**, for one specific reason beyond cost: the same FreeCAD model can be driven from the Python that already exists in this repository, so the enclosure and the BOM stay in sync with the sensor list instead of drifting apart. And `HANDOFF.md` already wants FreeCAD for the CFD path — parametric condenser-tube geometry → STEP → OpenFOAM — which would let the **skin temperature rise be derived rather than assumed** for a specific site. That is now a much smaller job than it was, because defect 44 already derived it analytically; CFD would be confirmation, not foundation.

**What to model, in order:**

1. IP66 enclosure, 600 × 400 × 200 mm, with a DIN-rail backplate and a **separate sunshade** standing 50 mm off the door — the shade is the single highest-value part, see §5.
2. Sample panel: isolation valves, Y-strainer, flow cell for conductivity + pH/ORP, sample cock, drain.
3. Cable-gland pattern and segregation (4–20 mA away from mains).
4. Mounting brackets for tower handrail and for plant-room wall.

**Do not design:** the sensors, the transmitter, the edge computer, or the valve. All bought. Designing any of them is a year you do not have before Sanabil closes.

---

## 3. The skid that ships — minimum viable, inference-first

| Item | Part | Verified spec | USD |
|---|---|---|---|
| Conductivity | **E+H Indumax CLS50D** toroidal | 2 µS/cm – 2000 mS/cm, ±(5 µS/cm + 0.5 % MV), IP68, integral Pt1000 | 1,889 |
| — assembly + cable | Dipfit CLA111 + CYK10 | to 100 m | 1,555 |
| pH **and** ORP, one body | **E+H Memosens CPS16E** | saves a channel over CPS11E + CPS12E | 860 |
| — cable | CYK10 | | 317 |
| Temperature | **E+H Easytemp TMR31** | Pt100 DIN class A, 4-wire, 316 | 143 |
| Transmitter | **E+H Liquiline CM444** | 4-channel Memosens, Modbus RTU/TCP, web server | 3,828 |
| Makeup flow | **GF Signet 2551** insertion magmeter | 0.05–10 m/s, ±1 % of reading + 0.01 m/s | 2,383 |
| Blowdown flow | GF Signet 2551 | | 1,515 |
| Edge compute | **Moxa UC-8210-T-LX-S** | **−40 … 70 °C**, IP30, Modbus RTU + TCP, 10 W, DIN rail | 749 |
| BACnet MS/TP gateway | **MSA FieldServer QuickServer** | Modbus RTU ↔ BACnet MS/TP, −20 … 70 °C | ~750 |
| Corrosion coupons | 4-station side-stream rack, **ASTM D2688** | weight loss **and pitting** | ~1,000 |
| | | **instruments** | **≈ 14,990** |
| Enclosure, sample panel, valves, conduit, install, commissioning | | Gulf rates `[U]` | +8,000 – 15,000 |
| | | **installed, per tower** | **≈ $23,000 – $30,000** |

Against the `controller_break_even_capex()` bound of **$267,000 for a three-year payback**, that clears with an order of magnitude to spare — which is the whole argument for the inference-first architecture.

### Two choices in that table that are not obvious

**Toroidal conductivity, not contacting — and the reason is a failure mode, not accuracy.** A contacting cell fouling in scaling water does not read noisy, it **reads low**: scale on the electrodes acts as a series insulator, the cell under-reports, and a bleed controller reads that as "not yet at setpoint" and *stops blowing down*. The failure drives the system deeper into the regime that caused it. Toroidal cells couple inductively through a bore and do not polarise. The upgrade costs $400–$1,400 per point. **Take it** — and note the incumbent Walchem panel ships a graphite contacting probe as standard, which is the installed base being replaced.

**Memosens is hot-swappable, which is an operations decision not a spec one.** The probe is calibrated in a bucket in an air-conditioned room and carried out to the deck. Nobody calibrates a glass electrode on a Gulf tower deck in July, and a procedure that requires it will not happen.

### The cheaper variant, and when to allow it

Swapping the whole E+H chain for a **Walchem Intuition-6 panel at $1,519** (NEMA 4X, Modbus/TCP + BACnet, probe and flow switch included) plus the Moxa takes instruments to ~$5,000 and installed to **$10,000–14,000**. It costs the toroidal cell, and with it trustworthy conductivity in scaling water — which is the input the entire cycles calculation rests on.

**Never on a reference site.** Acceptable on price-sensitive retrofits where the sale is scheduling, not chemistry.

---

## 4. Online silica — the honest version

Silica sets the cycles ceiling on these waters. The obvious move is to measure it. Three things make that the wrong move:

**Range.** Every mainstream online silica analyser serves the ppb boiler market. Hach 5500sc tops out at 5 mg/L; E+H CA80SI at 5 mg/L; Swan at 1 mg/L. A loop at 4–6 cycles on Gulf TSE runs **100–150 mg/L**. Only two instruments reach it: **Hach EZ1035sc** (1–100 mg/L with internal dilution) `[U]` and **Waltron 3141** (0–150 ppm), the only one with a published price — **$19,450–$25,450**, reagents **$3,866/yr**, monthly reagent changes, quarterly tubing.

**Matrix.** The E+H unit's own cross-sensitivity table caps interference-free operation at ≤2,000 mg/L NaCl and ~445 mg/L hardness. Gulf cooling water at 5 cycles exceeds both. And phosphate interferes: the citric-acid correction is specified to PO₄ ≤ 10 mg/L, which is exactly where a phosphate programme runs.

**And the one that decides it — the method goes blind at the condition it exists to detect.** Molybdate-blue measures **reactive (monomeric) silica only**. Once amorphous-silica solubility is crossed and polymerisation begins, the reading **falls** while the fouling risk **rises**. An instrument that goes quiet at the wall is not a safe single input for a ceiling-setting controller.

That last fact is not a reason to give up. It is the product:

> **Do not claim "we measure silica online."** Claim **"we predict silica and detect when the prediction breaks."**
>
> Run measured reactive silica — or, with no analyser at all, the conductivity residual of §5 — against mass-balance silica from a conservative tracer. **Divergence between prediction and measurement is a direct polymerisation alarm.** No commercial cooling-water controller found in this search does that.

Buy one Waltron 3141 for **one pilot tower** to calibrate the inference, and ship none.

---

## 5. What closes the "never measured" gap for nothing

This is implemented, in [`src/conductivity.py`](../src/conductivity.py), and it is the most valuable finding in this document.

Specific conductance is a **known function** of ion composition — McCleskey, Nordstrom, Ryan & Ball (2012), *Geochim. Cosmochim. Acta* 77:369–382, validated over ionic strength 0.0004–0.7 mol/kg, 0–95 °C and **30–70,000 µS/cm**, which contains our entire operating range. USGS publishes PHREEQCI input files implementing it and uses the **specific conductance imbalance** alongside charge balance as a routine quality check:

```
SCI % = 100 × (SC_calculated − SC_measured) / SC_measured
```

We compute the composition. A $1,889 sensor we were buying anyway measures the conductance. **The residual is a continuous, free check on the assumption every other number in this package rests on.**

It does **not** measure ions — one conductivity and one pH are two equations against eight-plus unknowns, and the inverse is underdetermined in principle. What it gives is the **direction**:

| residual | meaning |
|---|---|
| SCI ≈ 0 | the assumed composition still holds |
| **SCI > 0** — measured conductance below prediction | **ions have left solution: precipitation** |
| SCI < 0 | more ionic material than makeup × cycles accounts for: an unmeasured ion, a process leak, or cycles underestimated |

**The controller's job becomes: hold the residual near zero.** That is cheap, physically honest, degrades gracefully, and survives the "you cannot invert one equation" objection — because it never claims to.

**Prior art to read before writing claims:** US 6,280,635, US 6,315,909, US 7,105,095, US 8,361,384 (cycles control from a conservative tracer), and especially **US 8,696,912**, *"Raw water hardness determination in a water treatment system via the conductivity of soft or blended water"* — a granted patent on inferring hardness from conductivity.

**The structural limit, stated so it is not discovered later.** Published EC-inversion methods (Benettin & van Breukelen 2017; Zhang et al. 2026) close the underdetermined system by importing a makeup ion ratio from periodic lab analysis and assuming it stable between samples. **That assumption is exactly what our application breaks**, because Ca, alkalinity and silica are non-conservative — they are being removed by precipitation, which is the thing we are trying to detect. *You cannot infer the sink from a model that assumes no sink.* Hence: predict conservatively, and treat the residual as the signal.

**Monthly lab analysis per tower is non-negotiable.** It is the anchor for the whole inference chain and the cheapest line item in the product.

---

## 6. Corrosion monitoring

| Technique | What it gives | Cost |
|---|---|---|
| **Coupons — ASTM D2688**, 4-station side-stream rack | Ground truth: weight-loss rate **and pitting**. The reportable number | ~$1,000 |
| **LPR** — Cosasco 9020 transmitter + 7012 probe | General corrosion rate in hours instead of 90 days. Good as a fast diagnostic | `[U]` |

**Ship both; report coupons.** LPR cannot see pitting, under-deposit corrosion, or MIC — which are the mechanisms that actually perforate cooling-water piping. Do not let an LPR reading contradict a coupon and win.

Acceptance criteria are already in [`src/corrosion.py`](../src/corrosion.py) as UFC 3-230-13 Table 5-9 — mild steel Hx tubing <0.2 mpy excellent / >1.5 unacceptable, copper <0.1 / >0.5, stainless <0.1 acceptable — with the standard's own rider: **"any pitting is unacceptable."** A rate inside band with pits is a failure.

This matters more than it did last week. Defect 46 found that on the measured Riyadh water a **316 stainless** condenser reaches its chloride pitting limit at **1.85 cycles**, against a 4.52-cycle scaling ceiling. If a pilot site has stainless tubing, the coupon rack is not optional and the cycles recommendation must be re-derived.

---

## 7. Gulf deployment reality

**Nothing in §3 is an outdoor device.** Moxa is IP30, WAGO IP20, all DIN-rail. Every wet-chemistry analyser is rated 5–45 °C ambient — below a Gulf deck in July.

The correct arrangement is **compute in the plant room, sensors on the deck**, with RS-485 and 4–20 mA between them; Memosens cable runs to 100 m. Where an enclosure must sit outside, it needs shade *and* active cooling — an unshaded box in Gulf sun exceeds 70 °C internally, and you lose the electronics, not the sensors.

**Supply chain, and it is a real risk in both target geographies.** Wet-chemistry reagents are hazmat for air freight and degrade in a 45 °C sea container to Karachi; Hach silica reagent shelf life is 720 days *unopened*. Every analyser specified creates a recurring cross-border consumables dependency that a software product does not have. That argues for inference-first in Pakistan independently of price.

**And price the Saudi variant separately.** Under RCER, where acid dosing is prohibited, the acid loop and much of the pH instrumentation's *control* value disappear, and the cycles ceiling carries the entire optimisation. In that regime silica and alkalinity get **more** important relative to pH — the wrong direction for the cost argument. One skid does not fit both markets.

---

## 8. What this document does not establish

- Every analyser price in §4 and §6 except the Waltron 3141 is **quote-only**. Get three quotes before any of it reaches a financial model.
- Installation labour at Gulf rates is an **estimate**, not a quotation.
- Drift-per-month for pH and ORP **is not published by any vendor consulted**. E+H's CPS11E technical information gives two performance rows and no drift figure. In-service accuracy is dominated by junction fouling, not by a datasheet number, so the honest parameter is calibration interval — monthly to quarterly, electrode life 1–3 years. Treat any "±0.01 pH" as a bench number with no field meaning.
- **Sulfate has no good online instrument** at cooling-water concentrations. The gypsum index depends on it, and it must come from makeup analysis × cycles with all the error that implies. Unresolved by anything on this list.
