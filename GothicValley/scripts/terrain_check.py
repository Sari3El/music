# Phase 1 acceptance checks + top-view overlay against the master map of section 3.
import sys, os, json
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tlib import densify, sample, grid, HALF

ROOT = sys.argv[1]
M = json.load(open(f"{ROOT}/data/layout_manifest.json"))
HN = f"{ROOT}/terrain/H_natural_4033.npy"       # landforms are checked on the surface before the covered greybox voids
H = np.load(HN if os.path.exists(HN) else f"{ROOT}/terrain/H_4033.npy")
N = H.shape[0]; px = 2 * HALF / (N - 1)
R = {"poi": [], "roads": [], "features": {}, "pass": True}

# points of interest within 10 m (the sites of features use their own reference surface)
for p in M["points_of_interest"]:
    x, y, z = p["xyz"]
    if p["id"] == 9:
        got = float(sample(H, x, y + 12)[0])            # West Bridge: river level beside the deck
    elif p["id"] == 14:                                 # falls: the POI (82) lies on the 56 m drop between lip and pool
        top, bot = float(sample(H, x + 6, y)[0]), float(sample(H, x - 6, y)[0])
        got = z if bot - 10 <= z <= top + 10 else (top if z > top else bot)
        fl = M["water"]["falls"]
        foot = float(np.median(sample(H, np.full(9, x - 14.0), np.linspace(y - 4, y + 4, 9))))    # bed below the pool
        R["falls"] = dict(lip=round(top, 1), lip_target=fl["top_z"], pool=round(bot, 1), foot_bed=round(foot, 1), base_target=fl["base_z"],
                          ok=abs(top - fl["top_z"]) <= 4 and abs(foot - fl["base_z"]) <= 4 and bot >= fl["base_z"] - 8)
        R["pass"] &= R["falls"]["ok"]
    else:
        got = float(sample(H, x, y)[0])
    ok = abs(got - z) <= 10
    R["poi"].append(dict(id=p["id"], name=p["name"], target=z, terrain=round(got, 1), delta=round(got - z, 1), ok=ok))
    R["pass"] &= ok

# roads: grade along the graded bed (solved profiles), bridges / footbridge crossings / map edge excluded
RF = json.load(open(f"{ROOT}/data/roads_final.json"))
skip_pts = [c["xy"] for c in RF["_crossings"] if c["kind"] == "footbridge"] + [[-452, -855]]
for rid, r in RF.items():
    if rid.startswith("_"):
        continue
    if r["type"] == "bridge":
        R["roads"].append(dict(id=rid, type=r["type"], length=r["s"][-1], note="span over the ravine (greybox mesh)"))
        continue
    xy = np.array(r["xy"]); zd = np.array(r["z"])
    D, A, L = densify(xy, zd[:, None], step=2, smooth=False)
    z = sample(H, D[:, 0], D[:, 1])
    keep = np.ones(len(D), bool)
    for c in skip_pts:
        keep &= np.hypot(D[:, 0] - c[0], D[:, 1] - c[1]) > 40
    keep &= (np.abs(D[:, 0]) < 1480) & (np.abs(D[:, 1]) < 1480)
    s = np.arange(0, L[-1], 10.0)
    zs = np.interp(s, L, z); ks = np.interp(s, L, keep.astype(float)) > 0.99
    g = np.abs(np.diff(zs)) / 10.0
    g = g[ks[:-1] & ks[1:]]
    dev = np.abs(z - A[:, 0])[keep]
    item = dict(id=rid, type=r["type"], length=round(float(L[-1]), 0), max_grade_pct=round(float(g.max() * 100), 1),
                p95_grade_pct=round(float(np.percentile(g, 95) * 100), 1), profile_max_grade_pct=round(r["max_grade"] * 100, 1),
                rule_pct=round(r["rule"] * 100, 1), bed_dev_max_m=round(float(dev.max()), 2))
    item["ok"] = bool(np.percentile(g, 95) <= r["rule"] + 0.01)
    R["roads"].append(item)

