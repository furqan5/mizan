"""Build the research report from completed artifacts; no engineering calculation.
Every result displayed here is read from run/diagnostic/lookup JSON. Formatting
rounding is presentation only. This script creates no model pass thresholds.
"""
from pathlib import Path
import json,re,html,shutil
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'results/cdu_hybrid_verified/run.json'
DIAG=ROOT/'results/cdu_hybrid_diagnostics.json'
LOOKUP=ROOT/'results/itd_source_lookup.json'
CROSS=ROOT/'results/cdu_dry_cycles.json'
VERIFY=ROOT/'results/cdu_hybrid_verification.json'

def table(head,rows):
    return '\n'.join(['| '+' | '.join(head)+' |','| '+' | '.join(['---']*len(head))+' |']+
                     ['| '+' | '.join(str(x) for x in row)+' |' for row in rows])

SOURCES={
 'itd':dict(title='Crop, Moore and Pasricha, Revisiting Cooler is Better',publisher='arXiv',date='9 Jun 2026, v1',url='https://arxiv.org/abs/2606.11163',access='Supplied PDF, all seven pages extracted; Figure2 visually inspected and vector coordinates extracted; raw data unavailable.'),
 'ashrae':dict(title='Thermal Guidelines, Fifth Edition, Revised and Expanded, Table3.1',publisher='ASHRAE TC9.9',date='2021 / 2024 reference card',url='https://www.ashrae.org/file%20library/technical%20resources/bookstore/supplemental%20files/therm-gdlns-5th-r-e-refcard.pdf',access='Official reference card p8; primary water boundary verified.'),
 'ashrae_ch20':dict(title='ASHRAE Handbook2023, Chapter20: Data Centers and Telecommunication Facilities',publisher='ASHRAE',date='2023',url='https://handbook.ashrae.org/Handbooks/A23/SI/A23_Ch20/a23_ch20_si.aspx',access='Official text; CDU approach and FWS temperature boundary.'),
 'chiller':dict(title='EnergyPlus24.2 Chillers.idf: York YT1758kW/6.28COP/Vanes',publisher='NREL / EnergyPlus',date='v24.2.0',url='https://raw.githubusercontent.com/NREL/EnergyPlus/v24.2.0/datasets/Chillers.idf',access='Primary source coefficients and three curve domains read; object starts near line5512 in this version.'),
 'eir':dict(title='EnergyPlus24.2 Engineering Reference: Electric EIR Chiller',publisher='EnergyPlus documentation, Big Ladder host',date='24.2',url='https://bigladdersoftware.com/epx/docs/24-2/engineering-reference/chillers.html',access='Chiller energy balance and polynomial structure.'),
 'water2022':dict(title='Badruzzaman et al., Municipal reclaimed water as makeup water for cooling systems: Water efficiency, biohazards, and reliability',publisher='Water Resources and Industry28,100188',date='Dec 2022',url='https://doi.org/10.1016/j.wri.2022.100188',access='Existing13-page publisher PDF in sources; Table1 p3 and Table2 p4 mechanically extracted.'),
 'water2020':dict(title='Jutail et al., Use of treated sewage effluent as cooling tower makeup water - A pilot study',publisher='Water Technology',date='15 Dec 2020',url='https://www.watertechonline.com/water-reuse/article/14187302/use-of-treated-sewage-effluent-as-cooling-tower-makeup-water-a-pilot-study-print',access='Original engineer-authored pilot account; composition differs on several ions.'),
 'astm':dict(title='ASTM D1125-14, Electrical Conductivity and Resistivity of Water',publisher='ASTM International',date='2014 edition, cited method context',url='https://store.astm.org/d1125-14.html',access='Official scope; not a gravimetric TDS method.'),
 'water_tariff':dict(title='Marafiq Water Tariff',publisher='Marafiq',date='Checked7 Sep 2026; revised tariff effective7 Dec 2025',url='https://www.marafiq.com.sa/en/partnering-with-us/water-tariff/',access='Official indexed industrial tariff table; direct page retrieval timed out. VAT and site applicability not established.'),
 'fx':dict(title='Saudi Central Bank exchange-rate display',publisher='SAMA',date='2026 display; conversion assumption3.75 SAR/USD',url='https://www.sama.gov.sa/en-US',access='Official USD rate corroborated; exact site billing conversion remains contractual.'),
 'closest':dict(title='Chen et al., Physics-informed machine learning-based adaptive predictive control for energy-efficient hybrid-cooled data centers management',publisher='Applied Energy424,128414',date='AssignedDec2026 issue; Crossref deposit16 Jul2026',url='https://doi.org/10.1016/j.apenergy.2026.128414',access='Only metadata/preview; full text unavailable and unscored. Deposit date is not online-publication date.'),
 'patent':dict(title='ChemTreat US11780742B2, Methods for online control of a chemical treatment solution using scale saturation indices',publisher='USPTO document via Google Patents',date='10 Oct 2023',url='https://patents.google.com/patent/US11780742B2/en',access='All20 claims read; claims1,3,19,20 explicitly concern skin-temperature chemical-treatment control.'),
 'patent2':dict(title='ChemTreat US12358820B2, Systems and methods for online control of a chemical treatment solution using scale saturation indices',publisher='USPTO document via Google Patents',date='2025',url='https://patents.google.com/patent/US12358820B2/en',access='Prior repository scan retained; not a new freedom-to-operate analysis.'),
 'codesign':dict(title='Co-Design Optimization for Data Center Cooling System via Digital Twin',publisher='arXiv2605.15516',date='Suppliedv4',url='https://arxiv.org/abs/2605.15516',access='Supplied full PDF mechanically extracted and searched; CDU allocation and flow/supply co-design already studied.'),
 'dc_twin':dict(title='Digital Twin-Based Cooling System Optimization for Data Center',publisher='arXiv2603.01198',date='Suppliedv4',url='https://arxiv.org/abs/2603.01198',access='Supplied full PDF extracted; unconstrained savings explicitly separated from constrained results.'),
}

