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
    "line": SUBSIDIARY["line"],
    "product": SUBSIDIARY["product"],
    "meaning": "Mizan: the balance, the scale, the measure held level.",
}