X, Y = grid(N)
f = R["features"]
# castle brook: the ravine floor must follow the brook bed all the way (no dam), X 430 -> 1000
BRK = np.array(M["water"]["castle_brook"]["points_x_y_bedz_halfwidth"], float)
Db, Ab, _ = densify(BRK[:, :2], BRK[:, 2:3], step=4)
sel = (Db[:, 0] > 430) & (Db[:, 0] < 1000)
exc = sample(H, Db[sel, 0], Db[sel, 1]) - Ab[sel, 0]
f_rv = dict(max_excess_m=round(float(exc.max()), 1), at=[round(float(v), 1) for v in Db[sel][int(np.argmax(exc))]], ok=bool(exc.max() <= 3.0))
R["pass"] &= f_rv["ok"]
# crag top: flat +-1 m, size
ang = np.arctan2(Y - 308, X - 715)
top = np.abs(H - 204) <= 1.0                     # crag top is held at 203.85
lab, n = ndimage.label(top)
k = lab[int((310 + HALF) / px), int((720 + HALF) / px)]
crag = lab == k
xs, ys = X[crag], Y[crag]
f["ravine_bed"] = f_rv
f["crag_top"] = dict(z=204, flat_tolerance_m=1.0, extent_x=[round(float(xs.min())), round(float(xs.max()))],
                     extent_y=[round(float(ys.min())), round(float(ys.max()))],
                     size_m=[round(float(xs.max() - xs.min())), round(float(ys.max() - ys.min()))], spec="about 240 x 220 m")
def drop(x0, y0, dx, dy, dist=60):
    t = np.arange(0, dist, 0.75)
    z = sample(H, x0 + dx * t, y0 + dy * t)
    return float(z[0] - z.min())
f["cliff_south_m"] = round(drop(612, 330, -1, 0), 1)
f["cliff_east_m"] = round(drop(740, 418, 0, 1), 1)
f["saddle_north_z"] = round(float(sample(H, 880, 300)[0]), 1)
f["terrace_z"] = round(float(np.median(sample(H, np.linspace(700, 800, 20), np.linspace(-150, 80, 20)))), 1)
fl = sample(H, np.linspace(450, 680, 30), np.full(30, -120.0))
f["terrace_flank_slope_deg"] = round(float(np.degrees(np.arctan(np.median(np.diff(fl) / (230 / 29))))), 1)
fl_rav = float(sample(H, 742, 145)[0])
f["ravine_floor_at_bridge_z"] = round(fl_rav, 1)
f["ravine_depth_under_bridge_m"] = round(200 - fl_rav, 1)
prof = sample(H, np.full(60, 742.0), np.linspace(120, 170, 60))
f["ravine_wall_max_deg"] = round(float(np.degrees(np.arctan(np.max(np.abs(np.diff(prof))) / (50 / 59)))), 1)
f["city_crown_z"] = round(float(sample(H, -320, -525)[0]), 1)
f["market_square_z"] = round(float(sample(H, -452, -445)[0]), 1)
f["fen_basin_z"] = round(float(sample(H, -1230, -1230)[0]), 1)
rim = [float(sample(H, -1230 + 300 * np.cos(a), -1230 + 300 * np.sin(a))[0]) for a in np.linspace(0, 2 * np.pi, 72, endpoint=False)]
f["fen_rim_min_z"] = round(min(rim), 1)
f["relief_min_max"] = [round(float(H.min()), 1), round(float(H.max()), 1)]
gy, gx = np.gradient(H, px)
slope = np.degrees(np.arctan(np.hypot(gx, gy)))
f["rock_over_45deg_pct"] = round(float((slope > 45).mean() * 100), 1)
# river: a walkable way out (slope < 35 deg over 6 m) at least every 50 m on each bank
RIV = np.array(M["water"]["river"]["points_x_y_bedz_halfwidth"], float)
D, A, L = densify(RIV[:, :2], RIV[:, 2:], step=5)
gaps = {+1: [], -1: []}
for sgn in (+1, -1):
    last = 0.0; worst = 0.0
    for i in range(1, len(D) - 1):
        if D[i, 0] > 1180 or (D[i, 0] < -1050 and D[i, 1] > 1000):
            last = L[i]; continue                       # falls and the gorge are barriers by design
        t = D[i + 1] - D[i - 1]; t /= np.linalg.norm(t)
        nrm = np.array([-t[1], t[0]]) * sgn
        a = D[i] + nrm * (A[i, 1] + 1); b = D[i] + nrm * (A[i, 1] + 9)
        za, zb = sample(H, a[0], a[1])[0], sample(H, b[0], b[1])[0]
        if np.degrees(np.arctan(abs(zb - za) / 8)) < 35:
            worst = max(worst, L[i] - last); last = L[i]
    gaps[sgn] = round(worst, 1)
