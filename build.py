"""Prerender swordgen's parts into sword_parts.json, for the page (sword.py) to assemble.

Each part is drawn for every combination of the styles it depends on:
  pommel   the pommel
  guard    the guard and whether it has a langet
  grip     the grip, the pommel (where the grip starts) and the guard (where it ends)
  blade    the base and tip, the guard and langet (the guard's front face), with the
           positions that place the inscription and fullers
  phrase   each inscription, drawn from u = 0, with its length
The fullers are a few straight lines and are drawn by sword.py itself.

Then it checks sword.py's swords against swordgen's own for many random seeds.
Needs shapely (pip install shapely).

    python build.py
"""
from __future__ import annotations

import itertools
import json
import math
import random
import sys
from pathlib import Path

from PIL import ImageFont

import swordgen
from swordgen import PARTS, PHRASES, sword

import sword as page

OUT = Path(__file__).resolve().parent / "sword_parts.json"
L, H = 52.0, 9.86   # the sword's length and the guard's height, mm: the cards' size
STROKE = 0.35       # the pen's width, mm: the tarot cards' (cardgen.SIZES)
TOL = 0.004         # how far simplifying may move a line, mm
DIGITS = 2          # decimals kept, mm
CHECKS = 2000       # random swords to compare with swordgen
MATCH = 0.02        # how far an assembled sword may stray from swordgen's, mm
FILL_TOL = 0.06      # how far simplifying may move a fill's edge, mm (it lies under a line)
FILL_REACH = STROKE / 2   # the fills reach the lines' outer edges, closing gaps narrower than a line
FONT = Path(__file__).resolve().parent / "fonts" / "UncialAntiqua-Regular.ttf"   # the titles' font, as the page's
TAKE = "TAKE THIS"   # the title's first line
# each inscription's meaning (swordgen.PHRASES' notes), the title's second line, and its vibe, which
# colours the title (sword.VIBE_COLORS): aggressive, protective (or nurturing), or power (neutral)
TITLES = {
    "GIŠ KU A MA RU": ("BLADE OF THE DELUGE", "aggressive"),
    "GIŠ KU BAD": ("BLADE OF DEATH", "aggressive"),
    "GIŠ KU AN GIŠ BAR": ("BLADE OF THE FIRE GOD", "aggressive"),
    "GIŠ KU AN 40": ("BLADE OF THE GOD OF THE WATERS", "protective"),
    "GIŠ KU DA GUD": ("BLADE WITH THE STRENGTH OF THE OX", "power"),
    "GIŠ KU SI GUD": ("BLADE LIKE THE HORN OF THE OX", "power"),
    "GIŠ KU GUD AN": ("BLADE OF THE BULL OF HEAVEN", "aggressive"),
    "GIŠ KU DA UR MAH": ("BLADE WITH THE STRENGTH OF THE LION", "power"),
    "GIŠ KU ŠA UR MAH": ("BLADE WITH THE HEART OF A LION", "power"),
    "GIŠ KU UR BAR RA": ("BLADE OF THE WOLF", "aggressive"),
    "GIŠ KU SAG GIŠ RA": ("BLADE THAT STRIKES DOWN", "aggressive"),
    "GIŠ KU UD GAL": ("BLADE OF THE GREAT STORM", "aggressive"),
    "GIŠ KU DA KUR": ("BLADE WITH THE STRENGTH OF THE MOUNTAIN", "power"),
    "GIŠ KU KUR GAL": ("BLADE OF THE GREAT MOUNTAIN", "power"),
    "GIŠ KU UR SAG": ("BLADE OF THE HERO", "power"),
    "GIŠ KU UR SAG GAL": ("BLADE OF THE GREAT HERO", "power"),
    "GIŠ KU DA UR SAG": ("BLADE WITH THE STRENGTH OF THE HERO", "power"),
    "GIŠ KU DA GAL": ("BLADE OF GREAT STRENGTH", "power"),
    "GIŠ KU GUD GAL": ("BLADE OF THE GREAT BULL", "power"),
    "GIŠ KU UR MAH GAL": ("BLADE OF THE GREAT LION", "power"),
    "GIŠ KU ŠA GUD": ("BLADE WITH THE HEART OF THE OX", "protective"),
    "GIŠ KU SI GAL": ("BLADE OF THE GREAT HORN", "power"),
    "GIŠ KU NE GAL": ("BLADE OF THE GREAT FIRE", "aggressive"),
    "GIŠ KU A NE": ("BLADE OF WATER AND FIRE", "power"),
    "GIŠ KU UD MI": ("BLADE OF DAY AND NIGHT", "power"),
    "GIŠ KU SAG TAR": ("BLADE THAT CUTS OFF HEADS", "aggressive"),
    "GIŠ KU NE": ("BLADE OF FIRE", "aggressive"),
    "GIŠ KU DA KAL": ("BLADE OF STRENGTH", "power"),
    "GIŠ KU AN KAL": ("BLADE OF THE GUARDIAN SPIRIT", "protective"),
    "GIŠ KU EN DU": ("BLADE OF SONG", "protective"),
    "GIŠ KU E NE DI": ("BLADE OF PLAY AND DANCE", "protective"),
    "GIŠ KU MI MI": ("BLADE OF DARKNESS", "aggressive"),
}

