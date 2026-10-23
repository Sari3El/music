# Secondary sites (section 7) + road structures: castle stairs (landings, footbridges), serpentine low wall, stakes,
# watchtower, cemetery + mortuary chapel, gallows crossroads, abbey ruin, woodcutters' camp, stone circle, falls cave,
# East Faubourg, watermills + tannery, docks, hamlet, quarry, border post, west-pass rockfall, fen, West Bridge,
# signposts, backdrop mountains, blocking volumes. World metres, +X north, +Y east.
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gb_lib import Group, rect_minus, ground_snap
from tlib import sample

ROOT = sys.argv[1]
HN = f"{ROOT}/terrain/H_natural_4033.npy"
H = np.load(HN if os.path.exists(HN) else f"{ROOT}/terrain/H_4033.npy")
M = json.load(open(f"{ROOT}/data/layout_manifest.json"))
RF = json.load(open(f"{ROOT}/data/roads_final.json"))
gz = lambda x, y: float(sample(H, x, y)[0])
rng = np.random.default_rng(11)
ROOMS, VOIDS, VOID_PATHS, APRONS, MOVABLE, BLOCKERS, SIGNS = [], [], [], [], [], [], []
RSP = 0.45 + 2.2
POI = {p["id"]: p["xyz"] for p in M["points_of_interest"]}
groups = []


def G(name, folder):
    g = Group(name, folder)
    groups.append(g)
    return g


def R(name, x0, x1, y0, y1, z0, h, kind="site"):
    r = dict(name=name, x0=x0, x1=x1, y0=y0, y1=y1, z0=z0, z1=z0 + h, interior=kind)
    ROOMS.append(r)
    return r


def obox(g, c, t, ht, hn, z0, z1, mat, col=True):
    t = np.array(t, float) / np.linalg.norm(t); n = np.array([-t[1], t[0]])
    c = np.array(c, float)
    pts = [c - t * ht - n * hn, c + t * ht - n * hn, c + t * ht + n * hn, c - t * ht + n * hn]
    g.poly_prism([tuple(p) for p in pts], z0, z1, mat, col)


# road centre lines (2 m) for clearance tests
RP = []
for rid, r in RF.items():
    if rid.startswith("_"):
        continue
    xy = np.array(r["xy"])
    for a, b in zip(xy[:-1], xy[1:]):
        n = max(2, int(np.hypot(*(b - a)) / 2))
        for t in np.linspace(0, 1, n, endpoint=False):
            RP.append((*(a + (b - a) * t), r["width_m"] / 2, rid))
RPA = np.array([p[:3] for p in RP])


def road_clear(x, y, margin=2.0):
    """Distance from (x, y) to the nearest road edge (negative = on a road)."""
    d = np.hypot(RPA[:, 0] - x, RPA[:, 1] - y) - RPA[:, 2]
    return float(d.min()) - margin


def rect_clear(x0, x1, y0, y1, margin=2.0):
    return min(road_clear(x, y, margin) for x in np.linspace(x0, x1, 4) for y in np.linspace(y0, y1, 4))


def plinth(g, x0, x1, y0, y1, ztop, mat="GB_Stone"):
    zmin = min(gz(x, y) for x in (x0, x1) for y in (y0, y1))
    g.box(x0, x1, y0, y1, zmin - 0.8, ztop, mat)


def hut(g, name, x0, x1, y0, y1, door_side, h=4.3, t=0.5, mat="GB_Wood", roof="GB_Roof", pitch=45, kind="site", door_w=2.0,
        z=None, plinth_=True):
    """Small enterable building: one room (ceiling >= 4 m), a door, plinth and roof. door_side in n/s/e/w."""
    z = z if z is not None else round(max(gz(x, y) for x in (x0, x1) for y in (y0, y1)) + 0.2, 2)
    if plinth_:
        plinth(g, x0, x1, y0, y1, z - 0.3)
    r = R(name, x0 + t / 2, x1 - t / 2, y0 + t / 2, y1 - t / 2, z, h, kind)
    um = ((y0 + y1) / 2) if door_side in ("n", "s") else ((x0 + x1) / 2)
    g.room(r, doors=[(door_side, um - door_w / 2, um + door_w / 2, z, z + 3.0)], mat_wall=mat, t=t)
    ax = "x" if (x1 - x0) >= (y1 - y0) else "y"
    span = (y1 - y0) if ax == "x" else (x1 - x0)
    g.gable(x0, x1, y0, y1, z + h + 0.3, z + h + 0.3 + span / 2 * math.tan(math.radians(pitch)), roof, ax)
    # threshold ramp from the ground to the door sill
    zg = {"n": gz(x1 + 1.5, um), "s": gz(x0 - 1.5, um), "e": gz(um, y1 + 1.5), "w": gz(um, y0 - 1.5)}[door_side]
    if z - zg > 0.25:
        p0 = {"n": (x1 + 0.05 + (z - zg) / 0.3, um), "s": (x0 - 0.05 - (z - zg) / 0.3, um), "e": (um, y1 + 0.05 + (z - zg) / 0.3), "w": (um, y0 - 0.05 - (z - zg) / 0.3)}[door_side]
        p1 = {"n": (x1, um), "s": (x0, um), "e": (um, y1), "w": (um, y0)}[door_side]
        g.ramp(p0, p1, door_w + 0.6, zg, z, 1.0 + (z - zg), "GB_Stone")
    return z


def closed_house(g, x0, x1, y0, y1, front, storeys=2, pitch=55, upper="GB_Plaster", seed=0):
    fx, fy = {"+x": (x1, (y0 + y1) / 2), "-x": (x0, (y0 + y1) / 2), "+y": ((x0 + x1) / 2, y1), "-y": ((x0 + x1) / 2, y0)}[front]
    zf = gz(fx, fy) + 0.15
    plinth(g, x0, x1, y0, y1, zf)
    g.box(x0, x1, y0, y1, zf, zf + 4.0, "GB_Stone")
    ze = zf + 4.0 + 3.4 * (storeys - 1)
    if storeys > 1:
        g.box(x0, x1, y0, y1, zf + 4.0, ze, upper)
    ax = "x" if front in ("+x", "-x") else "y"
    span = (y1 - y0) if ax == "x" else (x1 - x0)
    g.gable(x0, x1, y0, y1, ze, ze + span / 2 * math.tan(math.radians(pitch)), "GB_Tile", ax)
    nrm = {"+x": (1, 0), "-x": (-1, 0), "+y": (0, 1), "-y": (0, -1)}[front]
    tng = np.array([-nrm[1], nrm[0]], float)
    obox(g, np.array([fx, fy]) + np.array(nrm) * 0.05, tng, 0.9, 0.08, zf, zf + 2.6, "GB_Wood", col=False)
    W_ = (y1 - y0) if front in ("+x", "-x") else (x1 - x0)
    for k in range(1, storeys):
        for u in (-W_ / 4, W_ / 4):
            obox(g, np.array([fx, fy]) + np.array(nrm) * 0.06 + tng * u, tng, 0.6, 0.06, zf + 4.0 + 3.4 * (k - 1) + 1.0,
                 zf + 4.0 + 3.4 * (k - 1) + 2.4, "GB_WinLit" if (seed + k + int(u)) % 3 == 0 else "GB_WinDark", col=False)
    return zf


def tree(g, x, y, h=9.0, r=3.5, dead=False):
    z = gz(x, y)
    g.cyl(x, y, 0.35 if not dead else 0.25, z - 0.5, z + h * (0.6 if not dead else 1.0), "GB_Wood", 8)
    if not dead:
        g.cone(x, y, r, z + h * 0.35, z + h, "GB_Hedge", 10, col=False)


