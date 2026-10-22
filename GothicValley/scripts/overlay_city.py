# City greybox footprints drawn over the city plan of the design document (acceptance: drift check against the diagram).
import sys, json
import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import ConvexHull

ROOT = sys.argv[1]
im = Image.open(f"{ROOT}/doc/city_plan.png").convert("RGB")
ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); dr = ImageDraw.Draw(ov)
A = 600 / 946; B = -760 - 427 * A; C = -459 / 720; E = -221 - 561 * C          # plan pixels <-> world (fitted on the 4 gates)
px = lambda X, Y: ((Y - B) / A, (X - E) / C)
col = {"Walls": (40, 40, 40, 200), "Gates": (10, 10, 10, 220), "Church": (90, 40, 120, 170), "Manor": (150, 60, 30, 160),
       "TownHall": (30, 90, 160, 170), "GuildHall": (30, 90, 160, 170), "Barracks": (30, 90, 160, 170), "Market": (200, 160, 40, 170),
       "Houses": (160, 70, 50, 150), "Int_": (220, 30, 30, 190)}
for g in json.load(open(f"{ROOT}/greybox/city_groups.json")):
    key = next((k for k in col if k in g["name"].replace("Houses_Market", "Houses_")), "Int_")
    for p in g["prims"]:
        v = np.array(p["v"])[:, :2]
        if len(np.unique(v.round(2), axis=0)) < 3:
            continue
        try:
            h = ConvexHull(v)
        except Exception:
            continue
        dr.polygon([px(*v[i]) for i in h.vertices], fill=col[key])
out = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
out.save(f"{ROOT}/greybox/city_overlay_plan.png")
print("overlay written")
