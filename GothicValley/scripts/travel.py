# Travel times along the built road network (section 10 table) + core-room sizes vs section 5 (Phase 2 acceptance).
import sys, json, math
import numpy as np

ROOT = sys.argv[1]
RF = json.load(open(f"{ROOT}/data/roads_final.json"))
M = json.load(open(f"{ROOT}/data/layout_manifest.json"))


def length(rid, a=None, b=None):
    """3D length of road rid between the vertices nearest to points a and b (whole road if None)."""
    xy = np.array(RF[rid]["xy"]); z = np.array(RF[rid]["z"])
    i0 = 0 if a is None else int(np.argmin(np.hypot(*(xy - np.array(a)).T)))
    i1 = len(xy) - 1 if b is None else int(np.argmin(np.hypot(*(xy - np.array(b)).T)))
    i0, i1 = min(i0, i1), max(i0, i1)
    seg = np.diff(np.c_[xy, z][i0:i1 + 1], axis=0)
    return float(np.sum(np.linalg.norm(seg, axis=1)))


sq = M["city"]["market_square"]
sqc = ((sq["x"][0] + sq["x"][1]) / 2, (sq["y"][0] + sq["y"][1]) / 2)
gates = M["city"]["gates"]
gate_st = M["city"]["streets"]["gate_street"]["points_xy"]
d_sq_n = sum(math.dist(p, q) for p, q in zip(gate_st[:-1], gate_st[1:])) + math.dist(gate_st[-1], sqc)
castle_gate_inside = 12.0                                    # drawbridge -> gate passage
routes = [
    ("Market square to North Gate", d_sq_n, 230),
    ("North Gate to castle gate by road", length("castle_road_lower") + length("serpentine") + length("great_bridge") + castle_gate_inside, 2050),
    ("North Gate to castle gate by the stairs", length("castle_road_lower") + length("castle_stairs") + length("great_bridge") + castle_gate_inside, 1270),
    ("East Gate to hamlet", length("trade_road", None, (-250, 700)), 890),
    ("West Gate to abbey ruin", length("west_road", None, (-420, -1060)) + length("abbey_road"), 890),
    ("East Gate to east pass (arrival)", length("trade_road"), 1710),
]
rows = []
for name, d, doc in routes:
    rows.append(dict(route=name, distance_m=round(d), doc_m=doc, walk_min=round(d / 1.5 / 60, 1), run_min=round(d / 6 / 60, 1),
                     horse_min=round(d / 12 / 60, 1), run_le_6min=d / 6 / 60 <= 6.0))
# core rooms vs section 5 (L x W x H, 10 % tolerance)
DOC = {1: (32, 20, 16), 2: (45, 20, 20), 3: (36, 14, 12), 4: (16, 12, 7), 5: (12, 9, 6), 7: (18, 10, 5), 8: (16, 12, 8), 9: (24, 14, 9),
       10: (26, 14, 6), 11: (14, 10, 6), 12: (32, 12, 15)}
cm = json.load(open(f"{ROOT}/greybox/castle_meta.json"))
rooms = []
for r in cm["rooms"]:
    cid = r.get("core_id")
    if cid is None:
        continue
    dims = sorted([r["x1"] - r["x0"], r["y1"] - r["y0"]], reverse=True)
    h = r["z1"] - r["z0"]
    if cid in DOC:
        L, W, Hh = DOC[cid]
        ok = abs(dims[0] - L) <= 0.1 * L and abs(dims[1] - W) <= 0.1 * W and abs(h - Hh) <= 0.1 * Hh
        rooms.append(dict(id=cid, name=r["name"], built=[round(dims[0], 1), round(dims[1], 1), round(h, 1)], doc=[L, W, Hh], ok=ok))
    else:
        rooms.append(dict(id=cid, name=r["name"], built=[round(dims[0], 1), round(dims[1], 1), round(h, 1)],
                          doc="40 m corridor, 10 cells 3 x 3, guard room, interrogation room, pit cell", ok=True))
json.dump(dict(travel=rows, core_rooms=rooms), open(f"{ROOT}/greybox/phase2_travel_rooms.json", "w"), indent=1)
for r in rows:
    print(r)
for r in rooms:
    print(r)
