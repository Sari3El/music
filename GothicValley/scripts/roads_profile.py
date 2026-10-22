# Final road profiles: Appendix A polylines (XY kept), elevations re-solved to respect the grade rules with the
# smallest deviation from the Appendix z values; crossings of the castle stairs with the serpentine resolved.
import sys, os, json
import numpy as np
from scipy.optimize import minimize
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tlib import densify

ROOT = sys.argv[1]
M = json.load(open(f"{ROOT}/data/layout_manifest.json"))
POIS = [p["xyz"] for p in M["points_of_interest"]]
OUT, LOG = {}, []
STEP = 10.0

# design decisions recorded in the build log
ADJUST = {
    ("serpentine", 5): (200.0, "hairpin on the barbican terrace: terrace is flat at +199 (MUST), Appendix says 205"),
    ("west_road", 1): (7.0, "West Bridge deck at +7 m: the -1 m of the Appendix is the river level (POI tolerance 10 m kept)"),
}


def solve(r, pts, limit):
    D, A, L = densify(pts[:, :2], pts[:, 2:3], step=2, smooth=r["type"] not in ("stairs", "bridge"))
    s = np.arange(0, L[-1] + 1e-6, STEP); s[-1] = L[-1]
    zd = np.interp(s, L, A[:, 0])
    # control-point positions along the curve
    cl = [int(np.argmin(np.hypot(D[:, 0] - x, D[:, 1] - y))) for x, y in pts[:, :2]]
    ck = [int(np.argmin(np.abs(s - L[c]))) for c in cl]
    n = len(s)
    lo, hi = zd - 14, zd + 14
    for j, k in enumerate(ck):
        x, y, z = pts[j]
        tol = 10.0 if any(np.hypot(px_ - x, py_ - y) < 30 for px_, py_, _ in POIS) else 12.0
        if j in (0, len(pts) - 1):
            tol = 0.5                                   # junctions / gates / map edge stay put
        lo[k], hi[k] = z - tol, z + tol
    ds = np.diff(s)
    g = limit
    while True:
        cons = [{"type": "ineq", "fun": lambda z, g=g: g * ds - np.diff(z), "jac": lambda z, g=g: -(np.eye(n, k=1) - np.eye(n))[:-1]},
                {"type": "ineq", "fun": lambda z, g=g: g * ds + np.diff(z), "jac": lambda z, g=g: (np.eye(n, k=1) - np.eye(n))[:-1]}]
        res = minimize(lambda z: np.sum((z - zd) ** 2), np.clip(zd, lo, hi), jac=lambda z: 2 * (z - zd),
                       bounds=list(zip(lo, hi)), constraints=cons, method="SLSQP", options={"maxiter": 500, "ftol": 1e-6})
        ok = res.success and np.all(np.abs(np.diff(res.x)) <= g * ds + 1e-3)
        if ok or g > 0.6:
            return D, L, s, res.x, zd, g, ok
        g += 0.01


ORDER = ["castle_road_lower", "serpentine", "castle_stairs", "great_bridge", "west_road", "trade_road",
         "abbey_road", "fen_path", "forest_track", "quarry_road", "mill_track", "dock_lane", "falls_path"]
RD = {r["id"]: r for r in M["roads"]}
for rid in ORDER:
    r = RD[rid]
    pts = np.array(r["points_xyz"], float)
    for j in (0, len(pts) - 1):                       # junctions: a branch starts/ends at the level of the road it meets
        for oid, o in OUT.items():
            oxy = np.array(o["xy"]); dd = np.hypot(oxy[:, 0] - pts[j, 0], oxy[:, 1] - pts[j, 1])
            if dd.min() < 6 and oid != rid:
                znew = float(np.array(o["z"])[int(np.argmin(dd))])
                if abs(znew - pts[j, 2]) > 0.3:
                    LOG.append(f"{rid} endpoint {pts[j, :2].tolist()} pinned to {oid} at z {znew:.1f} (Appendix {pts[j, 2]:.0f})")
                pts[j, 2] = znew
                break
    for (rid, k), (z, why) in ADJUST.items():
        if rid == r["id"]:
            LOG.append(f"{rid} point {k} {pts[k].tolist()} -> z {z}: {why}")
            pts[k, 2] = z
    limit = r.get("max_grade") or (np.tan(np.radians(r["max_angle_deg"])) if "max_angle_deg" in r else 0.35)
    if r["type"] == "bridge":
        D, A, L = densify(pts[:, :2], pts[:, 2:3], step=2, smooth=False)
        s = np.arange(0, L[-1] + 1e-6, STEP); z = np.interp(s, L, A[:, 0]); g, ok, zd = 0.04, True, z
    else:
        D, L, s, z, zd, g, ok = solve(r, pts, limit)
    xy = np.stack([np.interp(s, L, D[:, 0]), np.interp(s, L, D[:, 1])], 1)
    dev = np.abs(z - zd)
    OUT[r["id"]] = dict(type=r["type"], width_m=r["width_m"], s=s.round(2).tolist(), xy=xy.round(2).tolist(), z=z.round(2).tolist(),
                        max_grade=round(float(np.max(np.abs(np.diff(z)) / np.diff(s))), 4), rule=round(float(limit), 4),
                        rule_met=bool(g <= limit + 1e-6), max_dev_from_appendix_m=round(float(dev.max()), 1))
    tag = "OK" if g <= limit + 1e-6 else f"RULE NOT MET: best {g * 100:.0f}% (rule {limit * 100:.0f}%)"
    print(f"{r['id']:18s} {r['type']:9s} len {s[-1]:7.1f} max grade {OUT[r['id']]['max_grade'] * 100:5.1f}%  "
          f"dev max {dev.max():5.1f} m  {tag}", flush=True)
    if g > limit + 1e-6:
        LOG.append(f"{r['id']}: grade rule {limit * 100:.0f}% cannot be met on the Appendix polyline (best {g * 100:.0f}%); "
                   f"needs a longer alignment (open question)")

# stairs x serpentine: footbridge where the stairs pass over the road, level crossing otherwise
sp, st = OUT["serpentine"], OUT["castle_stairs"]
spxy, stxy = np.array(sp["xy"]), np.array(st["xy"])
cross = []
for i in range(1, len(stxy) - 1):
    d = np.hypot(spxy[:, 0] - stxy[i, 0], spxy[:, 1] - stxy[i, 1])
    j = int(np.argmin(d))
    if d[j] < 6:
        dz = st["z"][i] - sp["z"][j]
        kind = "footbridge" if dz > 5 else ("underpass" if dz < -4.5 else "level")
        if not cross or np.hypot(*(np.array(cross[-1]["xy"]) - stxy[i])) > 20:
            cross.append(dict(xy=stxy[i].round(1).tolist(), stairs_z=round(st["z"][i], 1), road_z=round(sp["z"][j], 1), kind=kind))
OUT["_crossings"] = cross
for c in cross:
    LOG.append(f"stairs x serpentine at {c['xy']}: stairs {c['stairs_z']} m, road {c['road_z']} m -> {c['kind']}")
    print("CROSSING", c)
json.dump(OUT, open(f"{ROOT}/data/roads_final.json", "w"))
open(f"{ROOT}/data/roads_log.txt", "w").write("\n".join(LOG) + "\n")
print("\n".join(LOG))
