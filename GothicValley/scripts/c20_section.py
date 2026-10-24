# Castle 2.0: vertical section of the walk-test shell + greybox boxes + walk-test nodes (debug of doorways).
# usage: c20_section.py ROOT axis(x|y) at a0 a1 z0 z1 out.png   (centred model frame; section plane axis = at)
import sys, json
import numpy as np
from PIL import Image, ImageDraw
ROOT, AX, AT, A0, A1, Z0, Z1, OUT = sys.argv[1], sys.argv[2], *map(float, sys.argv[3:8]), sys.argv[8]
M = json.load(open(f"{ROOT}/greybox/castle_meta.json")); T = np.array(M["model"]["origin"])
W = np.load(f"{ROOT}/assets/castle20/tris_world.npz")["tris"] - T
k = 1 if AX == "y" else 0; o = 1 - k                      # plane: coord k == AT; horizontal axis = o
S = 20
im = Image.new("RGB", (int((A1 - A0) * S), int((Z1 - Z0) * S)), (250, 250, 250)); d = ImageDraw.Draw(im)
P = lambda a, z: ((a - A0) * S, (Z1 - z) * S)
for a in range(int(A0), int(A1) + 1):
    d.line([P(a, Z0), P(a, Z1)], fill=(225, 225, 235) if a % 5 else (180, 180, 210))
for z in range(int(Z0), int(Z1) + 1):
    d.line([P(A0, z), P(A1, z)], fill=(225, 225, 235) if z % 5 else (180, 180, 210))
    if z % 5 == 0: d.text(P(A0, z), f"{z}", fill=(0, 0, 150))
for a in range(int(A0), int(A1) + 1, 5): d.text(P(a, Z1 - 0.3), f"{a}", fill=(0, 0, 150))
dd = W[:, :, k] - AT
cross = (dd.min(1) < 0) & (dd.max(1) > 0)
sel = W[cross]; ds = dd[cross]
for t, dv in zip(sel, ds):
    pts = []
    for i in range(3):
        a, b = t[i], t[(i + 1) % 3]; da, db = dv[i], dv[(i + 1) % 3]
        if (da < 0) != (db < 0):
            p = a + (b - a) * (da / (da - db)); pts.append(p)
    if len(pts) == 2 and all(A0 - 5 < p[o] < A1 + 5 for p in pts):
        d.line([P(pts[0][o], pts[0][2]), P(pts[1][o], pts[1][2])], fill=(0, 0, 0), width=2)
G = json.load(open(f"{ROOT}/greybox/castle_groups.json"))
for g in G:
    for p in g.get("prims", []):
        v = np.array(p["v"]) - T; lo, hi = v.min(0), v.max(0)
        if lo[k] < AT < hi[k]:
            d.rectangle([P(lo[o], hi[2]), P(hi[o], lo[2])], outline=(220, 0, 0) if p.get("col", True) else (0, 160, 0), width=2)
try:
    N = np.load(f"{ROOT}/assets/castle20/navd_castle.npz")
    c = np.stack([N["x"], N["y"], N["z"]], 1) - T
    m = np.abs(c[:, k] - AT) < 0.3
    for p, r in zip(c[m], N["r"][m]):
        x_, y_ = P(p[o], p[2]); d.ellipse([x_ - 3, y_ - 3, x_ + 3, y_ + 3], fill=(0, 170, 255) if r else (255, 150, 0))
except FileNotFoundError:
    pass
for cut in M["model"]["cuts"]:
    if "angle" in cut: continue
    rng = cut["x"] if k == 0 else cut["y"]
    if rng[0] < AT < rng[1]:
        r2 = cut["y"] if k == 0 else cut["x"]
        d.rectangle([P(r2[0], cut["z"][1]), P(r2[1], cut["z"][0])], outline=(160, 0, 200), width=1)
im.save(OUT)
