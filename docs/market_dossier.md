# Mizan — Market & Commercial Dossier

**Venture:** Furqan · **Product:** Mizan — retrofit edge controller for cooling-tower / condenser-water loops
**Prepared for:** Dhahran Techno Valley `.dvp` Cohort 2 application (deadline 31 Aug 2026)
**Compiled:** 29 August 2026

---

## How to read this document

Every quantitative claim carries one of three tags:

| Tag | Meaning |
|---|---|
| **[C]** | **Cited.** A working URL in the Sources section supports the figure. Use in submission. |
| **[A]** | **Analyst estimate / derived.** Arithmetic on a [C] figure, or a stated assumption. Label it as an estimate if quoted. |
| **[UNVERIFIED]** | Could not be confirmed. Quarantined in the final section. **Do not use in submission.** |

**Currency pegs used for all conversions [A]:** SAR 3.75 = USD 1.00; QAR 3.64 = USD 1.00 (both are long-standing official pegs).

**Two access limitations affected this research and are disclosed for honesty:**
1. `sera.gov.sa` and `se.com.sa` (the primary Saudi electricity tariff publishers) were **network-unreachable** throughout this research. Saudi electricity tariff figures below are therefore drawn from (a) SEC's own audited financial statements, which are primary and verifiable, and (b) secondary reporting. The gap is flagged explicitly.
2. Several trade sites returned HTTP 403 to automated fetching. Where a figure survives only in a search-engine extract of such a page, it is tagged and the limitation named.

---

# PRIORITY 1 — Tariffs and input prices

## 1.1 Saudi Arabia — electricity

### Published consumption tariff, non-residential

| Category | Bracket | Rate (halalas/kWh) | SAR/kWh | USD/kWh | Tag |
|---|---|---|---|---|---|
| Commercial | 1–6,000 kWh/month | 22 | 0.22 | 0.0587 | [C] secondary |
| Commercial | > 6,000 kWh/month | 32 | 0.32 | 0.0853 | [C] secondary |
| Residential (reference) | 1–6,000 kWh/month | 18 | 0.18 | 0.0480 | [C] secondary |
| Residential (reference) | > 6,000 kWh/month | 30 | 0.30 | 0.0800 | [C] secondary |
| **Surcharge — non-eligible industrial / commercial / agricultural** | all | **+2** | +0.02 | +0.0053 | **[C] primary (SEC financials)** |

**USD conversions are [A]** (arithmetic on the halala figure at the 3.75 peg).

### The surcharge and the Intensive Consumption Tariff — primary-source confirmed

This is the one Saudi electricity figure supported by an **audited primary document** — SEC's Interim Condensed Consolidated Financial Statements for the nine months ended 30 September 2025. Verbatim:

> "On 29 Shawwal 1446, corresponding to April 27, 2025, the Company announced that, based on the eligibility results for the Intensive Electricity Consumption Tariff, an additional charge of 2 halalas per kilowatt-hour (kWh) will be added to the electricity tariff for non-eligible customers in the industrial, commercial, and agricultural sectors. The new tariff will be applied starting from May 28, 2025…" **[C]**

The same note establishes the regulatory architecture, which matters for how a Dhahran reviewer will read tariff risk:

- Council of Ministers Resolution No. 111 (21 Sep 2021) approved a **heavy/intensive consumption tariff** for qualifying industrial, commercial and agricultural establishments; Decision No. 361 (20 Dec 2022) applied it from **1 January 2023**. **[C]**
- Eligibility is **application-based** — the consumer petitions for the tariff, and a cross-ministry committee chaired by the Ministry of Energy determines qualifying sectors. **[C]**
- Historic ceiling: highest band set at 32 halala/kWh in Jan 2016; reduced to 30 halala for some categories from 1 Jan 2018. **[C]**
- SEC is a **regulated-revenue** utility: required revenue is set on an asset-base model with a regulatory WACC, revised to **6.65% for 2024–2026**. **[C]**

**Eligibility criteria for the intensive tariff [C] secondary:** First cluster — facilities where electricity cost is ≥20% of operational cost; second cluster — 10%–19.9%. *Reported by SERA via secondary summary; the SERA page itself was unreachable.*

### Independent cross-check (recommended headline figure)

| Metric | Value | Date | Tag |
|---|---|---|---|
| Saudi **business** electricity price, all-in | **SAR 0.277/kWh = USD 0.074/kWh** | December 2025 | **[C]** |
| Saudi household electricity price, all-in | SAR 0.200/kWh = USD 0.053/kWh | December 2025 | [C] |

GlobalPetrolPrices states these retail prices "include the cost of power, distribution and transmission, and all taxes and fees" **[C]**. This is internally consistent with a 22–32 halala schedule plus the 2-halala surcharge plus 15% VAT, which lends it credibility as a blended effective rate **[A]**.

**Recommended for the application:** quote **USD 0.074/kWh (SAR 0.277) as the blended commercial/industrial effective rate, Dec 2025** and cite the schedule range 22–32 halalas separately. This is the defensible pairing.

### Time-of-use and capacity charges

- **No published time-of-use energy rate** was found for Saudi commercial or industrial customers. **[UNVERIFIED — see final section]**
- **No published capacity / demand charge (SAR/kW)** was located. Note that Council of Ministers Decision No. 333 (2009) directed the regulator to take "electricity consumption at peak times" into account when adjusting non-residential tariffs **[C]** — the statutory hook for peak pricing exists, but a current published ToU schedule could not be retrieved.
- VAT at 15% is added to the bill **[C] secondary**.

**Implication for Mizan's model:** with no verified ToU signal, the fan-speed leg of the optimisation should be valued at a **flat energy price**, not a peak-shifting arbitrage. Claiming ToU arbitrage would be caught.

---

## 1.2 Saudi Arabia — water

### National Water Company block tariff (municipal network)

Source: NWC schedule, reproduced in the U.S.–Saudi Business Council water sector brief (Feb 2022) **[C]**.

| Monthly consumption (m³) | Water (SAR/m³) | Sanitary wastewater (SAR/m³) | **Combined (SAR/m³)** | Combined (USD/m³) [A] |
|---|---|---|---|---|
| 0–15 | 0.10 | 0.05 | 0.15 | 0.04 |
| 16–30 | 1.00 | 0.50 | 1.50 | 0.40 |
| 31–45 | 3.00 | 1.50 | 4.50 | 1.20 |
| 46–60 | 4.00 | 2.00 | 6.00 | 1.60 |
| **60+** | **6.00** | **3.00** | **9.00** | **2.40** |

**Any district-cooling or industrial plant sits permanently in the 60+ block. The operative number is SAR 9.00/m³ ≈ USD 2.40/m³ for potable water with sewerage. [C] + [A]**

Corroborating figures from secondary reporting **[C] secondary**: commercial premises on a flat SAR 9/m³ plus sewerage and VAT; government entities at SAR 9/m³ for both services and SAR 6/m³ for water only. These are consistent with the top block above.

**Vintage caveat:** the underlying NWC table is as published in 2022. It has not been re-confirmed against a 2025/2026 NWC schedule. Treat SAR 9/m³ as *the last verifiable published figure*, not as certainly current. **[C, dated]**

### Marafiq industrial tariffs — Jubail & Yanbu (most relevant to Dhahran/Eastern Province)

Approved by the **Royal Commission for Jubail and Yanbu (RCJY)**, effective **7 December 2025** **[C]**:

| Service | SAR/m³ | USD/m³ [A] | Tag |
|---|---|---|---|
| Potable water | 8.04 | 2.144 | [C] |
| **Process water** | **8.04** | **2.144** | **[C]** |
| Industrial wastewater | 3.64 | 0.971 | [C] |
| Sanitary wastewater | 3.17 | 0.845 | [C] |
| Truck-fill / construction supply | 6.70 | 1.787 | [C] |
| **Sea-water cooling** | **69.16 per 1,000 m³ = 0.06916/m³** | **0.0184** | **[C]** |

**This is the single most useful water tariff pair in the dossier.** For an industrial cooling-tower operator inside Jubail or Yanbu, the marginal economics of blowdown are:

> **Cost avoided per m³ of blowdown reduced = SAR 8.04 (process makeup water not bought) + SAR 3.64 (industrial wastewater not discharged) = SAR 11.68/m³ ≈ USD 3.11/m³ [A]**

That derived figure is the number that makes the Mizan business case, and it rests entirely on two [C] line items from the same approved schedule. It is defensible.

**The sea-water cooling line is a warning, not an opportunity:** at SAR 0.069/m³, water is effectively free for Marafiq's once-through seawater users. Blowdown-reduction value collapses to near zero for those loops. See §5.

### Water production cost context (useful for the "national water scarcity" framing)

