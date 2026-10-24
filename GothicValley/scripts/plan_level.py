# Plan of the castle greybox at one level: horizontal section of every prim (colour by material, dark = collision-only)
# and room rectangles. usage: plan_level.py ROOT z_rel x0 x1 y0 y1 out.png   (centred model frame)
import sys, json
import numpy as np
from PIL import Image, ImageDraw
ROOT = sys.argv[1]; ZR = float(sys.argv[2]); X0, X1, Y0, Y1 = map(float, sys.argv[3:7]); OUT = sys.argv[7]
M = json.load(open(f"{ROOT}/greybox/castle_meta.json")); T = np.array(M["model"]["origin"])
G = json.load(open(f"{ROOT}/greybox/castle_groups.json"))
S = 12
im = Image.new("RGB", (int((X1 - X0) * S), int((Y1 - Y0) * S)), (245, 245, 245)); d = ImageDraw.Draw(im)
P = lambda x, y: ((x - X0) * S, (Y1 - y) * S)
COL = {"C2_Wall": (120, 120, 130), "C2_Floor": (190, 180, 160), "LB_Stone": (150, 140, 120), "LB_GlossyWood": (140, 90, 50),
       "GB_Metal": (30, 30, 40), "GB_Detail": (190, 40, 30), "LB_Sandstone": (200, 180, 130), "GB_WinLit": (255, 180, 60)}
z = ZR + T[2]
for g in G:
    for p in g["prims"]:
        v = np.array(p["v"]); lo, hi = v.min(0), v.max(0)
        if not (lo[2] <= z <= hi[2]):
            continue
        c = COL.get(p["m"], (100, 160, 200))
        if p["col"] == "only":
            c = (60, 60, 60)
        # footprint polygon: convex hull of the xy of the vertices
        xy = np.unique(np.round(v[:, :2] - T[:2], 3), axis=0)
        if len(xy) >= 3:
            ctr = xy.mean(0); ang = np.arctan2(xy[:, 1] - ctr[1], xy[:, 0] - ctr[0]); xy = xy[np.argsort(ang)]
            d.polygon([P(*q) for q in xy], fill=c if p["col"] is not False else None, outline=c)
for r in M["rooms"]:
    if r["z0"] - 0.5 <= z <= r["z1"]:
        d.rectangle([P(r["x0"] - T[0], r["y1"] - T[1]), P(r["x1"] - T[0], r["y0"] - T[1])], outline=(0, 140, 0), width=2)
        d.text(P(r["x0"] - T[0] + 0.3, r["y1"] - T[1] - 0.3), r["name"], fill=(0, 100, 0))
for x in range(int(X0), int(X1) + 1, 5):
    d.line([P(x, Y0), P(x, Y1)], fill=(210, 210, 230)); d.text(P(x + 0.2, Y1 - 0.2), str(x), fill=(0, 0, 160))
for y in range(int(Y0), int(Y1) + 1, 5):
    d.line([P(X0, y), P(X1, y)], fill=(210, 210, 230)); d.text(P(X0 + 0.2, y - 0.2), str(y), fill=(0, 0, 160))
d.text((5, im.height - 15), f"z = {ZR}", fill=(0, 0, 0))
im.save(OUT)