Pt = tuple[float, float]


def simplify(pl: list[Pt], tol: float = TOL) -> list[Pt]:
    """Ramer-Douglas-Peucker: drop points that lie within tol of the line through their
    neighbours (swordgen samples every 0.15 mm, for a plotter; an SVG needs only the corners)."""
    keep = [False] * len(pl)
    keep[0] = keep[-1] = True
    stack = [(0, len(pl) - 1)]
    while stack:
        a, b = stack.pop()
        (ax, ay), (bx, by) = pl[a], pl[b]
        dx, dy = bx - ax, by - ay
        n = math.hypot(dx, dy)
        far, fi = 0.0, -1
        for i in range(a + 1, b):
            px, py = pl[i]
            d = abs(dx * (py - ay) - dy * (px - ax)) / n if n else math.hypot(px - ax, py - ay)
            if d > far:
                far, fi = d, i
        if far > tol:
            keep[fi] = True
            stack += [(a, fi), (fi, b)]
    return [p for p, k in zip(pl, keep) if k]


def pack(lines: list[list[Pt]], du: float = 0.0, tol: float = TOL) -> list[list[float]]:
    """Each polyline simplified and flattened to [u0, v0, u1, v1, ...], rounded."""
    out = []
    for pl in lines:
        flat = []
        for u, v in simplify(pl, tol):
            flat += [round(u + du, DIGITS) + 0.0, round(v, DIGITS) + 0.0]
        out.append(flat)
    return out


def silhouette(lines: list[list[Pt]]) -> list[list[float]]:
    """The area the lines enclose, filled: each line thickened to the pen's outer edge, merged,
    and each piece's outline kept without its holes. Packed as pack() packs lines."""
    from shapely.geometry import LineString, Polygon
    from shapely.ops import unary_union
    ink = unary_union([LineString(pl).buffer(FILL_REACH, 4) for pl in lines if len(pl) > 1])
    pieces = getattr(ink, "geoms", [ink])
    # the fill's edge lies under the line, so it may stray by most of half a line unseen
    return pack([list(Polygon(p.exterior).simplify(FILL_TOL).exterior.coords) for p in pieces], tol=FILL_TOL)


def run(**style: str) -> tuple[list[list[Pt]], dict]:
    lines = sword(0.0, 0.0, L, H, False, **style)
    return lines, dict(swordgen.STAGES)


