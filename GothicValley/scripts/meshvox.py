# Voxelise triangle meshes (surfaces) into an occupancy grid: every triangle is sampled densely and the cells it touches
# are marked; used for asset shells (castle, houses) whose collision in Unreal is the mesh itself (complex collision).
import numpy as np
from numba import njit


@njit(cache=True)
def _mark(T, S, x0, y0, z0, dx, dz, step):
    nx, ny, nz = S.shape
    for t in range(T.shape[0]):
        a, b, c = T[t, 0], T[t, 1], T[t, 2]
        lab = np.sqrt(((b - a) ** 2).sum()); lac = np.sqrt(((c - a) ** 2).sum())
        nu = int(lab / step) + 1; nv = int(lac / step) + 1
        for iu in range(nu + 1):
            u = iu / nu
            for iv in range(nv + 1 - 0):
                v = iv / nv
                if u + v > 1.0:
                    break
                p = a + (b - a) * u + (c - a) * v
                i = int((p[0] - x0) / dx); j = int((p[1] - y0) / dx); k = int((p[2] - z0) / dz)
                if 0 <= i < nx and 0 <= j < ny and 0 <= k < nz:
                    S[i, j, k] = 1


def voxelise(T, bbox, dx=0.5, dz=0.1, step=None):
    """T: (n, 3, 3) triangles (world metres); bbox: x0, x1, y0, y1, z0, z1 -> uint8 grid (nx, ny, nz), 1 = surface."""
    x0, x1, y0, y1, z0, z1 = bbox
    nx, ny, nz = int((x1 - x0) / dx), int((y1 - y0) / dx), int((z1 - z0) / dz)
    S = np.zeros((nx, ny, nz), np.uint8)
    lo = T.min(1); hi = T.max(1)
    keep = (hi[:, 0] >= x0) & (lo[:, 0] <= x1) & (hi[:, 1] >= y0) & (lo[:, 1] <= y1) & (hi[:, 2] >= z0) & (lo[:, 2] <= z1)
    _mark(np.ascontiguousarray(T[keep], np.float64), S, x0, y0, z0, dx, dz, step or min(dx, dz) * 0.8)
    return S


@njit(cache=True)
def dilate_xy(S, r):
    """Grow occupied cells horizontally by r cells (square), every z layer (capsule radius)."""
    nx, ny, nz = S.shape
    O = S.copy()
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                if S[i, j, k]:
                    for di in range(-r, r + 1):
                        for dj in range(-r, r + 1):
                            ii, jj = i + di, j + dj
                            if 0 <= ii < nx and 0 <= jj < ny:
                                O[ii, jj, k] = 1
    return O


@njit(cache=True)
def fill_z(S, gap):
    """Close vertical gaps up to `gap` cells between marked cells (sloped faces sampled coarsely stay continuous)."""
    nx, ny, nz = S.shape
    for i in range(nx):
        for j in range(ny):
            last = -1000
            for k in range(nz):
                if S[i, j, k]:
                    if 0 < k - last <= gap:
                        for kk in range(last + 1, k):
                            S[i, j, kk] = 1
                    last = k
    return S
