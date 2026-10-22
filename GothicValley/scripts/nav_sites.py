# Walkability of the secondary sites: one nav_check run per site box, seeded from the nearest road (or bank) inside it.
import sys, os, json, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tlib import sample

ROOT = sys.argv[1]
H = np.load(f"{ROOT}/terrain/H_4033.npy")
RF = json.load(open(f"{ROOT}/data/roads_final.json"))
meta = json.load(open(f"{ROOT}/greybox/sites_meta.json"))
M = json.load(open(f"{ROOT}/data/layout_manifest.json"))
BOXES = {  # name: (x0, x1, y0, y1, z0, z1)
    "approach": (300, 770, -220, 110, 55, 222), "cemetery": (-175, -25, -445, -295, 5, 45), "abbey": (95, 205, -1245, -1150, 70, 110),
    "camp": (320, 440, -680, -560, 60, 110), "circle": (850, 910, -590, -530, 100, 140), "falls": (1140, 1235, -1165, -1085, 45, 125),
    "faubourg": (-520, -280, -210, 330, 0, 50), "mills_docks": (-830, -690, -545, -200, -15, 35), "hamlet": (-370, -130, 580, 820, -5, 50),
    "quarry": (150, 300, 1100, 1260, 90, 200), "border": (-390, -210, 1360, 1505, 70, 130), "fen": (-1420, -1080, -1380, -1080, -10, 30),
    "west_bridge": (-490, -410, -910, -790, -10, 40)}
seeds_extra = {"falls": [[1185.0, -1138.0]], "mills_docks": [[-760.0, -300.0]], "fen": []}
out = {}
for name, (x0, x1, y0, y1, z0, z1) in BOXES.items():
    seeds = []
    for rid, r in RF.items():
        if rid.startswith("_") or r["type"] == "bridge":
            continue
        xy = np.array(r["xy"]); zz = np.array(r["z"])
        inside = np.nonzero((xy[:, 0] > x0 + 3) & (xy[:, 0] < x1 - 3) & (xy[:, 1] > y0 + 3) & (xy[:, 1] < y1 - 3))[0]
        if len(inside):
            i = inside[len(inside) // 2]
            seeds.append([float(xy[i, 0]), float(xy[i, 1]), float(sample(H, xy[i, 0], xy[i, 1])[0])])
    for p in seeds_extra.get(name, []):
        seeds.append([p[0], p[1], float(sample(H, *p)[0])])
    rooms = [r for r in meta["rooms"] if x0 < (r["x0"] + r["x1"]) / 2 < x1 and y0 < (r["y0"] + r["y1"]) / 2 < y1]
    cfg = dict(name=f"site_{name}", bbox=[x0, x1, y0, y1, z0, z1], groups=["greybox/sites_groups.json"], meta=[],
               exclude=["SM_GB_Ruin_AbbeyTrapdoor", "SM_GB_Site_BorderGate"], seeds=seeds, probes={},
               levels={"all": [z0, z1]})
    tmp_meta = f"{ROOT}/greybox/nav/_meta_{name}.json"
    json.dump(dict(rooms=rooms), open(tmp_meta, "w"))
    cfg["meta"] = [os.path.relpath(tmp_meta, ROOT)]
    cp = f"{ROOT}/greybox/nav/cfg_{name}.json"
    json.dump(cfg, open(cp, "w"), indent=1)
    res = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "nav_check.py"), ROOT, cp], capture_output=True, text=True)
    rep = json.load(open(f"{ROOT}/greybox/nav/nav_site_{name}.json"))
    out[name] = dict(seeds=len(seeds), rooms=[(r["name"], r["reached"]) for r in rep["rooms"]], leaks=len(rep["leaks"]))
    print(name, "seeds", len(seeds), "| rooms", sum(r["reached"] for r in rep["rooms"]), "/", len(rep["rooms"]),
          [r["name"] for r in rep["rooms"] if not r["reached"]], "| leaks", len(rep["leaks"]), flush=True)
json.dump(out, open(f"{ROOT}/greybox/nav/nav_sites_summary.json", "w"), indent=1)
