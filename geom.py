"""The two geometry helpers swordgen and cuneiform need from cardgen, without its other dependencies."""
from __future__ import annotations

import math
from collections.abc import Sequence

Point = tuple[float, float]
Polyline = list[Point]

STEP = 0.15  # mm, sampling resolution for curves


def densify(poly: Sequence[Point], step: float = STEP) -> Polyline:
    """Insert points so no segment is longer than `step` (for clean clipping)."""
    out = [poly[0]]
    for (x0, y0), (x1, y1) in zip(poly, poly[1:]):
        d = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(d / step))
        out.extend((x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(1, n + 1))
    return out


def clamped_spline(xs: Sequence[float], ys: Sequence[float], d0: float, d1: float):
    """A cubic spline through (xs, ys) with its slope fixed at both ends to d0 and d1, as
    scipy's CubicSpline(xs, ys, bc_type=((1, d0), (1, d1))), so swordgen needs no scipy."""
    n = len(xs) - 1
    h = [xs[i + 1] - xs[i] for i in range(n)]
    sl = [(ys[i + 1] - ys[i]) / h[i] for i in range(n)]
    # the tridiagonal system for the second derivatives M at the knots
    a = [0.0] + h                                   # below the diagonal
    b = [2 * h[0]] + [2 * (h[i - 1] + h[i]) for i in range(1, n)] + [2 * h[-1]]
    c = h + [0.0]                                   # above the diagonal
    r = [6 * (sl[0] - d0)] + [6 * (sl[i] - sl[i - 1]) for i in range(1, n)] + [6 * (d1 - sl[-1])]
    for i in range(1, n + 1):                       # Thomas algorithm
        f = a[i] / b[i - 1]
        b[i] -= f * c[i - 1]
        r[i] -= f * r[i - 1]
    M = [0.0] * (n + 1)
    M[n] = r[n] / b[n]
    for i in range(n - 1, -1, -1):
        M[i] = (r[i] - c[i] * M[i + 1]) / b[i]

    def at(x: float) -> float:
        i = min(max(0, next((k for k in range(n) if x < xs[k + 1]), n - 1)), n - 1)
        p, q = xs[i + 1] - x, x - xs[i]
        return (M[i] * p ** 3 + M[i + 1] * q ** 3) / (6 * h[i]) + (ys[i] / h[i] - M[i] * h[i] / 6) * p \
            + (ys[i + 1] / h[i] - M[i + 1] * h[i] / 6) * q
    return at
