# Phase 1 - terrain blockout: layout model heightmap 4033 x 4033 (0.75 m), sections 3, 4 and 11 + Appendix A.
# World metres: +X north, +Y east, Z 0 = valley-floor reference. Image: rows = Y (west->east), columns = X (south->north),
# top-left pixel = [-1512, -1512]; value = 32768 + 64 * z.
import sys, os, json, glob, time
import numpy as np
from scipy import ndimage
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tlib import (axis, grid, spectral, smoothstep, densify, band_field, tension_interp, zoom_to, sample, HALF)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from terrain_core import flow, stream_power, diffuse, thermal
from castle_shape import rim_sd

ROOT = sys.argv[1]
OUT = f"{ROOT}/terrain"
os.makedirs(OUT, exist_ok=True)
M = json.load(open(f"{ROOT}/data/layout_manifest.json"))
# cuts requested by the greybox (covered voids under buildings, tunnel voids, aprons, extra pads): greybox/*_meta.json
FEAT = {"voids": [], "void_paths": [], "void_discs": [], "aprons": [], "pads": []}
for fn in sorted(glob.glob(f"{ROOT}/greybox/*_meta.json")):
    mm = json.load(open(fn))
    for k in FEAT:
        FEAT[k] += mm.get(k, [])
rng = np.random.default_rng(1440)
t0 = time.time()
log = lambda *a: print(f"[{time.time() - t0:6.1f}s]", *a, flush=True)
roads = {r["id"]: r for r in M["roads"]}
RIV = np.array(M["water"]["river"]["points_x_y_bedz_halfwidth"], float)
BRK = np.array(M["water"]["castle_brook"]["points_x_y_bedz_halfwidth"], float)
POI = {p["id"]: p for p in M["points_of_interest"]}

# ---------------------------------------------------------------- 1) control points of the layout model
P, V, W = [], [], []
add = lambda x, y, z, w=1.0: (P.append((x, y)), V.append(z), W.append(w))

for p in M["points_of_interest"]:
    if p["id"] in (1, 2, 3, 9, 14, 22):            # features (crag, terrace, serpentine, bridge, falls, gorge) shape these
        continue
    add(p["xyz"][0], p["xyz"][1], p["xyz"][2], 4.0)
for r in M["roads"]:
    if r["id"] in ("great_bridge",):
        continue
    for x, y, z in r["points_xyz"]:
        if (x, y) == (-452, -855):
            continue                                 # West Bridge deck, not ground
        add(x, y, z, 2.5)
# river banks (meadow level) and brook banks outside the ravine
Dr, Ar, Lr = densify(RIV[:, :2], RIV[:, 2:], step=30)
for (x, y), (bz, hw) in zip(Dr[::2], Ar[::2]):
    if x > 1150:
        continue                                     # upper valley + falls handled by features
    add(x, y, bz + 3.0, 2.0)
Db, Ab, Lb = densify(BRK[:, :2], BRK[:, 2:], step=30)
for (x, y), (bz, hw) in zip(Db[::2], Ab[::2]):
    if x < 420:
        add(x, y, bz + 2.0, 1.5)
# northern ridge: wandering foot (X 820-1030), steep face, crest 400-440, sheer band at the crest
fy = np.array([-1512, -1250, -1000, -700, -400, 0, 300, 600, 900, 1200, 1512])
fx = np.array([1000, 1030, 970, 990, 960, 900, 905, 870, 840, 870, 920])
river_y_at = lambda X: np.interp(X, RIV[:, 0][::-1], RIV[:, 1][::-1])
foot_j = {}
for y in np.arange(-1512, 1513, 75):
    foot = np.interp(y, fy, fx) + 55 * np.sin(y / 97.0 + 0.7) * np.sin(y / 233.0)      # lobes and re-entrants
    for x, z, w in ((foot, 165, 1.0), (foot + rng.uniform(110, 210), rng.uniform(270, 320), 1.0), (1410 + 25 * np.sin(y / 230), 418 + 18 * np.sin(y / 310 + 1), 1.5),
                    (1512, 432 + 8 * np.sin(y / 170), 1.0)):
        if abs(y - river_y_at(min(x, 1512))) < 170 and x > 1100:
            continue                                 # river notch through the ridge (falls)
        add(x, y, z, w)