# ====================================================================== castle stairs (3 m, landings every 15 m)
cs = RF["castle_stairs"]; sp = RF["serpentine"]
cxy, cz_, cs_s = np.array(cs["xy"]), np.array(cs["z"]), np.array(cs["s"])
spxy = np.array(sp["xy"])
FB = [c for c in RF["_crossings"] if c["kind"] == "footbridge"]
LV = [c for c in RF["_crossings"] if c["kind"] == "level"]
stairs_g = G("SM_GB_Castle_Stairs", "Environment/Castle")
foot_g = G("SM_GB_Castle_Footbridges", "Environment/Castle")
TAN28 = math.tan(math.radians(28))
sk = np.arange(0, cs_s[-1] + 1e-6, 15.0); sk[-1] = cs_s[-1]
PX = np.interp(sk, cs_s, cxy[:, 0]); PY = np.interp(sk, cs_s, cxy[:, 1]); PZ = np.interp(sk, cs_s, cz_)
STAIR_LOG = dict(pieces=0, landings=0, no_landing=0, max_angle_deg=0.0, footbridge_pieces=0, level_gaps=0)
for k in range(len(sk) - 1):
    a = np.array([PX[k], PY[k]]); b = np.array([PX[k + 1], PY[k + 1]]); z0, z1 = PZ[k], PZ[k + 1]
    L = np.linalg.norm(b - a)
    if L < 1.0:
        continue
    d = (b - a) / L; mid = (a + b) / 2
    if min(np.hypot(*(mid - np.array(c["xy"]))) for c in LV) < 9.0 or np.min(np.hypot(*(spxy - mid).T)) < 4.0:
        STAIR_LOG["level_gaps"] += 1                                    # the stairs meet the serpentine at grade here
        continue
    near_fb = min(np.hypot(*(mid - np.array(c["xy"]))) for c in FB) < 12.0
    dz = z1 - z0
    if abs(dz) < 0.2:
        stairs_g.ramp(tuple(a), tuple(b), 3.0, z0, z1, 1.0, "GB_Stone")
        continue
    n = max(1, int(round(abs(dz) / 0.2)))
    landing = 2.5
    if abs(dz) / max(L - landing, 0.1) > TAN28:
        landing = max(0.0, L - abs(dz) / TAN28)
    if landing < 1.2:
        landing = 0.0
        STAIR_LOG["no_landing"] += 1
    else:
        STAIR_LOG["landings"] += 1
    run = (L - landing) / n
    STAIR_LOG["max_angle_deg"] = max(STAIR_LOG["max_angle_deg"], math.degrees(math.atan(abs(dz) / (L - landing))))
    if dz > 0:
        stairs_g.stairs(tuple(a), tuple(d), 3.0, z0, z1, "GB_Stone", dz / n, run, solid=not near_fb)
        if landing:
            stairs_g.ramp(tuple(b - d * landing), tuple(b), 3.0, z1, z1, 1.2, "GB_Stone")
    else:
        if landing:
            stairs_g.ramp(tuple(a), tuple(a + d * landing), 3.0, z0, z0, 1.2, "GB_Stone")
        stairs_g.stairs(tuple(b), tuple(-d), 3.0, z1, z0, "GB_Stone", -dz / n, run, solid=not near_fb)
    STAIR_LOG["pieces"] += 1
    if near_fb:                                                         # footbridge: deck, parapets, piers clear of the road
        STAIR_LOG["footbridge_pieces"] += 1
        nrm = np.array([-d[1], d[0]])
        foot_g.ramp(tuple(a), tuple(b), 3.6, z0 - 0.3, z1 - 0.3, 0.9, "GB_Stone")
        for s_ in (-1, 1):
            foot_g.ramp(tuple(a + nrm * s_ * 1.75), tuple(b + nrm * s_ * 1.75), 0.3, z0 + 1.1, z1 + 1.1, 1.4, "GB_Stone")
        for p, zz in ((a, z0), (b, z1)):
            if np.min(np.hypot(*(spxy - p).T)) > 5.5:
                foot_g.box(p[0] - 1.2, p[0] + 1.2, p[1] - 1.8, p[1] + 1.8, gz(*p) - 1.0, zz - 1.2, "GB_Stone")

# serpentine: low wall on the valley side, stakes at the dead-wood edge, cart + horse skeleton at the first hairpin
wall_g = G("SM_GB_Castle_SerpentineWall", "Environment/Castle")
spz = np.array(sp["z"])
nwall = 0
for i in range(len(spxy) - 1):
    a, b = spxy[i], spxy[i + 1]; L = np.linalg.norm(b - a)
    if L < 1:
        continue
    d = (b - a) / L; nrm = np.array([-d[1], d[0]]); mid = (a + b) / 2
    if min(np.hypot(*(mid - np.array(c["xy"]))) for c in RF["_crossings"]) < 10 or i < 2 or i > len(spxy) - 4:
        continue
    zl, zr = gz(*(mid + nrm * 7)), gz(*(mid - nrm * 7))
    zm = (spz[i] + spz[i + 1]) / 2
    side = 1 if zl < zr else -1
    if zm - min(zl, zr) < 1.5:
        continue
    o = nrm * side * 3.0
    wall_g.ramp(tuple(a + o), tuple(b + o), 0.5, spz[i] + 1.0, spz[i + 1] + 1.0, 2.0, "GB_Stone")
    nwall += 1
props_g = G("SM_GB_Castle_RoadProps", "Environment/Props")
dw = M["zones"][[z["id"] for z in M["zones"]].index("dead_wood")]
dd = np.hypot(spxy[:, 0] - dw["centre"][0], spxy[:, 1] - dw["centre"][1])
edge_i = [i for i in range(len(spxy) - 1) if abs(dd[i] - dw["radius_m"]) < 25][:7]
nstakes = 0
for i in edge_i:
    a, b = spxy[i], spxy[i + 1]; L = np.linalg.norm(b - a); d = (b - a) / max(L, 1e-6); nrm = np.array([-d[1], d[0]])
    for s_ in np.arange(0, L, 4.0):
        for side in (-1, 1):
            p = a + d * s_ + nrm * side * 4.2
            z = gz(*p)
            hgt = 4.0 + rng.uniform(-0.6, 0.8)
            props_g.cyl(p[0], p[1], 0.14, z - 1.0, z + hgt, "GB_Wood", 6)
            if rng.random() < 0.3:
                props_g.box(p[0] - 0.05, p[0] + 0.05, p[1] - 0.25, p[1] + 0.25, z + hgt - 1.6, z + hgt - 0.6, "GB_Detail", col=False)  # rags
            nstakes += 1
hp = np.array(sp["xy"])[np.argmin(np.hypot(spxy[:, 0] - 436, spxy[:, 1] - 90))]
cp = hp + np.array([-9.0, 0.0]); zc = gz(*cp)
props_g.box(cp[0] - 1.0, cp[0] + 1.0, cp[1] - 2.0, cp[1] + 2.0, zc + 0.75, zc + 1.45, "GB_Wood")       # abandoned cart
for wx in (-1.1, 1.1):                                                                              # four wheels
    for wy in (-1.2, 1.2):
        props_g.wheel((cp[0] + wx, cp[1] + wy, zc + 0.6), (1, 0), 0.6, 0.06, "GB_Wood", col=False)
for dx_, dy_ in ((-1.1, -1.4), (1.1, -1.4)):
    props_g.cyl(cp[0] + dx_, cp[1] + dy_, 0.6, zc, zc + 0.15, "GB_Wood", 10, col=False)
props_g.box(cp[0] + 2.0, cp[0] + 2.6, cp[1] - 1.0, cp[1] + 1.5, zc, zc + 0.4, "GB_Interior", col=False)  # horse skeleton

# ====================================================================== 4 watchtower ruin (18 m, half collapsed)
wt = G("SM_GB_Ruin_Watchtower", "Environment/Ruins")
wx, wy, wz = POI[4]
best = max(((ox, oy) for ox in np.arange(-20, 21, 2.0) for oy in np.arange(-20, 21, 2.0) if math.hypot(ox, oy) <= 20),
           key=lambda o: min(rect_clear(wx + o[0] - 5.5, wx + o[0] + 5.5, wy + o[1] - 5.5, wy + o[1] + 5.5, 3.0), 6.0) - 0.01 * math.hypot(*o))
TX, TY = wx + best[0], wy + best[1]
HW = 5.5                                                                                             # 11 x 11 m tower, 1 m walls
tz = round(max(gz(x, y) for x in (TX - HW, TX + HW) for y in (TY - HW, TY + HW)) + 0.2, 2)
plinth(wt, TX - HW, TX + HW, TY - HW, TY + HW, tz - 0.3)
wrd = dict(x0=TX - HW + 0.5, x1=TX + HW - 0.5, y0=TY - HW + 0.5, y1=TY + HW - 0.5, z0=tz, z1=tz + 12.0)
wt.room(wrd, doors=[("s", TY - 1.2, TY + 1.2, tz, tz + 3.2)], windows=[("n", TY - 0.6, TY + 0.6, tz + 13.0, tz + 14.5)], mat_wall="GB_Stone", t=1.0, ceil=False)
R("Watchtower ruin (ground)", TX - HW + 1.0, TX + HW - 1.0, TY - HW + 1.0, TY + HW - 1.0, tz, 12.0, "ruin")
for (a0, a1, b0, b1, ztop) in ((TX - HW, TX + HW, TY + HW - 1.0, TY + HW, tz + 18.0), (TX + HW - 1.0, TX + HW, TY - HW, TY + HW, tz + 16.5),
                               (TX - HW, TX - HW + 1.0, TY - HW, TY + HW, tz + 15.0), (TX - HW, TX + HW, TY - HW, TY - HW + 1.0, tz + 13.5)):
    wt.box(a0, a1, b0, b1, tz + 12.3, ztop, "GB_Stone")                                             # broken crown
    wt.box(a0 + (0.0 if a1 - a0 > 2 else 0.0), a1, b0, b1, tz + 12.3, tz + 13.4, "GB_Stone")        # 1.1 m parapet everywhere