f["river_bank_exit_max_gap_m"] = gaps
json.dump(R, open(f"{ROOT}/terrain/phase1_checks.json", "w"), indent=1)

# report
for p in R["poi"]:
    print(f"POI {p['id']:2d} {p['name'][:28]:28s} target {p['target']:6.1f} terrain {p['terrain']:7.1f}  {'OK' if p['ok'] else 'FAIL'}")
for r in R["roads"]:
    print("ROAD", r)
for k, v in f.items():
    print("FEAT", k, v)

# hillshade + overlay
step = 2
Hs = H[::step, ::step]
gy, gx = np.gradient(Hs, px * step)
nz = 1 / np.sqrt(gx ** 2 + gy ** 2 + 1)
light = np.clip((-gx * 0.6 + gy * 0.3 + 1) * nz, 0, 1.4)
sl = np.degrees(np.arctan(np.hypot(gx, gy)))
col = np.dstack([0.42 + 0 * Hs, 0.50 + 0 * Hs, 0.33 + 0 * Hs])
col[sl > 40] = [0.55, 0.54, 0.52]
col[Hs > 405] = [0.92, 0.92, 0.94]
rd = np.load(f"{ROOT}/terrain/river_depth.npy")[::step, ::step].astype(np.float32)
col[rd > 0] = [0.25, 0.42, 0.58]
rm = np.load(f"{ROOT}/terrain/road_mask.npy")[::step, ::step]
col[rm > 0] = [0.82, 0.74, 0.58]
img = np.clip(col * light[..., None], 0, 1)
# contours every 20 m
cont = (np.floor(Hs / 20) != np.floor(ndimage.shift(Hs, (1, 0), order=0) / 20)) | (np.floor(Hs / 20) != np.floor(ndimage.shift(Hs, (0, 1), order=0) / 20))
img[cont] *= 0.75
# rows are Y (west->east) and columns X (south->north): rotate to the map view (north up, east right)
view = np.transpose(img, (1, 0, 2))[::-1]
im = Image.fromarray((view * 255).astype(np.uint8)).resize((1512, 1512), Image.LANCZOS)
d = ImageDraw.Draw(im)
to_px = lambda x, y: ((y + HALF) / (2 * HALF) * 1512, (HALF - x) / (2 * HALF) * 1512)
for p in M["points_of_interest"]:
    u, v_ = to_px(*p["xyz"][:2])
    d.ellipse([u - 9, v_ - 9, u + 9, v_ + 9], outline=(20, 20, 20), fill=(250, 250, 250), width=2)
    d.text((u - 6, v_ - 7), str(p["id"]), fill=(0, 0, 0))
for i in range(1, 6):
    g_ = i * 1512 / 6 + (1512 - 1512 * 3000 / 3024) / 2
    d.line([(0, g_), (1512, g_)], fill=(255, 255, 255), width=1); d.line([(g_, 0), (g_, 1512)], fill=(255, 255, 255), width=1)
im.save(f"{ROOT}/terrain/topview_phase1.png")
ref = Image.open(f"{ROOT}/doc/master_map_1500.png").convert("RGB")                  # the map frame spans -1500..1500 m
mine = im.crop((6, 6, 1506, 1506))
Image.blend(ref, mine, 0.55).save(f"{ROOT}/terrain/overlay_master_map.png")
side = Image.new("RGB", (3000, 1500)); side.paste(ref, (0, 0)); side.paste(mine, (1500, 0)); side.resize((2000, 1000)).save(f"{ROOT}/terrain/compare_master_map.png")
print("PASS_ALL_POI", R["pass"])