# south-west corner around the fen (keeps the basin closed)
for x, y, z in ((-1512, -1512, 60), (-1512, -1100, 55), (-1100, -1512, 50), (-1400, -900, 60), (-900, -1400, 70),
                (-1512, -1300, 55), (-1300, -1512, 52)):
    add(x, y, z, 1.5)
# upper river valley through the ridge (above the falls)
for x, y, bz, hw in RIV[:4]:
    add(x, y, bz + 4, 3.0)
# castle surroundings: crag base south/east, saddle north, ravine west (features add the crag itself)
for x, y, z in ((575, 260, 98), (575, 340, 96), (590, 420, 100), (660, 470, 104), (740, 480, 110), (820, 455, 135),
                (880, 380, 166), (885, 300, 166), (870, 220, 170), (640, 180, 140), (560, 200, 92), (520, 300, 85)):
    add(x, y, z, 2.0)
# barbican terrace + south flank (25 deg) - features flatten them exactly
for x, y, z in ((760, -150, 199), (760, 0, 199), (760, 90, 199), (700, -170, 197), (700, 60, 197), (620, -100, 160),
                (560, 40, 130), (480, -140, 100), (450, 60, 90)):
    add(x, y, z, 1.5)
# dark forest X 0..900 (20 -> 150 m)
for x in np.arange(60, 900, 210):
    for y in np.arange(-860, 1000, 210):
        if np.hypot(x - 720, y - 310) < 260 or (540 < x < 820 and -230 < y < 130):
            continue
        add(x + rng.uniform(-40, 40), y + rng.uniform(-40, 40), 25 + 125 * smoothstep(-50, 900, x) + rng.uniform(-12, 12), 0.5)
# east hills (Y > 1000): 100 -> 250 m, east pass notch from the road + POI
for x in np.arange(-950, 1000, 200):
    for y in (1120, 1320, 1500):
        z = 100 + 120 * smoothstep(-700, 1000, x) + 25 * (y - 1000) / 500 + rng.uniform(-15, 15)
        if abs(x + 300) < 120 and y > 1250:
            continue                                  # keep the pass free
        add(x, y, z, 0.6)
add(-150, 1460, 150, 1.0); add(-460, 1460, 140, 1.0)  # shoulders of the east pass
# west hills (Y < -1100), west of the river
for x in np.arange(-800, 1000, 200):
    for y in (-1300, -1480):
        if abs(x + 262) < 110 and y < -1350:
            continue
        add(x, y, 60 + 85 * smoothstep(-900, 900, x) + rng.uniform(-12, 12), 0.6)
add(-120, -1470, 105, 1.0); add(-420, -1470, 95, 1.0)  # shoulders of the west pass
# south hills (X < -1050) with the closed fen basin
for x in (-1130, -1330, -1512):
    for y in np.arange(-900, 1100, 200):
        add(x, y, 55 + 50 * smoothstep(-1050, -1512, x) + rng.uniform(-10, 10), 0.6)
for a in np.linspace(0, 2 * np.pi, 16, endpoint=False):
    add(-1230 + 320 * np.cos(a), -1230 + 320 * np.sin(a), 22 + 6 * np.sin(3 * a), 1.0)   # basin rim
    add(-1230 + 150 * np.cos(a), -1230 + 150 * np.sin(a), 3.3, 2.0)
# gorge (F6): hills either side of the river exit
for x, y, z in ((-1180, 1180, 45), (-1260, 1360, 42), (-1420, 1220, 48), (-1350, 1500, 40), (-1500, 1300, 50)):
    add(x, y, z, 1.5)
# farmland 5 -> 20 m (lowest towards the river, rising to the north and east)
for x in np.arange(-650, -40, 130):
    for y in np.arange(-80, 1010, 130):
        z = 6 + 9 * smoothstep(-690, 0, x) + 4 * smoothstep(700, 1010, y)
        add(x, y, z, 1.0)
# valley meadows between the city and the river
for x, y, z in ((-560, -230, 14), (-650, -360, 9), (-620, 30, 8), (-640, 300, 6), (-700, 600, 4), (-900, 900, 2)):
    add(x, y, z, 1.0)
