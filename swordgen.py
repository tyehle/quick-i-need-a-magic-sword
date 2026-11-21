"""Random swords for the item card back, built from interchangeable parts.

sword() draws one horizontal sword, hilt to the left (to the right if flipped), with a
cuneiform inscription on the blade by the hilt. It takes each part's style as a keyword:
pommel, grip, guard, base, fuller, tip, the langet and gpoint flags ("1" or "0") and the
phrase (sign names from cuneiform.SIGNS, space separated). PARTS lists every style and
PHRASES the inscriptions; random_style() draws a random sword whose parts go together.
Part defaults can be set with the environment variables POMMEL, GRIP, GUARD, BASE, FULLER,
TIP, LANGET and GPOINT.
"""
from __future__ import annotations

import math
import os

import cuneiform
from geom import Polyline, clamped_spline, densify
from cuneiform import box, sign

BLADE = 0.16        # the blade's half width at the guard, of the guard's height
LEAD = 5.0          # the inscription's earliest start, in blade half-widths from the guard
HEAD = 0.55         # the wedge heads' size on the blade
STYLE = "line"      # the inscription's cuneiform style (see cuneiform.STYLE)

Pt = tuple[float, float]


def opt(name: str, default: str) -> str:
    return os.environ.get(name, default)


def sword(cx: float, cy: float, L: float, H: float, flip: bool, **style: str) -> list[Polyline]:
    POMMEL = style.get("pommel", opt("POMMEL", "diamond-dot"))
    GRIP = style.get("grip", opt("GRIP", "wrap"))
    GUARD = style.get("guard", opt("GUARD", "diamond"))
    BASE = style.get("base", opt("BASE", "plain"))
    FULLER = style.get("fuller", opt("FULLER", "ridge"))
    TIP = style.get("tip", opt("TIP", "long"))
    # a subtle point on the guard's front, down the blade, for the guards whose front is straight
    # (on by default)
    GPOINT = style.get("gpoint", opt("GPOINT", "1")) == "1"
    # a langet: a bold point on the guard's front, part of the guard, lying on the blade's base
    # (it takes the subtle point's place where both would apply)
    LANGET = style.get("langet", opt("LANGET", "0")) == "1"
    if LANGET:
        GPOINT = False
    lw_, ll_ = 0.68 * BLADE * H, 1.4 * BLADE * H    # its half width and length
    phrase = style.get("phrase", PHRASES[0]).split()

    s = -1 if flip else 1
    P = lambda u, v: (cx + s * u, cy + v)
    line = lambda pts: densify([P(u, v) for u, v in pts])
    out: list[Polyline] = []

    def ring(uc: float, vc: float, r: float, a0: float = 0.0, a1: float = 2 * math.pi, n: int = 48) -> Polyline:
        return line([(uc + r * math.cos(a0 + (a1 - a0) * i / n), vc + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)])

    u0 = -L / 2
    pr = 0.11 * H                   # the pommel's half size
    gh = 0.065 * H                  # the grip's half height
    g0 = u0 + 2 * pr                # where the pommel meets the grip
    glen = 0.15 * L
    gt = 0.07 * H                   # the guard bar's thickness
    gq = 0.4 * H                    # the guard's half span
    qm = g0 + glen + gt / 2         # the guard's middle
    bw0 = BLADE * H
    tip = L / 2

    # --- pommel: returns where the grip starts
    if POMMEL == "diamond-dot":
        R = 1.3 * pr                     # a little larger than the pommel's size, to weigh as the discs do
        dc = g0 - R
        out.append(line([(dc - R, 0), (dc, -R), (dc + R, 0), (dc, R), (dc - R, 0)]))
        # a second stroke inside, small enough that it closes to a dot
        ip = 0.22
        out.append(line([(dc - ip, 0), (dc, -ip), (dc + ip, 0), (dc, ip), (dc - ip, 0)]))
        # the grip's outline runs on from the diamond's edges to its tip, and the grip proper
        # (its wrap and pattern) starts there, so nothing crosses into the diamond
        out += [line([(g0 - gh, sy * gh), (g0, sy * gh)]) for sy in (-1, 1)]
        gs = g0
    elif POMMEL in ("wheel", "cross"):
        r = pr * 1.05
        c = g0 - r
        # the grip meets the disc where its lines cross it
        gs = c + math.sqrt(r * r - gh * gh)
        out.append(ring(c, 0, r))
        if POMMEL == "wheel":
            out.append(ring(c, 0, 0.45 * r))
        else:
            # a cross in the disc
            q = 0.55 * r
            out += [line([(c - q, 0), (c + q, 0)]), line([(c, -q), (c, q)])]
    elif POMMEL == "lobed":
        # simplified: a bar across the grip's end with one low dome beyond it
        bar_h = 1.2 * pr
        bt = 0.35 * pr
        out.append(line([(g0, -bar_h), (g0 - bt, -bar_h), (g0 - bt, bar_h), (g0, bar_h), (g0, -bar_h)]))
        dome = [(g0 - bt - 0.9 * pr * math.cos(a_), bar_h * 0.85 * math.sin(a_)) for a_ in
                [-math.pi / 2 + math.pi * i / 30 for i in range(31)]]
        out.append(line(dome))
        gs = g0
    elif POMMEL in ("slot", "button", "clover"):
        # a disc on a short collar; "slot": a long oval inside it, along the blade;
        # "button": a cross inside and a small knob beyond it
        cl, ch = 0.22 * pr, 1.3 * gh
        # the clover's and spade's discs larger, so their emblems read; their grips a
        # little shorter for it
        big = POMMEL == "clover"
        r = (1.5 if big else 1.25) * pr
        g0 = g0 + (0.5 * pr if big else 0.0)
        c = g0 - cl - r * 0.97
        out.append(line([(g0, -ch), (g0 - cl, -ch), (g0 - cl, ch), (g0, ch), (g0, -ch)]))
        # the disc, open where the collar meets it
        a_ = math.asin(min(0.99, ch / r))
        out.append(ring(c, 0, r, a_, 2 * math.pi - a_, 48))
        if POMMEL == "slot":
            out.append(line([(c + 0.55 * r * math.cos(t_), 0.24 * r * math.sin(t_)) for t_ in [2 * math.pi * i / 32 for i in range(33)]]))
        else:
            if POMMEL == "button":
                q = 0.5 * r
                out += [line([(c - q, 0), (c + q, 0)]), line([(c, -q), (c, q)])]
            elif POMMEL == "clover":
                # a three-leaf clover nearly filling the disc, a leaf pointing away from
                # the grip; its stem runs from the disc's edge into the clover's centre,
                # and the leaves' outline stops short of it
                from shapely.geometry import Point
                from shapely.ops import unary_union
                ld, lr = 0.38 * r, 0.36 * r
                leaves = unary_union([Point(c + ld * math.cos(a), ld * math.sin(a)).buffer(lr, 32)
                                      for a in (math.pi, math.pi / 3, -math.pi / 3)])
                gapw = 0.30 * r
                piece: list[Pt] = []
                pieces = []
                for uu, vv in leaves.exterior.coords:
                    if uu > c and abs(vv) < gapw:
                        if len(piece) > 1:
                            pieces.append(piece)
                        piece = []
                    else:
                        piece.append((uu, vv))
                if len(piece) > 1:
                    pieces.append(piece)
                if len(pieces) > 1 and pieces[0][0] == pieces[-1][-1]:     # rejoin across the ring's start
                    pieces = [pieces[-1] + pieces[0][1:]] + pieces[1:-1]
                out += [line(pc) for pc in pieces]
                out.append(line([(c, 0), (c + 0.9 * r, 0)]))
            # the knob: a small circle sitting on the disc's far side
            kr = 0.32 * r
            kc = c - r - kr * 0.75
            ka = math.acos(min(1.0, (r * r - (r + kr * 0.75) ** 2 - kr * kr) / (-2 * (r + kr * 0.75) * kr)))
            out.append(ring(kc, 0, kr, ka - 2 * math.pi + 2 * math.pi, 2 * math.pi - ka, 24))
        gs = g0
    elif POMMEL == "fluted":
        # a cylinder on a collar, widening a little toward its rounded end (a gentle version of
        # the fishtail's flare), with two flutes that follow the taper so it reads as round
        cl, ch = 0.22 * pr, 1.3 * gh
        hw0, hw1 = 0.8 * pr, 1.0 * pr        # half width by the collar, and at the far end
        ln = 1.5 * pr
        u1 = g0 - cl
        out.append(line([(g0, -ch), (u1, -ch), (u1, ch), (g0, ch), (g0, -ch)]))
        hwu = lambda u: hw0 + (hw1 - hw0) * (u1 - u) / ln
        body = ([(u1, -hw0), (u1 - ln, -hw1)] + [(u1 - ln - hw1 * math.sin(a_), -hw1 * math.cos(a_)) for a_ in [math.pi * i / 24 for i in range(25)]]
                + [(u1 - ln, hw1), (u1, hw0)])
        out.append(line(body))
        for sv in (-1, 1):
            ua, ub = u1 - 0.2 * pr, u1 - ln - 0.25 * pr
            out.append(line([(ua, sv * 0.42 * hwu(ua)), (ub, sv * 0.42 * hwu(ub))]))
        gs = g0
    elif POMMEL == "onion":
        # a finial: a short neck, a smooth bulb, then curving in to a point
        nk = 0.3 * pr

        def bez(ps, n=16):
            k_ = len(ps) - 1
            from math import comb
            return [tuple(sum(comb(k_, j) * (1 - s) ** (k_ - j) * s ** j * ps[j][c] for j in range(k_ + 1)) for c in (0, 1))
                    for s in [i / n for i in range(n + 1)]]
        top = [(g0, gh)]
        top += bez([(g0 - nk, gh), (g0 - nk, 1.35 * pr), (g0 - 1.75 * pr, 1.3 * pr), (g0 - 1.95 * pr, 0.5 * pr)])
        top += bez([(g0 - 1.95 * pr, 0.5 * pr), (g0 - 2.05 * pr, 0.14 * pr), (g0 - 2.5 * pr, 0.0)])[1:]
        out.append(line(top + [(u_, -v_) for u_, v_ in reversed(top[:-1])]))
        out.append(line([(g0 - nk, -gh), (g0 - nk, gh)]))
        gs = g0
    elif POMMEL == "fishtail":
        # a collar, then flaring out to two points, the end between them rounded out, a ridge
        # down the middle
        nk = 0.25 * pr
        n = 16
        q = lambda p0, c, p2: [((1 - s) ** 2 * p0[0] + 2 * (1 - s) * s * c[0] + s * s * p2[0],
                                (1 - s) ** 2 * p0[1] + 2 * (1 - s) * s * c[1] + s * s * p2[1]) for s in [i / n for i in range(n + 1)]]
        tipt = (g0 - 2.2 * pr, 1.35 * pr)
        top = [(g0, gh), (g0 - nk, gh)]
        top += q((g0 - nk, gh), (g0 - 1.2 * pr, gh), tipt)[1:]                 # the flare, hollowed
        top += q(tipt, (g0 - 2.75 * pr, 0.75 * pr), (g0 - 2.75 * pr, 0.0))[1:]  # a rounded, convex end
        out.append(line(top + [(u_, -v_) for u_, v_ in reversed(top[:-1])]))
        out.append(line([(g0 - nk, -gh), (g0 - nk, gh)]))
        out.append(line([(g0 - nk - 0.35 * pr, 0.0), (g0 - 2.45 * pr, 0.0)]))     # a ridge down its middle
        gs = g0
    elif POMMEL == "stepped":
        # a collar a little wider than the grip, then the stepped tiers
        a, b = 0.55 * pr, pr
        cl, ch = 0.3 * pr, 1.35 * gh
        out.append(line([(g0, -ch), (g0 - cl, -ch), (g0 - cl, ch), (g0, ch), (g0, -ch)]))
        # a neck at the grip's width between the collar and the first step
        nk_ = 0.75 * pr
        g1_ = g0 - cl - nk_
        # the steps: up from the neck to the body, down again to a narrower end
        top = [(g0 - cl, gh), (g1_, gh), (g1_, b), (u0 + 0.1 * pr, b), (u0 + 0.1 * pr, a), (u0 - 0.45 * pr, a)]
        out.append(line(top + [(u_, -v_) for u_, v_ in reversed(top)]))
        gs = g0
    else:
        raise SystemExit(f"unknown POMMEL {POMMEL}")
    # where each part's lines end in `out`, and the numbers that place the later parts, for
    # build.py to cut the sword into prerendered pieces
    global STAGES
    STAGES = {"pommel": len(out), "gs": gs}

    # --- guard: its lines, and its faces toward the grip and the blade at a height v
    if GUARD in ("diamond", "block"):
        q0, q1 = qm - gt / 2, qm + gt / 2
        if GUARD == "diamond":
            d = 0.09 * H
            for sy in (-1, 1):
                out.append(line([(qm, sy * (gq - d)), (qm - d * 0.8, sy * (gq - d * 0.6)), (qm, sy * gq),
                                 (qm + d * 0.8, sy * (gq - d * 0.6)), (qm, sy * (gq - d))]))
            e = gq - d
        else:
            cw, ch = 0.075 * H, 0.08 * H       # square caps, wider than the bar
            for sy in (-1, 1):
                out.append(line([(q0, sy * (gq - ch)), (qm - cw, sy * (gq - ch)), (qm - cw, sy * gq), (qm + cw, sy * gq),
                                 (qm + cw, sy * (gq - ch)), (q1, sy * (gq - ch))]))
            e = gq - ch
        out.append(line([(q0, -e), (q0, e)]))
        if LANGET:
            out.append(line([(q1, -e), (q1, -lw_), (q1 + ll_, 0.0), (q1, lw_), (q1, e)]))
            face_b = lambda v: q1 + ll_ * max(0.0, 1 - abs(v) / lw_)
        elif GPOINT:
            pa, pp = 0.5 * gq, 0.6 * gt / 2
            out.append(line([(q1, -e), (q1, -pa), (q1 + pp, 0.0), (q1, pa), (q1, e)]))
            face_b = lambda v: q1 + pp * max(0.0, 1 - abs(v) / pa)
        else:
            out.append(line([(q1, -e), (q1, e)]))
            face_b = lambda v: q1
        face_g = lambda v: q0
    elif GUARD == "turned":
        bend = 0.12 * H
        tg2 = 0.7 * gt                    # half the band's thickness: a little heavier than the bar's
        cu = lambda t: qm + bend * t * t
        n = 30
        out.append(line([(cu(t) - tg2, gq * t) for t in [-1 + 2 * i / n for i in range(n + 1)]]))
        front_ = [(cu(t) + tg2, gq * t) for t in [-1 + 2 * i / n for i in range(n + 1)]]
        if LANGET:                       # the front broken by the langet's point
            fa = cu(lw_ / gq) + tg2
            out.append(line([p_ for p_ in front_ if p_[1] <= -lw_] + [(fa, -lw_), (cu(0) + tg2 + ll_, 0.0), (fa, lw_)]
                            + [p_ for p_ in front_ if p_[1] >= lw_]))
        else:
            out.append(line(front_))
        # flared ends: a short bar across each end
        for sy in (-1, 1):
            ue = cu(1.0)
            out.append(line([(ue - tg2 * 2.2, sy * gq), (ue + tg2 * 2.2, sy * gq)]))
        face_g = lambda v: cu(v / gq) - tg2
        if LANGET:
            face_b = lambda v: max(cu(v / gq) + tg2, cu(0) + tg2 + ll_ * (1 - abs(v) / lw_))
        else:
            face_b = lambda v: cu(v / gq) + tg2
    elif GUARD in ("flared", "pointed", "concave", "concave-arc"):
        # drawn as one outline (a shapely shape in u, v), its faces found from it
        from shapely.geometry import LineString, Point, Polygon as SPoly
        from shapely.ops import unary_union
        h2 = gt / 2

        def arm(c, hw, reach: float, cap: str = "round"):
            """A bar along v from -reach to reach: its centre line at u = c(v), half its
            width hw(v) measured square to the centre line, round or square ends."""
            n = 80
            vs = [-reach + 2 * reach * i / n for i in range(n + 1)]
            left, right = [], []
            for v in vs:
                dv = 1e-4
                du = (c(v + dv) - c(v - dv)) / (2 * dv)
                nl = math.hypot(1, du)
                nu, nv = 1 / nl, -du / nl              # the normal, toward the blade
                left.append((c(v) + hw(v) * nu, v + hw(v) * nv))
                right.append((c(v) - hw(v) * nu, v - hw(v) * nv))
            g = SPoly(left + list(reversed(right))).buffer(0)
            if cap == "round":
                g = unary_union([g, Point(c(reach), reach).buffer(hw(reach), 32), Point(c(-reach), -reach).buffer(hw(-reach), 32)])
            return g

        flare = lambda v, start, k_: 1 + k_ * max(0.0, (abs(v) - start * gq) / ((1 - start) * gq)) ** 1.6
        extras: list[list[Pt]] = []       # lines drawn inside the outline
        if GUARD == "flared":            # thick in the middle, narrowing, then flaring smoothly to
            # broad square-cut ends (the reference's last)
            fw = lambda v: h2 * (0.85 + 3.2 * (abs(v) / gq - 0.45) ** 2)
            shape = arm(lambda v: qm, fw, gq, "square")
        elif GUARD == "pointed":         # a bar whose ends sweep forward into points: the back edge
            n = 20                       # swelling out behind and round to the point, the front edge
            hb = 1.3 * h2                # curving sharply back in to the bar (the reference's first)
            tl, tw_ = 0.07 * H, 0.075 * H    # the point's length and width; the curves start further out
            ro = 0.095 * H

            def cubic(p0, c1, c2, p3):
                return [tuple((1 - s) ** 3 * p0[k] + 3 * (1 - s) ** 2 * s * c1[k] + 3 * (1 - s) * s * s * c2[k] + s ** 3 * p3[k]
                              for k in (0, 1)) for s in [i / (2 * n) for i in range(2 * n + 1)]]
            tipp = (qm + hb + tl, gq + 0.02 * H)
            # the top end: leaving the back in line with it, swelling out and round to the point,
            # then from the point curving sharply back to the front face
            rb, rv = -0.04, 0.14         # the outer curve rounding out past the end
            end = cubic((qm - hb, gq - ro), (qm - hb, gq + 0.1 * ro), (qm - hb - rb * H, gq + rv * H), tipp)
            end += cubic(tipp, (qm + hb + 0.3 * tl, gq - 0.05 * tw_), (qm + hb, gq - 0.45 * tw_), (qm + hb, gq - tw_))[1:]
            bottom = [(u_, -v_) for u_, v_ in end]
            shape = SPoly(list(reversed(bottom)) + end)
            if GPOINT:
                pa, pp = 0.5 * gq, 0.6 * hb
                shape = unary_union([shape, SPoly([(qm + hb - 0.01, -pa), (qm + hb + pp, 0.0), (qm + hb - 0.01, pa)])])
        elif GUARD in ("concave", "concave-arc"):
            # a hollowed front, thin in the middle and wider toward the ends. "concave": a flat back,
            # the ends slanting out a little going forward so it flares; "concave-arc": the back
            # curved too (less than the front), the ends slanting in a little toward the blade
            tc, te = 2.4 * h2, 4.6 * h2      # thicker in the middle, the same at the tips
            p_ = 2.6                         # flat through the middle, curving up toward the ends
            n = 40
            arc_ = GUARD == "concave-arc"
            kb = 0.55 * (te - tc) if arc_ else 0.0
            fl = (-0.06 if arc_ else 0.06) * gq              # the front corners' reach past the back's
            vs = [-gq + 2 * gq * i / n for i in range(n + 1)]
            gf = gq + fl
            vf = [-gf + 2 * gf * i / n for i in range(n + 1)]
            back = [(qm - h2 + kb * abs(v / gq) ** 2, v) for v in vs]
            front = [(qm - h2 + tc + (te - tc + kb) * abs(v / gf) ** p_, v) for v in reversed(vf)]
            shape = SPoly(back + front)
        def across(v: float) -> tuple[float, float]:
            cut = shape.intersection(LineString([(qm - 10, v), (qm + 10, v)]))
            x0_, _, x1_, _ = cut.bounds
            return x0_, x1_
        if LANGET:
            fl_, fr_ = across(-lw_)[1], across(lw_)[1]
            shape = unary_union([shape, SPoly([(fl_ - 0.02, -lw_), (across(0.0)[1] + ll_, 0.0), (fr_ - 0.02, lw_)])])
        out.append(line(list(shape.exterior.coords)))
        out += [line(e) for e in extras]
        face_g = lambda v: across(v)[0]
        face_b = lambda v: across(v)[1]
    else:
        raise SystemExit(f"unknown GUARD {GUARD}")
    STAGES["guard"] = len(out)

    # --- grip, from gs to the guard: the same height at both ends (where the pommel and
    # guard meet it), its profile a little different by style, and a different wrap
    ge = face_g(gh)
    glen_ = ge - gs
    U = lambda t: gs + glen_ * t
    # the profiles: the same height at both ends, shaped clearly in between
    if GRIP in ("twist", "ribbed", "stitched"):     # swelling in the middle
        sw_ = {"twist": 0.28, "ribbed": 0.22, "stitched": 0.28}[GRIP]
        w = lambda t: gh * (1 + sw_ * math.sin(math.pi * t))
    elif GRIP == "risers":               # three bumps where cords run under the leather
        w = lambda t: gh * (1 + 0.32 * sum(math.exp(-((t - c_) / 0.065) ** 2) for c_ in (0.25, 0.5, 0.75)))
    else:                                # wrap, lattice, wire, bands: straight
        w = lambda t: gh
    n = 40
    # the twist's cord turns lie over the grip: its outline breaks either side of each
    m_tw = 5
    tw_over = 0.22                              # how far a turn reaches past the outline, of w
    tw_raw = lambda t0, s_: t0 - 0.38 / m_tw * s_ - 0.3 / m_tw * (1 - s_ * s_)
    # the turns, overhang and all, fitted between the pommel and the guard with a
    # margin, so none runs into either
    tw_e = 1 + tw_over
    tw_ss = [-tw_e + 2 * tw_e * j / 48 for j in range(49)]
    tw_lo = min(tw_raw(0.5 / m_tw, s_) for s_ in tw_ss)
    tw_hi = max(tw_raw(1 - 0.5 / m_tw, s_) for s_ in tw_ss)
    tw_m = 0.7 / glen_                            # 0.7 mm, centre to centre: a clear gap after the pen
    tw_t = lambda t0, s_: tw_m + (tw_raw(t0, s_) - tw_lo) * (1 - 2 * tw_m) / (tw_hi - tw_lo)
    for sy in (-1, 1):
        if GRIP == "twist":
            cuts = sorted(tw_t((i + 0.5) / m_tw, -sy) for i in range(m_tw))
            gap_t = 0.22 / glen_
            ts = [i / (4 * n) for i in range(4 * n + 1)]
            seg: list[Pt] = []
            for tt in ts:
                if any(abs(tt - c_) < gap_t for c_ in cuts):
                    if len(seg) > 1:
                        out.append(line(seg))
                    seg = []
                else:
                    seg.append((U(tt), sy * w(tt)))
            if len(seg) > 1:
                out.append(line(seg))
        else:
            out.append(line([(U(i / n), sy * w(i / n)) for i in range(n + 1)]))

    if GRIP == "wrap":           # straight diagonal turns of a strap
        for i in range(6):
            a, b = (i + 0.2) / 6, (i + 0.8) / 6
            out.append(line([(U(a), w(a)), (U(b), -w(b))]))
    elif GRIP == "twist":        # round turns of a cord, standing out past the grip's outline
        for i in range(m_tw):
            t0 = (i + 0.5) / m_tw
            pts = []
            e = 1 + tw_over
            for j in range(25):
                s_ = -e + 2 * e * j / 24                    # across the grip and a little past it
                # a diagonal bowed toward the pommel, so each turn looks round
                tt = tw_t(t0, s_)
                pts.append((U(tt), -s_ * w(tw_t(t0, max(-1.0, min(1.0, s_))))))
            out.append(line(pts))
    elif GRIP == "lattice":      # crossed straps making diamonds, like the panel's lattice
        m = 4
        for i in range(m + 1):
            a = i / m
            for d in (-1, 1):
                b = a + d / m
                lo, hi = max(0.0, min(a, b)), min(1.0, max(a, b))
                if hi - lo < 1e-6:
                    continue
                # clip the diagonal from (a, top) to (b, bottom) to the grip's length
                f = lambda t: (t - a) / (b - a)            # 0 at the top, 1 at the bottom
                t0, t1 = lo, hi
                p0 = (U(t0), w(t0) * (1 - 2 * f(t0)))
                p1 = (U(t1), w(t1) * (1 - 2 * f(t1)))
                out.append(line([p0, p1]))
    elif GRIP == "wire":         # twisted wire: each turn a column of short slanted ticks, the
        m = 5                    # next turn twisted the other way, so the rows make a herringbone
        for i in range(m):
            tc = (i + 0.5) / m
            d = 1 if i % 2 else -1
            for j in range(2):
                v0 = -1 + j + 0.15
                v1 = j - 0.15
                dt = d * 0.2 / m
                out.append(line([(U(tc - dt), v0 * w(tc)), (U(tc + dt), v1 * w(tc))]))
    elif GRIP == "ribbed":       # many even rings
        for i in range(1, 8):
            tt = i / 8
            out.append(line([(U(tt), -w(tt)), (U(tt), w(tt))]))
    elif GRIP == "bands":        # plain, with pairs of rings at the ends and the middle
        for tc in (0.13, 0.5, 0.87):
            for dt in (-0.045, 0.045):
                tt = tc + dt
                out.append(line([(U(tt), -w(tt)), (U(tt), w(tt))]))
    elif GRIP == "risers":       # a ring over each riser
        for tc in (0.25, 0.5, 0.75):
            out.append(line([(U(tc), -w(tc)), (U(tc), w(tc))]))
    elif GRIP == "stitched":     # leather with a stitched seam down the middle
        k_ = 7
        for i in range(k_):
            a, b = (i + 0.2) / k_, (i + 0.75) / k_
            out.append(line([(U(a), 0.0), (U(b), 0.0)]))
    else:
        raise SystemExit(f"unknown GRIP {GRIP}")
    STAGES["grip"] = len(out)

    # --- blade: its top edge from the base, then the point; the bottom mirrors it
    q1 = face_b(bw0)
    grind = None                             # a ground section's V edge, for the fuller to stop on
    if BASE == "plain":
        base = [(face_b(bw0), bw0)]
        body0 = max(q1, face_b(0.0))
    elif BASE == "ricasso":
        nw = 0.62 * bw0
        a = face_b(nw)
        base = [(a, nw), (a + 1.4 * bw0, nw), (a + 1.9 * bw0, bw0)]
        body0 = a + 0.5 * bw0                # the fuller runs on into the narrow section
    elif BASE == "waist":
        # the edges curving in a little and out again just past the guard: a subtle bite taken
        # out of the blade by the hilt
        f_ = face_b(bw0)
        L_ = 3.0 * bw0
        base = [(f_ + L_ * i / 24, bw0 * (1 - 0.2 * math.sin(math.pi * i / 24))) for i in range(25)]
        body0 = max(q1, face_b(0.0))
    elif BASE == "taper":
        # the blade narrowing all the way to the guard, as the ricasso does but without the step;
        # this part ground flat, its edge a V across the blade where the fuller begins
        nw = 0.8 * bw0                       # a gentle taper
        a = face_b(nw)
        ut = a + 1.2 * bw0                   # where the taper reaches the full width (short)
        uv = ut + 0.9 * bw0                  # the V's point, on the middle
        base = [(a, nw), (ut, bw0)]
        out.append(line([(ut, -bw0), (uv, 0.0), (ut, bw0)]))
        grind = (ut, uv)
        body0 = uv
    elif BASE == "ecusson":
        # a small shield-shaped plate on the guard's front, pointing down the blade: square
        # shoulders, then curving in to a point
        e_ = 1.2 * bw0
        f_ = face_b(e_)
        sh_ = [(f_, -e_)]
        for i in range(13):
            tt = i / 12
            sh_.append((f_ + 0.35 * bw0 + 0.9 * bw0 * tt, -e_ * (1 - tt ** 1.6)))
        plate = sh_ + [(u_, -v_) for u_, v_ in reversed(sh_[:-1])]
        out.append(line(plate))
        # the blade's edges start where they meet the plate
        ttb = (1 - bw0 / e_) ** (1 / 1.6)
        base = [(f_ + 0.35 * bw0 + 0.9 * bw0 * ttb, bw0)]
        body0 = f_ + 1.25 * bw0
    elif BASE == "wrap":
        # a short band wrapped round the blade just beyond the guard, a little wider than the blade
        # (a chappe or binding, as on several medieval swords); the edges come out from under it
        cw_, cl_ = 1.18 * bw0, 0.85 * bw0
        f_ = face_b(cw_)
        out.append(line([(f_, -cw_), (f_ + cl_, -cw_), (f_ + cl_, cw_), (f_, cw_)]))
        base = [(f_ + cl_, bw0)]
        body0 = f_ + cl_
    elif BASE == "lugs":
        # a narrow ricasso ending in a pair of small hooks on the edges, pointing back toward the
        # hilt: the parrying lugs of a two-hander
        nw = 0.62 * bw0
        a = face_b(nw)
        u1 = a + 2.1 * bw0
        base = [(a, nw), (u1, nw), (u1 - 0.55 * bw0, 1.4 * bw0), (u1 + 0.1 * bw0, 1.45 * bw0), (u1 + 0.5 * bw0, bw0)]
        body0 = a + 0.5 * bw0                # the fuller runs on into the narrow section, past the lugs
    elif BASE == "choil":
        # a small round notch in each edge just past the guard, where the edge's sharpening stops
        f_ = face_b(bw0)
        r_ = 0.32 * bw0
        uc = f_ + 0.7 * bw0 + r_
        notch = [(uc - r_ * math.cos(a_), bw0 - r_ * math.sin(a_)) for a_ in [math.pi * i / 16 for i in range(17)]]
        base = [(f_, bw0)] + notch
        body0 = max(q1, face_b(0.0))
    else:
        raise SystemExit(f"unknown BASE {BASE}")

    if TIP == "long":
        sh = tip - 3.4 * bw0
        point = [(sh, 0.77 * bw0), (tip, 0.0)]
        ridge_stop = sh - 0.4 * bw0          # the fullers stop short of the point, uncrowded
    elif TIP == "longer":
        # the long point drawn out nearly twice as far; the fullers stop well before it
        sh = tip - 6.5 * bw0
        point = [(sh, 0.8 * bw0), (tip, 0.0)]
        ridge_stop = sh - 0.6 * bw0
    elif TIP == "ogive":
        # straight, then edges curving in to a sharp point (a parabola)
        sh = tip - 7.0 * bw0
        w1 = 0.8 * bw0
        point = [(sh + (tip - sh) * t, w1 * (1 - t * t)) for t in [i / 24 for i in range(25)]]
        ridge_stop = sh + 0.3 * (tip - sh)
    elif TIP == "leaf":
        # the edge from well back on the blade to the point as one clamped cubic spline (so its
        # slope and curvature run on without a break): it leaves the straight blade along its line,
        # bends out once into a broad swell, and curves over and in to the point at the cosine's
        # angle, with a single inflection. Lengths in blade half-widths from the tip: the swell
        # starts 17 back
        L_ = 17.0 * bw0
        sh = tip - L_
        # the straight blade narrows at the long tip's rate, so it is as wide by the inscription as
        # the other blades
        sh_long = tip - 3.4 * bw0
        w1 = bw0 + (0.77 * bw0 - bw0) * (sh - q1) / (sh_long - q1)
        wm = w1 + 0.19 * bw0
        bu, bv = base[-1]
        s0 = (w1 - bv) / (sh - bu) * L_          # the straight edge's slope, per unit of t
        k_end = -wm * math.pi / 2 / (6.5 / 17)   # the point's angle, as the cosine version's
        cs = clamped_spline([0.0, 0.5, 0.8, 1.0], [w1, 1.02 * wm, 0.72 * wm, 0.0], s0, k_end)
        point = [(sh + L_ * t, float(cs(t))) for t in [i / 120 for i in range(121)]]
        point[-1] = (tip, 0.0)
        ridge_stop = tip - 6.0 * bw0
    else:
        raise SystemExit(f"unknown TIP {TIP}")
    top = base + point
    out.append(line([(u, -v) for u, v in top]))
    out.append(line([(u, v) for u, v in top]))
    STAGES.update(blade=len(out), q1=q1, body0=body0, grind=grind, ridge_stop=ridge_stop)

    # --- the inscription by the hilt, then the fuller on to the point
    tall = max(box(n_)[3] - box(n_)[2] for n_ in phrase) / 2
    h = 0.7 * bw0 / tall
    gap = 0.75 * bw0
    clear = 0.7 * bw0
    # where the fuller (or ridge) starts, and a run before the inscription long enough not to be
    # read as a sign: the inscription moves down the blade if the base would cut it short
    if FULLER in ("double", "double-round"):
        r0 = grind[0] + (grind[1] - grind[0]) * (1 - FULLER_GAP) if grind else body0 + 0.3 * bw0
    else:
        r0 = body0
    start = max(q1 + LEAD * bw0, r0 + clear + MIN_RUN * bw0)
    x = start
    cuneiform.STYLE = STYLE
    for name in phrase:
        x0_, x1_, _, _ = box(name)
        w = (x1_ - x0_) * h
        px, py = P(x + w / 2, 0)
        out += sign(name, px, py, h, ang=math.pi if flip else 0.0, head=HEAD)
        x += w + gap
    end = x - gap
    STAGES.update(inscription=len(out), start=start, end=end)
    # the fullers always run a little way past the inscription, however long it is
    ridge_stop = max(ridge_stop, end + clear + 2.0 * bw0)
    global LAST_LEAD
    if FULLER == "ridge":
        LAST_LEAD = start - clear - body0
        out.append(line([(body0, 0), (start - clear, 0)]))
        out.append(line([(end + clear, 0), (ridge_stop, 0)]))
    elif FULLER in ("double", "double-round"):
        # two lines a little off the middle: short ones before the inscription, long
        # ones after it closing to meet short of the point
        f = FULLER_GAP * bw0
        if grind:                            # starting on the ground section's V
            s0 = grind[0] + (grind[1] - grind[0]) * (1 - f / bw0)
        else:
            s0 = body0 + 0.3 * bw0
        LAST_LEAD = start - clear - s0
        out += [line([(s0, sy * f), (start - clear, sy * f)]) for sy in (-1, 1)]
        meet = ridge_stop
        if FULLER == "double":           # the lines closing to a point
            for sy in (-1, 1):
                cv = max(end + clear, meet - 3.0 * bw0)       # where the lines start closing
                out.append(line([(end + clear, sy * f), (cv, sy * f), (meet, 0.0)]))
        else:                            # a groove ending round, as most fullers do
            ea = 2.4 * f                 # a long half ellipse, easing round rather than a half circle
            c_ = meet - ea
            out.append(line([(end + clear, -f), (c_, -f)]
                            + [(c_ + ea * math.sin(a_), -f * math.cos(a_)) for a_ in [math.pi * i / 24 for i in range(25)]]
                            + [(end + clear, f)]))
    elif FULLER == "none":               # the inscription alone (for proofing the text)
        pass
    else:
        raise SystemExit(f"unknown FULLER {FULLER}")
    return out


