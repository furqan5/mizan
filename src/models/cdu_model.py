"""
FURQAN / MIZAN :: Coolant Distribution Unit, for direct-to-chip liquid cooling.

WHAT THIS EXTENDS, AND WHERE THE PRODUCT BOUNDARY MOVES TO.

The Mizan core stops at the condenser. A liquid-cooled data centre puts two
more loops in front of it:

    cooling tower  --(FWS, plain water)-->  CDU plate HX  --(TCS, glycol)-->
    cold plates on the GPUs

FWS is the Facility Water System, the primary side: ordinary makeup water,
concentrated by evaporation, carrying every mineral the Mizan core already
models. TCS is the Technology Cooling System, the secondary side: a sealed
glycol loop that never evaporates and never concentrates.

THE POINT OF MODELLING IT AT ALL IS ONE NUMBER: the plate wall temperature on
the PRIMARY side. That wall is a heat-transfer surface in contact with
concentrated makeup water, exactly like a condenser tube, and it is hotter
than the bulk water for the same reason. Every retrograde mineral in
`chemistry.py` -- calcite, calcium phosphate -- is least soluble there. A
liquid-cooling vendor sizing a CDU has no reason to compute it and no tool
that would.

WHAT THIS MODULE DELIBERATELY DOES NOT DO.

No chip model, no DVFS, no two-phase behaviour, no rack-level allocation, no
CFD. The boundary is the GPU coolant supply temperature and it stops there.
Everything past that is somebody else's competence and pretending otherwise
would be the kind of unearned scope this package has spent a month removing.
"""

from __future__ import annotations

import math
import pathlib
import sys
from dataclasses import dataclass, field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import chemistry as chem            # noqa: E402


# ---------------------------------------------------------------------------
# Coolant properties
# ---------------------------------------------------------------------------
# 50/50 ethylene glycol / water by volume. cp falls with glycol fraction and
# rises with temperature; 3500 J/(kg.K) is the round number the specification
# asked for and sits inside the published band for this mixture over the
# 20-45 C range this loop runs in. It is carried as a NAMED CONSTANT with its
# basis stated rather than inlined, because a wrong cp moves the return
# temperature invariant directly and would be invisible.
#
# [U] The single value is a working figure, not a property correlation. If a
# design is ever sized on this rather than screened, replace it with a
# temperature-dependent fit and re-run. The sensitivity is linear in cp.
GLYCOL_50_CP_J_KGK = 3500.0
GLYCOL_50_RHO_KG_M3 = 1060.0

WATER_CP_J_KGK = 4181.0


# ---------------------------------------------------------------------------
# Temperature limits
# ---------------------------------------------------------------------------
# ASHRAE TC 9.9 liquid-cooling classes, by facility-supply water temperature.
# The class sets how warm the water reaching the CDU is permitted to be, and
# therefore how often a chiller can be switched off entirely. Warmer class,
# more free cooling, less compressor work -- and, for a tower, MORE
# evaporation per unit of heat rejected, which is exactly the trade this
# package exists to price.
ASHRAE_W_CLASSES = {
    "W17": 17.0,
    "W27": 27.0,
    "W32": 32.0,
    "W40": 40.0,
    "W45": 45.0,
}

# Cold-plate coolant RETURN limit. The invariant the specification named.
COLD_PLATE_RETURN_MAX_C = 42.0