# city hill: crown +36 at the church, gates
CW = M["city"]["wall_ellipse"]
for k, (x, y, z) in M["city"]["gates"].items():
    add(x, y, z, 4.0)
add(-450, -460, 34, 4.0); add(-320, -525, 36, 3.0); add(-330, -390, 35, 3.0); add(-600, -460, 22, 2.0)
log("control points", len(P))

# ---------------------------------------------------------------- 2) smooth surface through them (12 m grid)
Hc = tension_interp(253, P, V, W, tension=0.3, lam=30.0)
log("layout surface", round(float(Hc.min()), 1), round(float(Hc.max()), 1))

# ---------------------------------------------------------------- 3) natural detail + low-strength erosion (3 m grid)
NE = 1009
X3, Y3 = grid(NE)
H = zoom_to(Hc, NE).astype(np.float64)
hilly = np.clip(smoothstep(0, 400, X3) + smoothstep(950, 1300, np.abs(Y3)) + smoothstep(-950, -1300, X3), 0, 1)
flat_zone = ((X3 > -690) & (X3 < -40) & (Y3 > -130) & (Y3 < 1010)) | (((X3 + 450) / 260) ** 2 + ((Y3 + 460) / 330) ** 2 < 1)
H += (2.0 + 14.0 * hilly) * spectral(NE, 3.6, 11) * (~flat_zone) + 3.0 * spectral(NE, 2.8, 12) * hilly
ridge_zone = smoothstep(780, 950, X3) * smoothstep(1500, 1380, X3)
spurs = 1 - np.abs(spectral(NE, 3.3, 13))                               # spurs and gullies on the ridge face
H += 60 * ridge_zone * (spurs - 0.55) + 25 * ridge_zone * spectral(NE, 3.9, 14)
base = np.zeros(H.shape, bool); base[0, :] = base[-1, :] = base[:, 0] = base[:, -1] = True
for it in range(40):                                  # one low-strength hydraulic pass
    hf, rec, dist, order, area = flow(H, base)
    H = stream_power(H, rec, dist, order, area, 0.0006, 0.5, 3.0, base)
    H = diffuse(H, 0.08, base)
H = thermal(H.astype(np.float64), 3.0 * np.tan(np.radians(38)), 0.25, 6)   # thermal: talus at 38 deg
log("eroded")

# ---------------------------------------------------------------- 4) full resolution 4033 (0.75 m) + features
N = 4033
X, Y = grid(N)
H = zoom_to(H, N).astype(np.float32)
H += 0.35 * spectral(N, 2.6, 21) * (1 - 0.8 * zoom_to(flat_zone.astype(np.float32), N))
px = 0.75
log("upsampled")

# farmland: undulation under 2 m
farm = smoothstep(-20, 110, np.minimum.reduce([X + 690, -40 - X, Y + 130, 1010 - Y]) + 45 * spectral(N, 3.9, 54))
H = H * (1 - farm) + ndimage.gaussian_filter(H, 60) * farm

# fen: closed basin at +3 with standing pools
r_fen = np.hypot(X + 1230, Y + 1230)
fen = smoothstep(260, 120, r_fen + 25 * spectral(N, 3.8, 31))
H = H * (1 - fen) + (2.6 + 1.2 * spectral(N, 3.2, 32)) * fen
rim_z = 3 + 20 * smoothstep(250, 340, r_fen + 25 * spectral(N, 3.8, 33))
H = np.where(r_fen < 460, np.maximum(H, rim_z * smoothstep(460, 380, r_fen) + H * smoothstep(380, 460, r_fen)), H)   # closed basin

# river: bed, banks (walkable most of the way), fords, falls, gorge cliffs
Dr, Ar, Lr = densify(RIV[:, :2], RIV[:, 2:], step=3)
dist, att, side = band_field(Dr, Ar, N, 90)
bz, hw = att[..., 0], att[..., 1]
inb = np.isfinite(dist)
for fx_, fy_ in M["water"]["river"]["fords"]:
    f = smoothstep(30, 8, np.hypot(X - fx_, Y - fy_))
    bz = np.where(inb, bz * (1 - f) + (bz + 1.5) * f, bz)            # ford: bed raised, water 0.6 m deep
