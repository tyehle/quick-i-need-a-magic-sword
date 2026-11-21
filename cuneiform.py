"""Cuneiform-style signs built from wedges, in a box -1..1 each way (y down).

A wedge is a triangular head (pressed by the stylus's corner) with a thin tail; a
Winkelhaken is a head alone, pointing sideways. Each sign is a list of
(x, y, direction in degrees, tail length) for wedges, tail 0 for a Winkelhaken.
"""
from __future__ import annotations

import math

from geom import Polyline, densify

HEAD_L, HEAD_W = 0.42, 0.44
STYLE = "wedge"                 # "wedge": triangular heads; "nail": a cross-stroke at the head; "line": no heads
LINE_GAP = 0.4                  # the gap between stacked wedges in line style, in sign units
NAIL = 0.34                     # the nail head's length, in sign units       # a wedge's head, in sign units
HOOK_ARM, HOOK_W = 0.62, 1.0   # a Winkelhaken's arms: how far back, how far out

SIGNS: dict[str, list[tuple[float, float, float, float]]] = {
    "an":   [(-1, 0, 0, 2), (0, -1, 90, 2), (-0.72, 0.72, -45, 2.04), (0.72, -0.72, 135, 2.04)],   # heads spread round
    "ash":  [(-1, 0, 0, 2)],
    "dish": [(0, -1, 90, 2)],
    "min":  [(-0.4, -1, 90, 2), (0.4, -1, 90, 2)],
    "esh":  [(-0.65, -0.8, 90, 1.6), (0, -0.8, 90, 1.6), (0.65, -0.8, 90, 1.6)],
    "u":    [(0.35, 0, 180, 0)],
    "ud":   [(0.0, 0, 180, 0), (0.6, -1, 90, 2)],
    "ki":   [(-1, -0.6, 0, 2), (0.1, 0.35, 180, 0), (0.75, -0.6, 90, 1.6)],
    "ta":   [(-1, -0.55, 0, 2), (-1, 0.55, 0, 2), (0.3, -1, 90, 2)],
    "me":   [(-0.2, -1, 90, 2), (-1, -0.2, 0, 2)],
}


def hook(T, x: float, y: float, dx: float, dy: float, nx: float, ny: float, head: float,
         back: float = HOOK_ARM, out_: float = HOOK_W) -> list[Polyline]:
    """A Winkelhaken as in the font: a chevron, its arms `back` behind its point and
    `out_` to each side."""
    arms = [(x - dx * back + nx * out_, y - dy * back + ny * out_), (x, y),
            (x - dx * back - nx * out_, y - dy * back - ny * out_)]
    hl, hw = 0.42 * head, 0.36 * head
    tri = [(x, y), (x - dx * hl + nx * hw / 2, y - dy * hl + ny * hw / 2),
           (x - dx * hl - nx * hw / 2, y - dy * hl - ny * hw / 2), (x, y)]
    # at card sizes the pen's width already makes the point read as the head
    return [densify([T(*p) for p in arms])] + ([densify([T(*p) for p in tri])] if head >= 1.0 else [])