wt.spiral(TX, TY, RSP, tz, tz + 12.0, "GB_Stone", 0.2, 18.0, 180.0, shaft=False)
wt.floor_ring(TX - HW + 1.0, TX + HW - 1.0, TY - HW + 1.0, TY + HW - 1.0, tz + 12.0, (TX - RSP - 0.1, TX + RSP + 0.1, TY - RSP - 0.1, TY + RSP + 0.1))
R("Watchtower top floor (roofless)", TX - HW + 1.0, TX + HW - 1.0, TY - HW + 1.0, TY + HW - 1.0, tz + 12.0, 4.0, "ruin")
for k in range(4):
    wt.box(TX - 4.4 + k * 2.4, TX - 4.0 + k * 2.4, TY - 4.4, TY + 4.4, tz + 12.0, tz + 12.25, "GB_Wood", col=False)   # burnt beams
wt.cyl(TX + 6.5, TY + 6.5, 0.9, gz(TX + 6.5, TY + 6.5) - 0.1, gz(TX + 6.5, TY + 6.5) + 0.25, "GB_Stone", 10, col=False)   # campfire
wt.box(TX - 4.4, TX - 3.0, TY + 3.0, TY + 4.4, tz, tz + 0.5, "GB_Wood", col=False)                    # overturned table

# ====================================================================== 5 North Cemetery (120 x 120, chapel 14 x 22)
cem = G("SM_GB_Site_Cemetery", "Environment/City")
cx_, cy_, cz0 = POI[5]
CX0, CX1, CY0, CY1 = cx_ - 60, cx_ + 60, cy_ - 60, cy_ + 60
road_pts = np.array(RF["castle_road_lower"]["xy"])
for side, (fixed, a0, a1, ax) in {"s": (CX0, CY0, CY1, "y"), "n": (CX1, CY0, CY1, "y"), "w": (CY0, CX0, CX1, "x"), "e": (CY1, CX0, CX1, "x")}.items():
    for u in np.arange(a0, a1, 4.0):
        u1 = min(u + 4.0, a1)
        px_, py_ = ((fixed, (u + u1) / 2) if ax == "y" else ((u + u1) / 2, fixed))
        if road_clear(px_, py_, 1.5) < 0:
            continue                                                                                 # road gates
        zz = min(gz(*((fixed, u) if ax == "y" else (u, fixed))), gz(*((fixed, u1) if ax == "y" else (u1, fixed))))
        if ax == "y":
            cem.box(fixed - 0.3, fixed + 0.3, u, u1, zz - 0.8, zz + 2.2, "GB_Stone")
        else:
            cem.box(u, u1, fixed - 0.3, fixed + 0.3, zz - 0.8, zz + 2.2, "GB_Stone")
occupied = []


def place(w, h, tries=400, margin=3.0, near=None, spread=50):
    for _ in range(tries):
        if near is None:
            x = rng.uniform(CX0 + 4 + w / 2, CX1 - 4 - w / 2); y = rng.uniform(CY0 + 4 + h / 2, CY1 - 4 - h / 2)
        else:
            x = near[0] + rng.uniform(-spread, spread); y = near[1] + rng.uniform(-spread, spread)
        r = (x - w / 2, x + w / 2, y - h / 2, y + h / 2)
        if rect_clear(*r, margin) < 0:
            continue
        if any(not (r[1] + margin < o[0] or r[0] - margin > o[1] or r[3] + margin < o[2] or r[2] - margin > o[3]) for o in occupied):
            continue
        occupied.append(r)
        return r
    raise RuntimeError("no room to place")


r = place(14.0, 22.0, near=(cx_ + 30, cy_), spread=25)
mc = hut(cem, "Mortuary chapel", r[0], r[1], r[2], r[3], "s", h=7.0, t=0.8, mat="GB_Stone", roof="GB_Tile", pitch=55, kind="mortuary_chapel", door_w=3.0)
cem.box(r[0] + 5.0, r[1] - 5.0, r[3] - 3.0, r[3] - 1.2, mc, mc + 1.0, "GB_Stone")                     # bier / altar
for k in range(3):
    r = place(5.0, 7.0)
    hut(cem, f"Family mausoleum {k + 1}", r[0], r[1], r[2], r[3], "w" if k % 2 else "s", h=4.2, t=0.6, mat="GB_Stone", roof="GB_Stone", pitch=35, kind="mausoleum", door_w=1.8)
r = place(6.0, 6.0)
hut(cem, "Ossuary", r[0], r[1], r[2], r[3], "e", h=4.2, t=0.6, mat="GB_Stone", roof="GB_Tile", kind="ossuary", door_w=1.8)
r = place(4.5, 5.0)
hut(cem, "Watchman's hut", r[0], r[1], r[2], r[3], "s", h=4.1, t=0.4, mat="GB_Wood", roof="GB_Roof", kind="hut", door_w=1.8)
for k in range(7):                                                                                   # crooked yews
    r = place(2.0, 2.0, margin=1.0)
    tree(cem, (r[0] + r[1]) / 2, (r[2] + r[3]) / 2, h=8.0, r=2.5)
ng = 0
while ng < 300:
    x, y = rng.uniform(CX0 + 3, CX1 - 3), rng.uniform(CY0 + 3, CY1 - 3)
    if road_clear(x, y, 1.0) < 0 or any(o[0] - 1 < x < o[1] + 1 and o[2] - 1 < y < o[3] + 1 for o in occupied):
        continue
    z = gz(x, y)
    opened = ng % 23 == 0
    cem.box(x - 0.08, x + 0.08, y - 0.35, y + 0.35, z - 0.3, z + 0.9, "GB_Stone", col=False)
    cem.box(x + 0.2, x + 2.0, y - 0.4, y + 0.4, z - (0.4 if opened else 0.0), z + (0.05 if not opened else 0.0), "GB_Ground" if not opened else "GB_Interior", col=False)
    ng += 1

# ====================================================================== 10 gallows hill and crossroads
gal = G("SM_GB_Site_Gallows", "Environment/Props")
gx, gy, _ = POI[10]
zg = gz(gx, gy)
pts3 = [(gx + 2.0 * math.cos(math.radians(a)), gy + 2.0 * math.sin(math.radians(a))) for a in (90, 210, 330)]
for (px_, py_) in pts3:
    gal.box(px_ - 0.2, px_ + 0.2, py_ - 0.2, py_ + 0.2, zg - 1.0, zg + 5.0, "GB_Wood")
for (p, q) in zip(pts3, pts3[1:] + pts3[:1]):
    gal.ramp(p, q, 0.3, zg + 5.0, zg + 5.0, 0.3, "GB_Wood")
gal.ramp(pts3[0], tuple((np.array(pts3[1]) + np.array(pts3[2])) / 2), 0.3, zg + 5.0, zg + 5.0, 0.3, "GB_Wood")   # beam over the centre
gal.box(gx - 0.5, gx + 0.5, gy - 0.4, gy + 0.4, zg + 2.2, zg + 4.0, "GB_Metal", col=False)          # empty gibbet cage
gal.box(gx - 0.04, gx + 0.04, gy - 0.04, gy + 0.04, zg + 3.95, zg + 4.75, "GB_Metal", col=False)    # its chain
cxr = (-420.0, -1060.0)
zx = gz(cxr[0] + 6.0, cxr[1] + 6.0)
gal.box(cxr[0] + 5.8, cxr[0] + 6.2, cxr[1] + 5.8, cxr[1] + 6.2, zx - 0.5, zx + 3.2, "GB_Wood")      # wayside cross
gal.box(cxr[0] + 5.8, cxr[0] + 6.2, cxr[1] + 5.2, cxr[1] + 6.8, zx + 2.2, zx + 2.5, "GB_Wood")
zm_ = gz(cxr[0] - 6.0, cxr[1] + 6.0)
gal.box(cxr[0] - 6.3, cxr[0] - 5.7, cxr[1] + 5.8, cxr[1] + 6.2, zm_ - 0.3, zm_ + 1.0, "GB_Stone")   # milestone

