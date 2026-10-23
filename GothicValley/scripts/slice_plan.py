# Plan slices of a triangle soup (.npz from blend_tris.py): segments where the triangles cross z = h, drawn with a 1 m /
# 5 m grid, one image per height. usage: slice_plan.py TRIS.npz OUT_PREFIX h1 [h2 ...] [--px 20] [--skip name,name]
import sys
import numpy as np
from PIL import Image, ImageDraw
args = sys.argv[1:]
px = 20; skip = []
if "--px" in args:
    i = args.index("--px"); px = int(args[i + 1]); del args[i:i + 2]
if "--skip" in args:
    i = args.index("--skip"); skip = args[i + 1].split(","); del args[i:i + 2]
d = np.load(args[0]); T = d["tris"]; obj = d["obj"]; names = d["names"]
keep = np.array([not any(s in str(names[k]) for s in skip) for k in obj])
T = T[keep]; obj = obj[keep]
lo = T.reshape(-1, 3).min(0) - 2; hi = T.reshape(-1, 3).max(0) + 2
W, H = int((hi[0] - lo[0]) * px), int((hi[1] - lo[1]) * px)
cols = [(255, 80, 80), (80, 200, 255), (255, 220, 60), (120, 255, 120), (255, 120, 255), (255, 160, 60), (180, 180, 255), (200, 255, 200),
        (255, 255, 255), (160, 100, 60), (100, 160, 160), (220, 160, 220)]
for h in map(float, args[2:]):
    im = Image.new("RGB", (W, H), (25, 25, 30)); dr = ImageDraw.Draw(im)
    for gx in range(int(np.floor(lo[0])), int(hi[0]) + 1):
        X = (gx - lo[0]) * px; dr.line([(X, 0), (X, H)], fill=(70, 70, 80) if gx % 5 else (120, 120, 140))
        if gx % 5 == 0: dr.text((X + 2, 2), str(gx), fill=(160, 160, 180))
    for gy in range(int(np.floor(lo[1])), int(hi[1]) + 1):
        Y = H - (gy - lo[1]) * px; dr.line([(0, Y), (W, Y)], fill=(70, 70, 80) if gy % 5 else (120, 120, 140))
        if gy % 5 == 0: dr.text((2, Y + 2), str(gy), fill=(160, 160, 180))
    z = T[..., 2]
    s = (z.min(1) < h) & (z.max(1) > h)
    for t, k in zip(T[s], obj[s]):
        p = []
        for a, b in ((0, 1), (1, 2), (2, 0)):
            za, zb = t[a, 2], t[b, 2]
            if (za - h) * (zb - h) < 0:
                u = (h - za) / (zb - za); p.append(t[a] + u * (t[b] - t[a]))
        if len(p) == 2:
            dr.line([((p[0][0] - lo[0]) * px, H - (p[0][1] - lo[1]) * px), ((p[1][0] - lo[0]) * px, H - (p[1][1] - lo[1]) * px)],
                    fill=cols[k % len(cols)], width=2)
    dr.text((10, H - 20), f"z = {h}", fill=(255, 255, 255))
    im.save(f"{args[1]}_z{h:g}.png"); print("saved", f"{args[1]}_z{h:g}.png", im.size)