gorge = smoothstep(1000, 1150, -X + 0 * Y) * smoothstep(900, 1050, Y)                 # south-east exit (F6)
fall = M["water"]["falls"]
fx0 = fall["xy"][0]
below = inb & (X < fx0) & (X > 1150)
bz = np.where(below, np.minimum(bz, fall["base_z"]), bz)              # bed at the foot of the falls stays at +60
d = np.where(inb, dist, 1e3)
mw = 14 + 22 * (0.5 + 0.5 * spectral(N, 3.9, 61))                     # meadow strip 14-36 m, varies along the river
chan = (bz + 1.6 * smoothstep(0.55 * hw, hw + 2.0, d) + np.minimum(np.maximum(d - hw - 2.0, 0), mw) * 0.12
        + np.maximum(d - hw - 2.0 - mw, 0) * 0.35)                      # bank, meadow strip (~7 deg), then valley side
cliff = bz + 42 * smoothstep(hw, hw + 10, d)                                             # gorge: 40 m cliffs
chan = chan * (1 - gorge) + np.maximum(chan, cliff) * gorge
riv_w = smoothstep(hw + 34 + mw, hw + 2 + mw, d) * inb
H = np.where(riv_w > 0, H * (1 - riv_w) + np.minimum(H, chan) * riv_w, H)
H = np.where(inb & (X > 1140) & (X < fx0 + 1.5) & (d < hw + 90), np.maximum(H, chan), H)   # refill the eroded pit
exact = smoothstep(hw + 4 + mw, hw - 6 + mw, d) * inb * (1 - gorge) * (X < fx0 - 0.5)
H = np.where(exact > 0, H * (1 - exact) + chan * exact, H)             # channel + walkable banks exactly as designed
H = np.where(gorge * smoothstep(hw + 60, hw + 12, d) > 0, np.maximum(H, chan * gorge * smoothstep(hw + 60, hw + 12, d) + H * (1 - gorge * smoothstep(hw + 60, hw + 12, d))), H)
up = (X > fx0 + 1.5) & inb & (d < hw + 45 + 20 * spectral(N, 3.9, 55))     # hanging valley above the falls
lip = np.where(d < hw + 1, fall["top_z"], fall["top_z"] + 3 + np.maximum(d - hw - 1, 0) * 0.9)
upbed = np.maximum(bz, fall["top_z"]) + np.where(d < hw, 0, 1.6 + np.maximum(d - hw, 0) * 0.45)
near_f = smoothstep(80, 0, X - fx0)
H = np.where(up, np.maximum(H, upbed * (1 - near_f) + lip * near_f), H)
pool = (np.abs(X - (fx0 - 9)) < 9) & (d < hw + 4)                            # plunge pool at the foot
H = np.where(pool, np.minimum(H, fall["base_z"] - 4), H)
# foot of the falls drawn explicitly: pool, bed at +60 under the curtain, walkable banks, then the vertical face
foot = inb & (X > fx0 - 8) & (X <= fx0 + 1.6) & (d < hw + 30)
H = np.where(foot, np.where(pool, fall["base_z"] - 4, chan), H)
river_depth = np.where(inb & (d < hw), 1.5 + 1.5 * smoothstep(0, 6, hw - d), 0)
log("river")

# castle brook + ravine (V-shaped, walls ~75 deg, 90 m deep under the bridge)
Db, Ab, Lb = densify(BRK[:, :2], BRK[:, 2:], step=3)
dist_b, att_b, _ = band_field(Db, Ab, N, 160)
bzb, hwb = att_b[..., 0], att_b[..., 1]
inr = np.isfinite(dist_b) & (X > 425) & (X < 1045)
v_wall = bzb + np.maximum(dist_b - hwb, 0) * np.tan(np.radians(75))
rav_end = smoothstep(425, 470, X) * smoothstep(1045, 1015, X)
H = np.where(inr, np.minimum(H, v_wall * rav_end + H * (1 - rav_end)), H)
brook = np.isfinite(dist_b) & (X <= 440)
bch = bzb + 1.0 * smoothstep(0.5 * hwb, hwb + 1.5, dist_b) + np.maximum(dist_b - hwb - 1.5, 0) * 0.35
bw = smoothstep(hwb + 25, hwb + 6, np.where(brook, dist_b, 1e3)) * brook
H = np.where(bw > 0, H * (1 - bw) + np.minimum(H, bch) * bw, H)
log("brook + ravine")