# ====================================================================== 11 abbey ruin (roofless nave 45 x 14, reliquary below the choir)
ab = G("SM_GB_Ruin_Abbey", "Environment/Ruins")
ax_, ay_, az_ = POI[11]
NX0, NX1, NY0, NY1 = ax_ - 7.0, ax_ + 7.0, ay_ - 22.5, ay_ + 22.5
za = round(gz(ax_, ay_) + 0.1, 2)
for (a0, a1, b0, b1) in rect_minus((NX0 - 1.0, NX1 + 1.0, NY0 - 1.0, NY1 + 1.0), [(NX0 + 0.6, NX1 - 0.6, NY0 + 0.6, NY1 - 0.6)]):
    ab.box(a0, a1, b0, b1, min(gz(x, y) for x in (NX0, NX1) for y in (NY0, NY1)) - 1.0, za - 0.4, "GB_Stone")    # plinth ring (void inside)
R("Abbey nave (roofless)", NX0 + 0.6, NX1 - 0.6, NY0 + 0.6, NY1 - 0.6, za, 12.0, "ruin")
hts = [11, 13, 6, 3, 12, 9, 14, 4, 10, 12]
for side, xw in (("s", NX0), ("n", NX1)):
    hs = [hts[(k + (3 if side == "n" else 0)) % 10] for k in range(9)]
    br = [(side == "s" and k in (1, 2)) or (side == "n" and k in (6, 8)) for k in range(9)]   # road breach, collapses (V8 line)
    for k in range(9):
        y0_, y1_ = NY0 + k * 5.0, NY0 + (k + 1) * 5.0
        hh = hs[k]
        if br[k]:
            ab.box(xw - 0.6, xw + 0.6, y0_, y1_, za - 0.3, za + 0.6, "GB_Stone")
            continue
        ab.box(xw - 0.6, xw + 0.6, y0_, y0_ + 1.4, za - 0.3, za + hh, "GB_Stone")                     # pier
        ab.box(xw - 0.6, xw + 0.6, y0_ + 1.4, y1_, za - 0.3, za + 1.2, "GB_Stone")                    # sill
        nxt = 15.0 if k == 8 else (0.0 if br[k + 1] else hs[k + 1])                                 # next pier (east gable)
        if hh > 8 and nxt >= hh:
            ab.box(xw - 0.6, xw + 0.6, y0_ + 1.4, y1_, za + hh - 2.0, za + hh, "GB_Stone")           # standing arch: both springers up
v8 = next(v for v in M["hero_views"] if v["id"] == "V8")
c8 = np.array(v8["camera"][:2], float); d8 = np.array(v8["look_at"][:2], float) - c8; d8 /= np.linalg.norm(d8)
for k in range(4):                                                                                   # arcade piers inside
    for xr in (ax_ - 2.5, ax_ + 2.5):
        yr = NY0 + 9.0 + k * 9.0
        off = np.array([xr, yr]) - c8
        on_v8 = off @ d8 > 0 and abs(off[0] * d8[1] - off[1] * d8[0]) < 2.0                       # pier beside the V8 line:
        ab.cyl(xr, yr, 0.7, za, za + (1.2 if on_v8 else 9.0 if (k + int(xr)) % 2 else 4.0), "GB_Stone", 10)   # a broken stump
ab.wall("x", NY1 - 0.6, NY1 + 0.6, NX0 - 0.6, ax_ + 3.0, za - 0.3, za + 15.0, "GB_Stone",
        holes=[(ax_ - 1.5, ax_ + 1.5, za + 4.0, za + 12.0)])                                       # east gable (choir), empty window
ab.wall("x", NY1 - 0.6, NY1 + 0.6, ax_ + 3.0, NX1 + 0.6, za - 0.3, za + 7.5, "GB_Stone")            # its fallen north half
TWX, TWY = ax_, NY0 - 4.0
ab.box(TWX - 4.0, TWX + 4.0, TWY - 4.0, TWY - 3.0, za - 0.3, za + 9.0, "GB_Stone")                  # tower stump (8 x 8, 9 m)
ab.box(TWX - 4.0, TWX - 3.0, TWY - 4.0, TWY + 3.4, za - 0.3, za + 7.0, "GB_Stone")
ab.box(TWX + 3.0, TWX + 4.0, TWY - 4.0, TWY + 3.4, za - 0.3, za + 8.0, "GB_Stone")
for (a0, a1, b0, b1) in rect_minus((NX0 - 25.0, NX0 - 1.0, NY0 + 4.0, NY0 + 28.0), [(NX0 - 24.0, NX0 - 2.0, NY0 + 5.0, NY0 + 27.0)]):
    if b1 - b0 > 0.3 and a1 - a0 > 0.3:
        for u in np.arange(b0, b1, 6.0) if (b1 - b0) > (a1 - a0) else [b0]:
            for v in np.arange(a0, a1, 6.0) if (a1 - a0) >= (b1 - b0) else [a0]:
                aa1 = min(v + 6.0, a1) if (a1 - a0) >= (b1 - b0) else a1
                bb1 = min(u + 6.0, b1) if (b1 - b0) > (a1 - a0) else b1
                hh = 3.0 if rng.random() > 0.3 else 1.0
                ab.box(v, aa1, u, bb1, gz(v, u) - 0.5, gz(v, u) + hh, "GB_Stone")                     # cloister walls (broken)
for k in range(40):                                                                                  # overgrown graveyard
    x, y = NX1 + rng.uniform(4, 22), ay_ + rng.uniform(-20, 20)
    z = gz(x, y)
    ab.box(x - 0.08, x + 0.08, y - 0.3, y + 0.3, z - 0.3, z + 0.7, "GB_Stone", col=False)
# hidden reliquary under the choir: trapdoor (movable slab) and stair down
RQ0, RQ1, RQY0, RQY1 = ax_ - 3.0, ax_ + 3.0, NY1 - 12.0, NY1 - 2.0
rel = R("Abbey hidden reliquary", RQ0, RQ1, RQY0, RQY1, za - 5.0, 4.0, "ruin")
ab.room(rel, mat_wall="GB_Stone", t=0.8, ceil=False)
ab.stairs((ax_, RQY0 + 0.6), (0, 1), 2.5, za - 5.0, za, "GB_Stone", 0.2, 0.27)                      # rises east to the trapdoor
for (a0, a1, b0, b1) in rect_minus((NX0 - 0.8, NX1 + 0.8, NY0 - 0.8, NY1 + 0.8), [(ax_ - 1.3, ax_ + 1.3, RQY0 + 0.5, RQY0 + 7.4)]):
    ab.box(a0, a1, b0, b1, za - 0.35, za, "GB_Floor")                                                 # nave floor over the void
ab.box(ax_ + 1.6, ax_ + 2.6, RQY1 - 3.0, RQY1 - 1.8, za - 5.0, za - 4.0, "GB_Detail")                # reliquary chest
trap = G("SM_GB_Ruin_AbbeyTrapdoor", "Environment/Ruins")
trap.box(ax_ - 1.3, ax_ + 1.3, RQY0 + 4.6, RQY0 + 7.4, za - 0.05, za + 0.05, "GB_Wood")
MOVABLE.append(dict(name=trap.name, pivot=[ax_ - 1.3, RQY0 + 4.6, za]))
for xk in (ax_ - 1.6, ax_ + 1.3):                                                                    # low kerbs along the open part
    ab.box(xk, xk + 0.3, RQY0 + 0.5, RQY0 + 4.6, za - 0.35, za + 0.9, "GB_Stone")
ab.box(ax_ - 1.6, ax_ + 1.6, RQY0 + 0.2, RQY0 + 0.5, za - 0.35, za + 0.9, "GB_Stone")
VOIDS.append([NX0 + 0.6, NX1 - 0.6, NY0 + 0.6, NY1 - 0.6, za - 6.5])

# ====================================================================== 12 woodcutters' camp
wc = G("SM_GB_Site_WoodcuttersCamp", "Environment/Props")
occupied = []
CX0, CX1, CY0, CY1 = POI[12][0] - 40, POI[12][0] + 40, POI[12][1] - 40, POI[12][1] + 40
for k in range(2):
    r = place(6.0, 8.0, near=POI[12][:2], spread=30, margin=4.0)
    hut(wc, f"Log cabin {k + 1}", r[0], r[1], r[2], r[3], "s" if k == 0 else "n", h=4.2, t=0.5, mat="GB_Wood", roof="GB_Roof", kind="cabin")
r = place(3.0, 7.0, near=POI[12][:2], spread=30)
z = gz((r[0] + r[1]) / 2, (r[2] + r[3]) / 2)
for (a0, a1, b0, b1) in ((r[0], r[1], r[2], r[2] + 0.3), (r[0], r[1], r[3] - 0.3, r[3]), (r[0], r[0] + 0.3, r[2], r[3]), (r[1] - 0.3, r[1], r[2], r[3])):
    wc.box(a0, a1, b0, b1, z - 0.2, z + 0.4, "GB_Wood")                                                # saw pit frame
