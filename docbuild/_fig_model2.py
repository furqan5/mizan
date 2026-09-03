

# --------------------------------------------------------------------------
def fig_simulink_model(mode):
    """THE MODEL ARCHITECTURE, DRAWN FROM ITS OWN BUILD SCRIPT.

    Every block and signal is taken from build_mizan_model.m, which builds
    mizan_plant.slx from text.

    Drawing notes, because the first version of this figure was unreadable:
    block subtitles and most signal names were removed (the caption carries
    them), and routing is ORTHOGONAL rather than curved. Curved arcs that
    cross look like a mistake; right-angle routes that cross look like a
    schematic. The layout below has exactly one crossing.
    """
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

    g = GEOM[mode]
    fig, ax = plt.subplots(figsize=(g["figsize"][0], g["figsize"][0] * 0.58),
                           dpi=g["dpi"])
    base = g["base"]
    ax.set_xlim(0, 102); ax.set_ylim(0, 100); ax.axis("off")

    FILL = {"phys": "#E8EFF4", "sim": "#DCE9E9", "chem": "#F6E7E7",
            "ctrl": "#F5EEDC", "src": "#EFEFEF"}
    EDGE = {"phys": NAVY, "sim": TEAL, "chem": RED, "ctrl": AMBER, "src": GREY}

    B = {}

    def box(key, x, y, w, h, label, kind, tag=None):
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.5,rounding_size=1.2",
            linewidth=1.7, edgecolor=EDGE[kind], facecolor=FILL[kind], zorder=3))
        ax.text(x + w / 2, y + h / 2 + (1.6 if tag else 0), label,
                ha="center", va="center", fontsize=base - 2.2,
                weight="bold", color=INK_TXT, zorder=4)
        if tag:
            ax.text(x + w / 2, y + h / 2 - 2.6, tag, ha="center", va="center",
                    fontsize=base - 4.4, color=GREY, style="italic", zorder=4)
        B[key] = (x, y, w, h)

    def P(key, side, off=0.0):
        x, y, w, h = B[key]
        return {"L": (x, y + h / 2 + off), "R": (x + w, y + h / 2 + off),
                "T": (x + w / 2 + off, y + h), "B": (x + w / 2 + off, y)}[side]

    def route(pts, colour=GREY, lw=1.6, label=None, lat=None):
        """Orthogonal polyline through pts, arrowhead on the last segment."""
        for i in range(len(pts) - 2):
            ax.plot([pts[i][0], pts[i + 1][0]], [pts[i][1], pts[i + 1][1]],
                    color=colour, lw=lw, solid_capstyle="round", zorder=2)
        ax.add_patch(FancyArrowPatch(pts[-2], pts[-1], arrowstyle="-|>",
                                     mutation_scale=11, linewidth=lw,
                                     color=colour, zorder=2,
                                     shrinkA=0, shrinkB=0))
        if label and lat:
            ax.text(lat[0], lat[1], label, ha="center", va="center",
                    fontsize=base - 4.4, color=colour, zorder=5,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white",
                              ec="none", alpha=0.95))

    # ---- blocks --------------------------------------------------------
    box("clock", 4, 86, 15, 8, "Clock", "src")
    box("amb", 25, 86, 26, 8, "Ambient and load", "src")

    box("basin", 4, 64, 20, 10, "Basin temperature", "phys")
    box("chill", 28, 64, 17, 10, "Chiller", "phys")
    box("cond", 49, 64, 19, 10, "Condenser", "phys")
    box("tower", 72, 64, 25, 10, "Cooling tower", "phys")

    box("mass", 4, 46, 20, 10, "Loop thermal mass", "sim", "Simscape, 150 t")
    box("bal", 28, 46, 19, 10, "Basin heat balance", "phys")

    box("consts", 3, 24, 18, 10, "cycles = 4\nbulk pH = 8.7", "src")
    box("scale", 50, 24, 20, 10, "Scaling limit", "chem", "brucite pH at skin")

    box("fanp", 2, 6, 18, 10, "Fan power", "phys")
    box("delay", 24, 6, 20, 10, "Control interval", "ctrl")
    box("sup", 50, 5, 27, 12, "SUPERVISOR", "ctrl", "Stateflow, 4 states")

    # ---- signals, all orthogonal ---------------------------------------
    route([P("clock", "R"), P("amb", "L")], GREY)

    # ambient -> chiller (load) and -> tower (weather)
    ax_, ay = P("amb", "B", -4)
    cx, cy = P("chill", "T")
    route([(ax_, ay), (ax_, 79), (cx, 79), (cx, cy)], GREY,
          label="Q_evap", lat=(cx - 7.5, 80.6))
    rx, ry = P("amb", "R")
    tx, ty = P("tower", "T")
    route([(rx, ry), (tx, ry), (tx, ty)], GREY,
          label="T_db, rh", lat=(tx + 7.0, 90.8))

    # the closed physical cycle
    route([P("mass", "T"), P("basin", "B")], TEAL, 2.1)
    route([P("basin", "R"), P("chill", "L")], NAVY, 2.1)
    route([P("chill", "R"), P("cond", "L")], NAVY, 2.1)
    route([P("cond", "R"), P("tower", "L")], NAVY, 2.1)

    bx, by = P("tower", "B")
    hx, hy = P("bal", "R")
    route([(bx, by), (bx, hy), (hx, hy)], NAVY, 2.1,
          label="tower outlet", lat=(60, hy + 2.4))
    route([P("bal", "L"), P("mass", "R")], TEAL, 2.1,
          label="net heat", lat=(25.8, 53.6))

    # condenser -> chemistry
    sx, sy = P("cond", "B")
    kx, ky = P("scale", "T")
    route([(sx, sy), (sx, 38), (kx, 38), (kx, ky)], RED, 2.1,
          label="skin temp", lat=(sx + 9.5, 39.4))
    route([P("consts", "R"), P("scale", "L")], GREY)

    # chemistry -> supervisor
    mx, my = P("scale", "B")
    ux, uy = P("sup", "T", 6)
    route([(mx, my), (mx, 20), (ux, 20), (ux, uy)], RED, 2.1,
          label="margin", lat=(mx + 5.6, 21.4))

    # chiller envelope flag -> supervisor  (the one crossing, at x = 36)
    ex, ey = P("chill", "B")
    vx, vy = P("sup", "T", -6)
    route([(ex, ey), (ex, 20), (vx, 20), (vx, vy)], GREY,
          label="in envelope", lat=(ex - 0.5, 21.4))

    # supervisor -> delay -> fan power, and delay -> tower around the outside
    route([P("sup", "L"), P("delay", "R")], AMBER, 2.1,
          label="fan command", lat=(47, 13.4))
    route([P("delay", "L"), P("fanp", "R")], AMBER, 2.1)
    dx, dy = P("delay", "B")
    route([(dx, dy), (dx, 1.5), (100, 1.5), (100, by), (bx + 6, by)],
          AMBER, 2.1, label="fan %", lat=(88, 3.0))

    foot = ("Every block and signal is taken from build_mizan_model.m, which builds mizan_plant.slx from text. "
            "Colour: teal = Simscape physical network, navy = MATLAB Function"
            + chr(10) +
            "carrying the physics, red = chemistry, amber = Stateflow supervisor. "
            "The physical loop is a closed cycle, so the tower must reject the evaporator load plus the compressor work.")
    if mode == "report":
        fig.text(0.5, 0.02, foot, ha="center", fontsize=8.4, color=GREY,
                 linespacing=1.6)
        fig.tight_layout(rect=[0, 0.06, 1, 1])
        out = FIGS / "simulink_model.png"
    else:
        fig.tight_layout()
        out = SLIDE / "simulink_model.png"
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("   %-6s -> %s" % (mode, out.relative_to(ROOT)))

