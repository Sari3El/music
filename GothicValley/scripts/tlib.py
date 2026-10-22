# Terrain helpers for the gothic valley (world metres: +X north, +Y east; arrays are [iy, ix], row = Y, column = X)
import numpy as np
from scipy import sparse, ndimage
from scipy.sparse.linalg import spsolve

HALF = 1512.0


def axis(n):
    return np.linspace(-HALF, HALF, n)


def grid(n):
    a = axis(n)
    X, Y = np.meshgrid(a, a)          # X varies along columns, Y along rows
    return X, Y


def spectral(n, beta, seed):
    r = np.random.default_rng(seed)
    f = np.sqrt(np.fft.fftfreq(n)[:, None] ** 2 + np.fft.fftfreq(n)[None, :] ** 2)
    f[0, 0] = 1
    z = np.real(np.fft.ifft2(np.fft.fft2(r.standard_normal((n, n))) * f ** (-beta / 2)))
    return ((z - z.mean()) / z.std()).astype(np.float32)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def catmull(P, step=4.0):
    """Catmull-Rom through the control points; returns dense points and, per dense point, the control-segment
    index + fraction (to interpolate attributes linearly along each original segment)."""
    P = np.asarray(P, float)
    E = np.vstack([P[0] * 2 - P[1], P, P[-1] * 2 - P[-2]])
    out, seg, frac = [], [], []
    for i in range(1, len(E) - 2):
        p0, p1, p2, p3 = E[i - 1], E[i], E[i + 1], E[i + 2]
        n = max(2, int(np.hypot(*(p2 - p1)) / step))
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
            seg.append(i - 1); frac.append(t)
    out.append(E[-2]); seg.append(len(P) - 2); frac.append(1.0)
    return np.array(out), np.array(seg), np.array(frac)


def densify(P, attrs, step=4.0, smooth=True):
    """Dense polyline (x, y) + linearly interpolated attributes (by control segment) + cumulative length."""
    P = np.asarray(P, float)
    A = np.asarray(attrs, float)
    if smooth and len(P) > 2:
        D, seg, frac = catmull(P, step)
    else:
        D, seg, frac = [], [], []
        for i in range(len(P) - 1):
            n = max(2, int(np.hypot(*(P[i + 1] - P[i])) / step))
            for t in np.linspace(0, 1, n, endpoint=False):
                D.append(P[i] + (P[i + 1] - P[i]) * t); seg.append(i); frac.append(t)
        D.append(P[-1]); seg.append(len(P) - 2); frac.append(1.0)
        D, seg, frac = np.array(D), np.array(seg), np.array(frac)
    # attributes: interpolate by arc length inside each control segment (constant speed along the curve)
    L = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(D, axis=0).T))])
    At = np.zeros((len(D), A.shape[1]))
    for s in range(len(P) - 1):
        m = seg == s
        if m.sum() == 0:
            continue
        idx = np.nonzero(m)[0]
        if s == len(P) - 2:
            idx = np.append(idx, len(D) - 1) if idx[-1] != len(D) - 1 else idx
        l0, l1 = L[idx[0]], L[min(idx[-1] + 1, len(D) - 1)] if s < len(P) - 2 else L[idx[-1]]
        u = (L[idx] - l0) / max(l1 - l0, 1e-6)
        At[idx] = A[s] * (1 - u[:, None]) + A[s + 1] * u[:, None]
    return D, At, L