# barbican terrace: flat +199 (about 120 x 280 m), steady 25 deg south flank carrying the serpentine
tx, ty = np.maximum(np.abs(X - 751) - 31, 0), np.maximum(np.abs(Y + 36) - 124, 0)
ter_edge = 30 - np.hypot(tx, ty) - np.maximum(np.abs(X - 751) - 61, np.abs(Y + 36) - 154).clip(max=0) * 0 + 22 * spectral(N, 3.8, 51)
ter_edge = np.minimum(ter_edge, 118 - Y)                               # rounded outline, east edge on the ravine rim
ter = smoothstep(-2, 2, ter_edge)
flank_z = 199 - np.maximum(690 - X, 0) * np.tan(np.radians(25))
flank_m = (smoothstep(-170, 30, np.minimum(Y + 200, 120 - Y) + 70 * spectral(N, 3.9, 52))
           * smoothstep(250, 430, X + 60 * spectral(N, 3.9, 53)) * smoothstep(712, 690, X)) ** 1.5
H = np.where(flank_m > 0, H * (1 - flank_m) + np.maximum(H, flank_z) * flank_m, H)
H = H * (1 - ter) + 199.0 * ter
log("terrace")

# castle crag: lobed flat top +204 (+-1 m), sheer 80-130 m faces south and east, saddle +166 north
sd = rim_sd(X, Y)                                                        # signed distance to the crag rim (m)
crag_top = sd < 0
face = 203.85 - np.maximum(sd, 0) * np.tan(np.radians(82))              # cliff
H = np.where(sd < 70, np.maximum(H, face), H)
H = np.where(crag_top, 203.85, H)               # 15 cm under the L0 floors (no z-fighting), inside the +-1 m tolerance
# castle model (Castle 2.0): the crag top takes the relief of the hill the model was built on, raised from the rim
CM_ = json.load(open(f"{ROOT}/greybox/castle_meta.json")) if os.path.exists(f"{ROOT}/greybox/castle_meta.json") else {}
if "castle_plate" in CM_:
    from scipy.interpolate import RegularGridInterpolator
    cp = CM_["castle_plate"]; pl = np.load(f"{ROOT}/{cp['file']}")
    PZ = np.nan_to_num(pl["plate"], nan=float(np.nanmin(pl["plate"])))
    itp = RegularGridInterpolator((pl["xs"], pl["ys"]), PZ, bounds_error=False, fill_value=float(cp["min_rel"]))
    ox_, oy_, oz_ = cp["origin"]
    m_ = sd < 0
    hill = oz_ + np.maximum(itp(np.stack([X[m_] - ox_, Y[m_] - oy_], 1)), cp["min_rel"])
    w_ = smoothstep(0.0, -6.0, sd[m_])
    H[m_] = np.maximum(203.85, 203.85 * (1 - w_) + hill * w_)
    log("castle hill on the crag", float(hill.max()))
# the ravine wins over the terrace flank and the crag skirts: the castle brook runs through it from the ridge to X 430
inr2 = np.isfinite(dist_b) & (X > 375) & (X < 1045)
rav2 = smoothstep(375, 395, X) * smoothstep(1045, 1015, X)
H = np.where(inr2, np.minimum(H, v_wall * rav2 + H * (1 - rav2)), H)
log("crag + ravine re-cut")

# city hill: smooth crown +36 at the church, gates on their levels, steep 15 m bank to the river (west, south)
cpts = np.array([[-450, -460, 34], [-320, -525, 36], [-330, -390, 35], [-452, -445, 33], [-325, -375, 34]] +
                [list(v) for v in M["city"]["gates"].values()], float)