# --- the parts library, and random swords drawn from it --------------------------------
PARTS = {
    "pommel": ["diamond-dot", "wheel", "cross", "slot", "clover", "onion", "fishtail", "fluted", "lobed", "stepped"],
    "grip": ["wrap", "twist", "lattice", "wire", "ribbed", "bands", "risers", "stitched"],
    "guard": ["pointed", "concave", "concave-arc", "turned", "flared", "diamond", "block"],
    "base": ["plain", "ricasso", "waist", "taper", "ecusson", "wrap", "lugs", "choil"],
    "fuller": ["ridge", "double", "double-round"],
    "tip": ["long", "longer", "ogive", "leaf"],
}
PHRASES = [
    # "weapon of ..." (GIŠ.TUKUL, written GIŠ KU, then what it belongs to)
    "GIŠ KU A MA RU",       # the deluge (abūbu)
    "GIŠ KU BAD",           # death
    "GIŠ KU AN GIŠ BAR",    # Gibil, the fire god
    "GIŠ KU AN 40",         # Ea, god of the waters
    "GIŠ KU DA GUD",        # with the strength of the ox (á gu4)
    "GIŠ KU SI GUD",        # like the horn of the ox (si gu4)
    "GIŠ KU GUD AN",        # of the Bull of Heaven (gu4-an-na)
    "GIŠ KU DA UR MAH",     # with the strength of the lion (á ur-maḫ)
    "GIŠ KU ŠA UR MAH",     # with the heart of a lion (ša3 ur-maḫ)
    "GIŠ KU UR BAR RA",     # of the wolf (ur-bar-ra)
    "GIŠ KU SAG GIŠ RA",    # that strikes down (saĝ-ĝiš ra)
    "GIŠ KU UD GAL",        # of the great storm (u4 gal)
    "GIŠ KU DA KUR",        # with the strength of the mountain (á kur)
    "GIŠ KU KUR GAL",       # of the Great Mountain, Enlil (kur gal)
    "GIŠ KU UR SAG",        # of the hero (ur-saĝ)
    "GIŠ KU UR SAG GAL",    # of the great hero
    "GIŠ KU DA UR SAG",     # with the strength of the hero
    "GIŠ KU DA GAL",        # of great strength (á gal)
    "GIŠ KU GUD GAL",       # of the great bull
    "GIŠ KU UR MAH GAL",    # of the great lion
    "GIŠ KU ŠA GUD",        # with the heart of the ox
    "GIŠ KU SI GAL",        # of the great horn
    "GIŠ KU NE GAL",        # of the great fire (izi gal)
    "GIŠ KU A NE",          # of water and fire
    "GIŠ KU UD MI",         # of day and night (u4 ĝi6)
    "GIŠ KU SAG TAR",       # that cuts off heads (saĝ kud)
    "GIŠ KU NE",            # of fire (izi)
    "GIŠ KU DA KAL",        # of strength (usu, written Á.KAL)
    "GIŠ KU AN KAL",        # of the Lamma, the protective spirit
    "GIŠ KU EN DU",         # of song (en3-du)
    "GIŠ KU E NE DI",       # of play and dance (e-ne-di)
    "GIŠ KU MI MI",         # of darkness (kukku)
]
LANGET_ODDS = 0.3
FULLER_GAP = 0.22   # the double fuller's lines, either side of the middle, in blade half-widths
MIN_RUN = 2.6       # the fuller's shortest run before the inscription, in blade half-widths
LAST_LEAD = None    # the last sword's fuller run before its inscription, for checking MIN_RUN
STAGES: dict = {}   # the last sword's pieces (see sword())


def allowed(style: dict[str, str]) -> bool:
    """The combinations that don't work: a langet with the bases that cover the same place."""
    return not (style.get("langet") == "1" and style.get("base") in ("ecusson", "wrap"))


def random_style(rng, **fixed: str) -> dict[str, str]:
    """A random sword: each part drawn from PARTS (fixed ones kept), a langet now and then, a
    phrase, redrawn until the combination is allowed."""
    while True:
        style = {k: fixed.get(k, rng.choice(v)) for k, v in PARTS.items()}
        style["langet"] = fixed.get("langet", "1" if rng.random() < LANGET_ODDS else "0")
        style["phrase"] = fixed.get("phrase", rng.choice(PHRASES))
        if allowed(style):
            return style
