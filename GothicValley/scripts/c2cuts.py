# Boxes cut out of the Castle 2.0 shell (gate leaves, doorways, clutter inside the fitted rooms), exactly: triangles
# crossing a box are clipped by its planes and only the parts outside are kept. A cut is {x: [a, b], y: [a, b],
# z: [a, b]} in the centred model frame, or, with "angle" (deg) and "c" [cx, cy], x / y are ranges along the box's own
# axes (rotated by angle around c). Used by gb_castle2.py (walk-test triangles) and export_kit.py (Blender, bisect).
import math
import numpy as np


def planes(cut):
    """Box planes as (point, outward normal); a point is inside when it is behind all of them."""
    a = math.radians(cut.get("angle", 0.0)); cx, cy = cut.get("c", (0.0, 0.0))
    u = np.array([math.cos(a), math.sin(a), 0.0]); v = np.array([-math.sin(a), math.cos(a), 0.0]); w = np.array([0.0, 0.0, 1.0])
    o = np.array([cx, cy, 0.0])
    return [(o + u * cut["x"][0], -u), (o + u * cut["x"][1], u), (o + v * cut["y"][0], -v), (o + v * cut["y"][1], v),
            (w * cut["z"][0], -w), (w * cut["z"][1], w)]


def corners(cut):
    a = math.radians(cut.get("angle", 0.0)); cx, cy = cut.get("c", (0.0, 0.0))
    P = np.array([[x, y] for x in cut["x"] for y in cut["y"]])
    R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    return P @ R.T + [cx, cy]


def _split(poly, p0, n):
    """Split a convex polygon by a plane -> (part in front, part behind)."""
    d = (poly - p0) @ n
    front, back = [], []
    k = len(poly)
    for i in range(k):
        a, b, da, db = poly[i], poly[(i + 1) % k], d[i], d[(i + 1) % k]
        if da >= 0: front.append(a)
        if da <= 0: back.append(a)
        if (da > 0 > db) or (da < 0 < db):
            p = a + (b - a) * (da / (da - db)); front.append(p); back.append(p)
    f = np.array(front) if len(front) >= 3 else None
    b_ = np.array(back) if len(back) >= 3 else None
    return f, b_


def subtract(tris, cuts, eps=1e-6):
    """tris (n, 3, 3) minus the boxes -> (m, 3, 3), and the number of triangles removed or clipped."""
    out = tris
    touched = 0
    for cut in cuts:
        P = planes(cut)
        lo2, hi2 = corners(cut).min(0), corners(cut).max(0)
        mn, mx = out.min(1), out.max(1)
        cand = ((mx[:, 0] > lo2[0]) & (mn[:, 0] < hi2[0]) & (mx[:, 1] > lo2[1]) & (mn[:, 1] < hi2[1])
                & (mx[:, 2] > cut["z"][0]) & (mn[:, 2] < cut["z"][1]))
        idx = np.nonzero(cand)[0]
        if not len(idx):
            continue
        # exact test: a triangle is untouched when all its vertices are in front of one plane
        sep = np.zeros(len(idx), bool)
        for p0, n in P:
            sep |= (((out[idx] - p0) @ n) >= -eps).all(1)
        idx = idx[~sep]
        if not len(idx):
            continue
        touched += len(idx)
        keep = np.ones(len(out), bool); keep[idx] = False
        new = []
        for t in out[idx].astype(np.float64):
            poly = t
            for p0, n in P:
                f, poly = _split(poly, p0, n)
                if f is not None:
                    new.extend([f[0], f[i], f[i + 1]] for i in range(1, len(f) - 1))
                if poly is None:
                    break
        out = np.concatenate([out[keep], np.array(new, out.dtype).reshape(-1, 3, 3)]) if new else out[keep]
    return out, touched