def cite(key):
    s=SOURCES[key];return f"[{s['title']}]({s['url']})"

def presentation_spacing(text):
    """Editorial spacing only; protect link destinations and named identifiers."""
    phrases=['approach is','with','by','at','to','plus','the','The','reports',
             'sulfate','Claims','claims','and','near','line','Figure','Table',
             'Chapter','Handbook','EnergyPlus','legacy','contains','not','in',
             'Defect','defect','all','All','within','through','fixed','pH',
             'FWS','ECWT','PLR','clean','inherited','universal','Assigned',
             'Supplied','December','Jul','Dec','Checked','effective','SAR','USD',
             'rise','rises','are','of','existing','Existing','Xeon','nearest','assumed','be','At']
    def segment(s):
        for phrase in sorted(phrases,key=len,reverse=True):
            s=re.sub(r'\b'+re.escape(phrase)+r'(?=[0-9])',phrase+' ',s)
        s=re.sub(r'(?<=\d)(MW|mg/L|SAR|K|C|W|m3)\b',r' \1',s)
        s=re.sub(r'(?<=\d) C\b',' °C',s)
        s=re.sub(r'(?<=\d)%',' %',s)
        s=s.replace('(C)',' (°C)').replace('(K)',' (K)').replace('(W)',' (W)')
        s=s.replace('(mg/L)',' (mg/L)').replace('(%)',' (%)')
        s=re.sub(r'\bm3\b','m³',s)
        for a,b in [('Energy424,128414','Energy 424, 128414'),
                    ('DOI10.','DOI 10.'),('open and its strict','open and its strict'),
                    ('4cycles','4 cycles'),('claims1,3,19,20','claims 1, 3, 19, 20'),
                    ('Claims 1,3,19 and 20','Claims 1, 3, 19 and 20'),
                    ('at40C','at 40 °C'),('count15','count 15')]:
            s=s.replace(a,b)
        return s
    return ''.join(p if p.startswith('https://') or p.startswith('http://') else segment(p)
                   for p in re.split(r'(https?://[^)\s]+)',text))