A_ = np.stack([np.ones(len(cpts)), cpts[:, 0], cpts[:, 1], cpts[:, 0] ** 2, cpts[:, 1] ** 2, cpts[:, 0] * cpts[:, 1]], 1)
coef = np.linalg.lstsq(A_, cpts[:, 2], rcond=None)[0]
cz = coef[0] + coef[1] * X + coef[2] * Y + coef[3] * X ** 2 + coef[4] * Y ** 2 + coef[5] * X * Y
er = np.sqrt(((X + 450) / 230) ** 2 + ((Y + 460) / 300) ** 2)
inside = smoothstep(1.06, 1.0, er)
H = H * (1 - inside) + cz.astype(np.float32) * inside
nx, ny = (X + 450) / 230, (Y + 460) / 300
ws = smoothstep(0.15, 0.55, np.maximum(-nx, -ny) / np.maximum(er, 1e-3))                # west and south sides
bank = cz - 15 * smoothstep(1.03, 1.12, er)
bw_ = ws * smoothstep(1.35, 1.12, er) * (er > 1.0)
H = np.where(bw_ > 0, H * (1 - bw_) + np.minimum(H, bank) * bw_, H)
log("city hill coef", np.round(coef, 6).tolist())

# borders: sheer rock band at the northern crest; edge hills rise slightly (natural barriers before blocking volumes)
band = smoothstep(1425, 1465, X + 30 * spectral(N, 3.9, 56))
H = H + 35 * band                                                # sheer band at the crest
for e in (smoothstep(1420, 1512, Y), smoothstep(-1420, -1512, Y), smoothstep(-1420, -1512, X)):
    H = H + 18 * e * e * (H > 20)

# east pass: the trade road climbs an open valley (14 deg sides) to the border post instead of a cutting, so the
# establishing shot V7 looks west down the valley to the walls, the church tower and the castle
RF0 = json.load(open(f"{ROOT}/data/roads_final.json"))["trade_road"]
txy0, tz0 = np.array(RF0["xy"]), np.array(RF0["z"])
sel = txy0[:, 1] > 900
Dp, Ap, _ = densify(txy0[sel], tz0[sel][:, None], step=2, smooth=False)
dist_p, att_p, _ = band_field(Dp, Ap, N, 240)
vz = att_p[..., 0] + 0.25 * np.maximum(dist_p - 8, 0)
wp_ = smoothstep(950, 1060, Y) * np.isfinite(dist_p)
H = np.where(wp_ > 0, H * (1 - wp_) + np.minimum(H, vz) * wp_, H)
log("east pass valley")

# site pads (flat platforms at the listed elevations) + cuts requested by the greybox (stair shafts, tunnel exit)
PADS = [  # (x, y, z, radius, kind)
    (320, -95, 67, 16, "watchtower"), (-100, -370, 23, 58, "cemetery"), (150, -1200, 88, 38, "abbey"),
    (380, -620, 83, 55, "woodcutters"), (880, -560, 119, 22, "stone_circle"),
    (-250, 700, 7, 90, "hamlet"), (-390, -60, 19, 60, "faubourg"), (-300, 1440, 95, 25, "border_post"),
    (-262, -1440, 35, 25, "west_pass")] + [tuple(p) for p in FEAT.get("pads", [])]
for x, y, z, rad, kind in PADS:
    rr = np.hypot(X - x, Y - y) * (1 + 0.18 * spectral(N, 3.8, int(abs(x * 7 + y)) % 997))
    w_ = smoothstep(rad + 80, rad * 0.75, rr) ** 1.3 * (1 - np.clip(exact * 1.5, 0, 1))   # never fills the river channel
    H = H * (1 - w_) + z * w_
# gallows hill: low mound (+3 m) at the crossroads
w_ = smoothstep(45, 0, np.hypot(X + 560, Y + 1060)); H = H + 3.0 * w_ * w_
# quarry: 80 x 60 m terraced limestone cut into the hillside (3 benches)
qd = np.maximum(np.abs(X - 250) - 30, np.abs(Y - 1200) - 40)
for k, zq in enumerate((150, 158, 166)):
    m = smoothstep(4, 0, qd + 12 * k) * (Y > 1200 - 40 + 22 * k)
    H = np.where(m > 0, np.minimum(H, zq + 0.0 * m) * m + H * (1 - m), H)