wc.box(r[0] + 0.3, r[1] - 0.3, r[2] + 0.3, r[3] - 0.3, z - 0.2, z - 0.1, "GB_Ground", col=False)
for k in range(3):
    r = place(3.0, 6.0, near=POI[12][:2], spread=35)
    z = gz((r[0] + r[1]) / 2, (r[2] + r[3]) / 2)
    wc.box(r[0], r[1], r[2], r[3], z - 0.3, z + 1.4, "GB_Wood")                                       # log stacks
r = place(5.0, 5.0, near=POI[12][:2], spread=35)
z = gz((r[0] + r[1]) / 2, (r[2] + r[3]) / 2)
wc.cone((r[0] + r[1]) / 2, (r[2] + r[3]) / 2, 2.4, z - 0.3, z + 2.8, "GB_Ground", 12)               # charcoal kiln

# ====================================================================== 13 stone circle
sc = G("SM_GB_Site_StoneCircle", "Environment/Nature")
sx, sy, _ = POI[13]
for k in range(9):
    a = 2 * math.pi * k / 9 + 0.2
    px_, py_ = sx + 10.0 * math.cos(a), sy + 10.0 * math.sin(a)
    z = gz(px_, py_)
    obox(sc, (px_, py_), (math.cos(a + math.pi / 2), math.sin(a + math.pi / 2)), 0.65, 0.4, z - 0.8, z + 3.0 + 0.6 * (k % 3), "GB_Stone")
z = gz(sx, sy)
sc.box(sx - 1.5, sx + 1.5, sy - 0.8, sy + 0.8, z - 0.5, z + 0.9, "GB_Stone")                         # altar stone

# ====================================================================== 14 river falls: dry cave behind the water (from the bank)
fa = G("SM_GB_Site_FallsCave", "Environment/Nature")
fxy = M["water"]["falls"]["xy"]
FX = fxy[0] + 1.5                                                                                  # cliff face under the lip
CZ = M["water"]["falls"]["base_z"] + 2.0                                                          # dry, above the pool
cave = R("Cave behind the falls", FX, FX + 14.0, fxy[1] - 3.0, fxy[1] + 3.0, CZ, 4.5, "cave")
fa.box(FX - 0.5, FX + 14.5, fxy[1] - 3.5, fxy[1] + 3.5, CZ - 1.5, CZ, "GB_Stone")                    # floor
for y0_, y1_ in ((fxy[1] - 5.5, fxy[1] - 3.0), (fxy[1] + 3.0, fxy[1] + 5.5)):
    fa.box(FX, FX + 16.0, y0_, y1_, CZ - 1.5, CZ + 6.0, "GB_Stone")                                  # cave walls
fa.box(FX + 14.0, FX + 16.0, fxy[1] - 3.0, fxy[1] + 3.0, CZ - 1.5, CZ + 6.0, "GB_Stone")             # back wall
fa.box(FX, FX + 16.0, fxy[1] - 5.5, fxy[1] + 5.5, CZ + 4.5, M["water"]["falls"]["top_z"], "GB_Stone")   # rock over it
zb0 = gz(FX - 2.5, fxy[1] - 12.0)                                                                 # bank at the foot of the cliff
fa.ramp((FX - 2.5, fxy[1] - 12.0), (FX - 2.5, fxy[1] - 7.0), 3.0, zb0, CZ, 1.0 + abs(zb0 - CZ), "GB_Stone")    # off the bank
fa.box(FX - 4.0, FX + 0.2, fxy[1] - 7.0, fxy[1] + 3.0, CZ - 1.5, CZ, "GB_Stone")                    # ledge over the pool to the mouth
VOID_PATHS.append(dict(pts=[[FX - 0.5, fxy[1], CZ - 1.6], [FX + 15.0, fxy[1], CZ - 1.6]], half=5.0, note="falls cave"))

# ====================================================================== 15 East Faubourg (~50 buildings along the trade road)
fb_g = G("SM_GB_Site_Faubourg", "Environment/City")
fb_i = G("SM_GB_City_Int_FaubourgStables", "Environment/City")
tr = RF["trade_road"]; txy, tz_, ts_ = np.array(tr["xy"]), np.array(tr["z"]), np.array(tr["s"])
FAUB = []
occupied = []
spawn_fb = M["spawn_markers"][[s["id"] for s in M["spawn_markers"]].index("east_faubourg")]["xyz"]
occupied.append((spawn_fb[0] - 8, spawn_fb[0] + 8, spawn_fb[1] - 8, spawn_fb[1] + 8))
CXw, CYw, RAw, RBw = -450, -460, 230, 300
for s0 in np.arange(30.0, 430.0, 1.0):
    if len(FAUB) >= 52:
        break
    p = np.array([np.interp(s0, ts_, txy[:, 0]), np.interp(s0, ts_, txy[:, 1])])
    p2 = np.array([np.interp(s0 + 2, ts_, txy[:, 0]), np.interp(s0 + 2, ts_, txy[:, 1])])
    d = (p2 - p) / np.linalg.norm(p2 - p); nrm = np.array([-d[1], d[0]])
    for side in (-1, 1):
        W = rng.uniform(10, 13); D = rng.uniform(12, 16)
        c = p + nrm * side * (3.0 + 4.0 + D / 2) + d * W / 2
        r = (c[0] - D / 2, c[0] + D / 2, c[1] - W / 2, c[1] + W / 2) if abs(nrm[0]) > abs(nrm[1]) else (c[0] - W / 2, c[0] + W / 2, c[1] - D / 2, c[1] + D / 2)
        if math.hypot((c[0] - CXw) / RAw, (c[1] - CYw) / RBw) < 1.12:
            continue
        if rect_clear(*r, 3.0) < 0:
            continue
        if any(not (r[1] + 3.0 < o[0] or r[0] - 3.0 > o[1] or r[3] + 3.0 < o[2] or r[2] - 3.0 > o[3]) for o in occupied):
            continue
        occupied.append(r)
        front = ("+x" if side < 0 else "-x") if abs(nrm[0]) > abs(nrm[1]) else ("+y" if side < 0 else "-y")
        FAUB.append(dict(rect=[round(v, 2) for v in r], front=front))
kinds = ["inn", "stables", "smithy", "house", "house", "carters", "house", "inn", "house", "smithy"]
FB_INT = None
for k, f in enumerate(FAUB):
    x0, x1, y0, y1 = f["rect"]
    kind = kinds[k % len(kinds)]
    f["kind"] = kind
    if kind == "stables" and FB_INT is None:
        side_door = {"+x": "n", "-x": "s", "+y": "e", "-y": "w"}[f["front"]]
        hut(fb_i, "Faubourg stables", x0, x1, y0, y1, side_door, h=4.6, t=0.5, mat="GB_Timber", roof="GB_Tile", kind="faubourg_stables", door_w=3.4)
        FB_INT = f
        continue
    if kind == "carters":                                                                           # carters' yard: fence + shed
        z = gz((x0 + x1) / 2, (y0 + y1) / 2)
        for (a0, a1, b0, b1) in ((x0, x1, y0, y0 + 0.15), (x0, x1, y1 - 0.15, y1)):
            fb_g.box(a0, a1, b0, b1, z - 0.3, z + 1.2, "GB_Wood")
        fb_g.box(x0, x0 + 4.0, y0, y1, z, z + 3.0, "GB_Wood")
        continue
    closed_house(fb_g, x0, x1, y0, y1, f["front"], storeys=2 if kind != "inn" else 3, upper="GB_Timber" if k % 2 else "GB_Plaster", seed=k)
for k in range(6):                                                                                  # market stalls by the gate
    s0 = 18.0 + k * 6.0
    p = np.array([np.interp(s0, ts_, txy[:, 0]), np.interp(s0, ts_, txy[:, 1])])
    q = p + np.array([7.0 if k % 2 else -7.0, 0.0])
    if rect_clear(q[0] - 1.5, q[0] + 1.5, q[1] - 1.0, q[1] + 1.0, 1.0) < 0:
        continue
    z = gz(*q)
    fb_g.box(q[0] - 1.5, q[0] + 1.5, q[1] - 1.0, q[1] + 1.0, z, z + 0.9, "GB_Wood")
    fb_g.gable(q[0] - 1.8, q[0] + 1.8, q[1] - 1.4, q[1] + 1.4, z + 2.4, z + 3.0, "GB_Roof", "x", col=False)

