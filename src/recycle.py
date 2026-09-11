"""
FURQAN / MIZAN :: blowdown recycle, and the hard ceiling on any water saving.

THE RESULT THAT MATTERS IS THE ONE-LINE ONE.

A cooling tower loses water two ways: evaporation, which is the job, and
blowdown, which is the waste. No measure of any kind can save more than the
blowdown, because evaporation is what rejects the heat. So for a plant
currently running at C0 cycles:

    maximum possible makeup-water saving = 1 / C0

    C0 = 2  ->  50.0 %        C0 = 5  ->  20.0 %
    C0 = 3  ->  33.3 %        C0 = 6  ->  16.7 %
    C0 = 4  ->  25.0 %        C0 = 8  ->  12.5 %

That is arithmetic, not a model, and it settles a question this package kept
asking in more complicated ways. **A 20 % water saving is only available at
all if the plant currently runs at five cycles or fewer**, and a plant already
at six cannot reach it by any means -- not better control, not treatment, not
recycle, not a combination. The pre-registered V5 gate asked for 15 % against
a 4-cycle baseline, where the ceiling is 25 %; it was asking the controller to
capture 60 % of everything physically available. That was always a hard ask
and nobody had written down why.

WHAT RECYCLE DOES

The blowdown is treated and most of it comes back as makeup. Topology, from
the electrocoagulation literature:

    tower blowdown -> EC (Al or Mg electrodes) -> clarify -> RO -> permeate
    back to the tower;  concentrate to sewer or ZLD

Steady salt balance on the tower, with permeate concentration taken as zero
and drift D kept explicit:

    M_fresh * c_m  =  (B + D) * c_c           salt in = salt out
    M_fresh        =  E + D + B*(1 - r)       water in = water out
    C              =  c_c / c_m               cycles, the chemistry limit

Eliminating c_c and solving for the blowdown that holds the tower at C:

    B = (E + D*(1 - C)) / (C - 1 + r)

    M_fresh = E + D + B*(1 - r)

At r = 0 this reduces to the familiar M = E*C/(C-1), which is asserted in the
tests rather than assumed.

WHY IT IS THE STRONGEST WATER LEVER AVAILABLE

Recycle does not need the cycles to change. At a fixed 3 cycles -- the number
a Gulf TSE plant actually runs -- a recovery of r = 0.85 takes makeup from
1.500*E to 1.053*E, a **29.8 % saving with the conductivity setpoint left
exactly where the operator put it**. Raising cycles to 5 as well takes it to
31.3 %. Almost all of the benefit is the recycle, not the control.

That is an uncomfortable finding for a controller company and it is reported
here because it is true. The honest position is that Mizan's contribution to
a recycle scheme is not the water saving -- it is knowing what concentration
the loop may be run at without scaling, which is what sizes the RO and decides
whether the scheme works at all.

PARAMETERS AND THEIR BASIS

    EC silica removal      93.7 - 99.5 %   [C] EC literature, Al electrodes
    EC hardness removal    37.0 - 55.4 %   [C] same
    EC energy              0.18 - 3.05 kWh/m3
    RO recovery            50 - 85 %       [C]
    RO energy              1.5 - 6 kWh/m3
    brine silica ceiling   100 - 150 mg/L with antiscalant

    HONEST FLAG, carried from the source: the EC removals are reported from
    BATCH experiments. Continuous-flow flux and cake-layer behaviour on real
    tower blowdown is thin in the literature. Treat every removal fraction
    here as a parameter to be calibrated on a site, not as a constant.
"""

from __future__ import annotations

import chemistry as chem
from controller import DRIFT_FRACTION


# Ranges, not points. A single number here would be a false precision.
EC_BLOCK = {
    "SiO2_removal": (0.937, 0.995),      # [C]
    "hardness_removal": (0.370, 0.554),  # [C] Ca and Mg together
    "energy_kwh_per_m3": (0.18, 3.05),   # [C]
}
RO_BLOCK = {
    "recovery": (0.50, 0.85),            # [C]
    "energy_kwh_per_m3": (1.5, 6.0),     # [C]
    "brine_SiO2_max_mg_l": (100.0, 150.0),
}


def max_possible_saving_pct(cycles_now):
    """The hard ceiling on makeup-water saving, from any measure whatsoever.

    Evaporation cannot be recovered -- it is the heat rejection. So the most
    that can ever be saved is the blowdown, which is 1/C of the makeup.
    """
    if cycles_now <= 1.0:
        raise ValueError("cycles must exceed 1")
    return 100.0 / float(cycles_now)


