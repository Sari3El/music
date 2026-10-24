# Castle 2.0: oriented free rectangle of chosen covered volumes (rotated buildings). For each id: main floor level, principal
# axis of the footprint, the largest free rectangle in that frame (free over 0.5-3 m above the floor), and the ceiling.
# usage: c20_orient.py ROOT id [id ...]
import sys, json, math
import numpy as np
from scipy import ndimage
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from c20_rooms2_lib import max_rect

ROOT = sys.argv[1]
L = np.load(f"{ROOT}/assets/castle20/interiors_covered_lab.npz"); lab = L["lab"]; BB = L["bbox"]; DX = float(L["dx"])
for cid in map(int, sys.argv[2:]):
    comp = lab == cid
    anyc = comp.any(axis=2)
    lf = np.where(anyc, comp.argmax(axis=2), -1)
    vals, cnt = np.unique(lf[anyc], return_counts=True)
    kf = int(vals[np.argmax(cnt)])
    foot = (np.abs(lf - kf) <= 1) & comp[:, :, kf:kf + 6].all(axis=2)
    I, J = np.nonzero(foot)
    X = BB[0] + (I + 0.5) * DX; Y = BB[2] + (J + 0.5) * DX
    C = np.cov(np.vstack([X, Y])); w, v = np.linalg.eigh(C); ax = v[:, 1]
    ang = math.degrees(math.atan2(ax[1], ax[0]))
    best = None
    for a in np.arange(ang - 6, ang + 6.1, 1.0):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        cx, cy = X.mean(), Y.mean()
        U = (X - cx) * c + (Y - cy) * s; V = -(X - cx) * s + (Y - cy) * c
        h = 0.25
        u0, v0 = U.min() - 1, V.min() - 1
        G = np.zeros((int((U.max() - u0) / h) + 3, int((V.max() - v0) / h) + 3), bool)
        G[((U - u0) / h).astype(int), ((V - v0) / h).astype(int)] = True
        G = ndimage.binary_closing(G, iterations=2)
        i0, i1, j0, j1 = max_rect(G)
        area = (i1 - i0) * (j1 - j0) * h * h
        if best is None or area > best[0]:
            best = (area, a, cx, cy, u0 + i0 * h, u0 + i1 * h, v0 + j0 * h, v0 + j1 * h)
    area, a, cx, cy, ua, ub, va, vb = best
    um, vm = (ua + ub) / 2, (va + vb) / 2
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    ccx, ccy = cx + um * c - vm * s, cy + um * s + vm * c
    fl = BB[4] + (kf - 1) * DX
    print(json.dumps(dict(id=cid, floor=fl, angle=round(a, 1), centre=[round(ccx, 2), round(ccy, 2)], length=round(ub - ua, 2),
                          width=round(vb - va, 2), area=round(area, 1))))