# roads: graded beds from the solved profiles (data/roads_final.json): bed = width + 1 m each side, cut/fill over 8 m
RF = json.load(open(f"{ROOT}/data/roads_final.json"))
road_mask = np.zeros((N, N), np.uint8)
ROADK = {"cart road": 1, "track": 2, "footpath": 3, "stairs": 4, "bridge": 5}
FB = [c for c in RF["_crossings"] if c["kind"] == "footbridge"]
order = ["castle_stairs"] + [k for k in RF if k not in ("castle_stairs", "_crossings")]   # roads win over the stairs
for rid in order:
    r = RF[rid]
    if r["type"] == "bridge":
        continue
    xy = np.array(r["xy"]); zz = np.array(r["z"])[:, None]
    Dd, Ad, Ld = densify(xy, zz, step=2, smooth=False)
    dist_r, att_r, _ = band_field(Dd, Ad, N, r["width_m"] / 2 + 14)
    zr = att_r[..., 0]
    half = r["width_m"] / 2 + (1.0 if r["type"] != "footpath" else 0.3)
    blend = 8.0 if r["type"] in ("cart road", "stairs") else 4.0
    dd = np.where(np.isfinite(dist_r), dist_r, 1e3)
    w_ = smoothstep(half + blend, half, dd)
    if rid == "serpentine":                        # retaining walls where the stairs bridge over the road
        for c in FB:
            near = smoothstep(30, 15, np.hypot(X - c["xy"][0], Y - c["xy"][1]))
            w_ = np.maximum(w_ * (1 - near), smoothstep(half + 1.0, half, dd) * near)
    if rid == "castle_stairs":
        for c in FB:                               # the stairs fly over the road on a footbridge: no fill there
            w_ = w_ * (1 - smoothstep(16, 8, np.hypot(X - c["xy"][0], Y - c["xy"][1])))
    if rid == "west_road":
        w_ = w_ * (1 - smoothstep(40, 25, np.hypot(X + 452, Y + 855)))   # the West Bridge spans the river
    H = np.where(w_ > 0, H * (1 - w_) + zr * w_, H)
    road_mask = np.where(np.isfinite(dist_r) & (dist_r < r["width_m"] / 2), ROADK[r["type"]], road_mask)
log("roads graded")

# hero view V6 (third hairpin, "castle walls looming overhead"): the spur between the hairpin and the ravine rim rose
# 13 m above the doc camera within 15 m; it is notched under the sightline (1.5 m below it, 45 deg sides) for 60 m
v6 = next(v for v in M["hero_views"] if v["id"] == "V6")
c6, t6 = np.array(v6["camera"], float), np.array(v6["look_at"], float)
d6 = t6[:2] - c6[:2]; L6 = float(np.linalg.norm(d6)); d6 /= L6
along = (X - c6[0]) * d6[0] + (Y - c6[1]) * d6[1]
across = np.abs(-(X - c6[0]) * d6[1] + (Y - c6[1]) * d6[0])
cut = c6[2] + (t6[2] - c6[2]) * along / L6 - 1.5 + np.maximum(across - (4.0 + 0.3 * along), 0.0)
H = np.where((along > 2.0) & (along < 60.0), np.minimum(H, cut), H)
log("V6 sightline notch")

for x, y, z, rad, blend in FEAT["aprons"]:              # small graded platforms (tunnel mouth, doors)
    w_ = smoothstep(rad + blend, rad, np.hypot(X - x, Y - y))
    H = H * (1 - w_) + z * w_
np.save(f"{OUT}/H_natural_4033.npy", np.minimum(H, 440.0).astype(np.float32))      # surface before the covered voids (greybox reads it)
# covered voids: the landscape is lowered under buildings with underground levels and along tunnels, so no landscape
# surface ever cuts a room; the greybox covers every void (slabs, 1.6 m walls, talus) and hides the 0.75 m edge
for x0, x1, y0, y1, zb in FEAT["voids"]:
    m = (X >= x0) & (X <= x1) & (Y >= y0) & (Y <= y1)
    H = np.where(m, np.minimum(H, zb), H)
for x, y, r, zb in FEAT["void_discs"]:
    H = np.where(np.hypot(X - x, Y - y) <= r, np.minimum(H, zb), H)
