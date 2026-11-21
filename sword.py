"""Random swords assembled from prerendered parts, as SVG.

The parts come from sword_parts.json, made by build.py from swordgen. This module uses no
packages and keeps to what MicroPython supports, so the page can run it under MicroPython.
The sword is built along u (hilt to point) as swordgen draws it, then stood upright.
"""
import json
import math
import random

KEYS = ("pommel", "grip", "guard", "base", "fuller", "tip")   # the order swordgen draws them in
PAD = 1.0           # the margin round the sword, mm


def load(path="sword_parts.json"):
    with open(path) as f:
        return json.load(f)


def allowed(style):
    """As swordgen.allowed: a langet doesn't go with the bases that cover the same place."""
    return not (style["langet"] == "1" and style["base"] in ("ecusson", "wrap"))


def random_style(D, rng=random):
    """A random sword, drawn as swordgen.random_style draws it (the same rng calls, in order)."""
    while True:
        style = {}
        for k in KEYS:
            style[k] = rng.choice(D["options"][k])
        style["langet"] = "1" if rng.random() < D["const"]["langet_odds"] else "0"
        style["phrase"] = rng.choice(D["phrases"])
        if allowed(style):
            return style


def unpack(flat, du=0.0):
    return [(flat[i] + du, flat[i + 1]) for i in range(0, len(flat), 2)]


def assemble(D, style):
    """The sword's polylines, in swordgen's (u, v) and in swordgen's order."""
    c = D["const"]
    bw0 = c["bw0"]
    gk = style["guard"] + ("+langet" if style["langet"] == "1" else "")
    blade = D["blade"][style["base"] + "|" + style["tip"] + "|" + gk]
    grip = D["grips"][D["grip"][style["grip"] + "|" + style["pommel"] + "|" + style["guard"]]]
    out = [unpack(p) for p in D["pommel"][style["pommel"]] + D["guard"][gk] + grip + blade["lines"]]

    # the inscription and the fullers, placed as swordgen places them
    fuller = style["fuller"]
    phrase = style["phrase"]
    grind = blade["grind"]
    clear = 0.7 * bw0
    if fuller in ("double", "double-round"):
        r0 = grind[0] + (grind[1] - grind[0]) * (1 - c["fuller_gap"]) if grind else blade["body0"] + 0.3 * bw0
    else:
        r0 = blade["body0"]
    start = max(blade["q1"] + c["lead"] * bw0, r0 + clear + c["min_run"] * bw0)
    out += [unpack(p, start) for p in phrase["lines"]]
    end = start + phrase["length"]
    ridge_stop = max(blade["ridge_stop"], end + clear + 2.0 * bw0)
    if fuller == "ridge":
        out.append([(blade["body0"], 0.0), (start - clear, 0.0)])
        out.append([(end + clear, 0.0), (ridge_stop, 0.0)])
    elif fuller in ("double", "double-round"):
        f = c["fuller_gap"] * bw0
        s0 = grind[0] + (grind[1] - grind[0]) * (1 - f / bw0) if grind else blade["body0"] + 0.3 * bw0
        out += [[(s0, sy * f), (start - clear, sy * f)] for sy in (-1, 1)]
        meet = ridge_stop
        if fuller == "double":
            for sy in (-1, 1):
                cv = max(end + clear, meet - 3.0 * bw0)
                out.append([(end + clear, sy * f), (cv, sy * f), (meet, 0.0)])
        else:
            ea = 2.4 * f
            c_ = meet - ea
            out.append([(end + clear, -f), (c_, -f)]
                       + [(c_ + ea * math.sin(a), -f * math.cos(a)) for a in [math.pi * i / 24 for i in range(25)]]
                       + [(end + clear, f)])
    return out


def svg(lines, stroke):
    """The sword upright, its point at the top: (u, v) -> (v, -u). Sized by its viewBox alone, so
    it scales to fit whatever holds it, its lines (stroke, in mm) with it."""
    lines = [[(v, -u) for u, v in pl] for pl in lines]
    xs = [x for pl in lines for x, _ in pl]
    ys = [y for pl in lines for _, y in pl]
    x0, y0 = min(xs) - PAD, min(ys) - PAD
    w, h = max(xs) + PAD - x0, max(ys) + PAD - y0
    paths = "".join('<polyline points="' + " ".join("%.2f,%.2f" % p for p in pl) + '"/>' for pl in lines)
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="%.2f %.2f %.2f %.2f">' % (x0, y0, w, h)
            + '<g fill="none" stroke="currentColor" stroke-width="%s" stroke-linecap="round" '
              'stroke-linejoin="round">' % stroke + paths + "</g></svg>")


def random_svg(D, rng=random):
    return svg(assemble(D, random_style(D, rng)), D["const"]["stroke"])
