# Castle 2.0: buildings from their roofs. Roof faces (class 1) are rasterised on a 1 m grid, joined into connected roofs,
# and each roof gets its minimum-area oriented rectangle (rotating calipers on the hull), eave and ridge heights, and the
# hill height under it. -> assets/castle20/buildings.json (centred model frame, scale 160).
# usage: c20_buildings.py ROOT
import sys, json, math
import numpy as np
from scipy import ndimage

ROOT = sys.argv[1]
F = np.load(f"{ROOT}/assets/castle20/faces.npz"); K = np.load(f"{ROOT}/assets/castle20/classes.npz")
G = np.load(f"{ROOT}/assets/castle20/ground.npz")
names = F["names"]; keep = np.array([names[o] != "mesh14" for o in F["obj"]])
c = F["c"] * 160.0 + [-123.32, 90.64, 7.07]; cls = K["cls"]          # import frame -> centred frame (fit on the bounds)
roof = (cls == 1) & keep & (F["n"][:, 2] > 0.25) & (F["area"] * 160.0 ** 2 > 0.05)
R = c[roof]
x0, y0, h = -110.0, -95.0, 1.0
gi = ((R[:, 0] - x0) / h).astype(int); gj = ((R[:, 1] - y0) / h).astype(int)
M = np.zeros((int(220 / h), int(190 / h)), bool); M[gi, gj] = True
M = ndimage.binary_closing(M, iterations=1)
lab, n = ndimage.label(M)
pz = lambda x, y: float(np.nan_to_num(G["plate"], nan=0)[np.argmin(abs(G["xs"] - x)), np.argmin(abs(G["ys"] - y))])


def hull(P):
    P = sorted(set(map(tuple, P)))
    if len(P) < 3:
        return np.array(P)
    cr = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in P:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(P):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return np.array(lo[:-1] + up[:-1])


out = []
for k in range(1, n + 1):
    I, J = np.nonzero(lab == k)
    if len(I) < 25:
        continue
    pts = np.concatenate([np.stack([x0 + (I + a) * h, y0 + (J + b) * h], 1) for a in (0, 1) for b in (0, 1)])
    H_ = hull(pts)
    best = None
    for e in range(len(H_)):
        d = H_[(e + 1) % len(H_)] - H_[e]; a = math.atan2(d[1], d[0])
        cs, sn = math.cos(a), math.sin(a)
        U = H_[:, 0] * cs + H_[:, 1] * sn; V = -H_[:, 0] * sn + H_[:, 1] * cs
        ar = (U.max() - U.min()) * (V.max() - V.min())
        if best is None or ar < best[0]:
            best = (ar, a, U.min(), U.max(), V.min(), V.max())
    ar, a, u0, u1, v0, v1 = best
    if u1 - u0 < v1 - v0:                                              # long axis first
        a += math.pi / 2; u0, u1, v0, v1 = v0, v1, -u1, -u0
    cs, sn = math.cos(a), math.sin(a); um, vm = (u0 + u1) / 2, (v0 + v1) / 2
    cx, cy = um * cs - vm * sn, um * sn + vm * cs
    sel = lab[gi, gj] == k
    zr = R[sel, 2]
    deg = (math.degrees(a) + 360) % 180
    out.append(dict(id=k, centre=[round(cx, 2), round(cy, 2)], angle=round(deg, 1), length=round(u1 - u0, 1), width=round(v1 - v0, 1),
                    fill=round(len(I) * h * h / ar, 2), eave=round(float(np.percentile(zr, 3)), 2), ridge=round(float(zr.max()), 2),
                    plate=round(pz(cx, cy), 2)))
out.sort(key=lambda b: -b["length"] * b["width"])
json.dump(out, open(f"{ROOT}/assets/castle20/buildings.json", "w"), indent=1)
for b in out:
    print(b)