@dataclass
class CDUSubsystem:
    """One Coolant Distribution Unit and its plate heat exchanger.

    Sign convention throughout: heat flows SECONDARY -> PRIMARY. The secondary
    loop is the hot side because it has just come off the chips.
    """

    q_it_kw: float                       # IT heat into the secondary loop
    m_dot_sec_kg_s: float                # secondary (glycol) mass flow
    m_dot_sec_nom_kg_s: float            # nameplate secondary flow
    p_pump_sec_nom_kw: float             # nameplate secondary pump power
    approach_k: float = 5.0              # PHE approach, primary in -> secondary out
    cp_sec: float = GLYCOL_50_CP_J_KGK
    cp_pri: float = WATER_CP_J_KGK
    # Fraction of the wall-to-wall temperature difference that falls across
    # the PRIMARY film. 0.5 means the two films are equally resistive, which
    # is the right first assumption for a plate HX with water one side and a
    # 50/50 glycol the other; glycol's lower conductivity pushes it somewhat
    # below 0.5 in reality, which makes 0.5 the CONSERVATIVE choice here
    # because a higher value puts the wall hotter and scaling looks worse.
    primary_film_fraction: float = 0.5
    return_limit_c: float = COLD_PLATE_RETURN_MAX_C

    def pump_power_kw(self) -> float:
        """Affinity law, cubic in flow. The reason turning the secondary pump
        down is worth so much and the reason it cannot be turned down far."""
        if self.m_dot_sec_nom_kg_s <= 0:
            return 0.0
        ratio = self.m_dot_sec_kg_s / self.m_dot_sec_nom_kg_s
        return self.p_pump_sec_nom_kw * ratio ** 3

    def secondary_rise_k(self) -> float:
        """Temperature rise across the cold plates."""
        denom = self.m_dot_sec_kg_s * self.cp_sec
        if denom <= 0:
            return float("inf")
        return self.q_it_kw * 1000.0 / denom

    def solve(self, t_fws_c: float, m_dot_pri_kg_s: float) -> dict:
        """Solve the CDU at a given facility-water supply temperature.

        Returns every temperature the constraint checks need, plus the
        primary-side plate wall temperature that the chemistry model has to
        be evaluated at.
        """
        # Secondary supply to the chips sits one approach above the facility
        # water. Return is the supply plus the cold-plate rise.
        t_sec_supply = t_fws_c + self.approach_k
        rise = self.secondary_rise_k()
        t_sec_return = t_sec_supply + rise

        # Primary side takes the same duty plus the secondary pump's work,
        # which all ends up as heat in the loop.
        q_total_kw = self.q_it_kw + self.pump_power_kw()
        denom = m_dot_pri_kg_s * self.cp_pri
        pri_rise = float("inf") if denom <= 0 else q_total_kw * 1000.0 / denom
        t_fwr = t_fws_c + pri_rise

        # THE NUMBER THIS MODULE EXISTS FOR.
        #
        # Counterflow: the primary leaves at its hottest exactly where the
        # secondary enters at its hottest. That corner is the scaling-critical
        # point on the whole heat exchanger, and it is the analogue of the
        # condenser tube skin in the Mizan core.
        t_wall_primary = t_fwr + self.primary_film_fraction * (t_sec_return - t_fwr)

        return {
            "t_fws_c": float(t_fws_c),
            "t_fwr_c": float(t_fwr),
            "t_sec_supply_c": float(t_sec_supply),
            "t_sec_return_c": float(t_sec_return),
            "secondary_rise_k": float(rise),
            "primary_rise_k": float(pri_rise),
            "t_wall_primary_c": float(t_wall_primary),
            "p_pump_sec_kw": self.pump_power_kw(),
            "q_total_kw": float(q_total_kw),
            "m_dot_pri_kg_s": float(m_dot_pri_kg_s),
            "return_ok": bool(t_sec_return <= self.return_limit_c),
            "return_margin_k": float(self.return_limit_c - t_sec_return),
        }

    def scaling_state(self, state: dict, makeup, cycles: float,
                      ph: float, limits=None) -> dict:
        """Saturation state of the CONCENTRATED facility water at the plate
        wall, and at the tower basin for the prograde species.

        This is the whole reason the CDU is modelled inside Mizan rather than
        beside it: the wall temperature comes from the data-centre side and
        the saturation limit comes from the water side, and no existing tool
        joins them.
        """
        limits = chem.OPERATING_LIMITS if limits is None else limits
        conc = makeup.concentrate(cycles)
        sat = chem.saturation_state_split(
            conc, state["t_wall_primary_c"], state["t_fws_c"],
            pH_hot=ph, pH_cold=ph)
        violations = {k: sat[k] - limits[k] for k in limits if sat[k] > limits[k]}
        return {
            "SI": {k: sat[k] for k in limits},
            "eval_point": {k: sat.get(f"{k}_at") for k in limits},
            "violations": violations,
            "max_SI_over_limit": (max(violations.values())
                                  if violations else
                                  max(sat[k] - limits[k] for k in limits)),
            "zero_scaling": len(violations) == 0,
            "t_wall_primary_c": state["t_wall_primary_c"],
        }