def build_text(r,d,l,x,v):
    ann=r['annual']['coupled_vs_baseline'];inc=r['annual']['FWS_increment_only'];bins=r['bins']
    f=lambda v:f'{v:,.2f}'
    statuses=table(['Test','Outcome','Meaning'],[
        ['H1a: condenser -> GPU water',r['verdicts']['H1a']['status'],f"{r['verdicts']['H1a']['pairs']} matched pairs; water change {r['verdicts']['H1a']['max_change_K']:.6f}K at fixed FWS"],
        ['H1b: cycles -> skin gypsum',r['verdicts']['H1b']['status'],f"{r['verdicts']['H1b']['pairs']} pairs; minimum SI increase {r['verdicts']['H1b']['minimum_SI_increase']:.4f}"],
        ['H2: cycles constraint',r['verdicts']['H2_cycles']['status'],f"Witnesses in {r['verdicts']['H2_cycles']['weather_bins_with_witness']} of {len(bins)} weather bins"],
        ['H2: water-temperature constraint',r['verdicts']['H2_temperature']['status'],f"Witnesses in {r['verdicts']['H2_temperature']['weather_bins_with_witness']} of {len(bins)} bins; sampled domain only"],
        ['H3: chip-optimum gap','Not identifiable','No measured chip-to-water bridge'],
        ['H4: ITD annual cost','Not identifiable','Independent FWS reset priced separately']])
    summary=table(['Comparison','Energy: totals / mean ratios','Cost: totals / mean ratios','USD/year'],[
        ['Coupled vs baseline',f"{ann['energy']['ratio_of_totals_pct']:.2f}% / {ann['energy']['mean_of_ratios_pct']:.2f}%",f"{ann['cost']['ratio_of_totals_pct']:.2f}% / {ann['cost']['mean_of_ratios_pct']:.2f}%",f(ann['cost']['annual_difference'])],
        ['FWS reset increment only',f"{inc['energy']['ratio_of_totals_pct']:.2f}% / {inc['energy']['mean_of_ratios_pct']:.2f}%",f"{inc['cost']['ratio_of_totals_pct']:.2f}% / {inc['cost']['mean_of_ratios_pct']:.2f}%",f(inc['cost']['annual_difference'])]])
    bybin=table(['Bin','WB mean(C)','FWS(C)','CW(C)','Cycles','Fan(%)','USD/h'],[[x['bin'],f"{x['T_wb_C']:.1f}",f"{x['coupled_optimum']['T_fws_C']:.2f}",f"{x['coupled_optimum']['T_ecwt_C']:.2f}",f"{x['coupled_optimum']['cycles']:.0f}",f"{x['coupled_optimum']['fan_pct']:.1f}",f"{x['coupled_optimum']['cost_per_h']:.2f}"] for x in bins])
    wr=table(['Scenario','Na(mg/L)','Ion sum(mg/L)','Charge error(%)','Gypsum cycles'],[[x['source'].replace('_',' ')+(' + Na balance' if x['sodium_balancing_assumption'] else ''),f"{x['ions']['Na']:.1f}",f"{x['ion_sum_mg_L']:.1f}",f"{x['imbalance_repo_pct']:.2f}",f"{x['gypsum_operating_limit_cycles_at40C']:.2f}"] for x in d['makeup_analyses']])
    tariff=table(['Same schedules repriced','USD saved/year','Totals(%)','Mean ratios(%)'],[[x['label'].replace('_',' '),f(x['annual_saving_USD']),f"{x['ratio_of_totals_pct']:.2f}",f"{x['mean_of_ratios_pct']:.2f}"] for x in d['water_tariff_policy_repricing']])
    dry=table(['Dry approach(K)','In-curve hours','Unsupported hours'],[[a,sum(x['hours'] for x in d['dry_counterparts'] if x['dry_approach_K']==a and x['status'].startswith('IN_CURVE')),sum(x['hours'] for x in d['dry_counterparts'] if x['dry_approach_K']==a and x['status']=='UNSUPPORTED')] for a in [3.,5.,7.]])
    cross_sample=[s for s in x['rows'] if s['bin']==3 and s['status'].startswith('IN_CURVE')]
    cross_table=table(['Cycles','3 K dry approach','5 K dry approach','7 K dry approach'],
        [[cy]+[f"{next(s['crossover_USD_m3'] for s in cross_sample if s['cycles']==cy and s['dry_approach_K']==a):.2f}" for a in [3.,5.,7.]] for cy in [2,4,6]])
    lookup=table(['Chip(C)','Total(W)','Chip(C)','Total(W)'],[[l['points'][i]['T_chip_C'],l['points'][i]['P_total_W'],l['points'][i+5]['T_chip_C'],l['points'][i+5]['P_total_W']] for i in range(5)])
    max_fws=max(x['coupled_optimum']['T_fws_C'] for x in bins);max_gpu=max(x['coupled_optimum']['T_gpu_inlet_water_C'] for x in bins)
    margin=table(['FWS class','Upper limit(C)','Margin at max FWS(K)'],[[x,x[1:],f"{float(x[1:])-max_fws:.2f}"] for x in ['W17','W27','W32','W40','W45']])
    total_hours=sum(x['hours'] for x in bins);extra=sum(x['hours_above_validation'] for x in bins)
    body=f'''# MIZAN | One-CDU data-centre extension
8 Sep 2026 | Evidence reviewed 7 Sep 2026 | Internal engineering decision report

**Decision [Judgment]: retain the chemistry constraint service; do not pitch an ITD-driven hybrid benefit from this model.** Chemistry limits cycles inside the chiller domain, but the registered study finds no case where it lowers the maximum deliverable facility-water temperature. The original mandatory condenser-to-GPU-water sign assertion fails because the evaporator supply is controlled independently. This is a negative result for the proposed warmer-silicon-versus-colder-condenser thesis, not a reason to remove chemistry from MIZAN.

{statuses}

**Scope [Estimate]:** one equivalent CDU extends the existing tower/chiller/chemistry model to GPU inlet water. The {r['Q_IT_kW']/1000:.1f}MW liquid load is fixed; equivalent nominal capacity is {r['Q_nominal_kW']/1000:.3f}MW. CDU approach is5K, with3/5/7K diagnostic sensitivity. The inherited model scales the named chiller fit to plant duty; it does not select a physical machine bank. No junction, DVFS, ITD device or CDU allocation model is built. This is a steady-state grid study, not field validation or a controller release.

**Independent value [Estimate]:** optimising FWS within the existing curve yields USD{f(inc['cost']['annual_difference'])}/year incremental cooling-plant cost reduction against the same controller held at7C. That is not ITD savings. Actual ITD savings and chip-optimum shortfall remain undefined without a measured same-part/workload chip-to-water relation.

**Preservation [Verified, local]:** original V2 and V5-water gates remain failed. The protected files and existing user changes are preserved. The final verification record accompanies the package.

<!-- pagebreak -->
# The thermal boundary changes the thesis

**Verified source boundary:** ASHRAE W classes specify facility supply water, not GPU inlet water after the CDU. The actual GPU/OEM liquid-inlet limit and site W class were not supplied; the following margins are reference-class calculations, not equipment certification. {cite('ashrae')} and {cite('ashrae_ch20')}.

{margin}

**Governing closure [Estimate]:** T_GPU,water = T_FWS + A_CDU. With equal stream heat-capacity rates Cdot, both terminal approaches equal A_CDU; Q_CDU = Cdot*(T_return - T_supply). Here Cdot = Q_IT/5K, so each water loop rises5K. The heat exchanger has positive terminal differences and equal heat transfer on both sides. Pump heat, heat leaks, pressure losses, variable UA and unequal flows are excluded assumptions that require CDU selection data.

**Chiller/tower [Verified formulation; estimated inputs]:** Q_cond = Q_IT + P_chiller, and T_CW,return = T_ECWT + Q_cond/(m_CW*c_p). Units: kW / [(kg/s)*(kJ/kg/K)] = K. The solver uses the existing Poppe integration and fill law to find the fan speed satisfying Me_required = Me_fill, then replays the point through the original outlet solver. {cite('eir')}.

**Cost boundary [Estimate]:** reported electricity is compressor plus tower-fan power. Pump electricity and IT electricity are outside the cost sum; these percentages are not whole-facility energy reductions.

**Why H1a fails [Judgment from balance]:** at fixed FWS and CDU approach, dT_GPU,water/dT_ECWT=0 while the chiller can meet duty. Condenser warming changes compressor power and capacity. COP alone does not determine the controlled evaporator outlet temperature. An overload/trip is infeasibility, not a licensed extrapolation to warmer GPU water.

**Equipment bound [Verified]:** the source York curve is valid only for FWS{r['limits']['FWS_C'][0]:.2f} to{r['limits']['FWS_C'][1]:.2f}C, ECWT{r['limits']['ECWT_C'][0]:.2f} to{r['limits']['ECWT_C'][1]:.2f}C, and PLR{r['limits']['PLR'][0]:.2f} to{r['limits']['PLR'][1]:.2f}. All three bounds are enforced in the new wrapper, with raw PLR and a fixed nameplate. The legacy normalisation at the reference point is preserved as a model convention, not independently validated manufacturer performance. {cite('chiller')}.

<!-- pagebreak -->
# Coupled sweep and annual economics

**Estimate:** {total_hours:,} weather hours are represented by{len(bins)} equal-hour wet-bulb bins from the repository TMY file. Each row is a bin-centroid operating point. The FWS grid contains the two curve endpoints and7C; ECWT has nine equally spaced source-domain values plus32C. Cycles are2 through10; pH uses the registered grid. Fan speed is solved continuously within30-100%. A grid minimum is not a continuous global optimum.

{bybin}

The tower uses each bin's mean dry bulb and relative humidity. The WB column is the mean hourly wet bulb, which can differ from wet bulb recomputed from those two means.

**Baseline definition [Estimate]:** fixed4cycles, pH7.8 and FWS7C, choosing the feasible sampled ECWT nearest32C. The fixed-FWS counterfactual optimises the other variables over the same feasible grid. The coupled optimum also selects FWS. These counterfactuals differ from the legacy fan-grid study; the new totals are new scenario results, not revisions of its published gates.

{summary}

**Annual water [Estimate]:** coupled-versus-baseline reduction is {ann['water']['ratio_of_totals_pct']:.2f}% as ratio of totals and {ann['water']['mean_of_ratios_pct']:.2f}% as mean of hourly ratios; the annual difference is {f(ann['water']['annual_difference'])}m3. All{total_hours:,} represented hours must have both policies before totals are emitted.

**Aggregation [Derived]:** totals saving =100*sum[h_i*(B_i-O_i)]/sum[h_i*B_i]; mean-of-ratios =sum[h_i*100*(B_i-O_i)/B_i]/sum[h_i]. Absolute costs use the requested repository tariff dictionary, including electricity USD{r['tariffs']['elec_per_kwh']:.3f}/kWh and legacy water USD{r['tariffs']['water_per_m3']:.2f}/m3. Site tariff eligibility is not established.

**Validation boundary [Verified local inputs / judgment]:** {extra:,} underlying hours exceed the legacy wet-bulb validation maximum. Binning is an annual approximation and does not prove feasibility at every original hour. No field data validates this CDU extension, its makeup chemistry or its annual savings.

<!-- pagebreak -->
# What the ITD lookup does and does not identify

**Verified source scope:** Crop et al. study production Intel Xeons. Figure2 is average CPU temperature against power at fixed frequency for a specific Xeon8480/povray experiment, with derived components. It is not a GPU curve or a coolant curve. Figure5 uses per-part models and Figure6 is a simulated facility case; the paper's facility-saving range is not a measured MIZAN result. {cite('itd')}.

{lookup}

**Plot extraction [Verified method]:** numbers above come from the PDF vector paths, calibrated against the printed grid/tick values. The plotted minimum sample is {l['minimum_sample']['T_chip_C']:.1f}C and {l['minimum_sample']['P_total_W']:.1f}W. Display precision is not raw-data measurement precision. Piecewise-linear lookup is limited to the plotted range and refuses extrapolation. The curve is retained for internal research; its CC BY-NC-ND licence does not establish commercial deployment permission.

**H3 [Not identifiable]:** the coupled loop's maximum sampled water temperature is {max_gpu:.2f}C at the assumed5K CDU approach. Subtracting that from the plotted chip minimum gives {l['minimum_sample']['T_chip_C']-max_gpu:.2f}K, but this is only the chip-to-water rise REQUIRED to make that source part reach its plotted minimum. It is not the gap between its actual and optimal chip temperature. Actual chip temperature has not been modelled or measured here.

**H4 [Not identifiable]:** there is no defensible annual cost of reaching the ITD optimum until the required FWS target is identifiable. The companion JSON reports the cycles change and annual cost change caused by the independent allowed FWS reset in every bin. Fixed IT load intentionally prevents booking temperature-dependent CPU energy as a saving.

**Required evidence [Judgment]:** a measured table for the same device/part, workload and performance point, containing chip temperature, inlet water temperature, flow and power; an OEM liquid-inlet envelope; and the actual CDU approach/flow rating. An empirical lookup can then connect the boundaries without introducing a semiconductor device model. A generic thermal resistance or another Xeon part's optimum would not close this gap.

<!-- pagebreak -->
# Chemistry: source resolution is not defect closure

**Verified primary evidence:** the2022 paper Table1 reports sulfate566mg/L; that number was correctly transcribed. The2020 engineer-authored pilot account reports300mg/L and also differs on calcium, sodium, chloride and bicarbonate. Neither source reconciles the analyses. The primary PDF was already in the repository. {cite('water2022')} and {cite('water2020')}.

{wr}

**Derived diagnostics:** charge error above uses the repository denominator (cation+anion)/2; the common sum denominator would halve each percentage. Gypsum cycles are continuous roots of the existing operating-SI limit at40C, a chemistry-only sensitivity, not new field ceilings. The controller's sodium-balanced analysis is an explicit assumption. Missing silica remains unmeasured, not evidence of silica-free water.

**Method issue [Verified / inference]:** Table2 assigns ASTM D1125 to both conductivity and TDS; D1125 measures conductivity/resistivity. Thus a gravimetric TDS reference is not established. The ion-sum discrepancy is a real consistency concern, but it does not identify which ion is wrong or prove that sulfate must be300. Paired laboratory data and clarification of TDS methodology are required. {cite('astm')}.

**Mathematical correction [Derived]:** charge balance is linear: sum[z_i*mean(c_i)] = mean(sum[z_i*c_i]). Equal-weight averages of matched electroneutral samples remain electroneutral. Different sample sets, missingness, weights or analytical errors could explain the discrepancy; ordinary averaging alone does not. Defect17 remains open and its strict xfail is preserved.

**Thermal caution [Estimate]:** in {d['skin_gypsum_below_basin_count']} of {len(d['skin_sensitivity'])} accepted thermal states, skin gypsum SI is lower than basin SI. The inherited gypsum temperature relation is not globally retrograde. The clean3K versus inherited8K chemistry-only sensitivity changes feasible status for {d['skin_sensitivity_feasibility_changes']} states. The new study preserves legacy skin evaluation and reports this limitation; it does not certify that skin is always the worst point in the entire loop.

**Interpretation of H2 [Judgment]:** a cycles ceiling can bind while the chiller has spare capacity. That supports a chemistry constraint service. It does not establish that chemistry sets the maximum IT-water target or creates an antagonistic ITD trade-off. Those are different directions in the control space.

<!-- pagebreak -->
# Dry versus evaporative: price the valid comparison

**Verified tariff / conditional applicability:** Marafiq's industrial table lists process water at SAR8.04/m3 and industrial wastewater at SAR3.64/m3. At3.75SAR/USD these are separate makeup and discharge charges. The sum is a conditional value of avoided blowdown; charging wastewater treatment on evaporation overstates evaporative cost. Actual reclaimed-water service, discharge route, VAT and electricity classification still need the site's contracts. {cite('water_tariff')} and {cite('fx')}.

**Derived cost equation:** C_water=p_M*M+p_B*B, where M and B are makeup and blowdown in m3/h. For the dry comparison use p_E*(P_dry-P_wet)=p_M*M+p_B*B+C_chem when other terms are equal. This gives a break-even power penalty without inventing dry equipment performance. The JSON provides that budget by weather bin and the in-range makeup-price crossover.

{tariff}

**Estimate:** the above table reprices the same saved policies; it does not reoptimise them under a new tariff. Legacy requested prices remain in the main study. A coastal-outfall case with no wastewater bill is conditional and does not imply a discharge permit.

{dry}

**Domain failure [Verified bound / estimate]:** dry ECWT is assumed T_drybulb plus3/5/7K approach. Any point beyond the named chiller's range is rejected, including the hot Gulf regime needed to establish annual ROI. In-range counterparts assume a dry fan power equal to the reference tower fan nameplate purely for sensitivity. No full-year dry/evaporative verdict, annual ROI or universal16K priced penalty is supported by this machine map.

**Cycles sensitivity [Estimate]:** the companion study covers every tested cycles count, with {sum(s['status'].startswith('IN_CURVE') for s in x['rows'])} supported combinations. Example below: makeup-price crossover in USD/m3 at dry bulb {bins[3]['T_db_C']:.1f}C, recomputed wet bulb {bins[3]['coupled_optimum']['T_wb_actual_C']:.1f}C and fixed FWS {bins[3]['coupled_optimum']['T_fws_C']:.2f}C. Discharge is separately priced at USD{x['discharge_USD_m3']:.3f}/m3. Wet fan/ECWT choice can change with price. Below each crossover a sampled wet policy costs less; above it the assumed dry system costs less.

{cross_table}

**Judgment:** compare these conditional crossover budgets with a supplier's dry/adiabatic map and actual water contract before claiming annual ROI.

<!-- pagebreak -->
# Prior art and the decision that remains

**Closest paper [Verified metadata; inaccessible body]:** Chen et al., Applied Energy424,128414, DOI10.1016/j.apenergy.2026.128414, is assigned to the December2026 issue. Publisher preview and metadata are accessible; full methods/results were not obtained through publisher, Elsevier metadata endpoint, author/repository searches or OpenAlex. Its full-text chemistry count is UNAVAILABLE, not zero. It remains a dependency before a novelty pitch. {cite('closest')}.

**Patent counter-evidence [Verified]:** ChemTreat US11780742B2 already discloses online chemical dosage control based on a saturation parameter calculated using heat-exchanger skin temperature. Claims1,3,19 and20 are directly relevant. Skin-based chemistry alone is not a surviving novelty claim. The combined species-specific surface constraint and mechanical-energy optimisation is a candidate distinction requiring claim mapping; absence from a sampled corpus does not prove novelty or freedom to operate. {cite('patent')}.

**Corpus scope [Verified local scan]:** all eight supplied PDFs returned zero matches for the original exact CHEM regex under both layout and plain extraction, the latter including rotated text. The regex contains15 alternatives, described as nine term families in the legacy narrative. The legacy18-document total includes version repeats and background/device documents. Count it as sampled files/versions, not18 independent control studies or a census. Text layers, hyphenation and vocabulary limit this result; the closest paper remains unread. Existing prior-art documents are not rewritten.

**Already-covered work [Verified scope]:** CDU allocation and flow/supply co-design appear in the supplied co-design paper. The supplied twin paper distinguishes unconstrained from constrained cooling savings. Neither headline should be recycled as a new MIZAN benefit. {cite('codesign')} and {cite('dc_twin')}.

{table(['Option [Judgment]','Quantified basis','Decision / missing evidence'],[
 ['Existing-MIZAN constraint service',f"H2 cycles witnesses in{r['verdicts']['H2_cycles']['weather_bins_with_witness']}/{len(bins)} bins",'Preferred near-term hypothesis; needs site chemistry and shadow data'],
 ['One-CDU cool-water extension',f"FWS increment USD{f(inc['cost']['annual_difference'])}/yr, scenario only",'Keep as reproducible research; no ITD product claim'],
 ['Warm-water / dry-adiabatic study','Current hot-hour dry power unavailable','Obtain applicable machine/CDU maps and tariff contracts first']])}

**Verification handoff [Judgment]:** independently check the full Applied Energy manuscript, same-device temperature bridge, measured makeup analysis, corrosion/inhibitor programme, CDU ratings, site temperature/condensation limits, billing route, and dry equipment selection. Pump deltas, dynamics, redundancy, precipitation kinetics and hardware deployment are outside this model. Hardware demand is a small CPU-only steady-state sweep; no GPU training or simulation exceeding the stated laptop class is required.

**Reproduction [Verified local artifacts]:** the README gives all commands, including the cycles crossover. The first experiment failed the unchanged replay guard; its evidence is retained. The accepted run rejects {len(r['fault_injections'])} injected faults. A separate verifier passes {v['check_count']} checks, including extraction faults and replay of the original bad root. Maximum accepted forward error is {v['maximum_forward_replay_error_K']:.6f}K against the registered 0.001K. Source hashes, all candidates and both aggregation conventions accompany the results. Historical gate files are unchanged.
'''
    return presentation_spacing(body)