def box(name: str) -> tuple[float, float, float, float]:
    """The sign's extent in its own units (wedge ends and hook arms)."""
    pts = []
    for x, y, d, tail, *hk in SIGNS[name]:
        dx, dy = math.cos(math.radians(d)), math.sin(math.radians(d))
        if tail:
            pts += [(x, y), (x + dx * tail, y + dy * tail)]
        else:
            back, out_ = (hk + [HOOK_ARM, HOOK_W])[:2] if hk else (HOOK_ARM, HOOK_W)
            pts += [(x, y), (x - dx * back - dy * out_, y - dy * back + dx * out_),
                    (x - dx * back + dy * out_, y - dy * back - dx * out_)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    m = HEAD_W / 2                     # a head reaches about this far past its wedge's line
    return min(xs) - m, max(xs) + m, min(ys) - m, max(ys) + m


def sign(name: str, cx: float, cy: float, h: float, ang: float = 0.0, head: float = 1.0) -> list[Polyline]:
    """The sign centred on (cx, cy), h mm per unit (so 2h across), turned by ang radians;
    `head` scales the wedges' heads (smaller keeps a small sign's strokes apart)."""
    c, s = math.cos(ang), math.sin(ang)
    T = lambda x, y: (cx + h * (x * c - y * s), cy + h * (x * s + y * c))
    out = []
    x0, x1, y0, y1 = box(name)
    ox, oy = (x0 + x1) / 2, (y0 + y1) / 2               # centre the sign on its own box
    for x, y, d, tail, *hk in SIGNS[name]:
        x, y = x - ox, y - oy
        dx, dy = math.cos(math.radians(d)), math.sin(math.radians(d))
        nx, ny = -dy, dx
        if tail:
            hl, hw = HEAD_L * head, HEAD_W * head
        else:
            # a Winkelhaken: a chevron pointing along d, its point at (x, y), thick at
            # the point (a small head) with two arms trailing back
            out += hook(T, x, y, dx, dy, nx, ny, head, *hk)
            continue
        if STYLE == "line":
            # the wedge as a bare line; its head's end is implied by its direction. Where
            # one wedge carries straight on from another's end (A's stacked column) the
            # two would read as one long line, so each stops short, leaving a gap
            a, b = 0.0, tail
            for wx, wy, wd, t, *_ in SIGNS[name]:
                if not t or abs((wd - d + 180) % 360 - 180) >= 15:
                    continue
                ex, ey = wx + math.cos(math.radians(wd)) * t, wy + math.sin(math.radians(wd)) * t
                if math.hypot(x + ox - ex, y + oy - ey) < 0.06:            # we start at its end
                    a = LINE_GAP / 2
                if math.hypot(x + ox + dx * tail - wx, y + oy + dy * tail - wy) < 0.06:   # it starts at ours
                    b = tail - LINE_GAP / 2
            out.append(densify([T(x + dx * a, y + dy * a), T(x + dx * b, y + dy * b)]))
            continue
        if STYLE == "nail":
            # the head as a short cross-stroke, the wedge as a line from it
            out.append(densify([T(x + nx * NAIL / 2, y + ny * NAIL / 2), T(x - nx * NAIL / 2, y - ny * NAIL / 2)]))
            out.append(densify([T(x, y), T(x + dx * tail, y + dy * tail)]))
            continue
        b0, b1 = (x + nx * hw / 2, y + ny * hw / 2), (x - nx * hw / 2, y - ny * hw / 2)
        apex = (x + dx * hl, y + dy * hl)
        out.append(densify([T(*b0), T(*apex), T(*b1), T(*b0)]))
        if tail:
            out.append(densify([T(x, y), T(x + dx * tail, y + dy * tail)]))
    return out

# traced from Noto Sans Cuneiform: AN (sky, god) and KI (earth); "AN KI" = heaven and earth
SIGNS["AN"] = [(0, -1, 90, 2), (-1, 0, 0, 2), (-0.62, -0.62, 45, 1.75), (-0.62, 0.62, -45, 1.75)]
SIGNS["KI"] = [(-0.06, -1, 135, 1.3), (0.06, -1, 45, 1.3),          # the roof: two heads at the top
               (-1, 0.02, 45, 1.38), (1, 0.02, 135, 1.38),           # the sides, down to the foot
               (-0.32, -0.36, 0, 0.82), (-0.32, 0.0, 0, 0.95), (-0.32, 0.36, 0, 0.7)]
# the numbers 20 (MAN) and 30 (EŠ): two and three Winkelhaken nested, as in the font;
# after AN they spell gods' names: d20 Šamaš (the sun), d30 Sîn (the moon)
SIGNS["MAN"] = [(-0.62, 0, 180, 0), (0.08, 0, 180, 0)]
SIGNS["EŠ"] = [(-0.75, 0, 180, 0), (-0.2, 0, 180, 0), (0.35, 0, 180, 0)]
WIDTH = {"AN": 2.0, "KI": 2.0, "MAN": 1.32, "EŠ": 1.72}     # each sign's width, in sign units

# traced from Noto Sans Cuneiform, all in one scale (a unit is half TAR's height):
# nūru "light" = NU-U-RU; TAR (ku5) "to cut"; TI "life"
SIGNS["NU"] = [(-0.81, -0.13, 0, 1.62), (-0.40, -0.66, 90, 1.06), (-0.45, 0.53, -38, 1.35)]
SIGNS["U"] = [(0, 0, 180, 0, 0.62, 0.9)]
_r = 0.925
SIGNS["RU"] = [(-0.71 * _r, -0.79 * _r, 0, 1.14 * _r), (-0.78 * _r, 0.71 * _r, 0, 1.49 * _r),
               (-0.45 * _r, -0.71 * _r, 57, 0.84 * _r), (0.29 * _r, -0.71 * _r, 57, 0.85 * _r),
               (0.02 * _r, 0.0, 124, 0.72 * _r), (0.78 * _r, 0.0, 127, 0.81 * _r)]
SIGNS["TAR"] = [(-0.29, -0.33, 90, 1.33), (-0.53, -0.83, 44, 0.74), (-0.05, -0.35, 42, 0.93)]
_t = 1.6
SIGNS["TI"] = [(-0.88 * _t, 0, 0, 0.5 * _t), (-0.38 * _t, 0, 180, 0, 0.35 * _t, 0.32 * _t),
               (0.02 * _t, -0.5 * _t, 90, 1.0 * _t), (0.08 * _t, 0, 0, 0.49 * _t),
               (0.57 * _t, 0, 180, 0, 0.25 * _t, 0.2 * _t)]

# UR, traced (with NU: nu-ur, "nūr", light of ...)
SIGNS["UR"] = [(-0.91, -0.91, 90, 1.47), (-0.27, -0.91, 90, 0.75), (-0.53, -0.03, 0, 1.49),
               (1.02, -0.91, 90, 1.63), (-1.41, 0.72, 0, 2.43)]

# A (water; the syllable a), MA, DIŠ (1, and 60), traced
SIGNS["A"] = [(-0.30, -0.81, 90, 1.61), (0.29, -0.81, 90, 0.68), (0.29, -0.13, 90, 0.94)]
SIGNS["MA"] = [(-1.10, -0.45, 0, 0.72), (-0.24, -0.80, 90, 1.42), (-0.03, -0.06, 0, 0.86),
               (0.90, -0.80, 90, 1.42), (-0.44, 0.59, 0, 1.37)]
SIGNS["DIŠ"] = [(0, -0.80, 90, 1.61)]

# GIŠ (wood; the mark before tools and weapons), KU (read TUKUL after GIŠ: GIŠ.TUKUL
# "weapon"), UD (AN UD = dUTU, Šamaš the sun), BAR (AN GIŠ BAR = Gibil, fire), traced
SIGNS["GIŠ"] = [(-0.62, -0.37, 0, 1.0), (-0.62, 0.38, 0, 1.03), (0.41, -0.81, 90, 1.62)]
SIGNS["KU"] = [(-0.52, -0.68, 0, 0.95), (-0.53, -0.42, 90, 0.84), (-0.27, -0.01, 0, 0.72),
               (-0.65, 0.58, 0, 1.12), (0.45, -0.81, 90, 1.62)]
SIGNS["UD"] = [(-0.82, -0.29, -22, 1.12), (0.15, -0.92, 62, 1.07),
               (-0.77, 0.23, 22, 1.2), (0.63, 0.01, 109, 1.04)]
SIGNS["BAR"] = [(-0.26, -0.82, 90, 1.35), (-0.76, 0.62, 0, 1.52)]

# MAŠ (AN MAŠ = Ninurta), AB and BA (A.AB.BA = the sea), GUR (AN U GUR = Nergal),
# 40 (four Winkelhaken; AN 40 = Ea), traced
SIGNS["MAŠ"] = [(0.01, -0.81, 90, 1.62), (-0.80, 0.05, 0, 1.62)]
SIGNS["AB"] = [(-1.19, -0.26, 0, 0.98), (-1.19, 0.38, 0, 0.98), (-0.27, -0.27, -20, 1.18),
               (-0.25, 0.35, 20, 1.31), (1.0, -0.81, 90, 1.62)]
SIGNS["BA"] = [(-0.70, -0.15, -22, 1.19), (-0.70, 0.23, 18, 1.30), (-0.02, 0.03, 0, 0.66),
               (0.55, -0.81, 90, 1.62)]
SIGNS["GUR"] = [(-1.06, -0.39, 0, 1.89), (-1.06, 0.40, 0, 1.89), (-0.03, -0.81, 90, 1.62),
                (0.86, -0.81, 90, 1.62)]
SIGNS["40"] = [(x, y, 180, 0, 0.52, 0.41) for x in (-0.47, -0.05) for y in (-0.40, 0.39)]
# at blade size the font's tight 40 runs together: spread its chevrons
SIGNS["40"] = [(x, y, 180, 0, 0.42, 0.36) for x in (-0.62, 0.12) for y in (-0.48, 0.48)]
# KU: drop the short vertical's head clear of the top horizontal's
SIGNS["KU"][1] = (-0.53, -0.34, 90, 0.76)

# NE (read IZI, "fire") and BAD (read ÚŠ, "death"), traced
SIGNS["NE"] = [(-1.49, -0.52, 0, 1.48), (0.27, -0.42, 0, 0.95), (0.27, 0.33, 0, 1.0), (1.29, -0.86, 90, 1.62),
               (-1.49, 0.30, 15, 0.91), (0.06, -0.61, 145, 0.97), (-0.32, -0.34, 28, 0.6),
               (-0.49, 0.42, 30, 0.83)]
SIGNS["BAD"] = [(-1.05, -0.03, 0, 1.69), (0.64, -0.02, 180, 0, 0.42, 0.55)]

# EME "tongue" (KA, the mouth, with ME inside), simplified: KA's mesh of small wedges
# cut to two diagonals; its pointed frame, verticals and horizontals, and the ME kept
SIGNS["EME"] = [(-1.45, -0.14, -27, 1.11), (-1.47, 0.12, 28, 1.42),           # the frame's point
                (-0.82, -0.22, 37, 0.54), (-1.01, 0.19, 29, 0.70),            # the mesh, as two
                (-1.12, -0.14, 90, 0.77), (-0.35, -0.82, 90, 1.62),
                (-0.21, -0.41, 0, 1.55), (-0.21, 0.36, 0, 1.55),
                (0.48, -0.31, 90, 0.88), (0.55, 0.0, 0, 0.53),                # ME
                (1.37, -0.82, 90, 1.62)]


# --- round 91: signs for new phrases, traced from Noto Sans Cuneiform on the same grid (a unit is
# half TAR's height); dense rows of small wedges simplified so they don't clog at sword size
# ZI "life": a long horizontal, two verticals, and two rows of Winkelhaken (five each in the
# font, three here)
SIGNS["ZI"] = [(-1.23, 0.0, 0, 2.4), (-0.79, -0.73, 90, 1.45), (-0.40, -0.73, 90, 1.45)] + \
    [(x, y, 180, 0, 0.42, 0.34) for x in (-0.11, 0.34, 0.77) for y in (-0.39, 0.40)]
# KAL (also LAMMA, "protective spirit"; and with Á, usu "strength"): a box of two horizontals,
# two verticals, and two slanting wedges on the right
SIGNS["KAL"] = [(-1.02, -0.49, 0, 1.88), (-1.02, 0.48, 0, 1.93), (-1.10, -0.27, 90, 0.87),
                (-0.20, -0.67, 90, 1.36), (0.80, -0.82, 75, 0.75), (1.04, -0.08, 100, 0.95)]
# MAH "great" (ur-maḫ, "lion"): an open frame closing to a point on the right
SIGNS["MAH"] = [(-1.55, 0.21, 0, 0.43), (-1.07, -0.20, 90, 0.96), (-0.92, -0.35, 0, 1.37),
                (0.06, -0.61, 0, 0.79), (0.46, -1.02, 90, 0.81), (-0.66, 0.57, 0, 1.08),
                (-1.02, 0.95, -52, 0.58), (0.95, -0.95, 53, 1.0), (0.54, 0.90, -46, 1.47)]
# MI (ĝi6, "night"; doubled, kukku, "darkness"): a big Winkelhaken, then the font's four rows of
# paired horizontals as three long ones
SIGNS["MI"] = [(-1.58, 0.0, 180, 0, 0.8, 0.84)] + [(-0.75, y, 0, 2.35) for y in (-0.5, 0.0, 0.5)]
# DA (á, "arm, strength"): top and bottom horizontals, two verticals, a middle wedge ending in a
# small Winkelhaken; the font's five little stacked wedges as two
SIGNS["DA"] = [(-1.10, -0.61, 0, 1.86), (-1.10, 0.65, 0, 0.82), (-0.92, -0.2, 0, 0.45), (-0.92, 0.22, 0, 0.45),
               (-0.42, -0.50, 90, 1.30), (-0.38, 0.20, 0, 0.87), (0.49, 0.18, 180, 0, 0.30, 0.27),
               (0.90, -0.81, 90, 1.61)]
# E: three horizontals (four in the font), a vertical, and two slanting wedges on the right
SIGNS["E"] = [(-0.78, -0.5, 0, 1.16), (-0.70, 0.02, 0, 1.08), (-0.78, 0.55, 0, 1.08),
              (-0.09, -0.42, 90, 1.15), (0.43, -0.88, 75, 0.75), (0.42, -0.22, 98, 1.18)]
# DI: a diamond of four slanting wedges round two horizontals
SIGNS["DI"] = [(-0.19, -0.99, 127, 1.08), (0.19, -0.99, 53, 1.08), (-1.04, 0.06, 41, 1.41),
               (1.04, 0.06, 140, 1.36), (-0.29, -0.29, 0, 0.99), (-0.29, 0.10, 0, 0.97)]
# EN: a horizontal with a short vertical under it, two tall verticals with two small wedges
# between them (four in the font), and two Winkelhaken at their feet
SIGNS["EN"] = [(-0.88, 0.40, 0, 1.04), (-0.51, 0.56, 90, 0.29), (0.13, -0.85, 90, 1.22), (0.66, -0.85, 90, 1.15),
               (0.27, -0.50, 0, 0.32), (0.27, -0.12, 0, 0.32),
               (0.03, 0.46, 180, 0, 0.35, 0.3), (0.51, 0.46, 180, 0, 0.35, 0.3)]
# DU: an upper wedge ending in a Winkelhaken, two horizontals end to end below, a tall vertical
SIGNS["DU"] = [(-1.01, -0.53, 12, 1.38), (0.34, -0.24, 180, 0, 0.32, 0.37), (-1.16, 0.39, 0, 0.96),
               (-0.21, 0.39, 0, 1.15), (0.96, -0.82, 90, 1.63)]


# --- round 92: signs for animal and nature phrases, traced as above
# GUD (gu4, "ox"): two horizontals, a vertical, and two slanting wedges meeting in a point
SIGNS["GUD"] = [(-1.21, -0.37, 0, 1.23), (-1.21, 0.53, 0, 1.31), (0.12, -0.58, 90, 1.21),
                (0.10, -0.82, 36, 1.37), (0.10, 0.82, -36, 1.37)]
# SI ("horn"): two horizontals, a short vertical and a tall one
SIGNS["SI"] = [(-0.89, -0.67, 0, 1.43), (-0.70, 0.66, 0, 1.37), (-0.18, -0.29, 90, 0.87), (0.70, -0.84, 90, 1.61)]
# ŠA (ša3, "heart"): three horizontals (four in the font) closed by a short vertical, two crossing
# slanting wedges, a tall vertical
SIGNS["ŠA"] = [(-1.04, y, 0, 0.85) for y in (-0.42, 0.0, 0.42)] + \
    [(-0.19, -0.48, 90, 0.9), (-0.27, -0.65, 38, 1.34), (-0.27, 0.58, -36, 1.32), (0.84, -0.82, 90, 1.63)]
# SAG ("head"): two slanting wedges like an open hook, two verticals, two horizontals, a vertical
SIGNS["SAG"] = [(-1.2, -0.25, -42, 0.95), (-1.2, 0.13, 35, 1.48), (-0.65, -0.34, 90, 1.14), (-0.29, -0.82, 90, 1.62),
                (-0.12, -0.36, 0, 1.08), (-0.12, 0.31, 0, 1.16), (1.08, -0.82, 90, 1.62)]
# RA ("to strike"): a frame of two horizontals and two verticals, a small grid on the left
# (simplified)
SIGNS["RA"] = [(-0.60, -0.63, 0, 1.27), (-0.39, 0.60, 0, 1.19), (0.82, -0.80, 90, 1.57), (0.02, -0.36, 90, 1.16),
               (-0.93, -0.35, 0, 0.79), (-0.92, -0.19, 90, 0.82), (-0.59, -0.19, 90, 0.82)]
# KUR ("mountain"): three Winkelhaken in a triangle
SIGNS["KUR"] = [(-0.45, -0.32, 180, 0, 0.42, 0.36), (0.42, -0.08, 180, 0, 0.42, 0.36), (-0.02, 0.45, 180, 0, 0.42, 0.36)]
# GAL ("great"): three horizontals (four in the font) against a tall vertical, one horizontal past it
SIGNS["GAL"] = [(-1.29, y, 0, 1.2) for y in (-0.7, -0.04, 0.62)] + [(-0.07, -0.99, 90, 1.99), (0.06, -0.05, 0, 1.24)]
# MUL ("star", AN three times): three small ANs, two stacked on the left, one on the right
_s = 0.55
SIGNS["MUL"] = [(cx + _s * x, cy + _s * y, d, _s * t) for cx, cy in ((-0.63, -0.56), (-0.63, 0.52), (0.53, -0.02))
                for x, y, d, t in SIGNS["AN"]]


# --- round 94: simplifications for legibility at sword size
# EN without the two small wedges between its verticals (and without the tiny vertical under its
# horizontal, too small to plot)
SIGNS["EN"] = [(-0.88, 0.40, 0, 1.04), (0.13, -0.85, 90, 1.22), (0.66, -0.85, 90, 1.15),
               (0.03, 0.46, 180, 0, 0.35, 0.3), (0.51, 0.46, 180, 0, 0.35, 0.3)]
# SAG with its two crossing slanted wedges drawn as one open Winkelhaken clear of the verticals
SIGNS["SAG"] = [(-1.18, -0.05, 180, 0, 0.42, 0.55), (-0.55, -0.34, 90, 1.14), (-0.22, -0.82, 90, 1.62),
                (0.02, -0.36, 0, 1.0), (0.02, 0.31, 0, 1.08), (1.08, -0.82, 90, 1.62)]


# --- round 104: the shield word, KUŠ E ÍB (ᵏᵘˢguru₂₁)
# SU (read kuš, the leather determinative): top and bottom horizontals slanting in, a middle one,
# the font's two middle rows as one and four little verticals as two, a tall vertical
SIGNS["SU"] = [(-0.94, -0.46, -9, 1.52), (-0.94, 0.46, 9, 1.66), (-0.70, 0.0, 0, 1.6),
               (-0.26, -0.41, 90, 1.0), (0.26, -0.41, 90, 1.0), (0.72, -0.92, 90, 1.83)]
# TUM (read íb): on the left two horizontals with one little vertical between them (four in the
# font), each horizontal ending in a Winkelhaken; on the right a Z of two horizontals and a
# diagonal, and a long slanting wedge
SIGNS["TUM"] = [(-1.73, -0.41, 0, 1.0), (-1.73, 0.22, 0, 1.0), (-1.22, -0.29, 90, 0.72),
                (-0.78, -0.41, 180, 0, 0.42, 0.38), (-0.78, 0.22, 180, 0, 0.42, 0.38),
                (-0.14, -0.39, 1, 1.78), (-0.14, 0.70, 0, 1.78), (1.65, -0.33, 154, 1.30), (0.0, 0.22, 18, 1.82)]
