"""
FURQAN / MIZAN :: the Cycle Ceiling Report.

The product, at its smallest honest size.

A plant sends a water analysis and says what it currently runs at. This
returns a single page saying how many cycles of concentration that water can
actually support, which mineral stops it, what the incumbent index would have
told them instead, and what is missing from their analysis.

It controls nothing. There is no actuator, no setpoint written, no safety
case, and nothing to integrate. That is deliberate: it is the smallest thing
that is useful to a stranger, and the only thing that can be sold before a
pilot exists.

WHY THIS IS THE PRODUCT AND NOT THE OPTIMISER

    Qatar Cool run treated effluent at a maximum of 3 cycles and roughly 9 on
    polished water. The Aramco pilot ran groundwater at 2.0. Those plants are
    not badly optimised -- they are running on caution, because nothing tells
    them where the limit is. The gap between 3 and the true ceiling is the
    sale, and computing it needs speciation that no incumbent controller does.

WHAT IT REFUSES TO DO

    It will not report a ceiling as a single number when the analysis does not
    support one. If silica is unmeasured, the ceiling is reported as a RANGE
    across the plausible silica band, with the crossover marked -- because on
    this class of water that one missing number decides which mineral binds.

Run:  python scripts/ceiling_report.py [--demo] [--out PATH]
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import chemistry as chem          # noqa: E402
import controller as ctl          # noqa: E402
import recycle as rcy             # noqa: E402
import sidestream as ss           # noqa: E402

SILICA_BAND = (5.0, 45.0)         # plausible makeup range when unmeasured
SILICA_STEPS = 17


def _ceiling(water, T_hot, T_cold, pH, programme=None):
    lim = chem.limits_for_programme(programme)
    c = ss.ceiling_with(water, T_hot, T_cold, pH=pH, limits=lim)
    return c


def analyse(water, cycles_now, T_hot, T_cold, pH, tariffs, evap_kg_s,
            m_w_kg_s, programme=None, silica_measured=True,
            diurnal_amplitude_k=5.0):
    """Everything the report needs, as data. No formatting here."""
    out = {"water": water.name, "cycles_now": cycles_now,
           "T_hot": T_hot, "T_cold": T_cold, "pH": pH,
           "silica_measured": bool(silica_measured),
           "programme": programme}

    ceiling, binding = _ceiling(water, T_hot, T_cold, pH, programme)
    out["ceiling"] = ceiling

    # DEFECT 50, and it is the most embarrassing one in the register: THE FIX
    # FOR DEFECT 37 REPRODUCED DEFECT 37.
    #
    # Defect 37 was "the diurnal silica margin is computed and enforced by
    # nothing", and it was already the fourth instance of that shape. The fix
    # added `chemistry.limits_with_diurnal_margin()`. A guard written today to
    # stop this happening an eighth time found that function defined in
    # chemistry.py, exercised in tests/test_defect_regressions.py, and called
    # by NOTHING THAT MAKES A DECISION.
    #
    # The physics has not changed since defect 37 and it is not optional:
    # amorphous silica is prograde, so the ceiling falls as the basin cools
    # overnight, on a twelve-hour period, while the concentration can only
    # follow on half a week. A setpoint placed at the mean-temperature limit
    # is exceeded every night and no blowdown policy can prevent it.
    #
    # So the margin is APPLIED, and its cost is DISCLOSED. Reporting it as an
    # option would be the same mistake a third time.
    lim_marg = chem.limits_with_diurnal_margin(
        T_mean_c=T_cold, T_amplitude_k=diurnal_amplitude_k,
        programme=programme)
    c_marg, b_marg = ss.ceiling_with(water, T_hot, T_cold, pH=pH,
                                     limits=lim_marg)
    out["diurnal"] = {
        "amplitude_k": float(diurnal_amplitude_k),
        "T_mean_c": float(T_cold),
        "ceiling_no_margin": ceiling,
        "ceiling_with_margin": c_marg,
        "cost_cycles": ceiling - c_marg,
        "binding_with_margin": b_marg,
        "why": ("amorphous silica is prograde, so its solubility falls as the "
                "basin cools overnight. The limit moves on a twelve-hour "
                "period; the concentration can only follow on half a week."),
    }
    # the RECOMMENDED ceiling carries the margin
    out["ceiling"] = c_marg
    out["ceiling_no_diurnal_margin"] = ceiling
    ceiling, binding = c_marg, b_marg

    # DEFECT 49. `discharge.binding_ceiling()` computes scaling-vs-discharge
    # and returns whichever is lower, it is covered by its own test file, and
    # NOTHING OUTSIDE THOSE TESTS CALLED IT. Seventh instance of
    # computed-but-not-enforced (11, 26, 31, 37, 43, 45), and the one that
    # most directly misleads a customer: this report has been answering
    # "4.52 cycles" while a tested discharge ceiling of 3.33 sat unused. You
    # cannot recommend an operating point whose blowdown is illegal.
    #
    # REPORTED, NOT IMPOSED, and the distinction is the whole of the care
    # needed here. RCER-2015 binds Jubail and Yanbu. The water this report
    # defaults to is a RIYADH refinery, which is in neither, so the table may
    # not apply to it at all. Asserting an illegal operating point for a site
    # outside the jurisdiction would be its own defect.
    try:
        import discharge as dis
        out["discharge"] = {}
        for basis in ("max", "monthly_avg"):
            b = dis.binding_ceiling(water, T_hot, T_cold, pH=pH, basis=basis,
                                    limits=chem.limits_for_programme(programme))
            out["discharge"][basis] = {
                "cycles": b["cycles"], "binding": b["binding"],
                "parameter": b["parameter"],
                "discharge_cycles": b["discharge_cycles"],
                "scaling_cycles": b["scaling_cycles"],
            }
        out["discharge"]["jurisdiction"] = dis.JURISDICTION_NOTE
        out["discharge"]["applies_here"] = None   # unknown for this site
    except Exception as exc:                      # never fail the report on it
        out["discharge"] = {"error": str(exc)}
    out["binding"] = binding

    # what the incumbent index would say, at the same conditions
    out["lsi_now"] = chem.langelier_index(water.concentrate(cycles_now), T_hot,
                                          pH=pH)
    out["lsi_at_ceiling"] = chem.langelier_index(
        water.concentrate(max(ceiling, 1.01)), T_hot, pH=pH)
    sat = chem.saturation_state_split(water.concentrate(max(ceiling, 1.01)),
                                      T_hot, T_cold, pH_hot=pH, pH_cold=pH)
    out["si_at_ceiling"] = {k: v for k, v in sat.items()
                            if k.startswith("SI_") and not k.endswith("_at")}

    # the analysis itself
    checks = chem.validate_analysis(water, silica_declared=silica_measured,
                                    phosphate_declared=water.PO4 > 0)
    out["checks"] = {k: {"ok": bool(v[0]), "detail": v[1]}
                     for k, v in checks.items()}
    out["charge_balance_pct"] = water.charge_balance_pct()

    # DEFECT 39. If the analysis failed its own charge-balance check, say what
    # that costs the ceiling instead of leaving the reader to wonder. The
    # balance is closed both ways and the spread reported; see
    # sidestream.charge_closure_bracket().
    if not out["checks"]["charge_balance"]["ok"]:
        out["charge_closure"] = ss.charge_closure_bracket(
            water, T_hot, T_cold, pH=pH, limits=chem.limits_for_programme(programme))

    # phosphate requirement
    verdict, si_tcp = chem.phosphate_screen(water.concentrate(max(ceiling, 1.01)),
                                            T_hot, pH=pH)
    out["phosphate"] = {"verdict": verdict, "SI_tcp": si_tcp,
                        "measured": water.PO4 > 0, "PO4_mg_l": water.PO4}

    # water and money, at now vs at the ceiling
    rows = []
    for label, cy in (("current", cycles_now), ("ceiling", ceiling)):
        wb = ctl.water_balance(evap_kg_s, m_w_kg_s, max(cy, 1.001))
        mk = wb["makeup"] * 3.6
        bd = wb["blowdown"] * 3.6
        cost = ctl._water_cost_per_h(wb, tariffs)
        rows.append({"label": label, "cycles": cy, "makeup_m3_h": mk,
                     "blowdown_m3_h": bd, "water_cost_per_h": cost,
                     "water_cost_per_yr": cost * 8760.0})
    out["balance"] = rows
    out["saving_pct"] = (100.0 * (rows[0]["makeup_m3_h"] - rows[1]["makeup_m3_h"])
                         / rows[0]["makeup_m3_h"]) if rows[0]["makeup_m3_h"] else 0.0
    out["saving_per_yr"] = (rows[0]["water_cost_per_yr"]
                            - rows[1]["water_cost_per_yr"])
    out["max_possible_pct"] = rcy.max_possible_saving_pct(cycles_now)

    # What the controller may cost and still pay. NOT a price and not an
    # estimate -- a ceiling on one. We have no installed cost, and a second
    # sweep of the Wayback PDF collection found no published one either, so
    # the question is inverted the same way it already is for side-stream
    # treatment: not "what is the payback" but "quote us below this and the
    # economics close". See docs/chemistry_evidence.md S4.4.
    out["capex_ceiling"] = {
        str(int(y)): ss.controller_break_even_capex(out["saving_per_yr"], y)
        for y in (2.0, 3.0, 5.0)
    }

    # the silica sensitivity -- the honest part
    band = []
    lo, hi = SILICA_BAND
    for i in range(SILICA_STEPS):
        s = lo + (hi - lo) * i / (SILICA_STEPS - 1)
        w2 = chem.Water(name="probe", Na=water.Na, K=water.K, Ca=water.Ca,
                        Mg=water.Mg, Cl=water.Cl, SO4=water.SO4,
                        HCO3=water.HCO3, NO3=water.NO3, SiO2=s, PO4=water.PO4,
                        pH=water.pH, TDS=water.TDS)
        c, b = _ceiling(w2, T_hot, T_cold, pH, programme)
        band.append({"SiO2": s, "ceiling": c, "binding": b})
    out["silica_band"] = band
    flips = [b for b in band if b["binding"] == "SI_silica_am"]
    out["silica_crossover"] = flips[0]["SiO2"] if flips else None

    # if they want more than the ceiling gives, what does it take
    tgt = 20.0
    out["target_pct"] = tgt
    out["recovery_for_target"] = rcy.recovery_needed_for_saving(
        evap_kg_s, cycles_now, ceiling, tgt, m_w_kg_s)
    out["treatment"] = ss.survey(water, evap_kg_s, tariffs, T_hot, T_cold,
                                 baseline_cycles=cycles_now, pH=pH)
    for t in out["treatment"]:
        t["cost_check"] = ss.passes_cost_reality_check(
            t.get("break_even_per_m3") or 0.0)
    out["real_treatment_cost"] = ss.real_cost_per_m3()
    return out


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------
CSS = """
:root{--g:#F2F4F3;--s:#fff;--s2:#E8EDEB;--ink:#111A18;--ink2:#3D4B47;
--ink3:#6B7A75;--rule:#CBD6D1;--rule2:#E0E7E4;--acc:#1B6558;--accs:#DCEAE5;
--cop:#A4551F;--cops:#F4E5D8;--bad:#8E2F2C;--bads:#F6DFDD}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){
--g:#0C1211;--s:#141C1A;--s2:#1D2725;--ink:#E6EDEA;--ink2:#B3C1BC;
--ink3:#82938D;--rule:#2B3835;--rule2:#212C2A;--acc:#5FB9A5;--accs:#17302B;
--cop:#D98A4E;--cops:#33231A;--bad:#E28B86;--bads:#3A1F1E}}
:root[data-theme=dark]{--g:#0C1211;--s:#141C1A;--s2:#1D2725;--ink:#E6EDEA;
--ink2:#B3C1BC;--ink3:#82938D;--rule:#2B3835;--rule2:#212C2A;--acc:#5FB9A5;
--accs:#17302B;--cop:#D98A4E;--cops:#33231A;--bad:#E28B86;--bads:#3A1F1E}
*{box-sizing:border-box}
body{background:var(--g);color:var(--ink);margin:0;
font:15px/1.6 "IBM Plex Sans",-apple-system,Segoe UI,Roboto,sans-serif}
.wrap{max-width:880px;margin:0 auto;padding:56px 26px 80px}
h1,h2{font-family:Newsreader,Georgia,serif;font-weight:500;margin:0;
text-wrap:balance;letter-spacing:-.015em}
h1{font-size:2.6rem;line-height:1.05}
h2{font-size:1.45rem;line-height:1.2;margin-bottom:14px}
h3{font-size:.95rem;margin:0 0 6px}
p{margin:0}
.eyebrow{font-family:"IBM Plex Mono",monospace;font-size:.67rem;
letter-spacing:.14em;text-transform:uppercase;color:var(--ink3)}
.mono{font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums}
section{margin-top:44px;padding-top:26px;border-top:1px solid var(--rule)}
.hero{background:var(--s);border:1px solid var(--rule);border-left:4px solid var(--cop);
border-radius:3px;padding:26px 28px;margin-top:26px;display:flex;
flex-wrap:wrap;gap:28px;align-items:baseline}
.big{font-family:"IBM Plex Mono",monospace;font-size:3.1rem;font-weight:600;
line-height:1;color:var(--cop);font-variant-numeric:tabular-nums}
.tw{overflow-x:auto;border:1px solid var(--rule);border-radius:3px;background:var(--s)}
table{border-collapse:collapse;width:100%;min-width:480px;font-size:.87rem}
th,td{padding:9px 14px;text-align:left;border-bottom:1px solid var(--rule2)}
thead th{font-family:"IBM Plex Mono",monospace;font-size:.66rem;
letter-spacing:.09em;text-transform:uppercase;color:var(--ink3);font-weight:500}
tbody tr:last-child td{border-bottom:none}
td.n,th.n{text-align:right;font-family:"IBM Plex Mono",monospace;
font-variant-numeric:tabular-nums;white-space:nowrap}
.ok{color:var(--acc);font-weight:600}.no{color:var(--bad);font-weight:600}
.warn{color:var(--cop);font-weight:600}
.note{background:var(--s);border:1px solid var(--rule);border-radius:3px;
padding:17px 19px;margin-top:16px;display:flex;flex-direction:column;gap:7px}
.note.c{border-left:3px solid var(--cop)}.note.b{border-left:3px solid var(--bad)}
.note.a{border-left:3px solid var(--acc)}
ul{margin:6px 0 0;padding-left:19px;display:flex;flex-direction:column;gap:5px}
.band{display:flex;gap:2px;margin-top:14px;align-items:flex-end;height:96px}
.band i{flex:1;background:var(--acc);border-radius:2px 2px 0 0;position:relative;
min-height:3px;opacity:.85}
.band i.si{background:var(--cop)}
.bl{display:flex;justify-content:space-between;font-size:.7rem;
color:var(--ink3);margin-top:5px}
footer{margin-top:52px;padding-top:18px;border-top:1px solid var(--rule);
color:var(--ink3);font-size:.78rem}
"""


def _si_name(k):
    return {"SI_calcite": "calcite (CaCO3)", "SI_gypsum": "gypsum (CaSO4)",
            "SI_silica_am": "amorphous silica (SiO2)",
            "SI_tcp": "tricalcium phosphate"}.get(k, k)


def render(a, client="", site=""):
    e = html.escape
    d = dt.date.today().isoformat()
    bind = _si_name(a["binding"])
    sv = a["saving_pct"]
    rows = a["balance"]

    band = a["silica_band"]
    cmax = max(b["ceiling"] for b in band) or 1.0
    bars = "".join(
        f'<i class="{"si" if b["binding"]=="SI_silica_am" else ""}" '
        f'style="height:{100*b["ceiling"]/cmax:.1f}%" '
        f'title="{b["SiO2"]:.1f} mg/L -> {b["ceiling"]:.2f} cycles"></i>'
        for b in band)

    chk = "".join(
        f'<tr><td>{e(k.replace("_"," "))}</td>'
        f'<td class="{"ok" if v["ok"] else "no"}">{"PASS" if v["ok"] else "ATTENTION"}</td>'
        f'<td style="font-size:.82rem;color:var(--ink3)">{e(v["detail"][:150])}</td></tr>'
        for k, v in a["checks"].items())

    # DEFECT 39. An ATTENTION row in the table is not enough on its own: it
    # tells the reader something is wrong without telling them whether it
    # changes the answer. This row does.
    dsc = a.get("discharge") or {}
    if "max" in dsc and (dsc["max"]["binding"] == "DISCHARGE"
                         or dsc["monthly_avg"]["binding"] == "DISCHARGE"):
        mx, mo = dsc["max"], dsc["monthly_avg"]
        chk += (
            f'<tr><td>discharge permit, if RCER-2015 applies</td>'
            f'<td class="no">BINDS FIRST</td>'
            f'<td style="font-size:.82rem;color:var(--ink3)">'
            f'The blowdown at the scaling ceiling of '
            f'{mx["scaling_cycles"]:.2f} cycles would carry '
            f'{e(str(mx["parameter"]))} above the Royal Commission limit. On '
            f'the daily-maximum basis the permit binds at '
            f'<b>{mx["discharge_cycles"]:.2f} cycles</b>; on the monthly '
            f'average, at <b>{mo["discharge_cycles"]:.2f}</b>. '
            f'<b>This is reported, not imposed.</b> RCER-2015 binds Jubail '
            f'and Yanbu. If your outfall is elsewhere, or discharges to a '
            f'sewer or an irrigation system rather than to coastal water, a '
            f'different table applies and this row does not. Check your '
            f'permit before using either number.</td></tr>')

    cc = a.get("charge_closure")
    if cc:
        chk += (
            f'<tr><td>charge balance, closed both ways</td>'
            f'<td class="{"no" if cc["material"] else "ok"}">'
            f'{"MATERIAL" if cc["material"] else "IMMATERIAL"}</td>'
            f'<td style="font-size:.82rem;color:var(--ink3)">'
            f'The published cations do not account for the published anions, '
            f'by {abs(cc["cation_deficit_meq_kg"]):.2f} meq/kg. On a SECONDARY '
            f'effluent the likely missing species is ammonium '
            f'({cc["closes_with_NH4_mg_l_as_N"]:.0f} mg/L as N would close it), '
            f'which this model does not carry. Closing the balance with sodium '
            f'instead gives {cc["ceiling_Na_closure"]:.2f} cycles and closing it '
            f'by removing chloride gives {cc["ceiling_Cl_closure"]:.2f} — a spread '
            f'of {cc["spread_pct"]:.1f} %. The ceiling is set by '
            f'{e(_si_name(cc["binding_mineral"]))}, in whose ion product neither '
            f'sodium nor chloride appears. The analysis is incomplete; the '
            f'ceiling does not depend on how it is completed.</td></tr>')

    si = "".join(
        f'<tr><td>{e(_si_name(k))}</td><td class="n">{v:+.2f}</td>'
        f'<td>{"<span class=warn>binds</span>" if k==a["binding"] else ""}</td></tr>'
        for k, v in sorted(a["si_at_ceiling"].items(), key=lambda x: -x[1]))

    tre = "".join(
        f'<tr><td>{e(t["technology"].replace("_"," "))}</td>'
        f'<td class="n">{t["ceiling_after"]:.2f}</td>'
        f'<td class="n">{t["water_saved_vs_baseline_pct"]:+.1f} %</td>'
        f'<td class="n">${t["break_even_per_m3"]:.2f}</td>'
        f'<td class="n {"ok" if t["cost_check"]["pays"] else "no"}">'
        f'{"pays" if t["cost_check"]["pays"] else f"{t[chr(34)+chr(34)] if False else t["cost_check"]["shortfall_ratio"]:.0f}x short"}</td></tr>'
        for t in a["treatment"] if t["raises_ceiling"])

    xover = (f'{a["silica_crossover"]:.1f} mg/L' if a["silica_crossover"]
             else "not reached in band")
    rec = a["recovery_for_target"]
    rec_s = (f"{100*rec:.0f} % RO recovery on the blowdown"
             if rec else "NOT REACHABLE — see the ceiling note below")

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cycle Ceiling Report</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>{CSS}</style></head><body><div class="wrap">

<p class="eyebrow">Cycle Ceiling Report &middot; {e(d)}</p>
<h1>How far can this water be concentrated?</h1>
<p style="color:var(--ink2);margin-top:12px;max-width:60ch">
{e(client or "Prepared for the plant operator")}{" &middot; " + e(site) if site else ""}.
Analysis: <span class="mono">{e(a["water"])}</span>. Evaluated at a
{a["T_hot"]:.0f}&nbsp;&deg;C tube skin and a {a["T_cold"]:.0f}&nbsp;&deg;C basin,
pH {a["pH"]:.2f}.</p>

<div class="hero">
  <div><p class="eyebrow">Ceiling</p><p class="big">{a["ceiling"]:.1f}</p>
  <p style="font-size:.8rem;color:var(--ink3)">cycles of concentration</p></div>
  <div style="flex:1;min-width:230px">
    <h3>Stopped by {e(bind)}</h3>
    <p style="font-size:.88rem;color:var(--ink2)">You are running
    <b>{a["cycles_now"]:.1f}</b>. Moving to the ceiling cuts makeup water by
    <b>{sv:.1f} %</b> &mdash; about
    <b>${a["saving_per_yr"]:,.0f}/year</b> in water and discharge on this duty.</p>
  </div>
</div>

<section>
<p class="eyebrow">The part that decides everything</p>
<h2>What the standard index would have told you</h2>
<div class="tw"><table><thead><tr><th>Mineral</th><th class="n">Saturation index at the ceiling</th><th></th></tr></thead>
<tbody>{si}</tbody></table></div>
<div class="note c"><h3>Langelier index reads {a["lsi_at_ceiling"]:+.2f} at that point</h3>
<p style="font-size:.88rem;color:var(--ink2)">LSI is a calcium-carbonate index.
It is computed from pH, calcium and alkalinity, and it carries no information
about sulfate, silica or phosphate. Where the binding mineral is not calcite,
LSI cannot rank which species deposits first &mdash; it can read comfortable
while another mineral is already supersaturated.</p></div>
</section>

<section>
<p class="eyebrow">Water and money</p>
<h2>At your setpoint, and at the ceiling</h2>
<div class="tw"><table><thead><tr><th>Case</th><th class="n">Cycles</th>
<th class="n">Makeup m&sup3;/h</th><th class="n">Blowdown m&sup3;/h</th>
<th class="n">Water cost/year</th></tr></thead><tbody>
<tr><td>Current</td><td class="n">{rows[0]["cycles"]:.1f}</td>
<td class="n">{rows[0]["makeup_m3_h"]:.2f}</td><td class="n">{rows[0]["blowdown_m3_h"]:.2f}</td>
<td class="n">${rows[0]["water_cost_per_yr"]:,.0f}</td></tr>
<tr><td>At ceiling</td><td class="n">{rows[1]["cycles"]:.1f}</td>
<td class="n">{rows[1]["makeup_m3_h"]:.2f}</td><td class="n">{rows[1]["blowdown_m3_h"]:.2f}</td>
<td class="n">${rows[1]["water_cost_per_yr"]:,.0f}</td></tr>
</tbody></table></div>
<div class="note"><h3>The most you could ever save is {a["max_possible_pct"]:.1f} %</h3>
<p style="font-size:.88rem;color:var(--ink2)">At {a["cycles_now"]:.1f} cycles your
blowdown is {a["max_possible_pct"]:.1f} % of your makeup, and evaporation is the rest.
Evaporation is the heat rejection and cannot be recovered, so no measure of any
kind &mdash; control, treatment, recycle &mdash; can save more than that.
Reaching {a["target_pct"]:.0f} % would need {e(rec_s)}.</p></div>

<div class="note"><h3>What a controller may cost and still pay</h3>
<p style="font-size:.88rem;color:var(--ink2)">We will not quote you a payback,
because a payback needs an installed cost and we do not have one &mdash; nor,
as far as we can find, does anyone: a search of the Internet Archive's PDF
collection across fifteen cost, controls and retrofit queries returned nothing
citable on what a cooling-tower supervisory controller costs installed. So the
question is inverted. At <b>${a["saving_per_yr"]:,.0f}/year</b> on this duty,
the most the system may cost installed and still pay back is
<b>${a["capex_ceiling"]["2"]["break_even_capex_usd"]:,.0f}</b> over two years,
<b>${a["capex_ceiling"]["3"]["break_even_capex_usd"]:,.0f}</b> over three, and
<b>${a["capex_ceiling"]["5"]["break_even_capex_usd"]:,.0f}</b> over five.
<b>These are bounds, not prices.</b> They also assume the site actually reaches
the ceiling above, which is a SCALING ceiling and therefore an upper bound in
its own right &mdash; the operating ceiling is the minimum over several
constraints this model does not compute.</p></div>
</section>

<section>
<p class="eyebrow">What your analysis does not say</p>
<h2>Silica decides which mineral stops you</h2>
<div class="band">{bars}</div>
<div class="bl"><span>{SILICA_BAND[0]:.0f} mg/L SiO&#8322;</span>
<span>crossover to silica-bound at {e(xover)}</span>
<span>{SILICA_BAND[1]:.0f} mg/L</span></div>
<p style="font-size:.88rem;color:var(--ink2);margin-top:12px">Each bar is the
ceiling this water supports at that makeup silica. Green bars are limited by a
carbonate or sulfate mineral; copper bars are limited by amorphous silica,
which is <b>not pH-sensitive</b> &mdash; acid cannot buy cycles against it, and it
deposits at the <b>coldest</b> point in the loop, not the hottest.</p>
<div class="tw" style="margin-top:16px"><table><thead><tr><th>Check on the analysis</th>
<th>Result</th><th>Detail</th></tr></thead><tbody>{chk}</tbody></table></div>
</section>

<section>
<p class="eyebrow">Treatment programme</p>
<h2>Calcium phosphate</h2>
<div class="note {'c' if 'REQUIRED' in a['phosphate']['verdict'] else 'a'}">
<h3>SI {a["phosphate"]["SI_tcp"]:+.2f} &mdash; {e(a["phosphate"]["verdict"][:120])}</h3>
<p style="font-size:.88rem;color:var(--ink2)">Phosphate
{"is measured at " + f"{a['phosphate']['PO4_mg_l']:.1f} mg/L" if a["phosphate"]["measured"] else "is NOT in this analysis"}.
Calcium phosphate is kinetically inhibited &mdash; it tolerates far more
supersaturation than carbonate before it deposits &mdash; so what matters is not
the index alone but which inhibitor programme is dosed.</p></div>
{"<h2 style='margin-top:26px'>If you want to go past the ceiling</h2><div class='tw'><table><thead><tr><th>Side-stream treatment</th><th class='n'>New ceiling</th><th class='n'>Water saved</th><th class='n'>Break-even</th><th class='n'>Verdict</th></tr></thead><tbody>" + tre + "</tbody></table></div><p style='font-size:.82rem;color:var(--ink3);margin-top:10px'><b>None of these pay at your water price.</b> Break-even is what the saved water is worth per cubic metre treated. A costed engineering study of a precipitation-softening train (DiFilippo, Sylvan Source, Oct 2023 - 1 MGD, $25.4 M installed, $2.79 M/yr in chemicals) puts the real cost at <b>$2.02/m&sup3; in chemicals alone</b> and $2.94/m&sup3; with capital over twenty years. Side-stream treatment pays where <b>discharge is prohibited</b> and the alternative is zero liquid discharge - a regulatory driver, not a water-price one.</p>" if tre else ""}
</section>

<footer>
<p>Computed by first-principles aqueous speciation &mdash; ion association with
Davies activity coefficients, per-mineral evaluation at the temperature each
mineral actually binds at. Benchmarked against PHREEQC 3.9.0 and against the
US DOE pilot study DE-NT0006550.</p>
<p style="margin-top:8px">This is a diagnostic. It writes no setpoint and
controls nothing. Figures depend on the analysis supplied; where a species is
unmeasured that is stated rather than assumed.</p>
</footer>
</div></body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "results" / "ceiling_report.html"))
    ap.add_argument("--json", default=None)
    ap.add_argument("--cycles-now", type=float, default=3.0)
    ap.add_argument("--programme", default=None)
    ap.add_argument("--assumed-water", action="store_true",
                    help="run on rc.TSE with the imported 26.8 mg/L silica "
                         "instead of the measured 18 mg/L analysis")
    args = ap.parse_args()

    import run_controller as rc
    # DEFAULT IS THE MEASURED WATER. Until 11 Sep 2026 the worked example ran
    # on `rc.TSE`, whose silica of 26.8 mg/L is imported from Riyadh BRACKISH
    # GROUNDWATER -- a different water. A measured Saudi TSE make-up analysis
    # now exists (AlMajnouni & Jaffer, NACE Paper 577, Table 1: Riyadh
    # Refinery, SiO2 18 mg/L, PO4 1.0, ion sum closing to +1.2 % of TDS), and
    # a worked example about a cited water is worth more than one about a
    # plausible one. `--assumed-water` restores the old behaviour for the
    # sensitivity study that needs it.
    water = chem.ARAMCO_RIYADH_REFINERY_TSE if not args.assumed_water else rc.TSE
    silica_measured = not args.assumed_water
    a = analyse(water, cycles_now=args.cycles_now, T_hot=45.0, T_cold=32.0,
                pH=8.25, tariffs=rc.TARIFFS, evap_kg_s=4.2, m_w_kg_s=478.0,
                programme=args.programme,
                silica_measured=silica_measured)
    out = pathlib.Path(args.out)
    out.parent.mkdir(exist_ok=True)
    label = ("Worked example — Saudi refinery cooling tower"
             if silica_measured else "Worked example — Gulf district cooling")
    site = ("secondary treated sewage effluent makeup, measured analysis "
            "(NACE Paper 577 Table 1)" if silica_measured
            else "treated sewage effluent makeup, silica assumed")
    out.write_text(render(a, client=label, site=site),
                   encoding="utf-8")
    failed = [k for k, v in a["checks"].items() if not v["ok"]]
    if failed:
        # DEFECT 39. The console line is what gets pasted into a deck. It does
        # not get to be more confident than the analysis behind it.
        print(f"ANALYSIS CHECK FAILED: {', '.join(failed)}"
              " -- see the report for what it costs")
    print(f"ceiling      : {a['ceiling']:.2f} cycles, bound by {a['binding']}"
          f"  (carries the diurnal silica margin)")
    dn = a["diurnal"]
    if dn["cost_cycles"] > 0.005:
        print(f"  diurnal    : {dn['ceiling_no_margin']:.2f} at mean basin "
              f"temperature, {dn['ceiling_with_margin']:.2f} with the "
              f"+/-{dn['amplitude_k']:.0f} K overnight swing -- costs "
              f"{dn['cost_cycles']:.2f} cycles")
    else:
        print(f"  diurnal    : margin applied and costs nothing here, because "
              f"{a['binding']} binds before silica does. It is enforced "
              f"anyway -- on a higher-silica makeup it is the constraint.")
    cc = a.get("charge_closure")
    if cc:
        print(f"  closure    : {cc['ceiling_Cl_closure']:.2f} to "
              f"{cc['ceiling_Na_closure']:.2f} cycles depending on which ion "
              f"closes the balance -- "
              f"{'MATERIAL' if cc['material'] else 'immaterial'} "
              f"({cc['spread_pct']:.1f} %)")
    print(f"running at   : {a['cycles_now']:.1f}  ->  saving {a['saving_pct']:.1f} %")
    print(f"hard ceiling : {a['max_possible_pct']:.1f} % (1/C at the current setpoint)")
    print(f"saving       : ${a['saving_per_yr']:,.0f}/yr of water at this duty")
    cx = a["capex_ceiling"]["3"]
    print(f"capex ceiling: ${cx['break_even_capex_usd']:,.0f} installed for a "
          f"3-year payback (a BOUND, not a price)")
    dsc = a.get("discharge") or {}
    if "max" in dsc:
        mx, mo = dsc["max"], dsc["monthly_avg"]
        if mx["binding"] == "DISCHARGE" or mo["binding"] == "DISCHARGE":
            print(f"DISCHARGE    : {mx['discharge_cycles']:.2f} cycles on the "
                  f"daily-max basis, {mo['discharge_cycles']:.2f} on the "
                  f"monthly average, bound by {mx['parameter']}")
            print(f"             : IF RCER-2015 applies to this site. It binds "
                  f"Jubail and Yanbu; check before using it.")
    print(f"silica xover : {a['silica_crossover']}")
    print(f"written      -> {out}")
    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(a, indent=2, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