def render(md,out):
    fonts=Path('C:/Windows/Fonts')
    for name,file in [('Mizan','times.ttf'),('Mizan-Bold','timesbd.ttf'),('Mizan-Italic','timesi.ttf')]:
        pdfmetrics.registerFont(TTFont(name,str(fonts/file)))
    pdfmetrics.registerFontFamily('Mizan',normal='Mizan',bold='Mizan-Bold',italic='Mizan-Italic',boldItalic='Mizan-Bold')
    styles=getSampleStyleSheet()
    body=ParagraphStyle('B',fontName='Mizan',fontSize=10.5,leading=13.4,spaceAfter=8,textColor=colors.HexColor('#1b2933'))
    head=ParagraphStyle('H',parent=body,fontName='Mizan-Bold',fontSize=19,leading=23,spaceBefore=5,spaceAfter=13,textColor=colors.HexColor('#123747'))
    cell=ParagraphStyle('C',parent=body,fontSize=8.5,leading=10.5,spaceAfter=0)
    def rich(s):
        s=html.escape(s)
        s=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',lambda m:f'<link href="{m.group(2)}" color="#12627a">{m.group(1)}</link>',s)
        s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
        return s
    flow=[];lines=md.splitlines();i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line=='<!-- pagebreak -->':flow.append(PageBreak());i+=1;continue
        if line.startswith('# '):flow.append(Paragraph(rich(line[2:]),head));i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                vals=[v.strip() for v in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[-: ]+',v) for v in vals):rows.append(vals)
                i+=1
            n=len(rows[0]);width=A4[0]-88
            weights=([1.6,1.,3.2] if n==3 else [1.8,1,1,1] if n==4 else [1.9,1,1,1,1] if n==5 else [1]*n)
            widths=[width*w/sum(weights) for w in weights]
            data=[[Paragraph(rich(v),cell) for v in row] for row in rows]
            t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
            t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5eff2')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),0.8,colors.HexColor('#326070')),('LINEBELOW',(0,1),(-1,-1),0.25,colors.HexColor('#cfd9dd')),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
            flow.extend([t,Spacer(1,10)]);continue
        para=[line];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','<!--')):
            para.append(lines[i].strip());i+=1
        flow.append(Paragraph(rich(' '.join(para)),body))
    def footer(canvas,doc):
        canvas.setStrokeColor(colors.HexColor('#b5c7cf'));canvas.line(44,39,A4[0]-44,39)
        canvas.setFont('Mizan',8);canvas.setFillColor(colors.HexColor('#506875'))
        canvas.drawString(44,26,'FURQAN / MIZAN  |  Internal research  |  8 Sep 2026')
        canvas.drawRightString(A4[0]-44,26,str(doc.page))
    doc=SimpleDocTemplate(str(out),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=44,bottomMargin=52,title='MIZAN: One-CDU Data-Centre Extension',author='Furqan / MIZAN',pageCompression=1)
    doc.build(flow,onFirstPage=footer,onLaterPages=footer)

if __name__=='__main__':
    r=json.loads(RUN.read_text());d=json.loads(DIAG.read_text());l=json.loads(LOOKUP.read_text())
    x=json.loads(CROSS.read_text());v=json.loads(VERIFY.read_text())
    text=build_text(r,d,l,x,v)
    (ROOT/'research/report-source.md').write_text(text,encoding='utf-8')
    (ROOT/'docs/cdu_hybrid_research.md').write_text(text,encoding='utf-8')
    (ROOT/'research/claim-source-ledger.json').write_text(json.dumps(SOURCES,indent=2),encoding='utf-8')
    render(text,ROOT/'output/pdf/MIZAN_CDU_Hybrid_Research.pdf')
    print('Created report source, repository Markdown, source ledger and PDF.')