# ====================================================================== 16 watermills + tannery; docks + warehouses
mill = G("SM_GB_Site_Watermills", "Environment/City")
mill_i = G("SM_GB_City_Int_Watermill", "Environment/City")
mx, my, _ = POI[16]
riv = np.array(M["water"]["river"]["points_x_y_bedz_halfwidth"])


def river_at(y):
    """Centre x, bed z and half-width of the river where it runs along Y (south of the city)."""
    seg = riv[(riv[:, 1] > -700) & (riv[:, 1] < 200)]
    o = np.argsort(seg[:, 1])
    return tuple(float(np.interp(y, seg[o, 1], seg[o, k])) for k in (0, 2, 3))


rcx, rbz, rhw = river_at(my)
EDGE = rcx + rhw                                                                                      # north bank edge
for k, yy in enumerate((my - 16.0, my + 14.0)):
    x0, x1, y0, y1 = EDGE + 2.0, EDGE + 15.0, yy - 7.0, yy + 7.0
    zp = round(max(gz(x, y) for x in (x0, x1) for y in (y0, y1)) + 0.2, 2)
    if k == 0:
        hut(mill_i, "Watermill", x0, x1, y0, y1, "n", h=4.8, t=0.6, mat="GB_Stone", roof="GB_Tile", kind="watermill", door_w=2.4, z=zp)
        mill_i.box((x0 + x1) / 2 - 1.5, (x0 + x1) / 2 + 1.5, yy - 1.5, yy + 1.5, zp, zp + 1.0, "GB_Stone")   # millstones
    else:
        closed_house(mill, x0, x1, y0, y1, "+x", storeys=2, upper="GB_Timber")
    mill.wheel((EDGE + 0.6, yy, zp + 0.7), (1, 0), max(2.0, zp + 0.4 - rbz), 0.3, "GB_Wood", col=False)   # undershot wheel on the axle, rim in the stream
    mill.box(EDGE + 0.3, EDGE + 2.0, yy - 0.3, yy + 0.3, zp + 0.4, zp + 1.0, "GB_Wood", col=False)    # axle
