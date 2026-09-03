

# --------------------------------------------------------------------------
def fig_simulink_model(mode):
    """THE SIMULINK MODEL, DRAWN FROM ITS OWN BUILD SCRIPT.

    Every block and every signal below is taken from `build_mizan_model.m`,
    which constructs `mizan_plant.slx` from text. Drawing it here rather than
    screenshotting the Simulink canvas keeps it legible at print size, keeps
    it in the report's palette, and means it regenerates with everything else.

    The architecture is the argument. The physical loop is a CLOSED CYCLE --
    basin water heats through the condenser, is cooled by the tower, and
    returns -- carried as a Simscape thermal network so the loop's real
    thermal mass sets the time constant instead of a number somebody chose.
    The scaling limit hangs off the CONDENSER outlet, because that is where
    the skin is, and it is the only place in the diagram where chemistry and
    thermal state meet. The supervisor closes on that margin.
    """
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

    g = GEOM[mode]
    fig, ax = plt.subplots(figsize=(g["figsize"][0], g["figsize"][0] * 0.62),
                           dpi=g["dpi"])
    base = g["base"]
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")

    FILL = {"phys": "#E8EFF4", "sim": "#DCE9E9", "chem": "#F6E7E7",
            "ctrl": "#F5EEDC", "src": "#EFEFEF"}
    EDGE = {"phys": NAVY, "sim": TEAL, "chem": RED, "ctrl": AMBER, "src": GREY}

    boxes = {}

    def box(key, x, y, w, h, label, kind, sub=None):
        b = FancyBboxPatch((x, y), w, h,
                           boxstyle="round,pad=0.6,rounding_size=1.4",
                           linewidth=1.6, edgecolor=EDGE[kind],
                           facecolor=FILL[kind], zorder=3)
        ax.add_patch(b)
        ty = y + h / 2 + (1.5 if sub else 0)
        ax.text(x + w / 2, ty, label, ha="center", va="center",
                fontsize=base - 2.6, weight="bold", color=INK_TXT, zorder=4)
        if sub:
            ax.text(x + w / 2, y + h / 2 - 2.4, sub, ha="center", va="center",
                    fontsize=base - 4.2, color=GREY, style="italic", zorder=4)
        boxes[key] = (x, y, w, h)
        return b

    def edge(a, b, label=None, ao="R", bo="L", colour=GREY, lw=1.5,
             rad=0.0, lp=0.5, dx=0.0, dy=0.0, ls="-"):
        def port(k, side):
            x, y, w, h = boxes[k]
            return {"L": (x, y + h / 2), "R": (x + w, y + h / 2),
                    "T": (x + w / 2, y + h), "B": (x + w / 2, y)}[side]
        p0, p1 = port(a, ao), port(b, bo)
        ar = FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=11,
                             linewidth=lw, color=colour, zorder=2,
                             linestyle=ls,
                             connectionstyle="arc3,rad=%.2f" % rad)
        ax.add_patch(ar)
        if label:
            mx = p0[0] + (p1[0] - p0[0]) * lp + dx
            my = p0[1] + (p1[1] - p0[1]) * lp + dy
            ax.text(mx, my, label, ha="center", va="center",
                    fontsize=base - 4.6, color=colour, zorder=5,
                    bbox=dict(boxstyle="round,pad=0.18", fc="white",
                              ec="none", alpha=0.92))

    # ---- sources -------------------------------------------------------
    box("clock", 2, 88, 15, 8, "Clock", "src")
    box("amb", 23, 88, 26, 8, "Ambient and load", "src",
        "Dhahran diurnal profile")

    # ---- the physical loop, a closed cycle -----------------------------
    box("mass", 2, 66, 21, 11, "Loop thermal mass", "sim",
        "Simscape network, 150 t")
    box("basin", 29, 66, 20, 11, "Basin temperature", "phys", "the state")
    box("chill", 55, 66, 18, 11, "Chiller", "phys", "York YT bi-quadratic")
    box("cond", 79, 66, 19, 11, "Condenser", "phys", "duty and hot water")

    box("tower", 79, 46, 19, 11, "Cooling tower", "phys", "Poppe integrator")
    box("bal", 29, 46, 20, 11, "Basin heat balance", "phys", "net heat in")

    # ---- chemistry -----------------------------------------------------
    box("consts", 55, 28, 18, 10, "cycles = 4\nbulk pH = 8.7", "src")
    box("scale", 79, 28, 19, 11, "Scaling limit", "chem",
        "brucite pH at the SKIN")

    # ---- control -------------------------------------------------------
    box("sup", 47, 8, 26, 12, "SUPERVISOR", "ctrl",
        "Stateflow: shadow -> advisory ->\nclosed loop, with hard fallback")
    box("delay", 22, 9, 19, 10, "Control interval", "ctrl", "one-step delay")
    box("fanp", 2, 9, 16, 10, "Fan power", "phys", "affinity law")

    # ---- signals -------------------------------------------------------
    edge("clock", "amb")
    edge("amb", "chill", "Q_evap", ao="R", bo="T", rad=-0.18, dy=4)
    edge("amb", "tower", "T_db, rh", ao="R", bo="T", rad=-0.42, dx=14, dy=10)

    edge("mass", "basin", colour=TEAL, lw=2.0)
    edge("basin", "chill", "basin temp", colour=NAVY, lw=2.0)
    edge("chill", "cond", "Q_cond", colour=NAVY, lw=2.0)
    edge("cond", "tower", "hot water", ao="B", bo="T", colour=NAVY, lw=2.0,
         dx=9)
    edge("tower", "bal", "T reached", colour=NAVY, lw=2.0)
    edge("bal", "mass", "net heat", ao="L", bo="B", colour=TEAL, lw=2.0,
         rad=0.30, dx=-4, dy=-3)

    edge("cond", "scale", "skin temp", ao="B", bo="T", colour=RED, lw=2.0,
         dx=9)
    edge("consts", "scale", colour=GREY)
    edge("scale", "sup", "margin", ao="B", bo="R", colour=RED, lw=2.0,
         rad=0.22, dx=8, dy=-2)
    edge("chill", "sup", "in envelope", ao="B", bo="T", colour=GREY,
         rad=0.10, dx=-3)

    edge("sup", "delay", "fan command", colour=AMBER, lw=2.0)
    edge("delay", "fanp", colour=AMBER, lw=2.0)
    edge("delay", "tower", "fan %", ao="T", bo="B", colour=AMBER, lw=2.0,
         rad=-0.30, dx=22, dy=8)

    # ---- legend --------------------------------------------------------
    handles = [("Simscape physical network", TEAL),
               ("MATLAB Function (physics)", NAVY),
               ("Chemistry", RED),
               ("Stateflow supervisor", AMBER)]
    for i, (lab, col) in enumerate(handles):
        yy = 99 - i * 3.4
        ax.add_patch(FancyBboxPatch((55.5, yy - 1.1), 2.2, 2.2,
                                    boxstyle="round,pad=0.1,rounding_size=0.4",
                                    linewidth=1.4, edgecolor=col,
                                    facecolor="white", zorder=4))
        ax.text(59, yy, lab, fontsize=base - 4.4, color=GREY, va="center")

    foot = ("Every block and signal is taken from build_mizan_model.m, which constructs mizan_plant.slx from text. "
            "The loop is a closed cycle: the Simscape network carries the real"
            + chr(10) +
            "thermal mass, so the time constant is physical rather than chosen. The scaling limit hangs off the condenser outlet - the only point where chemistry meets thermal state.")
    if mode == "report":
        fig.text(0.5, 0.02, foot, ha="center", fontsize=8.4, color=GREY,
                 linespacing=1.6)
        fig.tight_layout(rect=[0, 0.065, 1, 1])
        out = FIGS / "simulink_model.png"
    else:
        fig.tight_layout()
        out = SLIDE / "simulink_model.png"
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("   %-6s -> %s" % (mode, out.relative_to(ROOT)))