def blowdown_for_cycles(evap_kg_s, cycles, recovery=0.0,
                        drift_fraction=DRIFT_FRACTION, m_w_kg_s=None):
    """Blowdown that holds the tower at `cycles`, with recycle recovery `r`.

    Returns (blowdown, drift, fresh_makeup) in kg/s.
    """
    if cycles <= 1.0:
        raise ValueError("cycles must exceed 1")
    r = float(recovery)
    if not 0.0 <= r < 1.0:
        raise ValueError("recovery must be in [0, 1)")
    D = 0.0 if m_w_kg_s is None else drift_fraction * float(m_w_kg_s)
    E = float(evap_kg_s)
    denom = cycles - 1.0 + r
    B = (E + D * (1.0 - cycles)) / denom
    B = max(B, 0.0)
    M_fresh = E + D + B * (1.0 - r)
    return B, D, M_fresh


def saving_vs_baseline_pct(evap_kg_s, cycles_now, cycles_new,
                           recovery=0.0, m_w_kg_s=None):
    """Fresh-makeup saving of (cycles_new, recovery) against (cycles_now, 0)."""
    _, _, m0 = blowdown_for_cycles(evap_kg_s, cycles_now, 0.0,
                                   m_w_kg_s=m_w_kg_s)
    _, _, m1 = blowdown_for_cycles(evap_kg_s, cycles_new, recovery,
                                   m_w_kg_s=m_w_kg_s)
    return 100.0 * (m0 - m1) / m0 if m0 > 0 else float("nan")


def recovery_needed_for_saving(evap_kg_s, cycles_now, cycles_new,
                               target_saving_pct, m_w_kg_s=None):
    """Smallest RO recovery that reaches `target_saving_pct`, or None.

    Returns None when the target exceeds the hard ceiling 1/C0 -- which is the
    answer the caller most needs, and is why this returns None rather than
    clipping or raising.
    """
    if target_saving_pct >= max_possible_saving_pct(cycles_now):
        return None
    lo, hi = 0.0, 0.999
    if saving_vs_baseline_pct(evap_kg_s, cycles_now, cycles_new, hi,
                              m_w_kg_s) < target_saving_pct:
        return None
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        s = saving_vs_baseline_pct(evap_kg_s, cycles_now, cycles_new, mid,
                                   m_w_kg_s)
        lo, hi = (lo, mid) if s >= target_saving_pct else (mid, hi)
    return hi


def treated_stream_chemistry(makeup, cycles, ec_silica_removal=None,
                             ec_hardness_removal=None):
    """The water the tower sees once recycled permeate is blended back.

    Conservative and deliberately so: the permeate is taken as pure, so the
    blended makeup is the fresh makeup diluted by the recycled fraction. The
    EC removals apply to what the RO then has to handle, which is what sets
    the brine silica ceiling -- not to the tower's own chemistry.
    """
    si_lo, si_hi = EC_BLOCK["SiO2_removal"]
    hd_lo, hd_hi = EC_BLOCK["hardness_removal"]
    rs = si_lo if ec_silica_removal is None else float(ec_silica_removal)
    rh = hd_lo if ec_hardness_removal is None else float(ec_hardness_removal)
    circ = makeup.concentrate(cycles)
    return {
        "circulating_SiO2_mg_l": circ.SiO2,
        "SiO2_into_RO_mg_l": circ.SiO2 * (1.0 - rs),
        "Ca_into_RO_mg_l": circ.Ca * (1.0 - rh),
        "Mg_into_RO_mg_l": circ.Mg * (1.0 - rh),
        "ec_silica_removal": rs,
        "ec_hardness_removal": rh,
    }


def ro_brine_silica_ok(makeup, cycles, ro_recovery,
                       ec_silica_removal=None, limit_mg_l=None):
    """Does the RO brine stay under its silica ceiling?

    This is the constraint that actually decides whether a recycle scheme is
    buildable, and it is the one the chemistry engine is uniquely able to
    answer. Silica concentrates in the brine by 1/(1-recovery), so a 85 %
    recovery multiplies it by 6.7.
    """
    lim = RO_BLOCK["brine_SiO2_max_mg_l"][0] if limit_mg_l is None else float(limit_mg_l)
    st = treated_stream_chemistry(makeup, cycles, ec_silica_removal)
    brine = st["SiO2_into_RO_mg_l"] / max(1.0 - float(ro_recovery), 1e-9)
    return {
        "brine_SiO2_mg_l": brine,
        "limit_mg_l": lim,
        "ok": brine <= lim,
        "headroom_mg_l": lim - brine,
        **st,
    }