def band_field(D, At, n, band):
    """Distance from every cell within `band` metres to the dense polyline D, nearest attributes and signed side.
    Returns dist (inf outside the band), attrs (n, n, k), side (+1 left / -1 right)."""
    a = axis(n); px = a[1] - a[0]
    dist = np.full((n, n), np.inf, np.float32)
    att = np.zeros((n, n, At.shape[1]), np.float32)
    side = np.zeros((n, n), np.int8)
    for i in range(len(D) - 1):
        p, q = D[i], D[i + 1]
        x0, x1 = min(p[0], q[0]) - band, max(p[0], q[0]) + band
        y0, y1 = min(p[1], q[1]) - band, max(p[1], q[1]) + band
        c0, c1 = max(0, int((x0 + HALF) / px)), min(n, int((x1 + HALF) / px) + 2)
        r0, r1 = max(0, int((y0 + HALF) / px)), min(n, int((y1 + HALF) / px) + 2)
        if c1 <= c0 or r1 <= r0:
            continue
        Xs, Ys = np.meshgrid(a[c0:c1], a[r0:r1])
        ab = q - p; L2 = ab @ ab
        if L2 < 1e-9:
            continue
        t = np.clip(((Xs - p[0]) * ab[0] + (Ys - p[1]) * ab[1]) / L2, 0, 1)
        dx, dy = Xs - (p[0] + t * ab[0]), Ys - (p[1] + t * ab[1])
        d = np.hypot(dx, dy)
        sub = dist[r0:r1, c0:c1]
        m = d < sub
        sub[m] = d[m]
        val = At[i][None, None, :] * (1 - t[..., None]) + At[i + 1][None, None, :] * t[..., None]
        att[r0:r1, c0:c1][m] = val[m]
        cr = ab[0] * dy - ab[1] * dx
        side[r0:r1, c0:c1][m] = np.where(cr[m] >= 0, 1, -1)
    return dist, att, side


def tension_interp(n, pts, vals, weights, tension=0.25, lam=50.0):
    """Smooth surface through scattered constraints: minimise (1-t)|Lap h|^2 + t|grad h|^2 + lam*w*(h(p)-v)^2."""
    a = axis(n); px = a[1] - a[0]
    N = n * n
    idx = np.arange(N).reshape(n, n)

    # gradient operators (forward differences)
    def diff(axis_):
        rows, cols, data = [], [], []
        if axis_ == 1:
            r = idx[:, :-1].ravel(); c = idx[:, 1:].ravel()
        else:
            r = idx[:-1, :].ravel(); c = idx[1:, :].ravel()
        k = np.arange(len(r))
        return sparse.csr_matrix((np.concatenate([-np.ones(len(r)), np.ones(len(r))]),
                                  (np.concatenate([k, k]), np.concatenate([r, c]))), shape=(len(r), N))
    Gx, Gy = diff(1), diff(0)
    Lap = (Gx.T @ Gx + Gy.T @ Gy)
    # bilinear constraint rows
    pts = np.asarray(pts, float)
    fx = (pts[:, 0] + HALF) / px; fy = (pts[:, 1] + HALF) / px
    ix = np.clip(np.floor(fx).astype(int), 0, n - 2); iy = np.clip(np.floor(fy).astype(int), 0, n - 2)
    ux, uy = fx - ix, fy - iy
    rows = np.repeat(np.arange(len(pts)), 4)
    cols = np.stack([idx[iy, ix], idx[iy, ix + 1], idx[iy + 1, ix], idx[iy + 1, ix + 1]], 1).ravel()
    data = np.stack([(1 - ux) * (1 - uy), ux * (1 - uy), (1 - ux) * uy, ux * uy], 1).ravel()
    C = sparse.csr_matrix((data, (rows, cols)), shape=(len(pts), N))
    W = sparse.diags(np.asarray(weights, float) * lam)
    A = (1 - tension) * (Lap.T @ Lap) + tension * Lap + C.T @ W @ C + sparse.identity(N) * 1e-8
    b = C.T @ (W @ np.asarray(vals, float))
    h = spsolve(A.tocsc(), b)
    return h.reshape(n, n)


def zoom_to(H, n):
    return ndimage.zoom(H, (n - 1) / (H.shape[0] - 1), order=3)[:n, :n]


def sample(H, x, y):
    n = H.shape[0]; px = 2 * HALF / (n - 1)
    x, y = np.atleast_1d(np.asarray(x, float)), np.atleast_1d(np.asarray(y, float))
    return ndimage.map_coordinates(H, [(y + HALF) / px, (x + HALF) / px], order=1, mode="nearest")