def free_cooling_available(t_wb_c: float, tower_approach_k: float,
                           cdu_approach_k: float,
                           w_class: str = "W32") -> tuple[bool, float]:
    """Can the tower alone meet the CDU's supply requirement, with the
    chiller off entirely?

    Returns (available, achievable_t_sec_supply_c).

    This is the single biggest energy lever in a liquid-cooled data centre and
    it is also the one that costs the most water: with the compressor off, all
    of the heat leaves through the tower, and in a hot dry climate most of
    that is latent. The trade is real and it is the reason this module reports
    both sides.
    """
    if w_class not in ASHRAE_W_CLASSES:
        raise ValueError(f"unknown ASHRAE class {w_class!r}; "
                         f"expected one of {tuple(ASHRAE_W_CLASSES)}")
    t_fws = t_wb_c + tower_approach_k
    t_sec_supply = t_fws + cdu_approach_k
    return bool(t_fws <= ASHRAE_W_CLASSES[w_class]), float(t_sec_supply)


def sized_for(q_it_kw: float, delta_t_k: float = 10.0,
              p_pump_nom_kw: float = None, **kw) -> CDUSubsystem:
    """Convenience constructor: size the secondary flow for a target rise.

    `delta_t_k` is the cold-plate temperature rise the loop is designed for.
    A larger rise means less flow and much less pump power (cubic), at the
    cost of a hotter return -- which is exactly what the 42 C invariant
    bounds.
    """
    m_dot = q_it_kw * 1000.0 / (GLYCOL_50_CP_J_KGK * delta_t_k)
    if p_pump_nom_kw is None:
        # 2 % of IT load at nameplate flow. [A -- an archetype, not a
        # measurement; declared so it can be replaced by a real pump curve.]
        p_pump_nom_kw = 0.02 * q_it_kw
    return CDUSubsystem(q_it_kw=q_it_kw, m_dot_sec_kg_s=m_dot,
                        m_dot_sec_nom_kg_s=m_dot,
                        p_pump_sec_nom_kw=p_pump_nom_kw, **kw)

# ---------------------------------------------------------------------------
# APPROACH TEMPERATURE -- the 5 K here is an archetype and the real spec is 3 K
# ---------------------------------------------------------------------------
# Google contributed "Project Deschutes", its fifth-generation CDU design, to
# the Open Compute Project as v1.0 in February 2026 -- the first CDU
# specification ever contributed to OCP. Headline targets: 2 MW thermal,
# 3 degC APPROACH, 500 GPM at 80-90 psi. [C OCP]
#
# This module's default approach is 5 K, an archetype chosen before that spec
# was read. The difference is not cosmetic and it runs the RIGHT way for the
# chemistry: a tighter approach means the facility water may be 2 K WARMER for
# the same GPU inlet temperature, which is 2 K of extra headroom against the
# amorphous-silica floor. Anyone quoting a free-cooling floor for a Deschutes-
# class CDU should use 3 K and get a more favourable answer than this module's
# default gives.
#
# 500 GPM at 2 MW also implies a secondary delta-T near 15-18 K rather than
# the 10 K default here, which is a second archetype worth replacing with the
# spec before any number is quoted to a data-centre operator.
DESCHUTES_SPEC = {
    "source": "Google Project Deschutes CDU v1.0, OCP, February 2026",
    "thermal_mw": 2.0,
    "approach_k": 3.0,
    "flow_gpm": 500.0,
    "pressure_psi": (80.0, 90.0),
}
