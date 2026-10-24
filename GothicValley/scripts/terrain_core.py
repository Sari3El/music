# Terrain helpers: fractal noise, priority-flood, drainage, implicit stream-power erosion (Braun & Willett 2013).
import numpy as np
import numba as nb

OFF_R = np.array([-1, -1, -1, 0, 0, 1, 1, 1], np.int64)
OFF_C = np.array([-1, 0, 1, -1, 1, -1, 0, 1], np.int64)
OFF_D = np.array([1.41421356, 1, 1.41421356, 1, 1, 1.41421356, 1, 1.41421356])


def spectral(n, beta, seed, lo=0.0):
    """Fractal (1/f^beta) noise, the statistical signature of real terrain."""
    r = np.random.default_rng(seed)
    f = np.sqrt(np.fft.fftfreq(n)[:, None] ** 2 + np.fft.fftfreq(n)[None, :] ** 2)
    f[0, 0] = 1
    amp = f ** (-beta / 2)
    amp[f < lo] = 0
    z = np.real(np.fft.ifft2(np.fft.fft2(r.standard_normal((n, n))) * amp))
    return (z - z.mean()) / z.std()


@nb.njit(cache=True)
def _heap_push(hk, hv, n, key, val):
    i = n
    hk[i] = key; hv[i] = val
    while i > 0:
        p = (i - 1) >> 1
        if hk[p] <= hk[i]:
            break
        hk[p], hk[i] = hk[i], hk[p]; hv[p], hv[i] = hv[i], hv[p]
        i = p
    return n + 1


@nb.njit(cache=True)
def _heap_pop(hk, hv, n):
    key, val = hk[0], hv[0]
    n -= 1
    hk[0] = hk[n]; hv[0] = hv[n]
    i = 0
    while True:
        l = 2 * i + 1; r = l + 1; m = i
        if l < n and hk[l] < hk[m]:
            m = l
        if r < n and hk[r] < hk[m]:
            m = r
        if m == i:
            break
        hk[m], hk[i] = hk[i], hk[m]; hv[m], hv[i] = hv[i], hv[m]
        i = m
    return key, val, n


@nb.njit(cache=True)
def flow(h, base):
    """Priority-flood (epsilon) from the base-level cells -> receivers, stack order (outlets first), drainage area."""
    R, C = h.shape
    N = R * C
    hf = h.ravel().copy()
    rec = np.arange(N)
    dist = np.ones(N)
    done = np.zeros(N, np.bool_)
    hk = np.empty(N + 8); hv = np.empty(N + 8, np.int64); n = 0
    stack = np.empty(N, np.int64); ns = 0
    bf = base.ravel()
    for i in range(N):
        if bf[i]:
            done[i] = True
            n = _heap_push(hk, hv, n, hf[i], i)
    while n > 0:
        key, i, n = _heap_pop(hk, hv, n)
        stack[ns] = i; ns += 1
        r0 = i // C; c0 = i % C
        for k in range(8):
            r = r0 + OFF_R[k]; c = c0 + OFF_C[k]
            if r < 0 or r >= R or c < 0 or c >= C:
                continue
            j = r * C + c
            if done[j]:
                continue
            done[j] = True
            if hf[j] <= hf[i]:
                hf[j] = hf[i] + 1e-4 * OFF_D[k]
            rec[j] = i; dist[j] = OFF_D[k]
            n = _heap_push(hk, hv, n, hf[j], j)
    # steepest descent receiver on the filled surface (keeps flow paths natural on slopes)
    for i in range(N):
        if bf[i]:
            continue
        r0 = i // C; c0 = i % C
        best = 0.0
        for k in range(8):
            r = r0 + OFF_R[k]; c = c0 + OFF_C[k]
            if r < 0 or r >= R or c < 0 or c >= C:
                continue
            j = r * C + c
            s = (hf[i] - hf[j]) / OFF_D[k]
            if s > best:
                best = s; rec[i] = j; dist[i] = OFF_D[k]
    # re-order the stack so every receiver comes before its donors
    pos = np.empty(N, np.int64)
    order = np.argsort(hf)
    area = np.ones(N)
    for t in range(N - 1, -1, -1):
        i = order[t]
        if rec[i] != i:
            area[rec[i]] += area[i]
    return hf.reshape(R, C), rec, dist, order, area.reshape(R, C)


@nb.njit(cache=True)
def stream_power(h, rec, dist, order, area, K, m, dx, fixed):
    """Implicit stream-power incision, receivers solved first (unconditionally stable)."""
    hf = h.ravel()
    a = area.ravel()
    fx = fixed.ravel()
    for t in range(hf.size):
        i = order[t]
        j = rec[i]
        if j == i or fx[i]:
            continue
        F = K * (a[i] * dx * dx) ** m / (dist[i] * dx)
        hi = (hf[i] + F * hf[j]) / (1.0 + F)
        if hi < hf[i]:
            hf[i] = max(hi, hf[j] + 1e-3)
    return hf.reshape(h.shape)


def diffuse(h, kd, fixed=None):
    lap = (np.roll(h, 1, 0) + np.roll(h, -1, 0) + np.roll(h, 1, 1) + np.roll(h, -1, 1) - 4 * h)
    lap[0, :] = lap[-1, :] = 0
    lap[:, 0] = lap[:, -1] = 0
    out = h + kd * lap
    if fixed is not None:
        out[fixed] = h[fixed]
    return out


@nb.njit(cache=True)
def thermal(h, talus, rate, iters):
    """Thermal weathering: material slides down where the slope exceeds the talus angle (rounded screes)."""
    R, C = h.shape
    for _ in range(iters):
        d = np.zeros_like(h)
        for r in range(1, R - 1):
            for c in range(1, C - 1):
                for k in range(8):
                    rr = r + OFF_R[k]; cc = c + OFF_C[k]
                    diff = h[r, c] - h[rr, cc] - talus * OFF_D[k]
                    if diff > 0:
                        mv = rate * diff / 8
                        d[r, c] -= mv; d[rr, cc] += mv
        h += d
    return h


def catmull(P, k=40):
    P = np.asarray(P, float)
    P = np.vstack([P[0] * 2 - P[1], P, P[-1] * 2 - P[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, k, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return np.array(out)


def dist_poly(X, Y, P, with_t=False):
    """Distance to a polyline (+ normalised curvilinear abscissa); chunked to keep memory low on big grids."""
    best = np.full(X.shape, 1e9); tpar = np.zeros(X.shape)
    cum = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    for i, (a, b) in enumerate(zip(P[:-1], P[1:])):
        ab = b - a; L = ab @ ab
        if L < 1e-9:
            continue
        lo = np.minimum(a, b) - 0; hi = np.maximum(a, b)
        t = np.clip(((X - a[0]) * ab[0] + (Y - a[1]) * ab[1]) / L, 0, 1)
        d = np.hypot(X - (a[0] + t * ab[0]), Y - (a[1] + t * ab[1]))
        m = d < best
        best = np.where(m, d, best)
        if with_t:
            tpar = np.where(m, (cum[i] + t * np.sqrt(L)) / cum[-1], tpar)
    return (best, tpar) if with_t else best