for vp in FEAT["void_paths"]:
    P = np.array(vp["pts"], float)
    Dd, Ad, _ = densify(P[:, :2], P[:, 2:3], step=1.0, smooth=False)
    dist_v, att_v, _ = band_field(Dd, Ad, N, vp["half"] + 2)
    m = np.isfinite(dist_v) & (dist_v <= vp["half"])
    H = np.where(m, np.minimum(H, att_v[..., 0]), H)
log("aprons + voids", len(FEAT["aprons"]), len(FEAT["voids"]), len(FEAT["void_discs"]), len(FEAT["void_paths"]))

# ground-floor rooms: the landscape must never show above a floor. Where it reaches a room's floor, it is lowered to the
# underside of the floor slab over the room and its walls (0.9 m), with a 45 deg bank outside (no trench); the bank
# never digs under another greybox piece (their bottoms are protected), so no neighbour is left hanging
ROOMS_ALL = []
for fn in sorted(glob.glob(f"{ROOT}/greybox/*_meta.json")):
    ROOMS_ALL += json.load(open(fn)).get("rooms", [])
PCS = []
for fn in sorted(glob.glob(f"{ROOT}/greybox/*_groups.json")):
    for g in json.load(open(fn)):
        for p_ in g["prims"]:
            if p_["col"] != "only":
                v_ = np.asarray(p_["v"]); PCS.append([*v_.min(0)[:2], *v_.max(0)[:2], v_[:, 2].min()])
PCS = np.array(PCS).reshape(-1, 5)
ax_ = X[0]; ncut = 0
for r in ROOMS_ALL:
    if r.get("sealed"):                                  # closed rooms under the landscape (library, secret stair)
        continue
    x0, x1, y0, y1, z0 = r["x0"], r["x1"], r["y0"], r["y1"], r["z0"]
    ci = np.nonzero((ax_ >= x0 - 4.5) & (ax_ <= x1 + 4.5))[0]; ri = np.nonzero((ax_ >= y0 - 4.5) & (ax_ <= y1 + 4.5))[0]
    if len(ci) == 0 or len(ri) == 0:
        continue
    win = np.ix_(ri, ci)
    Xw, Yw, Hw = X[win], Y[win], H[win]
    inner = (Xw >= x0) & (Xw <= x1) & (Yw >= y0) & (Yw <= y1)
    if not inner.any() or Hw[inner].max() <= z0 - 0.05 or z0 - np.median(Hw[inner]) > 3.0:      # skip upper floors
        continue
    dbox = np.maximum.reduce([x0 - Xw, Xw - x1, y0 - Yw, Yw - y1])
    low = np.minimum(Hw, z0 - 0.3 + np.maximum(dbox - 0.9, 0.0))
    near_ = (PCS[:, 0] < x1 + 4.5) & (PCS[:, 2] > x0 - 4.5) & (PCS[:, 1] < y1 + 4.5) & (PCS[:, 3] > y0 - 4.5)
    cx_, cy_ = (PCS[:, 0] + PCS[:, 2]) / 2, (PCS[:, 1] + PCS[:, 3]) / 2
    own = (cx_ > x0 - 0.9) & (cx_ < x1 + 0.9) & (cy_ > y0 - 0.9) & (cy_ < y1 + 0.9)
    for px0, py0, px1, py1, pz in PCS[near_ & ~own]:
        m_ = (Xw >= px0) & (Xw <= px1) & (Yw >= py0) & (Yw <= py1)
        if m_.any() and pz <= Hw[m_].max() + 0.3:                               # only pieces resting on the ground
            low = np.where(m_, np.maximum(low, np.minimum(Hw, pz)), low)
    H[win] = low; ncut += 1
log("ground-floor cuts", ncut)

# ---------------------------------------------------------------- 5) export + acceptance checks
H = np.minimum(H, 440.0).astype(np.float32)                      # relief -26 .. +440 m
np.save(f"{OUT}/H_4033.npy", H)
np.save(f"{OUT}/road_mask.npy", road_mask)
np.save(f"{OUT}/river_depth.npy", river_depth.astype(np.float16))
v = np.clip(np.round(32768 + 64 * H), 0, 65535).astype(np.uint16)
Image.fromarray(v).save(f"{OUT}/heightmap_base_4033.png")
log("heightmap written", float(H.min()), float(H.max()))