def recycle_energy_kwh_per_m3(ro_recovery, ec_energy=None, ro_energy=None):
    """Energy to recover one cubic metre of permeate. Ranges, midpoint used."""
    ec = sum(EC_BLOCK["energy_kwh_per_m3"]) / 2 if ec_energy is None else ec_energy
    ro = sum(RO_BLOCK["energy_kwh_per_m3"]) / 2 if ro_energy is None else ro_energy
    # EC treats the whole blowdown; RO treats it too, but only `recovery` of
    # it emerges as permeate, so the per-permeate energy is scaled up.
    return (ec + ro) / max(float(ro_recovery), 1e-9)


def recycle_pays(ro_recovery, tariffs, ec_energy=None, ro_energy=None):
    """Is recovered water cheaper than bought water, on energy alone?

    Ignores capital, membranes, electrodes and sludge entirely, so a FALSE
    here is decisive and a TRUE here is necessary but nowhere near sufficient.
    """
    e = recycle_energy_kwh_per_m3(ro_recovery, ec_energy, ro_energy)
    cost = e * tariffs["elec_per_kwh"]
    avoided = (tariffs.get("water_makeup_per_m3", tariffs["water_per_m3"])
               + tariffs.get("water_discharge_per_m3", 0.0))
    return {
        "energy_kwh_per_m3": e,
        "energy_cost_per_m3": cost,
        "water_value_per_m3": avoided,
        "margin_per_m3": avoided - cost,
        "pays_on_energy_alone": cost < avoided,
    }


# ---------------------------------------------------------------------------
# THE GULF'S OWN ANSWER, and it is a membrane
# ---------------------------------------------------------------------------
# Metito, "TSE RO" presentation to the Kahramaa District Cooling Workshop,
# Doha, 18 June 2014 -- the Qatari utility's own workshop on district cooling.
# This is what the Gulf market already does with treated sewage effluent, and
# any pitch has to be made against it rather than into a vacuum. [C]
#
#   Feed TSE, typical      TSS 5,  TDS 1,500 mg/L, BOD 5,  COD 50, pH 6.5-7.5
#   Feed TSE, at tap-off   TSS 7,  TDS 2,000 mg/L, BOD 7,  COD 65, pH 6-8
#                          temperature 22-35 C in both cases
#
#   Product water          pH 6.5-7.5, TDS 100-200 mg/L, TSS negligible
#                          -- explicitly "equivalent to Kahramaa POTABLE
#                          water quality", for district cooling make-up
#
#   Train    hypochlorite -> multimedia filters -> activated carbon ->
#            cartridge filters (or UF replacing all three) -> acid and
#            antiscalant -> SBS -> UV -> RO -> caustic for pH correction
#
#   Recovery  pre-treatment 92 %, RO 76 %, OVERALL 70 %, waste 30 %
#
# THE COMPETITIVE POINT, stated plainly. The Gulf's answer to TSE chemistry is
# to REMOVE THE CHEMISTRY: take TDS from 2,000 down to 150 and the scaling
# question stops being interesting. Empower did the same thing in Dubai with
# an RO polishing plant and an 80/20 blend. So a controller that manages
# scaling is competing against a membrane that eliminates it, and that
# membrane is deployed, financeable and award-winning.
#
# What survives the comparison is narrow and should be said in one sentence:
# RO throws away 30 % of the water it treats, and a plant that could run
# higher cycles safely would need less RO to begin with. Mizan sizes that
# question. It does not beat the membrane; it tells you how much membrane to
# buy, which is a smaller claim and a true one.
#
# The TDS figure is also a regional cross-check: Qatar TSE at 1,500-2,000
# mg/L against the Aramco TSE at 1,500. Two countries, one number.
METITO_KAHRAMAA_2014 = {
    "source": ("Metito, TSE RO presentation, Kahramaa District Cooling "
               "Workshop, Doha, 18 June 2014"),
    "feed_tse_typical": {"TSS": 5, "TDS": 1500, "BOD": 5, "COD": 50,
                         "pH": (6.5, 7.5), "T_C": (22, 35)},
    "feed_tse_actual": {"TSS": 7, "TDS": 2000, "BOD": 7, "COD": 65,
                        "pH": (6.0, 8.0), "T_C": (22, 35)},
    "product": {"TDS": (100, 200), "pH": (6.5, 7.5),
                "note": "equivalent to Kahramaa potable water quality"},
    "recovery": {"pretreatment": 0.92, "ro": 0.76, "overall": 0.70,
                 "waste_fraction": 0.30},
    "silica_reported": False,      # not in the presentation
}