MOVABLE.append(dict(name="SM_GB_Site_Watermills (wheels)", note="the wheel panels at the river margin; rotate them in a Blueprint"))
mx = EDGE + 8.0
for k in range(6):                                                                                  # tannery pits + racks downstream
    px_, py_ = mx + 2.0 + (k % 3) * 4.0, my + 34.0 + (k // 3) * 4.0
    z = gz(px_, py_)
    mill.box(px_ - 1.5, px_ + 1.5, py_ - 1.5, py_ + 1.5, z - 0.2, z + 0.6, "GB_Stone")
    mill.box(px_ - 1.2, px_ + 1.2, py_ - 1.2, py_ + 1.2, z + 0.3, z + 0.55, "GB_Ground", col=False)
for k in range(3):
    px_, py_ = mx + 14.0, my + 30.0 + k * 5.0
    z = gz(px_, py_)
    for dy_ in (-1.8, 1.8):
        mill.box(px_ - 0.1, px_ + 0.1, py_ + dy_ - 0.1, py_ + dy_ + 0.1, z - 0.3, z + 2.4, "GB_Wood")
    mill.box(px_ - 0.05, px_ + 0.05, py_ - 1.8, py_ + 1.8, z + 2.2, z + 2.3, "GB_Wood")
    mill.box(px_ - 0.02, px_ + 0.02, py_ - 1.6, py_ + 1.6, z + 0.8, z + 2.2, "GB_Detail", col=False)  # hides drying
dock = G("SM_GB_Site_Docks", "Environment/City")
dock_i = G("SM_GB_City_Int_DockWarehouse", "Environment/City")
dl = RF["dock_lane"]; dxy = np.array(dl["xy"]); dz_ = np.array(dl["z"])
de = dxy[-1]; dze = dz_[-1]
for k, (yy0, yy1) in enumerate(((-520.0, -490.0), (-485.0, -455.0), (-450.0, -420.0))):
    x0 = river_at((yy0 + yy1) / 2)[0] + river_at((yy0 + yy1) / 2)[2] + 6.0
    x1 = x0 + 15.0
    if k == 1:
        hut(dock_i, "Dock warehouse", x0, x1, yy0, yy1, "n", h=6.0, t=0.6, mat="GB_Timber", roof="GB_Tile", kind="dock_warehouse", door_w=4.0)
    else:
        closed_house(dock, x0, x1, yy0, yy1, "+x", storeys=2, upper="GB_Timber", seed=k)
for yy in np.arange(-525.0, -415.0, 5.0):                                                            # quay along the bank
    ex = river_at(yy + 2.5)[0] + river_at(yy + 2.5)[2]
    qz = max(gz(ex + 1.5, yy + 2.5), river_at(yy)[1] + 3.2)
    dock.box(ex - 0.5, ex + 3.0, yy, yy + 5.0, river_at(yy)[1] - 1.0, qz, "GB_Stone")
    if int(yy) % 15 == 0:
        dock.box(ex - 5.0, ex - 0.5, yy + 1.2, yy + 3.8, qz - 0.4, qz - 0.1, "GB_Wood")               # jetties
        for dx_ in (-4.5, -2.5):
            dock.cyl(ex + dx_, yy + 1.4, 0.15, river_at(yy)[1] - 1.0, qz - 0.4, "GB_Wood", 6)

# ====================================================================== 17 farming hamlet (12 farmsteads, wooden church)
ham = G("SM_GB_Site_Hamlet", "Environment/City")
ham_c = G("SM_GB_Site_HamletChurch", "Environment/City")
hx, hy, _ = POI[17]
occupied = []
sp_h = M["spawn_markers"][[s["id"] for s in M["spawn_markers"]].index("hamlet")]["xyz"]
occupied.append((sp_h[0] - 8, sp_h[0] + 8, sp_h[1] - 8, sp_h[1] + 8))
CX0, CX1, CY0, CY1 = hx - 95, hx + 95, hy - 95, hy + 95
r = place(10.0, 18.0, near=(hx + 25, hy - 20), spread=20, margin=4.0)
zc = hut(ham_c, "Hamlet wooden church", r[0], r[1], r[2], r[3], "w", h=6.0, t=0.4, mat="GB_Wood", roof="GB_Roof", pitch=60, kind="church_wood", door_w=2.4)
ham_c.box(r[0] + 2.0, r[1] - 2.0, r[2] - 0.6, r[2] - 0.4, zc, zc + 3.0, "GB_Wood", col=False)       # door barred from inside (bar)
tcx, tcy = (r[0] + r[1]) / 2, r[2] + 2.5
ham_c.box(tcx - 2.0, tcx + 2.0, tcy - 2.0, tcy + 2.0, zc + 6.3, zc + 12.0, "GB_Wood")
ham_c.cone(tcx, tcy, 2.6, zc + 12.0, zc + 26.0, "GB_Roof", 8)                                         # tall shingled spire
for k in range(8):                                                                                    # row of fresh graves
    gx_, gy_ = r[1] + 4.0, r[2] + 2.0 + k * 2.0
    zz = gz(gx_, gy_)
    ham_c.box(gx_ - 0.9, gx_ + 0.9, gy_ - 0.4, gy_ + 0.4, zz, zz + 0.35, "GB_Ground", col=False)
    ham_c.box(gx_ + 0.9, gx_ + 1.0, gy_ - 0.3, gy_ + 0.3, zz, zz + 1.0, "GB_Wood", col=False)
FARMS = []
for k in range(12):
    r = place(22.0, 20.0, margin=3.5)
    x0, x1, y0, y1 = r
    burnt = k == 5
    closed_house(ham, x0, x0 + 9.0, y0, y0 + 12.0, "+x", storeys=1 if burnt else 2, upper="GB_Timber", seed=k) if not burnt else \
        ham.box(x0, x0 + 9.0, y0, y0 + 12.0, gz(x0, y0) - 0.5, gz(x0, y0) + 1.6, "GB_Interior")       # burnt farm: charred stumps
    zb = gz(x1 - 5.0, y1 - 6.0)
    ham.box(x1 - 10.0, x1, y1 - 12.0, y1, zb - 0.5, zb + 5.0, "GB_Wood")                               # barn
    ham.gable(x1 - 10.0, x1, y1 - 12.0, y1, zb + 5.0, zb + 10.0, "GB_Roof", "x")
    for (a0, a1, b0, b1) in ((x0, x1, y0 - 0.1, y0 + 0.05), (x0, x1, y1 - 0.05, y1 + 0.1)):
        ham.box(a0, a1, b0, b1, gz(a0, b0) - 0.2, gz(a0, b0) + 1.1, "GB_Wood", col=False)             # fences
    FARMS.append(dict(rect=[round(v, 1) for v in r], burnt=burnt))
r = place(3.0, 3.0)
ham.cyl((r[0] + r[1]) / 2, (r[2] + r[3]) / 2, 1.2, gz((r[0] + r[1]) / 2, (r[2] + r[3]) / 2) - 0.3, gz((r[0] + r[1]) / 2, (r[2] + r[3]) / 2) + 0.9, "GB_Stone", 12)
r = place(12.0, 12.0)
z = gz((r[0] + r[1]) / 2, (r[2] + r[3]) / 2)
ham.cyl((r[0] + r[1]) / 2, (r[2] + r[3]) / 2, 6.0, z - 0.4, z + 0.15, "GB_Ground", 16)               # threshing floor

# ====================================================================== 18 quarry: crane, carts, workers' hut
qy = G("SM_GB_Site_Quarry", "Environment/Props")
qx_, qy_, qz_ = POI[18]
cr = (qx_ - 10.0, qy_ - 25.0)
z = gz(*cr)
qy.box(cr[0] - 0.4, cr[0] + 0.4, cr[1] - 0.4, cr[1] + 0.4, z - 0.5, z + 12.0, "GB_Wood")              # timber crane mast
qy.ramp((cr[0], cr[1]), (cr[0], cr[1] + 14.0), 0.5, z + 11.0, z + 9.0, 0.5, "GB_Wood")               # jib over the cut
qy.box(cr[0] - 3.0, cr[0] + 3.0, cr[1] - 3.0, cr[1] + 3.0, z - 0.3, z + 0.6, "GB_Wood")              # treadwheel base
qy.wheel((cr[0] + 1.8, cr[1], z + 0.6 + 2.6), (1, 0), 2.6, 0.6, "GB_Wood", col=False)               # treadwheel beside the mast
for k in range(2):
    c = (qx_ - 20.0 + k * 6.0, qy_ - 58.0)
    zz = gz(*c)
    qy.box(c[0] - 1.0, c[0] + 1.0, c[1] - 2.0, c[1] + 2.0, zz + 0.75, zz + 1.45, "GB_Wood")
    for wx in (-1.1, 1.1):
        for wy in (-1.2, 1.2):
            qy.wheel((c[0] + wx, c[1] + wy, zz + 0.6), (1, 0), 0.6, 0.06, "GB_Wood", col=False)
x0q, y0q = max(((qx_ + ox, qy_ + oy) for ox in np.arange(-70, -30, 4.0) for oy in np.arange(-70, -20, 4.0)),
               key=lambda o: min(rect_clear(o[0], o[0] + 6.0, o[1], o[1] + 5.0, 2.0), 3.0) - 0.02 * abs(gz(o[0], o[1]) - gz(o[0] + 6, o[1] + 5)))
hut(qy, "Quarry workers' hut", x0q, x0q + 6.0, y0q, y0q + 5.0, "n", h=4.2, t=0.4, mat="GB_Wood", roof="GB_Roof", kind="hut")

# ====================================================================== 19 east pass border post; 20 west pass rockfall
bp = G("SM_GB_Site_BorderPost", "Environment/Props")
bx_, by_, bz_ = POI[19]
tr_end = txy[-1]
pal_y = by_ + 22.0
zr = gz(bx_, pal_y)
for xx in np.arange(bx_ - 70.0, bx_ + 70.0, 0.9):
    if abs(xx - float(np.interp(pal_y, txy[:, 1], txy[:, 0]))) < 3.5:
        continue
    zz = gz(xx, pal_y)
    bp.cyl(xx, pal_y, 0.22, zz - 1.0, zz + 4.5 + 0.4 * ((int(xx * 3) % 3)), "GB_Wood", 6)
rcx = float(np.interp(pal_y, txy[:, 1], txy[:, 0]))
gate = G("SM_GB_Site_BorderGate", "Environment/Props")
gate.box(rcx - 3.5, rcx + 3.5, pal_y - 0.15, pal_y + 0.15, zr, zr + 4.2, "GB_Wood")                   # closed gate (static)
bp.box(rcx - 0.2, rcx + 0.2, pal_y - 12.0, pal_y - 11.6, zr + 0.9, zr + 1.1, "GB_Wood")
bp.box(rcx - 3.6, rcx - 3.2, pal_y - 12.0, pal_y - 11.6, zr - 0.5, zr + 1.2, "GB_Wood")               # toll barrier post
hut(bp, "Border guard hut", rcx + 6.0, rcx + 11.0, pal_y - 14.0, pal_y - 8.0, "s", h=4.1, t=0.4, mat="GB_Wood", roof="GB_Roof", kind="hut")
BLOCKERS.append(dict(name="BV_EastPass", centre=[bx_, pal_y + 40.0, zr + 50.0], extent=[150.0, 40.0, 120.0], note="behind the palisade"))
wp = G("SM_GB_Site_WestPassRockfall", "Environment/Nature")
wx_, wy_, wz_ = POI[20]
for k in range(16):
    px_, py_ = wx_ + rng.uniform(-14, 14), wy_ + rng.uniform(-6, 10)
    z = gz(px_, py_)
    s = rng.uniform(2.0, 5.0)
    a = rng.uniform(0, math.pi)
    obox(wp, (px_, py_), (math.cos(a), math.sin(a)), s, s * rng.uniform(0.6, 1.0), z - 1.0, z + s * rng.uniform(0.9, 1.6), "GB_Rock")
cc = (wx_ + 10.0, wy_ + 18.0); z = gz(*cc)
wp.box(cc[0] - 1.0, cc[0] + 1.0, cc[1] - 2.0, cc[1] + 2.0, z + 0.75, z + 1.45, "GB_Wood")               # abandoned cart
for wx in (-1.1, 1.1):                                                                              # four wheels
    for wy in (-1.2, 1.2):
        wp.wheel((cc[0] + wx, cc[1] + wy, z + 0.6), (1, 0), 0.6, 0.06, "GB_Wood", col=False)
wp.box(cc[0] + 2.0, cc[0] + 3.0, cc[1] - 1.2, cc[1] + 1.2, z, z + 0.8, "GB_Detail", col=False)        # dead horse
BLOCKERS.append(dict(name="BV_WestPass", centre=[wx_, wy_ - 50.0, wz_ + 40.0], extent=[120.0, 40.0, 100.0], note="behind the rockfall"))

# ====================================================================== 21 the fen: plank walkways, hut on stilts, dead birches
fen = G("SM_GB_Site_Fen", "Environment/Nature")
fen_i = G("SM_GB_City_Int_FenHut", "Environment/Nature")
fp = np.array(RF["fen_path"]["xy"])[-1]
path = [fp, fp + np.array([-40.0, -30.0]), fp + np.array([-90.0, -10.0]), fp + np.array([-130.0, 40.0]), fp + np.array([-160.0, 10.0])]
WZ = max(3.6, max(gz(*(a + (b - a) * t)) for a, b in zip(path[:-1], path[1:]) for t in np.linspace(0, 1, 20)) + 0.4)   # deck above pools
for a, b in zip(path[:-1], path[1:]):
    fen.ramp(tuple(a), tuple(b), 1.8, WZ, WZ, 0.15, "GB_Wood")
    L = np.linalg.norm(b - a); d = (b - a) / L
    for s_ in np.arange(0, L, 3.0):
        p = a + d * s_
        fen.cyl(p[0], p[1], 0.12, gz(*p) - 1.0, WZ - 0.15, "GB_Wood", 6)
z0f = gz(*fp)
fen.ramp(tuple(fp + (fp - path[1]) / np.linalg.norm(fp - path[1]) * max(0.5, (z0f - WZ) / 0.25 if z0f > WZ else 0.5)), tuple(fp), 1.8, z0f, WZ, 0.4, "GB_Wood")
hc = path[3]
hut(fen_i, "Fen hut on stilts", hc[0] - 3.0, hc[0] + 3.0, hc[1] + 1.0, hc[1] + 7.0, "w", h=4.1, t=0.3, mat="GB_Wood", roof="GB_Roof",
    kind="fen_hut", z=WZ + 0.0, plinth_=False)
for dx_ in (-2.8, 2.8):
    for dy_ in (1.2, 6.8):
        fen_i.cyl(hc[0] + dx_, hc[1] + dy_, 0.18, gz(hc[0] + dx_, hc[1] + dy_) - 1.0, WZ - 0.3, "GB_Wood", 6)
for k in range(25):
    px_, py_ = fp[0] + rng.uniform(-200, 60), fp[1] + rng.uniform(-120, 120)
    tree(fen, px_, py_, h=rng.uniform(5, 9), dead=True)
SIGNS += [dict(name=f"wisp_{k}", xyz=[float(fp[0] + rng.uniform(-150, 0)), float(fp[1] + rng.uniform(-80, 80)), WZ + 1.5], kind="drifting light") for k in range(8)]

# ====================================================================== 22 river gorge: blocking volume behind the rapids
gx_, gy_, gzz = POI[22]
BLOCKERS.append(dict(name="BV_Gorge", centre=[gx_ - 120.0, gy_ + 120.0, gzz + 60.0], extent=[100.0, 100.0, 120.0], note="beyond the rapids"))
for nm, c, e in (("BV_North", [1506.0, 0.0, 300.0], [6.0, 1512.0, 400.0]), ("BV_South", [-1506.0, 0.0, 200.0], [6.0, 1512.0, 400.0]),
                 ("BV_East", [0.0, 1506.0, 250.0], [1512.0, 6.0, 400.0]), ("BV_West", [0.0, -1506.0, 250.0], [1512.0, 6.0, 400.0])):
    BLOCKERS.append(dict(name=nm, centre=c, extent=e, note="map edge, behind ridge / hills / passes"))

# ====================================================================== 9 West Bridge (five arches, 60 m, shrine mid-span)
wb = G("SM_GB_Site_WestBridge", "Environment/City")
wr = RF["west_road"]; wxy, wzz, wss = np.array(wr["xy"]), np.array(wr["z"]), np.array(wr["s"])
YA, YB = -825.0, -885.0
xa_ = float(np.interp(-YA, -wxy[:, 1], wxy[:, 0])); xb_ = float(np.interp(-YB, -wxy[:, 1], wxy[:, 0]))
za_ = float(np.interp(-YA, -wxy[:, 1], wzz)); zb_ = float(np.interp(-YB, -wxy[:, 1], wzz))
wb.ramp((xa_, YA), (xb_, YB), 5.0, za_, zb_, 1.6, "GB_Stone")                                        # deck
for s_ in (-1, 1):
    wb.ramp((xa_ + s_ * 2.75, YA), (xb_ + s_ * 2.75, YB), 0.5, za_ + 1.1, zb_ + 1.1, 2.7, "GB_Stone")  # 1.1 m parapets
for k in range(1, 5):
    yp = YA + (YB - YA) * k / 5
    xp = xa_ + (xb_ - xa_) * k / 5; zt = za_ + (zb_ - za_) * k / 5 - 1.6
    wb.box(xp - 3.5, xp + 3.5, yp - 1.5, yp + 1.5, gz(xp, yp) - 2.0, zt, "GB_Stone")                  # piers
    wb.box(xp - 3.8, xp + 3.8, yp - 2.2, yp + 2.2, gz(xp, yp) - 2.0, gz(xp, yp) + 1.5, "GB_Stone")   # cutwaters
for k in range(5):
    y0_ = YA + (YB - YA) * k / 5 - (1.5 if k else 0) * np.sign(YB - YA)
    y1_ = YA + (YB - YA) * (k + 1) / 5 + (1.5 if k < 4 else 0) * np.sign(YB - YA)
    xm = xa_ + (xb_ - xa_) * (k + 0.5) / 5; zm = za_ + (zb_ - za_) * (k + 0.5) / 5
    wb.box(xm - 2.6, xm + 2.6, min(y0_, y1_), max(y0_, y1_), zm - 2.6, zm - 1.6, "GB_Stone")         # arch rings (spandrels)
for s_ in (-1, 1):                                                                                   # abutments
    yy = YA if s_ < 0 else YB; xx = xa_ if s_ < 0 else xb_; zz = za_ if s_ < 0 else zb_
    wb.box(xx - 3.5, xx + 3.5, min(yy, yy - 4.0 * s_), max(yy, yy - 4.0 * s_), gz(xx, yy) - 3.0, zz, "GB_Stone")
ym = (YA + YB) / 2; xm = (xa_ + xb_) / 2; zm = (za_ + zb_) / 2
wb.box(xm - 3.0 - 1.2, xm - 3.0, ym - 1.2, ym + 1.2, zm, zm + 2.6, "GB_Stone")                       # shrine niche on the parapet
wb.pyramid(xm - 4.4, xm - 2.8, ym - 1.4, ym + 1.4, zm + 2.6, zm + 3.6, "GB_Tile")
wb.box(xm - 3.6, xm - 3.2, ym - 0.3, ym + 0.3, zm + 1.1, zm + 2.0, "GB_Detail", col=False)

# ====================================================================== signposts at every crossroads
sgn = G("SM_GB_Props_Signposts", "Environment/Props")
ends = []
for rid, r in RF.items():
    if rid.startswith("_") or r["type"] in ("bridge",):
        continue
    for p in (r["xy"][0], r["xy"][-1]):
        others = [o for o, rr in RF.items() if not o.startswith("_") and o != rid and
                  np.min(np.hypot(*(np.array(rr["xy"]) - np.array(p)).T)) < 8]
        if others and not any(np.hypot(p[0] - e[0], p[1] - e[1]) < 15 for e in ends):
            ends.append(p)
for p in ends:
    best = None
    for a in np.radians(np.arange(0, 360, 30)):
        q = (p[0] + 6.0 * math.cos(a), p[1] + 6.0 * math.sin(a))
        if road_clear(*q, 0.5) > 0:
            best = q
            break
    if best is None:
        continue
    z = gz(*best)
    sgn.box(best[0] - 0.12, best[0] + 0.12, best[1] - 0.12, best[1] + 0.12, z - 0.6, z + 2.8, "GB_Wood")
    for k, a in enumerate((0.0, 2.1, 4.2)):
        obox(sgn, (best[0] + 0.5 * math.cos(a), best[1] + 0.5 * math.sin(a)), (math.cos(a), math.sin(a)), 0.55, 0.04, z + 2.0 - k * 0.35, z + 2.25 - k * 0.35, "GB_Wood", col=False)
    SIGNS.append(dict(name="signpost", xyz=[round(best[0], 1), round(best[1], 1), round(z, 1)], kind="castle/church/mill pictograms"))

# ====================================================================== backdrop: low-poly mountain ring beyond the playable square
bd = G("SM_GB_Backdrop_Mountains", "Environment/Landscape")
NA, NR = 192, 7
radii = np.array([1750.0, 2400.0, 3200.0, 4200.0, 5400.0, 6800.0, 8500.0])
hn = np.random.default_rng(5).normal(size=(NR, NA))
for _ in range(3):                                                                                # smooth along the ring
    hn = (np.roll(hn, 1, 1) + 2 * hn + np.roll(hn, -1, 1)) / 4
hn /= hn.std()
Vb = []
for i, rr in enumerate(radii):
    for k in range(NA):
        a = 2 * math.pi * k / NA
        prof = [0.0, 220.0, 420.0, 640.0, 820.0, 700.0, -300.0][i]
        north = max(math.cos(a), 0.0) ** 1.5
        base = prof * (1.0 + 0.9 * north)                                                         # Carpathians behind the ridge
        h = base * (1 + 0.28 * hn[i, k]) if 0 < i < NR - 1 else prof
        Vb.append((rr * math.cos(a), rr * math.sin(a), max(h, -50)))
Fb = []
for i in range(NR - 1):
    for k in range(NA):
        a0, a1 = i * NA + k, i * NA + (k + 1) % NA
        b0, b1 = (i + 1) * NA + k, (i + 1) * NA + (k + 1) % NA
        Fb.append([a0, a1, b1]); Fb.append([a0, b1, b0])
bd.add(Vb, Fb, "GB_Rock", col=False)

# ====================================================================== outputs
print("ground-snapped pieces", ground_snap(groups, H, sample))
json.dump([g.to_json() for g in groups], open(f"{ROOT}/greybox/sites_groups.json", "w"))
meta = dict(rooms=ROOMS, voids=VOIDS, void_paths=VOID_PATHS, aprons=APRONS, movable=MOVABLE, blockers=BLOCKERS, markers=SIGNS,
            stairs=STAIR_LOG, serpentine_wall_segments=nwall, stakes=nstakes, watchtower_xy=[TX, TY], faubourg_buildings=len(FAUB),
            faubourg=FAUB, farms=FARMS, west_bridge=dict(y=[YA, YB], deck_z=[round(za_, 2), round(zb_, 2)]))
json.dump(meta, open(f"{ROOT}/greybox/sites_meta.json", "w"), indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
print("sites groups", len(groups), "rooms", len(ROOMS), "faubourg", len(FAUB), "stairs", STAIR_LOG, "wall segs", nwall, "stakes", nstakes,
      "signposts", len([s for s in SIGNS if s["name"] == "signpost"]))
