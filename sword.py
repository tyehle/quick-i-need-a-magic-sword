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


class Deck:
    """Deals the numbers 0..n-1 in shuffled rounds, so each comes up once before any repeats.
    Each new round is reshuffled until its first `apart` share none with the last round's last
    `apart`, so nothing comes up again soon across the join."""

    def __init__(self, n, rng=random, apart=5):
        self.n, self.rng, self.apart = n, rng, min(apart, n // 2)
        self.order, self.last = [], []

    def shuffled(self):
        order = list(range(self.n))
        for i in range(self.n - 1, 0, -1):      # Fisher-Yates (MicroPython has no random.shuffle)
            j = int(self.rng.random() * (i + 1))
            order[i], order[j] = order[j], order[i]
        return order

    def deal(self):
        if not self.order:
            while True:
                order = self.shuffled()
                if not any(k in self.last for k in order[:self.apart]):
                    break
            self.last = order[len(order) - self.apart:]
            self.order = order
        return self.order.pop(0)


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


FONT = "Uncial Antiqua"   # the title's font (fonts/, loaded by index.html)
TAKE_COLOR = "#111111"    # "TAKE THIS", in the sword's ink
VIBE_COLORS = {            # the sword's name, by its vibe (build.TITLES)
    "aggressive": "#c0392b",   # brick red
    "protective": "#238544",   # green: protective or nurturing
    "power": "#6b21a8",        # purple: neutral power
}
FILL = "#ffffff"           # inside the sword, against the page's #f4f4f4
TITLE_SIZE = 3.5    # the title's letter size, mm, unless too long to fit beside the sword
TITLE_FIT = 0.92    # the most of the sword's length a title line may take
TITLE_GAP = 2.2     # from the sword's widest point to the nearer edge of the letters, mm
TITLE_LEAD = 1.3    # from one line's baseline to the next, in letter sizes
CAP = 0.99          # how far the font's letters reach above the baseline, in letter sizes
DROP = 0.3          # and below it (Uncial Antiqua's)


def fills(D, style):
    """The sword's insides, as polygons in (u, v): the hilt's (pommel, grip and guard) and the
    blade's (with the guard that closes it)."""
    gk = style["guard"] + ("+langet" if style["langet"] == "1" else "")
    hilt = D["fills"][D["fill"][style["grip"] + "|" + style["pommel"] + "|" + style["guard"]]]
    blade = D["blade"][style["base"] + "|" + style["tip"] + "|" + gk]["fill"]
    return [unpack(p) for p in hilt + blade]


def svg(lines, stroke, take=None, name=None, color=TAKE_COLOR, shapes=()):
    """The sword upright, its point at the top: (u, v) -> (v, -u), and its title beside it.
    Sized by its viewBox alone, so it scales to fit whatever holds it, its lines (stroke, in
    mm) with it.

    take and name are each a list of (text, length in ems) lines: take set to the sword's left,
    the name to its right, its first line nearest the sword. All are turned a quarter turn
    counterclockwise, so they read up the page as the inscription does (the first line on top),
    and are centred on the sword's length, at one size: take in TAKE_COLOR, the name in color.
    shapes are the sword's insides, filled with FILL under its lines."""
    lines = [[(v, -u) for u, v in pl] for pl in lines]
    shapes = [[(v, -u) for u, v in pl] for pl in shapes]
    xs = [x for pl in lines for x, _ in pl]
    ys = [y for pl in lines for _, y in pl]
    sx0, sx1, sy0, sy1 = min(xs), max(xs), min(ys), max(ys)
    x0, x1 = sx0, sx1
    text = ""
    if take and name:
        size = min([TITLE_SIZE] + [TITLE_FIT * (sy1 - sy0) / em for _, em in take + name])
        lead = TITLE_LEAD * size
        cy = (sy0 + sy1) / 2
        # turned counterclockwise, the letters' tops point left: on the left the baseline is the
        # nearer edge (the last line nearest), on the right the tops are (the first line nearest)
        left = sx0 - TITLE_GAP - DROP * size
        right = sx1 + TITLE_GAP + CAP * size
        placed = ([(t, left - (len(take) - 1 - i) * lead) for i, (t, _) in enumerate(take)]
                  + [(t, right + i * lead) for i, (t, _) in enumerate(name)])
        for k, (t, bx) in enumerate(placed):
            text += ('<text fill="%s" transform="translate(%.2f %.2f) rotate(-90)">%s</text>'
                     % (TAKE_COLOR if k < len(take) else color, bx, cy, t))
        x0 = left - (len(take) - 1) * lead - CAP * size
        x1 = right + (len(name) - 1) * lead + DROP * size
        text = ('<g font-family="%s, serif" font-size="%.3f" text-anchor="middle">'
                % (FONT, size) + text + "</g>")
    x0, y0 = x0 - PAD, sy0 - PAD
    w, h = x1 + PAD - x0, sy1 + PAD - y0
    pts = lambda pl: " ".join("%.2f,%.2f" % p for p in pl)
    paths = "".join('<polyline points="' + pts(pl) + '"/>' for pl in lines)
    insides = "".join('<polygon points="' + pts(pl) + '"/>' for pl in shapes)
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="%.2f %.2f %.2f %.2f">' % (x0, y0, w, h)
            + '<g fill="%s" stroke="none">' % FILL + insides + "</g>"
            + '<g fill="none" stroke="currentColor" stroke-width="%s" stroke-linecap="round" '
              'stroke-linejoin="round">' % stroke + paths + "</g>" + text + "</svg>")


def random_svg(D, rng=random, deck=None):
    """A random sword and its title; with a Deck over D["phrases"], the inscription is the
    deck's next rather than a random one."""
    style = random_style(D, rng)
    if deck:
        style["phrase"] = D["phrases"][deck.deal()]
    c, phrase = D["const"], style["phrase"]
    lines = assemble(D, style)
    # the name on one line if it fits at full size, else in two
    length = max(u for pl in lines for u, _ in pl) - min(u for pl in lines for u, _ in pl)
    name = phrase["title"]
    if name[0][1] * TITLE_SIZE > TITLE_FIT * length:
        name = phrase["title_wrap"]
    return svg(lines, c["stroke"], [(c["take"], c["take_em"])], name,
               VIBE_COLORS[phrase["vibe"]], fills(D, style))