| Metric | Value | Tag |
|---|---|---|
| SWCC weighted-average desalination production cost (2020) | SAR 2.27/m³ = USD 0.61/m³ | [C] |
| SWCC production cost, newest RO plants | SAR 1.27/m³ = USD 0.39/m³ | [C] |
| Kingdom-wide weighted-average desalination cost (2020) | SAR 2.13/m³ | [C] |
| Inferred total SWCC project cost per m³ (2020) | SAR 22/m³ = USD 5.90/m³ | [C] (source's own inference) |
| Total Saudi water demand (2020) | 15.98 billion m³ | [C] |
| Industrial water demand (2020) | 1.7 billion m³ (10% of total) | [C] |
| Urban water demand (2020) | 3.63 billion m³, 63% desalinated | [C] |

---

## 1.3 Qatar — Kahramaa electricity and water

### Electricity

| Metric | Value | Date | Tag |
|---|---|---|---|
| **Qatar business electricity price, all-in** | **QAR 0.130/kWh = USD 0.036/kWh** | December 2025 | **[C]** |
| Qatar household electricity price, all-in | QAR 0.115/kWh = USD 0.032/kWh | December 2025 | [C] |

Published Kahramaa commercial slab structure, reported in secondary sources as 9 dirhams/kWh (QAR 0.09) for the first 4,000 kWh, 12 dirhams (QAR 0.12) for 4,001–15,000 kWh and 14 dirhams (QAR 0.14) above 15,001 kWh, with industrial customers on 9–12 dirhams **[UNVERIFIED — vintage and category unconfirmed; see final section]**.

**Note the useful cross-check [A]:** the independent Dec-2025 business figure of QAR 0.130/kWh falls precisely between the reported top two commercial slabs (0.12 and 0.14). That coherence raises confidence in the slab structure without making it citable. **Use QAR 0.130/kWh (USD 0.036/kWh) as the headline.**

**Qatar electricity is roughly half the Saudi price (USD 0.036 vs 0.074/kWh) [A].** The fan-energy leg of Mizan's value proposition is therefore materially weaker in Qatar than in Saudi Arabia, and the water leg correspondingly more important. This should be stated openly in the application rather than averaged away.

### Water

Kahramaa water tariffs for **commercial and industrial** customers could not be verified. The frequently-cited slab set of QR 4.40 / 5.40 / 6.40 / 7.40 per m³ traces to a **Gulf Times article dated 13 October 2015** describing a residential/expatriate restructuring **[C for existence and date; not applicable to commercial/industrial in 2026]**. Kahramaa's own tariff pages expose only a calculator, not a rate table. **[UNVERIFIED — see final section]**

---

## 1.4 Bulk sulphuric acid (98%), Saudi Arabia / Gulf

| Period | Price (USD/tonne) | USD/kg [A] | Basis | Tag |
|---|---|---|---|---|
| Q3 2025 (Sep) | 148.33 | 0.148 | Saudi Arabia | [C] |
| Q4 2025 (Dec) | 159.67 | 0.160 | Saudi contract spreads | [C] |
| Q1 2026 (Mar) | 183.33 | 0.183 | **Ex-Jeddah** | [C] |
| **Q2 2026 (Jun)** | **380.33** | **0.380** | **Ex-Jeddah** | **[C]** |

Source: ChemAnalyst pricing page (a commercial market-intelligence provider; the free page carries the quarterly assessments) **[C]**.

**This series contains a material warning.** Prices roughly **doubled between Q1 and Q2 2026**, attributed by the source to Strait of Hormuz disruptions in June 2026 that "sharply reduced sulfur exports, constraining feedstock and tightening acid supply chains" **[C]**.

**Recommended treatment in the application [A]:**
- Do **not** headline USD 380/t — a reviewer will read it as cherry-picking the spike.
- Do **not** headline USD 148/t — a reviewer will read it as cherry-picking the trough.
- Present the **range USD 148–380/t over the last four quarters** and run the economics at a **base case near USD 180–200/t**, explicitly noting Hormuz exposure. Volatility in the acid price is an *argument for* dose optimisation, not against it — make that point rather than hiding the number.

**Important scope caveat [A]:** these are **bulk commodity assessments**, not delivered small-lot prices to a district-cooling plant. A plant buying drummed or IBC-packed 98% acid with delivery, HSE handling and a distributor margin will pay a substantial multiple of the bulk figure. If the model uses a delivered price, it must be tagged as an estimate — no delivered Gulf small-lot price was found. **[UNVERIFIED for delivered pricing]**

---

## 1.5 Cooling-water treatment / antiscalant service contract pricing

| Benchmark | Value | Tag |
|---|---|---|
| Scale & corrosion inhibitor programme, good-quality (2026) | **USD 2.50 – 4.50 per 1,000 US gallons of makeup water** | [C] secondary |
| Same, expressed per m³ | **USD 0.66 – 1.19 per m³ of makeup water** | [A] (÷ 3.78541) |
| Industry "well-run programme" band (2023) | USD 2.50 – 3.00 per 1,000 gal | [C] secondary |
| "Reasonable" band | USD 3.00 – 4.00 per 1,000 gal | [C] secondary |
| Diagnostic rule | Above USD 4.00 or below USD 2.50 per 1,000 gal signals over- or under-treatment | [C] secondary |
| Threshold at which operators reconsider chemical programmes | Combined chemical + labour spend > USD 50,000/year | [C] secondary |

**Source-quality note, stated plainly:** these benchmarks come from US water-treatment vendors' own published guidance (EAI Water, H2O Cooling, Clear Comfort). Two of the three pages returned HTTP 403 to direct fetching and the figures survive via search-engine extraction. They are **US benchmarks, not Gulf-specific**, and they are **vendor-published**. Treat as an order-of-magnitude anchor, cite the range not a point, and do not present them as Gulf pricing. **No published Gulf water-treatment contract price was found. [UNVERIFIED]**

**Pricing model of incumbents [C]:** the sector is priced as a **chemical service contract billed on treated/makeup water volume**, not as a device sale. This is strategically significant for Mizan and is developed in §4.3.

---

# PRIORITY 2 — Named target accounts

## 2.1 Saudi Arabia — confirmed (9 organisations)

| # | Legal entity | Confirmed site(s) | Capacity | Why it fits | Tag |
|---|---|---|---|---|---|
| 1 | **Saudi Tabreed District Cooling Company** | Portfolio-wide | **349,000 TR contracted** | Largest independent DC operator in KSA; evaporative condenser-water loops across a multi-site portfolio — one commercial relationship, many retrofit units | [C] |
| 2 | Saudi Tabreed — **King Abdullah Financial District (KAFD), Riyadh** | 2 plants | **100,000 TR** | Flagship Riyadh asset; 10-year contract extension signed with KAFD, so operator has a long horizon to amortise a retrofit | [C] |
| 3 | Saudi Tabreed — **Jabal Omar, Makkah** | Phases 1–2 | **55,000 TR** | Large single-site load; Makkah water cost and scarcity are acute | [C] |
| 4 | Saudi Tabreed — **King Salman Park, Riyadh** | 1st DC plant | **60,000 TR**, 25-year agreement | Greenfield with a 25-year O&M horizon — ideal for embedded controls | [C] |
| 5 | Saudi Tabreed — **King Khalid International Airport, Riyadh** | Phase 1 | **20,000 TR** | Continuous critical load; airport operators carry formal energy-performance obligations | [C] |
| 6 | Saudi Tabreed — **King Faisal Specialist Hospital, Jeddah** | Ph1 37,000 + Ph2 25,000 | **62,000 TR** | Healthcare = zero tolerance for condenser fouling; strong reliability argument | [C] |
| 7 | Saudi Tabreed — **Saudi Aramco** cooling system | — | **32,000 TR** | Direct commercial proof that Aramco procures third-party district cooling — the single most useful reference for a DTV application | [C] |
| 8 | **Saudi Aramco** (own utilities) | Ras Tanura Refinery complex; Abqaiq, Hawiyah (SAPCO/PCPC sites) | Refinery 550,000 bbl/d; PCPC 876 MW + 3.26 Mlb/hr steam | Aramco maintains **its own engineering standards for cooling water treatment** covering **open evaporative recirculating**, once-through and closed systems — i.e. it owns the exact asset class and already has a technical governance framework to plug into | [C] |
| 9 | **Power & Water Utility Company for Jubail and Yanbu (Marafiq)** — incl. **Jubail & Yanbu District Cooling Company ("Marafiq Cool")**, a JV 80% Saudi Tabreed / 20% Marafiq | Jubail & Yanbu Industrial Cities | Marafiq overall: 4.8 GW power; 56.6 million m³/day seawater | Only Saudi operator that **publishes its own approved water tariff schedule** (§1.2) — so the value case can be computed from the customer's own published numbers. **Target the district-cooling entity, not the seawater once-through business** (see §5) | [C] |

**10th Saudi slot — ENOWA (NEOM):** a **25,000 TR district cooling plant at OXAGON** is confirmed as planned by ENOWA, NEOM's energy/water subsidiary **[C]**. Listed as a **pipeline prospect, not an operating account** — no evidence was found that the plant is operating. Do not present ENOWA as an installed asset.

## 2.2 Qatar — confirmed (5 organisations)

| # | Legal entity | Confirmed site(s) | Capacity | Why it fits | Tag |
|---|---|---|---|---|---|
| 1 | **Qatar District Cooling Company (Qatar Cool)** | 5 plants | **237,000 TR total** | Largest Qatari DC operator | [C] |
| 2 | Qatar Cool — **The Pearl-Qatar, Integrated DC Plant** | 1 plant | **130,000 TR** (described at inauguration in Nov 2010 as the world's largest DC plant) | Single largest addressable loop in Qatar | [C] |
| 3 | Qatar Cool — **West Bay** | 3 plants | **92,500 TR combined** (30,000 + 37,000 + 35,000 TR; third plant has 25,000 TRh thermal storage and **uses TSE**) | Qatar Cool has **switched West Bay to TSE** and publicly documented the resulting condenser-chemistry difficulty — a warm, self-identified pain point | [C] |
| 4 | **Qatar Foundation** — District Cooling Central Plants, Education City | Main plants + 3 emergency stations | **152,000 TR main + 33,000 TR emergency = 185,000 TR** | Plants run **completely on TSE for condenser cooling** — the highest-scaling-risk makeup water in the region, on a single owner's campus | [C] |
| 5 | **Marafeq Qatar** — Lusail City district cooling | Marina, Wadi, West, North plants | **500,000 TR connected**; ~**630,000 TR** at full build-out; network is the world's largest DC network at 123.5 km | Largest single DC scheme in the Gulf; Northern plant tank alone 12,000 TR | [C] |
| 6 (bonus) | **QatarEnergy** — Ras Laffan Common Cooling Water System | Ras Laffan Industrial City | 937,000 m³/hr seawater capacity; system explicitly "receiv[es] return blowdown water from **re-circulating seawater cooling towers** located on multiple end-user plots" | **Confirmed recirculating cooling towers with blowdown** — a genuine industrial-cooling fit, though on seawater chemistry (see §5) | [C] |

## 2.3 Candidates checked and DISCARDED — with reasons

Discarding these is a credibility asset, not a gap. Show this table to the reviewer.

| Candidate | Verdict | Evidence | Tag |
|---|---|---|---|
| **Red Sea Global** | **DISCARD** | Its district cooling plant (**32,500 TR**) is deliberately **dry-cooled with zero water consumption**, using marine-grade aluminium dry coolers — "we opted for dry-cooled technology with zero water consumption". **There is no cooling tower and no blowdown.** Also corroborated by a separate report of 132 Güntner dry coolers on the Red Sea project | [C] |
| **Saudi Electricity Company (SEC)** | **DISCARD as a cooling-tower account** | SEC's coastal thermal fleet uses **once-through seawater condenser cooling**, not evaporative towers; the arid climate makes air-cooled condensers inefficient so coastal siting with seawater is the norm. SEC remains relevant **only** as the electricity-tariff counterparty | [C] |
| **ACWA Power** | **DISCARD (unconfirmed)** | No evidence found that ACWA Power operates evaporative cooling-tower/condenser-water loops; its Saudi IWPP fleet is coastal seawater-cooled | [UNVERIFIED] |
| **SWCC / Saudi Water Authority** | **DISCARD** | Desalination producer and now regulator (renamed from SWCC to Saudi Water Authority in **March 2024**). Not a cooling-tower operator | [C] |
| **SWPC (Saudi Water Partnership Company)** | **DISCARD** | Procurement entity for private-sector water/sewage projects, formerly Water & Electricity Company. Does not operate cooling assets | [C] |
| **Kahramaa** | **DISCARD as an account; RETAIN as regulator** | Kahramaa is the Qatari **regulator** of the district-cooling sector (with the Ministry of State for Energy Affairs) and the tariff-setter. It reports sector statistics rather than operating condenser loops. Route to market, not a customer | [C] |
| **NEOM / ENOWA** | **PIPELINE ONLY** | 25,000 TR OXAGON plant confirmed as planned; no confirmation of operating cooling assets | [C] |

---

# PRIORITY 3 — Market sizing, policy and incumbents

## 3.1 Installed district-cooling capacity and market size

### Qatar — the strongest sizing data in this dossier

| Metric | Value | Tag |
|---|---|---|
| **District cooling plants in Qatar (2023)** | **70 plants** | **[C]** |
| **Combined installed capacity (2023)** | **1.153 million TR** | **[C]** |
| Mandatory-connection threshold | Standalone buildings outside service zones must adopt district cooling at **≥1,500 TR** cooling demand | [C] |
| Regulator | Kahramaa with Ministry of State for Energy Affairs | [C] |
| 2026 regulatory package | Four ministerial decisions: No. 03 (service zones & building eligibility), No. 04 (operator access to public land), No. 05 (infrastructure relocation), No. 06 (damage compensation) | [C] |

**Qatar is the better-evidenced of the two markets and the 1.153 million TR / 70-plant figure is the single cleanest TAM anchor in this document.**

### Saudi Arabia

| Metric | Value | Tag |
|---|---|---|
| Market size 2024 | **USD 1,515.0 million** | [C] |
| Forecast 2030 | **USD 2,585.3 million** | [C] |
| CAGR 2025–2030 | **9.4%** | [C] |
| Largest technology segment | Electric chillers, **49.0%** share (2024), also fastest-growing | [C] |
| Fastest-growing end-use | Residential, 10.9% CAGR | [C] |
| **Government capacity target** | **3 million TR by 2030** | [C] — see caveat |

**Caveat on the 3 million TR figure [A]:** it appears in a market-research vendor page and consultancy blogs as a "government target". **No primary Saudi government document stating this target was located.** Cite it as *"reported industry target"* with attribution to the market-research source, never as an official government commitment. A DTV reviewer may well know the provenance.

**No verified figure for Saudi Arabia's currently *installed* district-cooling capacity in TR was found. [UNVERIFIED]** Use the USD market-size figures, which are properly sourced, and the named-account capacities in §2.1 (which sum to a verifiable **349,000 TR for Saudi Tabreed alone**) as a bottom-up floor.

### Water consumed by district cooling — Qatar, verified

| Metric | Value | Source & date | Tag |
|---|---|---|---|
| **Water saved by Qatari DC plants, 2024** | **18.5 million m³** | Kahramaa, 25 Mar 2025 | **[C]** |
| Equivalent framing given by Kahramaa | Enough to supply ~18,000 villas | Kahramaa | [C] |
| **DC plants using recycled water** | **41 plants** | Kahramaa | **[C]** |
| **Recycled share of total DC makeup water** | **82%** | Kahramaa | **[C]** |

Verbatim: *"41 District Cooling plants utilised recycled water, accounting for 82% of the total makeup water used in district cooling"* — Kahramaa **[C]**.

**This is the most valuable single statistic in the dossier for the Mizan thesis [A].** It establishes that (a) Qatari district cooling consumes makeup water at a scale the regulator tracks and publicises, and (b) **82% of that makeup is already recycled water** — i.e. the high-TDS, high-scaling-potential feedstock that makes skin-temperature saturation control matter. The market has already moved to the water chemistry Mizan is built for.

**No equivalent Saudi figure for water consumed by district cooling was found. [UNVERIFIED]**

## 3.2 TSE reuse policy and mandates

### Qatar

| Finding | Tag |
|---|---|
| Kahramaa "emphasises the importance of switching to the use of treated wastewater or any available and appropriate alternative water resources instead of potable water in **all district cooling plants**" | [C] |
| Qatar's 2026 ministerial decisions regulate service zones, operator land access, relocation and compensation — a maturing licensed-operator regime | [C] |
| "Most district cooling plants utilize treated water, helping save significant quantities of desalinated water" | [C] |
| **Qatar Foundation** Education City DC central plants **completely transformed to TSE for condenser cooling** (announced Dec 2023), delivered with Kahramaa | [C] |
| **Qatar Cool** completely switched its two operational West Bay plants from potable water to TSE; **1.7 million m³** of potable water avoided over 18 months | [C] |

### Saudi Arabia

| Finding | Tag |
|---|---|
| NWC operates a **Treated Sewage Effluent Initiative (TSEI)** distributing TSE via dedicated networks; end users are "most commonly industrial, agricultural, or commercial sectors" | [C] |
| National target: raise treated-wastewater reuse from **17.3% (2019) to 25% by 2025** | [C] |
| Treated wastewater reused, 2019 | 4.9 million m³/day | [C] |
| Municipal wastewater production, 2018 | 2.9 million m³/day, projected 5.1 million m³/day by 2050 | [C] |
| Plan to raise national wastewater treatment capacity **50% to 8.4 million m³/day** | [C] |
| SERA's founding mandate (Council of Ministers Resolution No. 236, 1422H / 2001) covers electricity, water desalination **and district cooling** | [C] |
| Constraint acknowledged in the literature: TSE "is not utilized to its full potential due to limited infrastructure, challenges in overcoming perception, and **limited regulatory oversight and pricing incentives**" | [C] |

**No Saudi TSE *tariff* (SAR/m³) and no explicit Saudi *mandate* requiring district cooling to use TSE were found. [UNVERIFIED — both]** Qatar has the clearer policy push; Saudi Arabia has the initiative and the targets but the pricing signal could not be evidenced.

### Why TSE matters technically — verified operator testimony

Qatar Cool's own published account of the TSE migration is the best third-party validation of the Mizan problem statement found in this research **[C]**:

- The plants "were operational and designed for potable water… design parameters of the cooling technology were specifically intended for certain water qualities and tolerances, which may not have supported the waste water quality."
- **"Severe scaling was observed on condenser surfaces"** with groundwater as makeup, and scale formation "could potentially reduce the heat transfer through the exchanger and cooling load, and increase pressure drop and condensing pressure."
- Mitigation required blending TSE with potable water and raising the ratio gradually **over 1.5 years** — an operationally expensive workaround for what is fundamentally a saturation-control problem.

**This is the strongest available external evidence that the problem Mizan solves is real, expensive and self-reported by a marquee operator.** Quote it.

## 3.3 Incumbent cooling-water controllers — and the core differentiation question

### THE HEADLINE FINDING

> **Skin-temperature saturation evaluation is NOT novel and is NOT free. ChemTreat holds granted US patent 11,780,742 B2 (granted 10 Oct 2023) whose independent claim requires determining heat-exchanger skin temperature from inlet and outlet temperatures and using it to compute a scale saturation index that drives chemical dosing.**

This must be confronted directly in the application. Attempting to claim skin-temperature saturation as novel will fail due diligence.

**However, the patent's scope is narrower than the claim it appears to pre-empt, and the gaps are exactly where Mizan sits.** The detail is below.

### US 11,780,742 B2 — the critical piece of prior art

| Field | Value | Tag |
|---|---|---|
| Title | *Methods for online control of a chemical treatment solution using scale saturation indices* | [C] |
| **Assignee** | **ChemTreat Inc** | [C] |
| Inventors | Kevin Boudreaux, Bill Gonzalez, Kerry Killough | [C] |
| Priority / filing | 24 Apr 2020 / 24 Nov 2020 | [C] |
| **Granted** | **10 Oct 2023** | [C] |
| Family | US20210331942A1, WO2021216131A1, EP4396139A4, CN114409125A; citing family incl. US12391591B2, US12358820B2, US11521138B1 (Freeport Minerals) | [C] |

**Claim 1 requires, verbatim:** *"measuring an inlet-side temperature and an outlet-side temperature of the heat exchanger and determining a skin temperature of the heat exchanger based on the inlet-side temperature and the outlet-side temperature; determining a dosage… based on… the skin temperature of the heat exchanger."* **[C]**

**And the specification, verbatim:** *"The skin temperature is the temperature on the surface of the heat exchanger tubes that contacts the water. It can be thought of as a quasi-average between the process side and the cooling water side of the heat exchanger and is the temperature that is considered to be important when discussing the saturation index of water."* **[C]**

**What the ChemTreat patent does NOT do — verified by full-text search:**

| Mizan element | Present in US11780742? | Tag |
|---|---|---|
| Skin-temperature saturation | **YES — claimed** | [C] |
| **Ion-specific speciation** | **NO** — uses empirical indices: LSI (primary), Puckorius, Ryznar, Larson-Skold, Stiff-Davis, Oddo-Tomson | [C] |
| **Blowdown / cycles-of-concentration control** | **NO** | [C] |
| **Acid dosing / pH control** | **NO** | [C] |
| **Fan-speed control** | **NO** | [C] |
| Scale species covered | Focused on **calcium carbonate**; abstract mentions calcium/silica/magnesium but methods and examples are CaCO₃ | [C] |
| Actuated variable | **Antiscalant feed rate only** | [C] |

### Incumbent-by-incumbent assessment

| Vendor / product | What it actually does | Skin temperature? | Ion-specific speciation? | Controls blowdown/CoC? | Pricing model |
|---|---|---|---|---|---|
| **Ecolab / Nalco Water — 3D TRASAR** | Real-time monitoring of chemical concentration (fluorescent tracer), corrosion rate, conductivity, ORP, pH; detects upsets and takes corrective action. Premium tier adds a **deposit sensor** for real-time scale/biofilm identification, OMNI asset intelligence on ECOLAB3D, and 24/7 remote monitoring from the Global Intelligence Center (programme launched **29 Apr 2024**) **[C]** | **No evidence found.** Nalco's published material and its granted controller patent use **bulk** inlet/outlet temperatures | **No.** Published description centres on **LSI** prediction ("predicts the value of the Langelier Saturation Index… and the dosage of products required for scale control") **[C] secondary** | **Reported yes** in one trade article: Nalco's Scale Index monitors the "system scale boundary" and can "adjust the blowdown rate (cycle control), adjust system pH, or adjust chemical treatment dosage" **[C] secondary — the page returned 403 to direct fetch; treat as indicative, verify before citing** | Chemical service contract with instrumented control; no public price. 20,000th installation milestone published **[C]** |
| **Ecolab USA — US 11,668,535 B2** (*Cooling water monitoring and control system*, filed 9 Nov 2018, granted 6 Jun 2023) | Monitors **heat-exchanger thermal-efficiency trends** to detect fouling, classifies the cause as scale / corrosion / biofouling, and controls chemical additive injection accordingly | **No.** Full-text check: measures **bulk stream temperatures at heat-exchanger inlets/outlets**; no skin or surface-temperature computation described | **No.** Full-text check: **does not mention saturation indices at all** (no Langelier, Ryznar or similar) | **No** — explicitly does not control cycles of concentration, blowdown, acid dosing or fan speed | n/a |
| **ChemTreat — US 11,780,742 B2 / FlexPro®** | See above. FlexPro is the commercial cooling scale/corrosion inhibitor line (phosphorus- and zinc-free options, fluorescent-traced automatic feed; >1,000–1,500 applications claimed) **[C]** | **YES — the only confirmed instance** | **No** — empirical indices | **No** — antiscalant feed only | Chemical programme; the control method is an attachment to chemical sales |
| **Veolia Water Technologies — Hydrex™ AquaVista / Aquavista 5C** | Automated control and monitoring for dosing cooling-water chemicals in open and closed circuits; measures pH, conductivity, redox, product content, corrosion rate; remote monitoring; collects data, calculates and executes corrections **[C]** | **No evidence found** | **No evidence found** | **YES — but conventionally.** "Both cooling tower blowdown and the feed of cooling tower chemical treatments are most often controlled through automated systems such as Veolia's Hydrex™ 5C PLC controller"; benefits include "optimizing blow-down water and related discharges" **[C]**. This is **conductivity/pH setpoint control**, not saturation-driven optimisation | Chemicals + controller package |
| **Kurita — S.sensing™ MX / VP, Kurita Connect 360** | Modular analyser system for industrial cooling water; standard pH and conductivity electrodes, polymer and chlorine concentration control, and **KPIs for corrosion, scaling and biofilm**; data visualised on Kurita Connect 360 with alerts and suggestions **[C]** | **No evidence found** | **No evidence found** | **No evidence found** | Chemicals + monitoring package |

### Verdict on the differentiation claim — state it this way

**What is already taken:**
1. **Skin-temperature saturation evaluation** — claimed by ChemTreat, granted 2023. **Not available as a novelty claim, and a freedom-to-operate question.**
2. **Ion-association / speciation saturation modelling** — long-established, not novel. French Creek Software's **WaterCycle** (company founded 1990) computes saturation for **18+ scales** using an ion-association model that "does not rely on traditional indices (LSI, Larson Skold, etc.)", comparing "hundreds of possible ion pair combinations" **[C]**. The manual states these ion-association saturation levels "have been in use by the major water treatment companies **since the early 70's**" **[C]**.
3. **Blowdown control against a saturation index** — the concept dates to **1984**: US 4,460,008 and US 4,464,315 establish the "trip point for blowdown is normally established by utilizing the Langelier's Saturation Index to calculate the conductivity that would occur after a predetermined number of cycles of concentration" **[C]**. **These are long expired** — the concept is public domain.

**What appears genuinely open — and this is the defensible position:**

WaterCycle is an **offline design and what-if tool**, not an online controller. Direct full-text search of its manual found **zero occurrences** of "skin", "surface temperature" or "heat exchanger" **[C]** — it works from *bulk* system temperature profiles, explicitly advising evaluation "at both the lowest and highest temperatures anticipated" **[C]**. It also already helps "estimate sulfuric or Hydrochloric acid requirements to maintain a prescribed pH" and set "control limits based on concentration ratio (cycles of concentration), pH, and temperature profiles" **[C]** — but as a human-in-the-loop planning exercise.

So the genuine white space is the **intersection**, not any single element:

> **Ion-specific speciation (French Creek has it, offline, at bulk temperature) evaluated at skin temperature (ChemTreat has it, online, with empirical LSI-family indices) driving simultaneous closed-loop actuation of fan speed, blowdown and acid dose (nobody found doing all three against a saturation objective).**

Frame the claim as **the co-optimisation of three actuators against an ion-specific, skin-temperature saturation objective**. Do not frame it as "we invented skin-temperature saturation" or "we invented ion-specific speciation". Both would be falsified in ten minutes by a competent reviewer.

## 3.4 Patents and startups on dynamic cycles-of-concentration optimisation

| Reference | Relevance | Tag |
|---|---|---|
| **US 11,780,742 B2** (ChemTreat, 2023) | **Blocking-risk art.** Skin-temperature SSI → antiscalant dose | [C] |
| **US 11,668,535 B2** (Ecolab USA, 2023) | Heat-exchanger efficiency → fouling-cause classification → chemical dose | [C] |
| **US 12,298,093** (second Ecolab/Kurita-adjacent "Cooling water monitoring and control system" hit) | Same family area; not individually examined | [C] existence only |
| **US 4,460,008 / US 4,464,315** (1984) | Foundational LSI-based blowdown trip-point control. **Expired — public domain** | [C] |
| **US 8,496,847 / US 9,227,864** | *Method and composition for operation of evaporative cooling towers at increased cycles of concentration* — **chemistry-based** route to higher CoC, not a control algorithm | [C] existence and title |
| **US 4,659,459** | Automated systems for introducing chemicals into water treatment systems | [C] existence |
| **US 7,179,384 B2** (Nalco) | Cooling water system control via rate of consumption of fluorescent polymer — the tracer-based control lineage behind 3D TRASAR | [C] existence |
| **French Creek Software** (est. 1990) — WaterCycle, hyd-RO-dose, DownHole SAT, MineSAT, WatSIM | Ion-association speciation modelling; **offline software, not a controller**. The closest competitor on the physics, the furthest on the product | [C] |
| **KETOS** (SHIELD platform) | Real-time water-quality monitoring (TDS, pH, conductivity, temperature) for data-centre cooling — **monitoring, not closed-loop co-optimisation** | [C] |
| DOE benchmark worth citing | Many cooling towers operate at only **2–4 cycles**; raising cycles from **3 to 6 cuts makeup water ~20% and blowdown ~50%** | [C] secondary (attributed to US DOE) |

**No venture-backed startup was found doing ion-specific, skin-temperature, multi-actuator cooling-tower co-optimisation.** The competitive threat is the incumbent chemical majors' patent estates, not startups. **[A]**

**Recommendation, stated bluntly:** commission a proper **freedom-to-operate opinion on US 11,780,742 B2 and its family (EP4396139, CN114409125)** before making claims to DTV about a defensible IP position. Note the CN and EP members — if Furqan intends to file in the Gulf, examiners will find this family.

---

# PRIORITY 4 — Procurement

## 4.1 Job titles that own cooling-water treatment and chemical budgets

**Honest framing:** exhaustive Gulf-specific title verification would require LinkedIn/organisational access that this research could not reach. The titles below are **confirmed to exist in the Gulf district-cooling sector**, with the ownership mapping marked as inference.

| Title | Confirmed to exist in Gulf DC | Role in a Mizan sale | Tag |
|---|---|---|---|
| **Plant Operator / District Cooling Plant Operator** | **Yes** — Saudi Tabreed job postings. Duties explicitly include *"checking water treatment chemicals tank levels and make-up if necessary"* and *"carrying out daily scheduled water analysis and recording the readings"*, monitoring via SCADA | **User / champion.** Feels the pain daily; no budget | **[C]** |
| **Operations and Plant Management** (function) | **Yes** — Saudi Tabreed has a named Operations and Plant Management team responsible for "managing plant operations, overseeing maintenance and commissioning… optimizing system performance" | **Economic buyer for O&M-funded retrofits** | [C] for existence; [A] for budget ownership |
| **Chemical Application Engineer** | **Yes** — posted in Gulf DC recruitment; plans and executes chemical cleaning for HVAC, chilled-water networks and industrial process systems | **Technical evaluator** | [C] |
| **Procurement Director** | **Yes** — a documented Tabreed role (subsequently GM of Cooltech, the group's water-treatment arm) | **Contracting gate** | [C] |
| **Programme Director, multi-utility** | **Yes** — e.g. Suez Environnement's programme director for Marafeq Qatar's multi-utility projects covering district cooling, water and wastewater | **Sponsor at large integrated operators** | [C] |
| Head of Asset Management / Technical Services Manager | Not confirmed for Gulf DC specifically | Likely capex approver | **[UNVERIFIED]** |
| Chief Sustainability / ESG Officer | Not confirmed for Gulf DC specifically | Likely co-sponsor given water-saving reporting | **[UNVERIFIED]** |

**A structurally important observation [A]:** Tabreed operates **Cooltech**, its own water-treatment chemicals and services business, and appointed its former Procurement Director as Cooltech's GM **[C]**. At Tabreed-family accounts, Mizan may be selling *through* or *against* a related-party chemical supplier. That is a real channel consideration and worth naming in the application — it shows commercial awareness.

## 4.2 Which budget line pays

**No Gulf district-cooling operator publishes its cost-line structure. The following is reasoned, not sourced. [A]**

| Budget line | Likelihood | Reasoning |
|---|---|---|
| **Water treatment / chemicals (opex)** | **Most likely primary** | Mizan directly reduces acid and antiscalant consumption; incumbents already bill here (§1.5), so a comparable line item exists and has a named owner |
| **O&M** | **Likely secondary** | Retrofit installation, commissioning and ongoing service naturally sit here |
| **Energy** | **Hardest to access** | Fan-energy savings accrue to the electricity bill, typically a separate cost centre from chemicals. Cross-charging between the two is a known organisational friction and should be assumed, not wished away |
| **Water / utilities** | Plausible at integrated operators | Marafiq and Marafeq buy and sell both water and cooling, so water savings are visible in one P&L |
| **Capex** | Avoid if possible | Triggers a longer approval chain; an opex/service pricing model likely shortens the cycle materially |

**Strategic read [A]:** the cleanest pitch is to the **water-treatment/chemicals line**, positioning the energy saving as *upside that another department books*. Selling primarily on fan energy means selling into the budget line least likely to fund the purchase.

## 4.3 Incumbent pricing model — and why it is a moat, not a price umbrella

Incumbents (Ecolab/Nalco, Veolia, Kurita, ChemTreat) sell **chemical service contracts** in which instrumentation and control are **bundled as an attachment to chemical volume** **[C]**. Benchmarks are quoted **per 1,000 gallons of makeup water treated** (§1.5) **[C]**.

**The strategic consequence, stated plainly [A]:**

> A vendor whose revenue scales with chemical volume has a **structural disincentive** to minimise acid and antiscalant dose. Mizan's value proposition is precisely to reduce that consumption. This is a genuine wedge — but it also means **every incumbent on site is a hostile stakeholder**, and the incumbent typically holds the relationship with the operator's water-treatment budget owner.

Consider selling **outcome-based** (share of verified water + chemical + energy saving) rather than as a device. It aligns with the buyer, it sidesteps a capex approval, and it is the pricing model the incumbents structurally cannot match.

## 4.4 Procurement cycle times and vendor registration

### Saudi Aramco

| Requirement | Detail | Tag |
|---|---|---|
| Legal entity | Must establish a licensed legal entity in the Kingdom | [C] secondary |
| Portal | Pre-qualification via the **SAP Ariba** supplier portal | [C] secondary |
| Documentation | Company docs, financial statements, technical credentials, quality certifications (ISO 9001, API, ASME as applicable), HSE credentials, product/service catalogues | [C] secondary |
| Assessment | Technical capability, financial health, quality management, HSE performance, **IKTVA localisation score** | [C] secondary |
| **IKTVA** | Mandatory: two-step (survey + **5-year action plan**), with certified third-party verification and **annual IKTVA reports** | [C] secondary |
| **Timeline — Saudi entity already in place** | **8–16 weeks** | [C] secondary |
| **Timeline — entity setup and registration concurrent** | **12–22 weeks** (i.e. 3–6 months) | [C] secondary |

**Source-quality warning:** all Aramco figures come from **corporate-services firms that sell registration assistance** — i.e. parties with an incentive to present the process as tractable. No Aramco-published timeline was located. Treat 8–22 weeks as a **best case**, and note that registration is only the gate to *bidding*, not to a first order. **[A]**

### Etimad (Saudi government entities)

| Requirement | Detail | Tag |
|---|---|---|
| What it is | Ministry of Finance unified e-procurement platform — tender publication, bid submission, contract management, bank guarantees, payment tracking for nearly every government entity | [C] secondary |
| **RHQ condition** | **Since 1 January 2024**, foreign-company eligibility for Etimad tenders is linked to establishing a **Regional Headquarters in the Kingdom** | [C] secondary |
| Alternative routes | (a) MISA (Ministry of Investment) licence with valid CR permits direct registration; (b) work through a Saudi-registered commercial agent authorised with the Ministry of Commerce | [C] secondary |
| Foreign supplier option | "Foreign Supplier" registration with professional practice licence attached | [C] secondary |
| **Local content** | The **Local Content & Government Procurement Authority (LCGPA)** has made local-content scores directly influence award decisions — price is no longer the sole factor | [C] secondary |

### SEC and large private operators

**No published procurement cycle time was found for SEC, Saudi Tabreed, Marafiq, Qatar Cool or Marafeq Qatar. [UNVERIFIED]** Do not state a figure for these.

### Practical route-to-market read [A]

1. **Private operators first** (Saudi Tabreed, Qatar Cool, Marafeq Qatar) — no Etimad/RHQ gate, and Saudi Tabreed alone offers 349,000 TR across a multi-site portfolio under one relationship.
2. **Aramco second** — realistically 8–22 weeks to registration *plus* technical qualification against Aramco's own cooling-water-treatment engineering standards, which is the harder gate and is not covered by the registration timelines above.
3. **Government/SEC last** — the RHQ requirement makes this materially harder for a pre-revenue venture.
4. **Localisation is not optional.** IKTVA at Aramco and LCGPA scoring on Etimad both reward local content, which argues for a Saudi entity and a Saudi manufacturing or assembly partner early. For a DTV application specifically, this is a strength to lead with, not a cost to bury.

---

# 5. Findings that CONTRADICT or CONSTRAIN the venture thesis

**Present these proactively. A Dhahran reviewer will find them, and pre-empting them is worth more than the ground they concede.**

| # | Finding | Severity | Evidence |
|---|---|---|---|
| **1** | **Skin-temperature saturation is patented.** ChemTreat's US 11,780,742 B2 (granted Oct 2023) claims determining heat-exchanger skin temperature from inlet/outlet temperatures and using it to compute a scale saturation index driving chemical dose. International family members exist (EP, CN, WO) | **CRITICAL — novelty + FTO** | [C] |
| **2** | **Ion-specific speciation is decades old.** French Creek's ion-association model has been in commercial water-treatment use "since the early 70's"; WaterCycle covers 18+ scales and explicitly rejects LSI-family indices | **HIGH — kills the "ion-specific is novel" claim** | [C] |
| **3** | **Blowdown control against a saturation index dates to 1984.** US 4,460,008 / US 4,464,315 set blowdown trip points from LSI-derived cycles of concentration. (Mitigating: **expired**, so free to practise) | **MEDIUM** | [C] |
| **4** | **Nalco reportedly already adjusts blowdown, pH AND dose** from its Scale Index / "scale boundary" monitoring — the same three-actuator envelope Mizan proposes | **HIGH if confirmed** — source page returned 403; **verify before relying on the gap** | [C] secondary, unverified page |
| **5** | **Flagship Saudi giga-projects are going dry-cooled.** Red Sea Global's 32,500 TR plant is deliberately **zero-water** with dry coolers. If dry cooling becomes the giga-project default, the greenfield addressable market shrinks even as district cooling grows | **HIGH — strategic** | [C] |
| **6** | **Much Gulf industrial cooling is once-through seawater, not evaporative.** SEC's coastal thermal fleet uses once-through seawater; Marafiq's Jubail/Yanbu core business is seawater cooling at **SAR 0.069/m³** — at that price, blowdown-reduction value is ~nil | **HIGH — narrows the account list** | [C] |
| **7** | **Qatar's electricity is ~half Saudi's** (USD 0.036 vs 0.074/kWh). The fan-energy leg of the value stack is materially weaker in Qatar | **MEDIUM — pricing/segmentation** | [C] + [A] |
| **8** | **No verified time-of-use tariff in Saudi Arabia.** Any value attributed to shifting fan energy across a peak/off-peak spread is unsupported | **MEDIUM — remove from model unless verified** | [UNVERIFIED] |
| **9** | **Sulphuric acid price doubled in one quarter** (USD 183 → 380/t, Q1→Q2 2026, Hormuz disruption). Acid-saving value is highly volatile | **MEDIUM — argues for scenario ranges, and is genuinely a point in Mizan's favour if framed as dose-optimisation value under price volatility** | [C] |
| **10** | **Incumbents' revenue scales with chemical volume.** Every incumbent on site is structurally opposed to Mizan and typically owns the budget-holder relationship | **MEDIUM — channel risk** | [C] + [A] |
| **11** | **Qatar's makeup water is already 82% recycled.** Cuts both ways: it validates the chemistry problem, but means the "switch to TSE" transition value is largely *already captured* in Qatar. Mizan must sell **ongoing optimisation**, not transition enablement | **MEDIUM — messaging** | [C] |

### The single most important thing to change in the pitch

Stop claiming skin temperature or ion speciation as the invention. **Claim the co-optimisation.** The verified, defensible position is:

> *No incumbent or patent found combines (a) ion-specific mineral speciation, (b) evaluated at condenser skin temperature, (c) driving simultaneous closed-loop control of fan speed, blowdown and acid dose. ChemTreat has (b) with empirical LSI-family indices and antiscalant dose only. French Creek has (a) offline at bulk temperature. Veolia and Nalco control blowdown and dose on conductivity/pH setpoints. The combination is the contribution.*

That sentence is fully supported by the [C] evidence in §3.3 and will survive scrutiny. The current framing will not.

---

# 6. Sources

### Priority 1 — Tariffs and input prices
1. Saudi Electricity Company — Interim Condensed Consolidated Financial Statements, nine months ended 30 Sep 2025 (**primary; tariff history, 2-halala surcharge, Intensive Consumption Tariff, WACC**) — https://argaamplus.s3.amazonaws.com/f2a3ad5f-51ed-41d4-be79-00548eb202ba.pdf
2. SERA — Consumption Tariff (**page network-unreachable during research; listed for the reviewer's own verification**) — https://www.sera.gov.sa/en/consumer/electric-tariff/electric-tariff-categories/consumption-tariff
3. Saudi Electricity Company — Tariff Rates (**network-unreachable during research**) — https://www.se.com.sa/en-us/customers/Pages/TariffRates.aspx
4. GlobalPetrolPrices — Saudi Arabia electricity prices, December 2025 — https://www.globalpetrolprices.com/Saudi-Arabia/electricity_prices/
5. GlobalPetrolPrices — Qatar electricity prices, December 2025 — https://www.globalpetrolprices.com/Qatar/electricity_prices/
6. U.S.–Saudi Business Council — *Saudi Arabia's Water Sector*, Economic Brief, Feb 2022 (**NWC block tariff Table 1; SWCC costs; TSE reuse targets**) — https://ussaudi.org/wp-content/uploads/2022/02/Water-2022-Economic-Brief.pdf
7. Zawya / MEED Projects — *Saudi Arabia's Marafiq revises industrial water tariffs* (RCJY-approved, effective 7 Dec 2025) — https://www.zawya.com/en/projects/utilities/saudis-arabias-marafiq-revises-industrial-water-tariffs-wtf1ohqn
8. Sahm Capital — same Marafiq tariff revision — https://www.sahmcapital.com/news/content/projects-saudi-arabias-marafiq-revises-industrial-water-tariffs-2025-10-06
9. ChemAnalyst — Sulphuric Acid price trends (Saudi Arabia, Ex-Jeddah quarterly assessments) — https://www.chemanalyst.com/Pricing-data/sulphuric-acid-70
10. Gulf Times — *Kahramaa hikes water, electricity tariffs*, 13 Oct 2015 (**dated; residential slabs only**) — https://www.gulf-times.com/story/458727/kahramaa-hikes-water-electricity-tariffs
11. Kahramaa — Tariff pages (**calculator only; no rate table published**) — https://www.km.qa/CustomerService/Pages/Tariff.aspx and https://www.km.qa/CustomerService/Pages/tariffCalculation.aspx
12. EAI Water — *What should operating a cooling tower's water treatment cost?* (**403 to direct fetch**) — https://eaiwater.com/what-should-operating-a-cooling-towers-water-treatment-cost/
13. H2O Cooling — *Cooling Tower Operating Cost: 2026 Facility Guide* (**403**) — https://h2ocooling.com/cooling-tower-operating-cost/
14. Clear Comfort — *What Your Cooling Tower Treatment Really Costs* (**403**) — https://clearcomfort.com/cooling-tower-chemical-treatment-cost/

### Priority 2 — Named accounts
15. Saudi Tabreed — corporate site and news — https://www.sauditabreed.com/en/article/saudi-tabreed-consolidates-its-leadership-position-through-10-year-contract-extension-with-kafd
16. KAFD — Saudi Tabreed 10-year contract extension — https://kafd.sa/en/media-centre/saudi-tabreed-secures-10-year-contract-extension-with-kafd/
17. PR Newswire — Saudi Tabreed alliance wins KAFD district cooling, 100,000 TR — https://www.prnewswire.com/news-releases/saudi-tabreed-alliance-win-a-district-cooling-contract-providing-king-abdullah-financial-district-in-riyadh-having-a-capacity-of-100-thousand-tons-of-cooling-100878864.html
18. Zawya — Saudi Tabreed to build King Salman Park's first district cooling plant (60,000 TR) — https://www.zawya.com/en/projects/utilities/saudi-tabreed-to-build-king-salman-parks-first-district-cooling-plant-pj3k3f1m
19. STOM (Saudi Tabreed O&M) — overview — https://www.stom.sa/en/overview
20. Marafiq — Jubail and Yanbu District Cooling Company (Marafiq Cool) — https://www.marafiq.com.sa/en/about-us/companies-jvs-projects/jubail-and-yanbu-district-cooling-company-marafiq-cool/
21. Marafiq — Jubail Seawater Cooling — https://www.marafiq.com.sa/en/about-us/services/water-services/jubail-seawater-cooling/
22. Marafiq — Annual Report 2024 — https://www.marafiq.com.sa/media/qexf1oqe/marafiq-annual-report-2024-en-final-v0-24-03-2025.pdf
23. Aramco — Saudi Aramco Power Company (SAPCO) — https://www.aramco.com/en/what-we-do/operations/power-systems
24. Saudi Aramco Engineering Encyclopedia — *Cooling Water Treatment* desktop standards (confirms open evaporative recirculating systems in scope) — https://www.scribd.com/document/699680958/Engineering-Encyclopedia-Saudi-Aramco-DeskTop-Standards-Cooling-Water-Treatment
25. Arab News — NEOM's ENOWA plans 25,000 TR district cooling plant in OXAGON — https://www.arabnews.com/node/2140721/business-economy
26. Qatar Cool — Our Districts — https://qatarcool.com/qa/about-us/our-districts/
27. Global District Energy Climate Awards — Qatar Cool Integrated District Cooling Plant (The Pearl) — https://www.districtenergyaward.org/integrated-district-cooling-plant-idcp/
28. Global District Energy Climate Awards — Qatar Foundation District Cooling Central Plants — https://www.districtenergyaward.org/wp-content/uploads/2021/07/Qatar-Foundation_summary.pdf
29. QNA — QF's District Cooling Central Plants completely transformed to treated sewage water (24 Dec 2023) — https://www.qna.org.qa/en/News-Area/News/2023-12/24/0044-qf's-district-cooling-central-plants-completely-transformed-to-treated-sewage-water
30. Gulf Times — Kahramaa completes transformation of QF's District Cooling Central Plant — https://www.gulf-times.com/article/674197/qatar/kahramaa-completes-transformation-of-qfs-district-cooling-central-plant
31. Qatari Diar — Lusail City sets two Guinness World Records for its district cooling system — https://www.qataridiar.com/media/news/lusail-city-sets-two-guinness-world-records-its-district-cooling-system-0
32. Gulf Times — Lusail district cooling network recognised by Guinness — https://www.gulf-times.com/article/728489/qatar/world-record-breakthrough-qatars-lusail-district-cooling-network-recognised-by-guinness
33. Marafeq Qatar — Projects — https://www.marafeq.com.qa/main.php?content=Projects&link=48&type=content
34. Consolidated Contractors — Ras Laffan Common Cooling Water System Phase II (**recirculating seawater cooling towers with blowdown**) — https://www.ccel.ae/project/ras-laffan-common-cooling-water-system-phase-ii/
35. DMS Projects — QatarEnergy Ras Laffan Common Cooling Water System Phase 3 — https://www.dmsprojects.net/qatar/projects/qp-ras-laffan-common-cooling-water-system-phase-3/PRJ00020899
36. Araner — *Red Sea Global district cooling plant with zero water consumption* (**dry-cooled, 32,500 TR**) — https://www.araner.com/blog/red-sea-global-district-cooling-plant-with-zero-water-consumption
37. Cooling Post — 132 Güntner dry coolers for Red Sea project — https://www.coolingpost.com/features/132-guntner-dry-coolers-for-red-sea-project/
38. Wikipedia — Saudi Water Authority (SWCC renamed March 2024) — https://en.wikipedia.org/wiki/Saudi_Water_Authority

### Priority 3 — Market sizing, policy, incumbents, IP
39. The Peninsula Qatar — *New regulations accelerate growth of Qatar's district cooling sector* (**70 plants, 1.153 million TR, 2026 ministerial decisions, 1,500 TR threshold**) — https://thepeninsulaqatar.com/article/14/06/2026/new-regulations-accelerate-growth-of-qatars-district-cooling-sector
40. IDEA / District Energy — *District Cooling plants save 18.5 million cubic metres of water in 2024* (**Kahramaa, 25 Mar 2025; 41 plants, 82% recycled makeup**) — https://www.districtenergy.org/blogs/district-energy/2025/03/25/district-cooling-plants-save-185-million-cubic-met
41. The Peninsula Qatar — same Kahramaa water-saving report — http://thepeninsulaqatar.com/article/23/03/2025/district-cooling-plants-save-185-million-cubic-metres-of-water-in-2024
42. P&S Market Research — Saudi Arabia District Cooling Market (USD 1,515.0m 2024 → USD 2,585.3m 2030, 9.4% CAGR) — https://www.psmarketresearch.com/market-analysis/saudi-arabia-district-cooling-market
43. Qatar Cool — *Employing Treated Sewage Effluent (TSE) is no easy feat* (**severe condenser scaling; 18-month blending programme**) — https://qatarcool.com/qa/employing-treated-sewage-effluent-tse-is-no-easy-feat/
44. Qatar Cool — *District Cooling Embraces Treated Sewage Effluent (TSE)* — https://qatarcool.com/qa/district-cooling-embraces-treated-sewage-effluent-tse-2/
45. Qatar Tribune — Qatar Cool switches to treated sewage water in West Bay plants — https://www.qatar-tribune.com/article/80736/BUSINESS/Qatar-Cool-switches-to-treated-sewage-water-in-West-Bay-plants
46. MEWA — National Water Strategy — https://www.mewa.gov.sa/en/Ministry/Agencies/TheWaterAgency/Topics/Pages/Strategy.aspx
47. **US 11,780,742 B2 — ChemTreat Inc, *Methods for online control of a chemical treatment solution using scale saturation indices* (skin temperature claim)** — https://patents.google.com/patent/US11780742B2/en
48. USPTO full-text image of the same patent — https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11780742
49. **US 11,668,535 B2 — Ecolab USA Inc, *Cooling water monitoring and control system*** — https://patents.google.com/patent/US11668535B2/en
50. US 12,298,093 — Cooling water monitoring and control system — https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12298093
51. US 4,460,008 — Indexing controller apparatus for cooling water tower systems (1984, LSI-based blowdown) — https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/4460008
52. US 4,464,315 — Indexing controller system and method of automatic control of cooling water tower systems — https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/4464315
53. US 8,496,847 — Method and composition for operation of evaporative cooling towers at increased cycles of concentration — https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8496847
54. US 7,179,384 B2 — Nalco, Control of cooling water system using rate of consumption of fluorescent polymer — https://patents.google.com/patent/US7179384B2/en
55. **French Creek Software — WaterCycle Rx User Manual (ion-association model; no skin/surface-temperature capability; acid estimation; CoC control limits)** — https://www.frenchcreeksoftware.com/Manuals/WaterCycle-Rx-User-Manual.pdf
56. French Creek Software — *The Practical Application of Ion Association Model Saturation Level Indices* — https://www.frenchcreeksoftware.com/online-library/The-Practical-Application-of-Ion-Association-Model-Saturation-Level-Indices-to-Commercial-Water-Treatment-Problem-Solving/
57. Environmental Expert — WaterCycle modelling software (18+ scales, ion association, not LSI) — https://www.environmental-expert.com/software/watercycle-modeling-software-185123
58. Ecolab — 3D TRASAR Technology for Cooling Water — https://www.ecolab.com/en-us/offerings/nwwt/3d-trasar-technology-for-cooling-water
59. Ecolab / Nalco Water — Premium Cooling Water Program launch, 29 Apr 2024 — https://www.ecolab.com/nalco-water/news/2024/04/nalco-water-launches-premium-cooling-water-program
60. Water Tech Online — *On-Line Systems Aid Cooling System Chemistry Control* (**Nalco Scale Index adjusting blowdown/pH/dose; page returned 403 to direct fetch**) — https://www.watertechonline.com/process-water/article/16210493/on-line-systems-aid-cooling-system-chemistry-control
61. Veolia Water Technologies — Hydrex™ AquaVista automated cooling water treatment — https://www.veoliawatertechnologies.com/en/press-releases/veolia-brings-first-class-automated-cooling-water-treatment-hydrex-tm-aquavista-asia
62. Veolia Water Technologies — Cooling tower water treatment — https://www.veoliawatertech.com/en/expertise/applications/cooling-tower-water-treatment
63. Kurita Europe — S.sensing™ MX modular analyser for industrial cooling water — https://www.kurita.eu/en/solutions/sensing-mx/
64. Kurita Europe — S.sensing™ VP / Kurita Connect 360 — https://www.kurita.eu/solutions/s-sensing-value/
65. ChemTreat — FlexPro® non-phosphorus, non-zinc cooling treatment — https://www.chemtreat.com/solutions/featured-innovations/flexpro/
66. ChemTreat — *Corrosion, Scale, and Biofouling Control in Cooling Systems* (Water Essentials Handbook) — https://chemtreat.com/solutions/water-essentials-handbook-chapter-corrosion-scale-and-biofouling-control-in-cooling-systems
67. KETOS — Conventional vs AI data centre cooling and wastewater — https://ketos.co/conventional-vs-ai-data-center-cooling-options-and-how-much-wastewater-is-being-generated
68. US DOE FEMP — Best Management Practice #10: Cooling Tower Management — https://www.energy.gov/cmei/femp/best-management-practice-10-cooling-tower-management
69. Water Tech Online — *Use of Treated Sewage Effluent as Cooling Tower Makeup Water — A Pilot Study* — https://www.watertechonline.com/water-reuse/article/14187302/use-of-treated-sewage-effluent-as-cooling-tower-makeup-water-a-pilot-study-print

### Priority 4 — Procurement
70. The Org — Saudi Tabreed District Cooling Company, Operations and Plant Management team — https://theorg.com/org/saudi-tabreed-district-cooling-company/teams/operations-and-plant-management
71. Joblum — District Cooling Plant Operator, Saudi Tabreed (**water treatment chemical duties in the job description**) — https://sa.joblum.com/job/district-cooling-plant-operator/2213
72. Bayt — District Cooling jobs, Middle East (Chemical Application Engineer role definition) — https://www.bayt.com/en/international/jobs/district-cooling-jobs/
73. Areeco — How to register as an Aramco vendor in Saudi Arabia, 2026 guide — https://areeco.com.sa/how-to-register-as-an-aramco-vendor-in-saudi-arabia-step-by-step-guide-for-foreign-companies-2026/
74. ISO Consultants KSA — Aramco vendor registration process 2026 — https://isoconsultantsksa.com/saudi-aramco-vendor-registration-process-2026/
75. ProPartner Group — Saudi Aramco vendor registration / IKTVA programme — https://www.propartnergroup.com/blog/2022/10/how-to-become-a-saudi-aramco-supplier/
76. Motaded — Saudi public tender bidding via Etimad: a foreign company's guide — https://motaded.com.sa/blog/saudi-public-tender-bidding-etimad-foreign-companys-guide-motaded
77. Sell to State — Etimad guide, Saudi Arabia tender search — https://www.selltostate.com/blog/etimad-saudi-arabia-guide/
78. TendersGo — Saudi Arabia public procurement tenders 2026: Etimad portal guide and foreign bidding (**RHQ requirement from 1 Jan 2024**) — https://www.tendersgo.ai/post/saudi-arabia-public-procurement-tenders-2026-etimad-portal-guide-forei-5816

---

# 7. UNVERIFIED — DO NOT USE IN SUBMISSION

Everything below could not be confirmed to the standard set at the top of this document. Each entry records what was attempted.

### Tariffs

| Item | Status | What was tried |
|---|---|---|
| **Saudi electricity tariff from the primary regulator** | **NOT VERIFIED AT SOURCE** | `sera.gov.sa` and `se.com.sa` both returned connection-refused across multiple attempts and multiple URL paths; browser navigation to sera.gov.sa was denied. The 22/32-halala commercial figures rest on secondary reporting only. **The 2-halala surcharge and the tariff history ARE primary-verified via SEC's audited financials — use those.** |
| **Saudi commercial tariff — conflicting figures** | **CONFLICT** | One tariff-calculator site gives commercial as a flat 20 halalas and government 32; the more widely reported schedule is commercial 22 (≤6,000 kWh) / 32 (>6,000 kWh). **These are irreconcilable without the SERA schedule. Do not present a single commercial figure as certain** — use the GlobalPetrolPrices blended business rate instead |
| **Saudi industrial tariff, standalone rate** | **NOT FOUND** | Repeated searches returned only the commercial/residential schedule plus the intensive-consumption framework. No standalone industrial halala/kWh rate located |
| **Saudi time-of-use tariff** | **NOT FOUND** | The 2009 Council of Ministers decision authorises peak-time consideration, but no published ToU schedule was retrievable |
| **Saudi capacity / demand charge (SAR/kW)** | **NOT FOUND** | Searched SERA, SEC, ESMAP tariff schedule (403), SEC financials (no "capacity charge" occurrence in full text) |
| **Intensive Consumption Tariff — the actual rate** | **NOT FOUND** | Eligibility thresholds (≥20%, 10–19.9% electricity-to-opex) are reported secondarily; **the tariff rate itself was never located** |
| **Kahramaa commercial/industrial electricity slabs** | **NOT VERIFIED** | The 9/12/14-dirham commercial and 9–12-dirham industrial slabs appear only in Scribd-hosted documents of unknown vintage. Kahramaa's own site publishes a calculator, not a table. *Directionally corroborated* by the Dec-2025 business rate of QAR 0.130/kWh, but not citable |
| **Kahramaa commercial/industrial WATER tariff** | **NOT FOUND** | The QR 4.40/5.40/6.40/7.40 slabs come from a **2015** Gulf Times article on residential/expatriate rates. No current commercial or industrial water tariff was located |
| **Saudi TSE tariff for district cooling (SAR/m³)** | **NOT FOUND** | Multiple targeted searches of NWC, Saudi Water Authority, MEWA and trade press. The TSEI is documented; **its pricing is not public**. One academic source states TSE suffers from "limited regulatory oversight and pricing incentives", which is consistent with there being no published tariff |
| **Qatar TSE tariff for district cooling** | **NOT FOUND** | Same searches; only qualitative statements that TSE opex is ~20% of seawater and ~30% of well water cost for district cooling, from a UAE trade site — **not a tariff, and not citable as one** |
| **NWC tariff currency (2025/2026)** | **UNCERTAIN** | The block table is verified as published, but sourced via a Feb 2022 brief. Not re-confirmed against a current NWC schedule |
| **Delivered small-lot sulphuric acid price, Gulf** | **NOT FOUND** | Only bulk Ex-Jeddah commodity assessments were located. Any delivered/drummed price used in the model must be labelled an assumption |
| **Gulf-specific water-treatment contract pricing** | **NOT FOUND** | All benchmarks located are **US** and **vendor-published**, and two of three pages blocked direct fetching |

### Market sizing

| Item | Status | What was tried |
|---|---|---|
| **Saudi installed district-cooling capacity in TR** | **NOT FOUND** | Only the *forward target* of 3 million TR by 2030 (market-research/consultancy sourced, no primary government document) and bottom-up named-account capacities |
| **Saudi "3 million TR by 2030" as an official target** | **PROVENANCE UNCONFIRMED** | Appears in market-research and consultancy pages attributed to "the Saudi government"; **no primary government source located.** Attribute to the market-research firm if used at all |
| **Water consumed by district cooling in Saudi Arabia** | **NOT FOUND** | Qatar's equivalent figure IS verified (18.5 million m³ saved, 82% recycled makeup). No Saudi analogue exists in public sources found |
| **Saudi mandate requiring TSE in district cooling** | **NOT FOUND** | Targets and the TSEI initiative are documented; **no mandate** was located. Qatar has the clearer regulatory push |
| **Strategy&/PwC district cooling report contents** | **INACCESSIBLE** | Returned HTTP 403. URL retained in Sources for manual retrieval — likely the best single source for GCC capacity by country if it can be opened |

### Accounts

| Item | Status | What was tried |
|---|---|---|
| **ACWA Power operating evaporative cooling towers** | **NOT CONFIRMED — discarded** | No evidence found; its Saudi IWPP fleet is coastal seawater-cooled |
| **Marafiq Cool district cooling capacity in TR** | **NOT FOUND** | Marafiq publishes seawater cooling volumes (m³/day), not district cooling TR |
| **AMAALA district cooling capacity** | **NOT FOUND** | The 32,500 TR figure belongs to the Red Sea project plant, **not** AMAALA. Do not attribute it to AMAALA |
| **Trojena district cooling capacity** | **NOT FOUND** | Only OXAGON's 25,000 TR was located |
| **ENOWA OXAGON plant operational status** | **UNKNOWN** | Reported as planned; no commissioning confirmation |

### Incumbents and IP

| Item | Status | What was tried |
|---|---|---|
| **Whether Nalco's Scale Index actually adjusts blowdown, pH and dose** | **NOT VERIFIED — HIGH PRIORITY TO RESOLVE** | The claim appears in a Water Tech Online article extract; the page returned **403** to direct fetch and could not be read in full. **This is the single most consequential open question in the dossier** — if true, Nalco already operates the three-actuator envelope. Obtain the article before finalising any "no incumbent does this" claim |
| **3D TRASAR technical specification** | **NOT OBTAINED** | Ecolab's public pages are marketing-level and disclose neither control variables nor indices. LSI attribution rests on secondary summary |
| **3D TRASAR / Veolia / Kurita pricing** | **NOT FOUND** | No vendor publishes cooling-water controller or programme pricing; all direct enquiries to sales |
| **Kurita "S.sensing MC"** | **DOES NOT APPEAR TO EXIST** | Kurita publishes S.sensing MX and S.sensing VP. No MC variant found |
| **US 12,298,093 detailed claims** | **NOT EXAMINED** | Identified by title only; not individually reviewed |
| **Whether any patent claims skin-temperature + ion speciation + multi-actuator control together** | **NOT EXHAUSTIVELY SEARCHED** | Google Patents' faceted search interface was not machine-readable via available tooling. **A professional patent search is required before any novelty claim is made to DTV** |

### Procurement

| Item | Status | What was tried |
|---|---|---|
| **Aramco procurement cycle time from Aramco itself** | **NOT FOUND** | All timelines (8–16 / 12–22 weeks) come from **corporate-services firms selling registration assistance** — an interested party. Treat as best case |
| **SEC vendor registration process and cycle time** | **NOT FOUND** | No published SEC supplier process located |
| **Private operator (Tabreed, Qatar Cool, Marafeq) procurement cycle times** | **NOT FOUND** | Not published |
| **Job titles that specifically own the chemicals budget at Gulf DC operators** | **PARTIALLY VERIFIED** | Plant Operator, Operations and Plant Management, Chemical Application Engineer, Procurement Director and multi-utility Programme Director are all **confirmed to exist**. **Which of them holds signing authority over the chemicals budget is inference, not evidence** |
| **Whether energy savings can be cross-charged to a water-treatment budget** | **INFERENCE ONLY** | No operator publishes cost-centre structure |