def build() -> dict:
    plain = dict(pommel="wheel", grip="wrap", guard="diamond", base="plain", fuller="ridge", tip="long",
                 langet="0", phrase=PHRASES[0])
    pommels, guards, grips, grip_at, blades = {}, {}, [], {}, {}
    fills, fill_at = [], {}
    seen: dict[str, int] = {}
    seen_fill: dict[str, int] = {}
    for pm, gd, gp in itertools.product(PARTS["pommel"], PARTS["guard"], PARTS["grip"]):
        lines, st = run(**{**plain, "pommel": pm, "guard": gd, "grip": gp})
        pommels[pm] = pack(lines[:st["pommel"]])
        g = pack(lines[st["guard"]:st["grip"]])
        key = json.dumps(g)
        if key not in seen:              # the same grip often fits several pommels and guards
            seen[key] = len(grips)
            grips.append(g)
        grip_at[f"{gp}|{pm}|{gd}"] = seen[key]
        # the hilt's fill: the pommel, guard and grip together close the grip's area
        f = silhouette(lines[:st["grip"]])
        key = json.dumps(f)
        if key not in seen_fill:
            seen_fill[key] = len(fills)
            fills.append(f)
        fill_at[f"{gp}|{pm}|{gd}"] = seen_fill[key]
    for gd, lg, bs, tp in itertools.product(PARTS["guard"], "01", PARTS["base"], PARTS["tip"]):
        if not swordgen.allowed({"langet": lg, "base": bs}):
            continue
        lines, st = run(**{**plain, "guard": gd, "langet": lg, "base": bs, "tip": tp})
        gk = gd + ("+langet" if lg == "1" else "")
        guards[gk] = pack(lines[st["pommel"]:st["guard"]])
        blades[f"{bs}|{tp}|{gk}"] = {
            "lines": pack(lines[st["grip"]:st["blade"]]),
            # the blade's fill: the guard closes the blade's area at the hilt
            "fill": silhouette(lines[st["pommel"]:st["guard"]] + lines[st["grip"]:st["blade"]]),
            "q1": st["q1"], "body0": st["body0"], "ridge_stop": st["ridge_stop"],
            "grind": list(st["grind"]) if st["grind"] else None,
        }
    missing = [ph for ph in PHRASES if ph not in TITLES]
    assert not missing, f"no title for {missing}"
    font = ImageFont.truetype(str(FONT), 1000)
    em = lambda text: font.getlength(text) / 1000      # a line's length, in ems
    phrases = []
    for ph in PHRASES:
        lines, st = run(**{**plain, "phrase": ph})
        phrases.append({"text": ph, "lines": pack(lines[st["blade"]:st["inscription"]], -st["start"]),
                        "length": st["end"] - st["start"], "title": [[TITLES[ph][0], em(TITLES[ph][0])]],
                        "title_wrap": wrap(TITLES[ph][0], em), "vibe": TITLES[ph][1]})
    return {
        "const": {"stroke": STROKE, "bw0": swordgen.BLADE * H, "lead": swordgen.LEAD, "min_run": swordgen.MIN_RUN,
                  "fuller_gap": swordgen.FULLER_GAP, "langet_odds": swordgen.LANGET_ODDS,
                  "take": TAKE, "take_em": em(TAKE)},
        "options": PARTS, "phrases": phrases,
        "pommel": pommels, "guard": guards, "grips": grips, "grip": grip_at, "blade": blades,
        "fills": fills, "fill": fill_at,
    }


def wrap(text: str, em) -> list[list]:
    """The text in two lines, broken between the words where the longer line is shortest, with
    each line's length in ems (one line if it is one word)."""
    words = text.split()
    if len(words) < 2:
        return [[text, em(text)]]
    splits = [(" ".join(words[:i]), " ".join(words[i:])) for i in range(1, len(words))]
    best = min(splits, key=lambda s: max(em(s[0]), em(s[1])))
    return [[t, em(t)] for t in best]


def far(a: list[Pt], b: list[Pt]) -> float:
    """How far polyline a strays from polyline b: its points' greatest distance from b."""
    def to_seg(p, q, r):
        dx, dy = r[0] - q[0], r[1] - q[1]
        n = dx * dx + dy * dy
        t = 0.0 if n == 0 else max(0.0, min(1.0, ((p[0] - q[0]) * dx + (p[1] - q[1]) * dy) / n))
        return math.hypot(p[0] - q[0] - t * dx, p[1] - q[1] - t * dy)
    segs = list(zip(b, b[1:])) or [(b[0], b[0])]
    return max(min(to_seg(p, q, r) for q, r in segs) for p in a)


def check(D: dict) -> int:
    """Assemble random swords with sword.py and compare them, line by line, with swordgen's."""
    bad = 0
    for seed in range(CHECKS):
        want_style = swordgen.random_style(random.Random(seed))
        style = page.random_style(D, random.Random(seed))
        if {**style, "phrase": style["phrase"]["text"]} != want_style:
            print(f"seed {seed}: styles differ\n  {want_style}\n  {style}")
            bad += 1
            continue
        want = sword(0.0, 0.0, L, H, False, **want_style)
        got = page.assemble(D, style)
        if len(got) != len(want):
            print(f"seed {seed}: {len(got)} lines, swordgen drew {len(want)}")
            bad += 1
            continue
        worst = max(max(far(g, w), far(w, g)) for g, w in zip(got, want))
        if worst > MATCH:
            print(f"seed {seed}: strays {worst:.3f} mm from swordgen ({want_style})")
            bad += 1
    return bad


def main() -> int:
    D = build()
    text = json.dumps(D, separators=(",", ":"))
    OUT.write_text(text)
    print(f"wrote {OUT.name}: {len(text) / 1e3:.0f} kB, {len(D['grips'])} grips, {len(D['blade'])} blades")
    bad = check(json.loads(text))
    print(f"checked {CHECKS} random swords against swordgen: {CHECKS - bad} match")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
