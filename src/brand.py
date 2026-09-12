"""
FURQAN :: the house brand, in one place
=======================================
Both names are Arabic and both are load-bearing, so the taglines are built
from what they actually mean rather than from marketing vocabulary.

  FURQAN  (الفرقان)  from the root f-r-q, "to separate". The criterion; the
                     thing that distinguishes true from false. As a company
                     line that is not decoration -- it is this group's whole
                     method. A first-principles model with few parameters
                     cannot absorb a bad input; it fails loudly and so it
                     SEPARATES a real effect from a fitted one. A regression
                     with free exponents cannot.

  MIZAN   (الميزان)  the balance, the scale, equilibrium. The product holds
                     a balance between energy and water that no single
                     discipline currently prices.

The parent is the energy thesis and the physics-plus-AI method; the
subsidiary is the first product built on it.
"""

PARENT = {
    "name": "FURQAN",
    "tagline": "The criterion for energy.",
    "line": ("Deep physics and physics-informed AI for hard energy "
             "infrastructure — we separate what is measured from what is "
             "merely modelled."),
    "meaning": ("Furqan (الفرقان), from the Arabic root f-r-q, to separate: "
                "the criterion that distinguishes the true from the false."),
    "scope": ("First-principles models of energy systems, with "
              "physics-informed machine learning where — and only where — "
              "the physics runs out."),
}

SUBSIDIARY = {
    "name": "MIZAN",
    "tagline": "The balance between energy and water.",
    "line": ("Energy-water supervisory controller for cooling-tower and "
             "condenser-water loops in Gulf district cooling."),
    "meaning": ("Mizan (الميزان): the balance, the scale, the measure held "
                "level."),
    "product": "energy-water supervisory controller",
    "parent_line": "A Furqan venture",

    # The NAME tagline above says what Mizan means. This says what the tool
    # does, and the two jobs are different -- a buyer who already knows the
    # name still needs one line telling them what they are buying.
    #
    # "The limit, computed." earns its place on three counts:
    #   * it is literally the product. Every incumbent controller holds a
    #     conductivity setpoint somebody guessed; this one computes the
    #     ceiling from ion chemistry and says which mineral sets it.
    #   * it names the gap rather than the benefit. Three unrelated operators
    #     -- an RO vendor, a food plant and a university -- independently say
    #     silica sets their cycles, and none of them can say where the limit
    #     is. The Cycle Ceiling Report is the smallest sellable answer.
    #   * it pairs with the name instead of competing with it. Mizan is the
    #     balance; a balance is an instrument for establishing a quantity, not
    #     a slogan about saving money.
    #
    # It also survives the honest version of our own results, which matters:
    # a tagline about SAVING WATER would be contradicted by the annual study,
    # where the water saving is negative inside the validated envelope. A
    # tagline about KNOWING THE LIMIT is not.
    "product_tagline": "The limit, computed.",
    "product_line": (
        "Every cooling tower has a cycles-of-concentration ceiling set by "
        "mineral chemistry. Almost nobody knows where theirs is, so they run "
        "two to four cycles on caution. Mizan computes the ceiling from an "
        "ion-association model, says which mineral sets it, and holds the "
        "loop against it."),
    # THE POSITIONING LINE, added 12 Sep 2026. The tagline says what the tool
    # does in three words; this says which two markets it does it in and what
    # three constraints it respects. Each of those three is a module, not an
    # adjective, which is the only reason the line is allowed to exist:
    #
    #   chemistry-aware    chemistry.py -- ion association, Davies activity
    #                      coefficients, benchmarked against PHREEQC 3.9.0
    #   metallurgy-safe    corrosion.py -- Larson-Skold plus chloride pitting.
    #                      316 stainless caps this water at 1.85 cycles, below
    #                      the 3.0 operators run and the 4.52 the scaling
    #                      chemistry allows
    #   permit-compliant   discharge.py -- RCER-2015 tables. On this water the
    #                      permit binds at 3.33 cycles on NITRATE, before the
    #                      chemistry binds at 4.52
    #
    # HONEST TENSE. "Runs" is the target, not the present. It runs no plant
    # today; it runs a validated model of one. Say "built to run" until a
    # pilot exists, and the line stops being a claim we cannot support.
    "positioning": (
        "A dual-domain AI supervisory controller that runs Saudi district "
        "cooling plants and data-center CDUs at the true water-energy "
        "ceiling -- chemistry-aware, metallurgy-safe, permit-compliant."),
    "positioning_tense_caveat": (
        "No plant runs on this yet. Until a pilot exists the defensible verb "
        "is 'built to run', not 'runs'."),
    "alternates": (
        # Kept because each says something the winner does not.
        "Know the ceiling before you hit it.",
        "Every tower has a limit. Most are guessing where.",
    ),
}

# LaTeX-safe variants (no non-Latin script, which the Times New Roman text
# font cannot set; the Arabic is carried in the plain-text fields above for
# the deck's speaker notes and for the web copy).
PARENT_TEX = {
    "name": PARENT["name"],
    "tagline": PARENT["tagline"],
    "line": PARENT["line"].replace("—", "---"),
    "meaning": ("Furqan, from the Arabic root f-r-q, to separate: the "
                "criterion that distinguishes the true from the false."),
}
SUBSIDIARY_TEX = {
    "name": SUBSIDIARY["name"],
    "tagline": SUBSIDIARY["tagline"],
    "product_tagline": SUBSIDIARY["product_tagline"],
    "line": SUBSIDIARY["line"],
    "product": SUBSIDIARY["product"],
    "meaning": "Mizan: the balance, the scale, the measure held level.",
}
