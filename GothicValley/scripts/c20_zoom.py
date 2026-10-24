# Castle 2.0: zoomed map of the walk test (top reached level per 0.5 m cell, centred frame) with model slices overlaid.
# usage: c20_zoom.py ROOT x0 x1 y0 y1 zslice out.png
import sys
import numpy as np
from PIL import Image, ImageDraw
ROOT = sys.argv[1]; X0_, X1_, Y0_, Y1_, ZS = map(float, sys.argv[2:7]); OUT = sys.argv[7]
top = np.load(f"{ROOT}/assets/castle20/walk_top.npy"); h = 0.5; GX, GY = -105, -90
W = (np.load(f"{ROOT}/assets/castle20/tris_world.npz")["tris"] - [719.0, 290.0, 195.4]) if len(sys.argv) > 8 else np.load(f"{ROOT}/assets/castle20/tris.npz")["tris"]
S = 16
im = Image.new("RGB", (int((X1_ - X0_) / h * S), int((Y1_ - Y0_) / h * S)), (240, 240, 240)); d = ImageDraw.Draw(im)
P = lambda x, y: ((x - X0_) / h * S, (Y1_ - y) / h * S)
for i in range(int((X0_ - GX) / h), int((X1_ - GX) / h)):
    for j in range(int((Y0_ - GY) / h), int((Y1_ - GY) / h)):
        v = top[i, j]
        if np.isnan(v): continue
        t = float(np.clip((v - ZS + 3) / 6, 0, 1))
        x, y = GX + i * h, GY + j * h
        d.rectangle([P(x, y + h), P(x + h, y)], fill=(int(120 + 135 * t), int(200 - 60 * t), int(255 - 200 * t)))
        if (i + j) % 4 == 0: d.text(P(x + 0.05, y + h - 0.05), f"{v:.1f}", fill=(0, 0, 0))
dz = W[:, :, 2] - ZS; cr = (dz.min(1) < 0) & (dz.max(1) > 0)
for t, dv in zip(W[cr], dz[cr]):
    pts = []
    for i in range(3):
        a, b, da, db = t[i], t[(i + 1) % 3], dv[i], dv[(i + 1) % 3]
        if (da < 0) != (db < 0): pts.append(a + (b - a) * (da / (da - db)))
    if len(pts) == 2 and all(X0_ - 2 < p[0] < X1_ + 2 and Y0_ - 2 < p[1] < Y1_ + 2 for p in pts):
        d.line([P(pts[0][0], pts[0][1]), P(pts[1][0], pts[1][1])], fill=(0, 0, 0), width=2)
for x in range(int(X0_), int(X1_) + 1):
    d.line([P(x, Y0_), P(x, Y1_)], fill=(150, 150, 200) if x % 5 == 0 else (215, 215, 225))
    if x % 5 == 0: d.text(P(x + 0.1, Y1_ - 0.1), str(x), fill=(0, 0, 160))
for y in range(int(Y0_), int(Y1_) + 1):
    d.line([P(X0_, y), P(X1_, y)], fill=(150, 150, 200) if y % 5 == 0 else (215, 215, 225))
    if y % 5 == 0: d.text(P(X0_ + 0.1, y - 0.1), str(y), fill=(0, 0, 160))
im.save(OUT)
