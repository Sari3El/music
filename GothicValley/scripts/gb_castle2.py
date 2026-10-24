# The vampires' castle (model « Castle 2.0 », EldersCrawler) on the crag, replacing the phase-2 greybox castle.
# The model is placed at scale 160 (assets/castle20/castle20_island.blend, centred frame: footprint centred, lowest
# point at z = 0) with its gate facing the Great Bridge; the crag top takes the relief of the hill the model was built on
# (data/castle20_plate.npz); the Great Bridge is re-aimed at the new gate; the gate leaves of the model are cut out and
# replaced by two Movable leaves; interiors are fitted into the model's own halls and towers. World metres, +X north.
# Writes greybox/castle_groups.json + castle_meta.json (same names as the greybox castle, read by the other scripts),
# data/placements_castle.json, greybox/nav_castle.json and the walk-test triangles of the shell (assets/castle20).
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gb_lib import Group, rect_minus
from tlib import sample
from c2cuts import subtract

ROOT = sys.argv[1]
HN = f"{ROOT}/terrain/H_natural_4033.npy"
H = np.load(HN if os.path.exists(HN) else f"{ROOT}/terrain/H_4033.npy")
gz = lambda x, y: float(sample(H, np.atleast_1d(float(x)), np.atleast_1d(float(y)))[0])
T = np.array([719.0, 290.0, 195.4])                  # centred model frame -> world (POI 1 within its 10 m)
SC = 160.0
GATE_CUT = dict(x=[-3.0, 2.4], y=[-48.9, -47.6], z=[6.0, 14.2])   # centred frame
groups, ROOMS, MOVABLE, LIGHTS, PL = [], [], [], [], []


def G(name, folder):
    g = Group(name, folder); groups.append(g)
    return g


def W(x, y, z=0.0):
    return [x + T[0], y + T[1], z + T[2]]


def obox(g, c, t, ht, hn, z0, z1, mat, col=True):
    t = np.array(t, float) / np.linalg.norm(t); n = np.array([-t[1], t[0]]); c = np.array(c, float)
    pts = [c - t * ht - n * hn, c + t * ht - n * hn, c + t * ht + n * hn, c - t * ht + n * hn]
    g.poly_prism([tuple(p) for p in pts], z0, z1, mat, col)


# ---------------------------------------------------------------- the shell
PL.append(dict(mesh="SM_C2_Castle", folder="Environment/Castle", loc=T.round(3).tolist(), yaw=0.0, scale=[1.0, 1.0, 1.0], collision="complex"))
plate = np.load(f"{ROOT}/data/castle20_plate.npz")
pz = lambda x, y: float(plate["plate"][np.argmin(abs(plate["xs"] - x)), np.argmin(abs(plate["ys"] - y))])
GATE = np.array([-0.3, -48.2])                       # outer face of the gate leaves (centred frame)
gate_w = W(*GATE, pz(*GATE))

# ---------------------------------------------------------------- approach: barbican (kept), Great Bridge to the new gate
app = G("SM_GB_Castle_Approach", "Environment/Castle")
app.wall("y", 729.0, 731.0, 74.0, 100.0, 199.0, 213.0, "GB_Stone")
app.wall("y", 753.0, 755.0, 74.0, 100.0, 199.0, 213.0, "GB_Stone")
app.box(731.0, 753.0, 74.0, 100.0, 207.0, 213.0, "GB_Stone")
for xc in (730.0, 754.0):
    app.cyl(xc, 97.0, 5.0, 196.0, 219.0, "GB_Stone", 16); app.cone(xc, 97.0, 5.6, 219.0, 227.0, "GB_Roof", 16)
RIM = np.array([gate_w[0], 193.0])                   # where the deck lands on the crag, in line with the gate
BR0 = np.array([742.0, 80.0]); z0, z1 = 199.1, gz(*RIM) + 0.05
d = RIM - BR0; L = float(np.linalg.norm(d)); u = d / L; nrm = np.array([-u[1], u[0]])
DRAW = 10.0                                         # drawbridge: last 10 m of the deck, hinged on the crag side
B1 = BR0 + u * (L - DRAW); zb1 = z0 + (z1 - z0) * (L - DRAW) / L
app.ramp(BR0, B1, 6.0, z0, zb1, 2.0, "GB_Stone")
for s in (-1, 1):
    app.ramp(BR0 + nrm * s * 3.25, B1 + nrm * s * 3.25, 0.5, z0 + 1.1, zb1 + 1.1, 1.1, "GB_Stone")
PIERS = []
for f in (0.3, 0.47, 0.63, 0.8):
    c = BR0 + u * L * f; zt = z0 + (z1 - z0) * f - 2.0
    zb = min(gz(*(c + u * a + nrm * b)) for a in (-2.5, 2.5) for b in (-3, 3)) - 1.0
    obox(app, c, u, 2.5, 3.0, zb, zt, "GB_Stone")
    PIERS.append(dict(at=c.round(1).tolist(), bottom=round(zb, 1), top=round(zt, 1), height=round(zt - zb, 1)))
app.ramp(RIM - u * 0.5, RIM + u * 4.0, 7.0, z1, z1, 1.5, "GB_Stone")           # abutment on the rim
draw = G("SM_GB_Castle_Drawbridge", "Environment/Castle")
draw.ramp(B1, RIM - u * 0.5, 5.8, zb1, z1, 0.6, "GB_Wood")
MOVABLE.append(dict(name="SM_GB_Castle_Drawbridge", pivot=[round(RIM[0] - u[0] * 0.5, 2), round(RIM[1] - u[1] * 0.5, 2), round(z1, 2)],
                    motion="hinge", note="hinge on the crag side; raised, it closes the castle"))
# forecourt: torches on posts along the way from the bridge to the gate
for k, f in enumerate((0.25, 0.75)):
    for s in (-1, 1):
        p = RIM + (np.array(gate_w[:2]) - RIM) * f + np.array([s * 4.5, 0.0])
        zz = gz(*p)
        app.box(p[0] - 0.15, p[0] + 0.15, p[1] - 0.15, p[1] + 0.15, zz - 0.5, zz + 2.6, "GB_Wood")
        app.box(p[0] - 0.12, p[0] + 0.12, p[1] - 0.12, p[1] + 0.12, zz + 2.6, zz + 2.9, "GB_WinLit", False)
        LIGHTS.append(dict(name=f"castle_forecourt_torch_{k}{'ab'[s > 0]}", xyz=[round(p[0], 2), round(p[1], 2), round(zz + 3.0, 2)],
                           lumens=900, radius=10, color=[1.0, 0.55, 0.25], shadows=False))

# ---------------------------------------------------------------- gate leaves (the model's are cut out): open inward
gl = G("SM_GB_Castle_GateLeafW", "Environment/Castle"); gr = G("SM_GB_Castle_GateLeafE", "Environment/Castle")
gz0 = gate_w[2]
for g_, xh, sgn in ((gl, -3.0, 1), (gr, 2.4, -1)):
    xa, xb = sorted((xh, xh + sgn * 0.18))
    g_.box(xa + T[0], xb + T[0], GATE[1] + T[1], GATE[1] + T[1] + 2.75, gz0, gz0 + 6.8, "FC_WoodPlanks")
    MOVABLE.append(dict(name=g_.name, pivot=[round(xh + T[0], 2), round(GATE[1] + T[1], 2), round(gz0, 2)], motion="hinge",
                        note="gate leaf open against the passage wall; swings 90 deg to close the gate"))
LIGHTS.append(dict(name="castle_gate_passage", xyz=W(-0.3, -40.0, pz(-0.3, -40.0) + 4.5), lumens=1500, radius=14, color=[1.0, 0.6, 0.3], shadows=True))

# ---------------------------------------------------------------- rooms (centred model frame; see data/castle20_rooms.json)
CUTS = [dict(GATE_CUT, what="gate leaves")]           # model faces removed (centre inside the box, optional normal test)
gR = G("SM_GB_Castle_Rooms", "Environment/Castle")
gF = G("SM_GB_Castle_Furniture", "Environment/Castle")
CORE = {"Great Hall": 1, "Throne Room": 2, "Banquet Hall": 3, "War Room": 4, "Lord's Study": 5, "Dungeon": 6, "Larder": 7, "Kitchen": 8,
        "Library": 9, "Crypt": 10, "Lord's Apartments": 11, "Chapel": 12}


def Wb(x0, x1, y0, y1):
    return x0 + T[0], x1 + T[0], y0 + T[1], y1 + T[1]


def room(name, x0, x1, y0, y1, fz, h, **kw):
    a_, b_, c_, d_ = Wb(x0, x1, y0, y1)
    r = dict(name=name, x0=round(a_, 2), x1=round(b_, 2), y0=round(c_, 2), y1=round(d_, 2), z0=round(fz + T[2], 2),
             z1=round(fz + T[2] + h, 2), interior="castle", **kw)
    if name in CORE:
        r["core_id"] = CORE[name]
    ROOMS.append(r)


def light(name, x, y, z, lm=2500, rad=12, sh=False, col=(1.0, 0.68, 0.4)):
    LIGHTS.append(dict(name=name, xyz=W(x, y, z), lumens=lm, radius=rad, color=list(col), shadows=sh))


def kit(key, x, y, z, yaw=0.0, s=1.0):
    PL.append(dict(mesh=key.replace("PF_", "SM_"), folder="Props/LibraryKit", loc=[round(v, 3) for v in W(x, y, z)], yaw=yaw,
                   scale=[s, s, s] if np.isscalar(s) else list(s)))


def kitbox(key, x, y, z, yaw=0.0, s=1.0):
    """Kit piece + its bounding box as collision."""
    kit(key, x, y, z, yaw, s)
    k = KIT[key]; R_ = np.array([[math.cos(math.radians(yaw)), -math.sin(math.radians(yaw))], [math.sin(math.radians(yaw)), math.cos(math.radians(yaw))]])
    lo, hi = np.array(k["lo"]) * s, np.array(k["hi"]) * s
    pts = [tuple(R_ @ p + [x + T[0], y + T[1]]) for p in ([lo[0], lo[1]], [hi[0], lo[1]], [hi[0], hi[1]], [lo[0], hi[1]])]
    gF.poly_prism(pts, z + T[2] + lo[2], z + T[2] + hi[2], "GB_Stone", "only")


def B(g, x0, x1, y0, y1, z0, z1, mat, col=True):
    a_, b_, c_, d_ = Wb(x0, x1, y0, y1)
    g.box(a_, b_, c_, d_, z0 + T[2], z1 + T[2], mat, col)


def door_cut(x0, x1, y0, y1, fz, h=2.9, what="door"):
    CUTS.append(dict(x=[x0, x1], y=[y0, y1], z=[fz + 0.04, fz + h], what=what))


def table(x, y, fz, L_, axis, w=1.2, seats=True):
    """Long trestle table with benches (oak), along `axis` ('x' or 'y')."""
    if axis == "y":
        B(gF, x - w / 2, x + w / 2, y - L_ / 2, y + L_ / 2, fz + 0.74, fz + 0.82, "LB_GlossyWood")
        for yy in np.linspace(y - L_ / 2 + 0.4, y + L_ / 2 - 0.4, max(2, int(L_ / 3) + 1)):
            B(gF, x - w / 2 + 0.1, x + w / 2 - 0.1, yy - 0.08, yy + 0.08, fz, fz + 0.74, "LB_GlossyWood", False)
        if seats:
            for s_ in (-1, 1):
                B(gF, x + s_ * (w / 2 + 0.35) - 0.18, x + s_ * (w / 2 + 0.35) + 0.18, y - L_ / 2 + 0.2, y + L_ / 2 - 0.2, fz, fz + 0.45, "LB_GlossyWood")
        B(gF, x - w / 2 - 0.6, x + w / 2 + 0.6, y - L_ / 2, y + L_ / 2, fz, fz + 0.82, "GB_Stone", "only")
    else:
        B(gF, x - L_ / 2, x + L_ / 2, y - w / 2, y + w / 2, fz + 0.74, fz + 0.82, "LB_GlossyWood")
        for xx in np.linspace(x - L_ / 2 + 0.4, x + L_ / 2 - 0.4, max(2, int(L_ / 3) + 1)):
            B(gF, xx - 0.08, xx + 0.08, y - w / 2 + 0.1, y + w / 2 - 0.1, fz, fz + 0.74, "LB_GlossyWood", False)
        if seats:
            for s_ in (-1, 1):
                B(gF, x - L_ / 2 + 0.2, x + L_ / 2 - 0.2, y + s_ * (w / 2 + 0.35) - 0.18, y + s_ * (w / 2 + 0.35) + 0.18, fz, fz + 0.45, "LB_GlossyWood")
        B(gF, x - L_ / 2, x + L_ / 2, y - w / 2 - 0.6, y + w / 2 + 0.6, fz, fz + 0.82, "GB_Stone", "only")


def candelabrum(x, y, fz, h=1.9):
    B(gF, x - 0.25, x + 0.25, y - 0.25, y + 0.25, fz, fz + 0.12, "LB_Metal")
    B(gF, x - 0.05, x + 0.05, y - 0.05, y + 0.05, fz, fz + h, "LB_Metal", False)
    for dx_, dy_ in ((0, 0), (0.22, 0), (-0.22, 0), (0, 0.22), (0, -0.22)):
        B(gF, x + dx_ - 0.03, x + dx_ + 0.03, y + dy_ - 0.03, y + dy_ + 0.03, fz + h, fz + h + 0.22, "LB_CandleLight", False)
    B(gF, x - 0.3, x + 0.3, y - 0.05, y + 0.05, fz + h - 0.05, fz + h, "LB_Metal", False)
    B(gF, x - 0.05, x + 0.05, y - 0.3, y + 0.3, fz + h - 0.05, fz + h, "LB_Metal", False)


KIT = json.load(open(f"{ROOT}/data/kit_library.json"))
RJ = json.load(open(f"{ROOT}/data/castle20_rooms.json"))

# Great Hall: the model's own cross-shaped hall with its pillars (reached from the palace court); long tables down the nave
gh = RJ["Great Hall"]; x0_, x1_, y0_, y1_ = gh["rect"]; fz = gh["floor"]
B(gR, x0_ - 0.5, x1_ + 0.5, y0_, y1_, fz - 0.25, fz + 0.03, "C2_Floor")
for xc in (x0_ + 2.0, x1_ - 2.0):
    table(xc, (y0_ + y1_) / 2, fz + 0.03, (y1_ - y0_) - 5.0, "y")
for yc in (y0_ + 4.5, (y0_ + y1_) / 2, y1_ - 4.5):
    kit("PF_LB_Chandelier", (x0_ + x1_) / 2, yc, fz + 9.0, 0.0, 1.3)
    light(f"castle_great_hall_{yc:.0f}", (x0_ + x1_) / 2, yc, fz + 4.0, 3500, 16, sh=yc == y0_ + 4.5)
for yc in (y0_ + 1.2, y1_ - 1.2):
    for xc in (x0_ + 0.5, x1_ - 0.5):
        candelabrum(xc, yc, fz + 0.03)
room("Great Hall", -10.0, 14.2, 34.3, 49.7, fz + 0.03, 10.6, note="the model's pillared hall in the palace (nave vault at +10.6 m, aisles 4.7 m)")

VOIDS, APRONS = [], []
U1F, U2F = 7.03, 0.03                  # undercroft floors (centred frame), wholly under the terrain of the palace (>= 20.3)
GHF = 21.85                            # Great Hall aisles (model floor at 21.82) at the head of the grand stair


def ground_rel(x, y):
    return gz(x + T[0], y + T[1]) - T[2]


def passage(name, pin, pout, axis, fz, w=1.7, h=2.9, apron=True):
    """Doorway through the model's wall from pin (room side) to pout (outside): exact cut, threshold, jambs and lintel;
    the ground outside is graded to the threshold (apron) when it lies higher or lower."""
    pin, pout = np.asarray(pin, float), np.asarray(pout, float)
    lo_, hi_, mid = np.minimum(pin, pout), np.maximum(pin, pout), (pin + pout) / 2
    if axis == 0:
        bx = (lo_[0] - 1.0, hi_[0] + 1.0, mid[1] - w / 2, mid[1] + w / 2)
    else:
        bx = (mid[0] - w / 2, mid[0] + w / 2, lo_[1] - 1.0, hi_[1] + 1.0)
    door_cut(*bx, fz, h, f"door {name}")
    B(gR, *bx, fz - 0.3, fz + 0.03, "C2_Floor")
    if axis == 0:
        a, b = lo_[0] - 0.5, hi_[0] + 0.5
        B(gR, a, b, bx[2] - 0.3, bx[2], fz, fz + h + 0.4, "C2_Wall"); B(gR, a, b, bx[3], bx[3] + 0.3, fz, fz + h + 0.4, "C2_Wall")
        B(gR, a, b, bx[2] - 0.3, bx[3] + 0.3, fz + h, fz + h + 0.4, "C2_Wall")
    else:
        a, b = lo_[1] - 0.5, hi_[1] + 0.5
        B(gR, bx[0] - 0.3, bx[0], a, b, fz, fz + h + 0.4, "C2_Wall"); B(gR, bx[1], bx[1] + 0.3, a, b, fz, fz + h + 0.4, "C2_Wall")
        B(gR, bx[0] - 0.3, bx[1] + 0.3, a, b, fz + h, fz + h + 0.4, "C2_Wall")
    d = (pout - pin) / (np.linalg.norm(pout - pin) + 1e-9)
    if apron:
        q = pout + d * 1.5
        APRONS.append([round(q[0] + T[0], 2), round(q[1] + T[1], 2), round(fz + T[2], 2), 1.6, 4.0])        # (z = fz: stable)
    return bx


def liner(x0, x1, y0, y1, fz, h, t=0.4, doors=(), mw="LB_Stone", mf="C2_Floor", mc="LB_Stone", ft=0.4, thick=None, ceil=True):
    """Room built of its own walls (outside the clear rectangle), floor (top at fz + 0.03) and ceiling slab (at fz + h).
    doors: (side, u0, u1, height) with side n (x1), s (x0), e (y1), w (y0) and u along the wall (centred frame)."""
    th = {**dict(n=t, s=t, e=t, w=t), **(thick or {})}
    hol = {s: [] for s in "nsew"}
    for s, u0, u1, hh in doors:
        hol[s].append((u0 + (T[1] if s in "ns" else T[0]), u1 + (T[1] if s in "ns" else T[0]), fz + T[2], fz + hh + T[2]))
    z0w, z1w = fz - ft + T[2], fz + h + ft + T[2]
    if th["s"] > 0:
        gR.wall("y", x0 - th["s"] + T[0], x0 + T[0], y0 - th["w"] + T[1], y1 + th["e"] + T[1], z0w, z1w, mw, hol["s"])
    if th["n"] > 0:
        gR.wall("y", x1 + T[0], x1 + th["n"] + T[0], y0 - th["w"] + T[1], y1 + th["e"] + T[1], z0w, z1w, mw, hol["n"])
    if th["w"] > 0:
        gR.wall("x", y0 - th["w"] + T[1], y0 + T[1], x0 + T[0], x1 + T[0], z0w, z1w, mw, hol["w"])
    if th["e"] > 0:
        gR.wall("x", y1 + T[1], y1 + th["e"] + T[1], x0 + T[0], x1 + T[0], z0w, z1w, mw, hol["e"])
    B(gR, x0, x1, y0, y1, fz - ft, fz + 0.03, mf)
    if ceil is True:
        B(gR, x0 - th["s"], x1 + th["n"], y0 - th["w"], y1 + th["e"], fz + h, fz + h + ft, mc)
    elif ceil:                                                                   # list of holes in the ceiling slab
        for (a0, a1, b0, b1) in rect_minus((x0 - th["s"], x1 + th["n"], y0 - th["w"], y1 + th["e"]), ceil):
            B(gR, a0, a1, b0, b1, fz + h, fz + h + ft, mc)


def _rib(p, q, axis, c, zs, rise, w, d, mat, n):
    """Pointed rib from p to q along `axis` ('x' or 'y') at the other coordinate c: continuous sloped segments."""
    zf = lambda t: zs + rise * math.sin(math.pi * t) ** 0.7
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n
        u0, u1 = p + (q - p) * t0, p + (q - p) * t1
        za, zb = zf(t0), zf(t1)
        if axis == "y":
            v = [(c - w / 2, u0, za - d / 2), (c - w / 2, u1, zb - d / 2), (c + w / 2, u1, zb - d / 2), (c + w / 2, u0, za - d / 2),
                 (c - w / 2, u0, za + d / 2), (c - w / 2, u1, zb + d / 2), (c + w / 2, u1, zb + d / 2), (c + w / 2, u0, za + d / 2)]
        else:
            v = [(u0, c - w / 2, za - d / 2), (u1, c - w / 2, zb - d / 2), (u1, c + w / 2, zb - d / 2), (u0, c + w / 2, za - d / 2),
                 (u0, c - w / 2, za + d / 2), (u1, c - w / 2, zb + d / 2), (u1, c + w / 2, zb + d / 2), (u0, c + w / 2, za + d / 2)]
        f = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
        if (axis == "y") == (q > p):                                   # keep the faces outward
            f = [r[::-1] for r in f]
        gF.add([(a_ + T[0], b_ + T[1], c_ + T[2]) for a_, b_, c_ in v], f, mat, False)


def arch_y(x, ya, yb, zs, rise, w=0.5, d=0.45, mat="C2_Wall", n=16):
    """Pointed rib along y (between ya and yb), springing at zs, centred on x (visual only)."""
    _rib(ya, yb, "y", x, zs, rise, w, d, mat, n)


def arch_x(y, xa, xb, zs, rise, w=0.5, d=0.45, mat="C2_Wall", n=16):
    _rib(xa, xb, "x", y, zs, rise, w, d, mat, n)


def pier(x, y, fz, h, s=0.45, mat="C2_Wall"):
    B(gR, x - s, x + s, y - s, y + s, fz - 0.05, fz + h, mat)
    B(gF, x - s - 0.12, x + s + 0.12, y - s - 0.12, y + s + 0.12, fz, fz + 0.35, mat, False)            # base
    B(gF, x - s - 0.1, x + s + 0.1, y - s - 0.1, y + s + 0.1, fz + h - 0.9, fz + h - 0.6, mat, False)   # capital


def barrel_up(x, y, fz, r=0.38, h=0.95, mat="LB_GlossyWood"):
    gF.cyl(x + T[0], y + T[1], r, fz + T[2], fz + h + T[2], mat, 12, True)
    for zb in (0.15, h - 0.2):
        gF.cyl(x + T[0], y + T[1], r + 0.02, fz + zb + T[2], fz + zb + 0.06 + T[2], "LB_Metal", 12, False)


def barrel_lying(x, y, z, axis, r=0.42, hw=0.55):
    gF.wheel((x + T[0], y + T[1], z + T[2]), axis, r, hw, "LB_GlossyWood", 12, False)
    for s in (-0.7, 0.7):
        a = np.array(axis, float) / np.linalg.norm(axis)
        gF.wheel((x + a[0] * hw * s + T[0], y + a[1] * hw * s + T[1], z + T[2]), axis, r + 0.02, 0.04, "LB_Metal", 12, False)


def hearth(x0, x1, y0, y1, fz, hood_z, top, side):
    """Fireplace against a wall: hearth stone, glowing fire, hood and chimney breast to `top`. side: wall at 'n','s','e','w'."""
    B(gR, x0, x1, y0, y1, fz - 0.05, fz + 0.3, "LB_Stone")
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    B(gF, cx - 0.5, cx + 0.5, cy - 0.35, cy + 0.35, fz + 0.3, fz + 0.55, "GB_WinLit", False)
    e = 0.35
    hx0, hx1, hy0, hy1 = x0 - e, x1 + e, y0 - e, y1 + e
    if side == "n": hx1 = x1
    if side == "s": hx0 = x0
    if side == "e": hy1 = y1
    if side == "w": hy0 = y0
    B(gF, hx0, hx1, hy0, hy1, fz + hood_z, fz + hood_z + 0.9, "LB_Stone", False)
    bx0, bx1, by0, by1 = {"n": (x1 - 0.6, x1, y0, y1), "s": (x0, x0 + 0.6, y0, y1), "e": (x0, x1, y1 - 0.6, y1), "w": (x0, x1, y0, y0 + 0.6)}[side]
    B(gF, bx0, bx1, by0, by1, fz + hood_z + 0.9, top, "LB_Stone", False)
    for s_ in (0, 1):                                                                                    # jambs
        if side in "ns":
            B(gR, x0, x1, (y0 if s_ == 0 else y1 - 0.3), (y0 + 0.3 if s_ == 0 else y1), fz, fz + hood_z, "LB_Stone")
        else:
            B(gR, (x0 if s_ == 0 else x1 - 0.3), (x0 + 0.3 if s_ == 0 else x1), y0, y1, fz, fz + hood_z, "LB_Stone")


def bars_y(x0, x1, y, fz, h, gaps=(), mat="GB_Metal"):
    """Iron bars along x at y (cell fronts), with open gaps (doorways): visual bars + collision panel."""
    for xa, xb in rect_minus_1d((x0, x1), gaps):
        for xb_ in np.arange(xa + 0.08, xb - 0.04, 0.16):
            B(gF, xb_ - 0.025, xb_ + 0.025, y - 0.025, y + 0.025, fz, fz + h, mat, False)
        B(gF, xa, xb, y - 0.04, y + 0.04, fz + h - 0.08, fz + h, mat, False)
        B(gF, xa, xb, y - 0.04, y + 0.04, fz + 1.0, fz + 1.06, mat, False)
        B(gF, xa, xb, y - 0.06, y + 0.06, fz, fz + h, mat, "only")


def rect_minus_1d(r, gaps):
    out = [r]
    for g0, g1 in gaps:
        out = [s for a, b in out for s in ((a, min(b, g0)), (max(a, g1), b)) if s[1] - s[0] > 0.05]
    return out


def sarcophagus(x, y, fz, axis="x", L=2.3, Wd=1.0, lord=False):
    hx, hy = (L / 2, Wd / 2) if axis == "x" else (Wd / 2, L / 2)
    if lord:
        B(gR, x - hx - 0.8, x + hx + 0.8, y - hy - 0.6, y + hy + 0.6, fz - 0.05, fz + 0.25, "LB_Stone")
        B(gR, x - hx - 0.4, x + hx + 0.4, y - hy - 0.3, y + hy + 0.3, fz + 0.25, fz + 0.5, "LB_Stone")
        fz = fz + 0.5
    B(gF, x - hx, x + hx, y - hy, y + hy, fz, fz + 0.8, "LB_Stone")
    B(gF, x - hx - 0.08, x + hx + 0.08, y - hy - 0.08, y + hy + 0.08, fz + 0.8, fz + 0.95, "C2_Wall")
    B(gF, x - hx + 0.15, x + hx - 0.15, y - hy + 0.15, y + hy - 0.15, fz + 0.95, fz + 1.12, "C2_Wall")
    B(gF, x - hx - 0.1, x + hx + 0.1, y - hy - 0.1, y + hy + 0.1, fz, fz + 1.12, "GB_Stone", "only")


def chair(x, y, fz, face, high=False):
    """Chair facing `face` (unit xy): seat, back on the far side."""
    B(gF, x - 0.25, x + 0.25, y - 0.25, y + 0.25, fz + 0.42, fz + 0.5, "LB_GlossyWood", False)
    for sx_ in (-0.2, 0.2):
        for sy_ in (-0.2, 0.2):
            B(gF, x + sx_ - 0.03, x + sx_ + 0.03, y + sy_ - 0.03, y + sy_ + 0.03, fz, fz + 0.42, "LB_GlossyWood", False)
    bx, by = x - face[0] * 0.23, y - face[1] * 0.23
    hh = 1.6 if high else 1.05
    if abs(face[0]) > 0.5:
        B(gF, bx - 0.03, bx + 0.03, y - 0.25, y + 0.25, fz + 0.5, fz + hh, "LB_GlossyWood", False)
    else:
        B(gF, x - 0.25, x + 0.25, by - 0.03, by + 0.03, fz + 0.5, fz + hh, "LB_GlossyWood", False)
    B(gF, x - 0.27, x + 0.27, y - 0.27, y + 0.27, fz, fz + 0.5, "GB_Stone", "only")


def torch(name, x, y, z, wall, lm=600, rad=8):
    """Wall torch: iron bracket + flame; wall = direction from the torch to the wall (unit xy)."""
    B(gF, x - 0.05, x + 0.05, y - 0.05, y + 0.05, z - 0.45, z, "LB_Metal", False)
    B(gF, x + wall[0] * 0.15 - 0.04, x + wall[0] * 0.15 + 0.04, y + wall[1] * 0.15 - 0.04, y + wall[1] * 0.15 + 0.04, z - 0.3, z - 0.22, "LB_Metal", False)
    B(gF, x - 0.07, x + 0.07, y - 0.07, y + 0.07, z, z + 0.22, "GB_WinLit", False)
    light(name, x - wall[0] * 0.3, y - wall[1] * 0.3, z + 0.3, lm, rad, col=(1.0, 0.55, 0.25))


def spiral_stair(g, cx, cy, r_out, core, z0, z1, deg, start):
    """Spiral of 0.2 m steps: stone wedges (visual) and a helical ramp of sloped hulls through the centres of the treads
    (walkable collision, as for the kit spirals of the lodge), core column."""
    n = int(round((z1 - z0) / 0.2)); sh = (z1 - z0) / n
    for i in range(n):
        a0 = math.radians(start + deg * i); a1 = a0 + math.radians(deg + 2); zt = z0 + sh * (i + 1)
        pts = [(cx + core * math.cos(a0) + T[0], cy + core * math.sin(a0) + T[1]), (cx + r_out * math.cos(a0) + T[0], cy + r_out * math.sin(a0) + T[1]),
               (cx + r_out * math.cos(a1) + T[0], cy + r_out * math.sin(a1) + T[1]), (cx + core * math.cos(a1) + T[0], cy + core * math.sin(a1) + T[1])]
        g.poly_prism(pts, zt - 0.35 + T[2], zt + T[2], "LB_Stone", False)
    cen = [math.radians(start + deg * (i + 0.5)) for i in range(-1, n + 1)]
    zc = [z0] + [z0 + sh * (i + 1) for i in range(n)] + [z1]
    for b0, b1, za, zb in zip(cen[:-1], cen[1:], zc[:-1], zc[1:]):
        bm = (b0 + b1) / 2
        o0, o1 = r_out * np.array([math.cos(b0), math.sin(b0)]), r_out * np.array([math.cos(b1), math.sin(b1)])
        inn = 0.15 * np.array([math.cos(bm), math.sin(bm)])
        A_ = np.array([[*o0, 1], [*o1, 1], [*inn, 1]]); cz = np.linalg.solve(A_, [za, zb, (za + zb) / 2])
        quad = [0.15 * np.array([math.cos(b0), math.sin(b0)]), o0, o1, 0.15 * np.array([math.cos(b1), math.sin(b1)])]
        top = [(q[0] + cx + T[0], q[1] + cy + T[1], cz[0] * q[0] + cz[1] * q[1] + cz[2] + T[2]) for q in quad]
        g.add([(a, b, c - 0.35) for a, b, c in top] + top, [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]],
              "GB_Stone", "only")
    g.cyl(cx + T[0], cy + T[1], core, z0 + T[2], z1 + T[2], "LB_Stone", 10, True)


# Throne Room: inside the main block of the palace, behind the Great Hall (door through the dividing wall). Behind its
# west wall, the secret stair chamber: a panel beside the throne opens on a spiral down to the crypt (L-2).
TX0, TX1, TY0, TY1, TFZ, TH = -19.5, 11.5, 51.0, 62.0, fz, 11.0
TT0 = -15.0                                                            # west wall of the throne room proper
SPX, SPY, SPH = -17.5, 59.0, 2.0                                       # secret spiral: centre, clear half-width of its shaft
DAIS = TFZ + 0.6
CUTS.append(dict(x=[TX0, TX1], y=[TY0, TY1], z=[TFZ + 0.035, TFZ + TH], what="model clutter inside the Throne Room (to the lining)"))
DX0, DX1 = 0.75, 3.75                                                  # door on the axis of the Great Hall nave
door_cut(DX0, DX1, y1_ - 0.2, TY0 + 0.6, TFZ, 3.6, "door Great Hall -> Throne Room")
gR.wall("x", TY0 - 0.4 + T[1], TY0 + T[1], TX0 - 0.4 + T[0], TX1 + 0.4 + T[0], TFZ - 0.3 + T[2], TFZ + TH + 0.3 + T[2], "LB_Sandstone",
        holes=[(DX0 + T[0], DX1 + T[0], TFZ + T[2], TFZ + 3.6 + T[2])])
gR.wall("x", TY1 + T[1], TY1 + 0.4 + T[1], TX0 - 0.4 + T[0], TX1 + 0.4 + T[0], TFZ - 0.3 + T[2], TFZ + TH + 0.3 + T[2], "LB_Sandstone")
gR.wall("y", TX0 - 0.4 + T[0], TX0 + T[0], TY0 + T[1], TY1 + T[1], TFZ - 0.3 + T[2], TFZ + TH + 0.3 + T[2], "LB_Sandstone")
gR.wall("y", TX1 + T[0], TX1 + 0.4 + T[0], TY0 + T[1], TY1 + T[1], TFZ - 0.3 + T[2], TFZ + TH + 0.3 + T[2], "LB_Sandstone")
SD0, SD1 = SPY - 0.7, SPY + 0.7                                        # secret door, on the top tier of the dais
gR.wall("y", TT0 - 0.4 + T[0], TT0 + T[0], TY0 + T[1], TY1 + T[1], TFZ - 0.3 + T[2], TFZ + TH + T[2], "LB_Sandstone",
        holes=[(SD0 + T[1], SD1 + T[1], DAIS + T[2], DAIS + 2.4 + T[2])])
pan = G("SM_GB_Castle_SecretPanel", "Environment/Castle")
B(pan, TT0 - 0.32, TT0 - 0.08, SD0 + 0.02, SD1 - 0.02, DAIS + 0.01, DAIS + 2.38, "LB_Sandstone")
MOVABLE.append(dict(name="SM_GB_Castle_SecretPanel", pivot=W(TT0 - 0.2, SD1, DAIS), motion="hinge",
                    note="secret panel in the wall behind the dais (sandstone like the wall); swings into the stair chamber"))
B(gR, TT0 - 0.4, TX1, TY0, TY1, TFZ - 0.3, TFZ + 0.03, "C2_Floor")
for (a0, a1, b0, b1) in rect_minus((TX0, TT0 - 0.4, TY0, TY1), [(SPX - SPH, SPX + SPH, SPY - SPH, SPY + SPH)]):
    B(gR, a0, a1, b0, b1, TFZ - 0.3, DAIS, "C2_Floor")                                        # stair chamber floor = dais top
B(gR, TX0 - 0.4, TX1 + 0.4, TY0 - 0.4, TY1 + 0.4, TFZ + TH, TFZ + TH + 0.4, "LB_GlossyWood")
for xb in np.arange(TT0 + 2.5, TX1 - 1.0, 3.5):                                                   # coffered ceiling beams
    B(gF, xb - 0.2, xb + 0.2, TY0, TY1, TFZ + TH - 0.5, TFZ + TH, "LB_GlossyWood", False)
for xp in np.arange(TT0 + 4.0, TX1 - 1.0, 6.0):                                                   # wall pilasters
    for yp in (TY0 + 0.25, TY1 - 0.25):
        if yp < TY0 + 1 and abs(xp - (DX0 + DX1) / 2) < 2.6:
            continue                                                                               # (not before the door)
        B(gR, xp - 0.45, xp + 0.45, yp - 0.25, yp + 0.25, TFZ, TFZ + TH, "LB_Stone")
# dais and throne at the south end (-X), red carpet from the door, banners, candelabra, chandeliers
yc = (TY0 + TY1) / 2
for k_, (dx_, hh) in enumerate(((5.0, 0.2), (4.2, 0.4), (3.4, 0.6))):
    B(gR, TT0, TT0 + dx_, yc - 4.0 + 0.4 * k_, yc + 4.0 - 0.4 * k_, TFZ, TFZ + hh, "LB_Stone")
tz_ = DAIS
B(gF, TT0 + 1.0, TT0 + 2.0, yc - 0.8, yc + 0.8, tz_, tz_ + 0.5, "LB_GlossyWood")                 # seat
B(gF, TT0 + 0.6, TT0 + 1.0, yc - 0.85, yc + 0.85, tz_, tz_ + 3.4, "LB_GlossyWood")               # tall back
B(gF, TT0 + 0.62, TT0 + 0.98, yc - 0.55, yc + 0.55, tz_ + 3.4, tz_ + 3.9, "GB_Detail")            # crest
B(gF, TT0 + 1.05, TT0 + 1.95, yc - 0.7, yc + 0.7, tz_ + 0.5, tz_ + 0.62, "GB_Detail")             # cushion
for s_ in (-1, 1):
    B(gF, TT0 + 1.0, TT0 + 2.05, yc + s_ * 0.8 - 0.12, yc + s_ * 0.8 + 0.12, tz_, tz_ + 1.05, "LB_GlossyWood")
B(gF, TT0 + 0.6, TT0 + 2.05, yc - 0.95, yc + 0.95, tz_, tz_ + 1.2, "GB_Stone", "only")
B(gF, TT0 + 5.0, (DX0 + DX1) / 2 + 1.0, yc - 1.4, yc + 1.4, TFZ + 0.03, TFZ + 0.05, "GB_Detail", False)   # carpet
B(gF, (DX0 + DX1) / 2 - 1.4, (DX0 + DX1) / 2 + 1.4, yc - 1.4, TY0 + 0.1, TFZ + 0.03, TFZ + 0.05, "GB_Detail", False)
for xp in np.arange(TT0 + 7.0, TX1 - 2.0, 6.0):
    for yp, s_ in ((TY0 + 0.05, 1), (TY1 - 0.05, -1)):
        y_a, y_b = sorted((yp, yp + s_ * 0.06))
        B(gF, xp - 0.9, xp + 0.9, y_a, y_b, TFZ + 3.0, TFZ + 8.5, "GB_Detail", False)                # banners
for xp in np.arange(TT0 + 7.0, TX1 - 1.0, 6.0):
    for yp in (yc - 2.6, yc + 2.6):
        candelabrum(xp, yp, TFZ + 0.03)
for xp in (TT0 + 8.0, (TT0 + TX1) / 2 + 3.0):
    kit("PF_LB_Chandelier", xp, yc, TFZ + TH - 0.5, 0.0, 1.5)
    light(f"castle_throne_{xp:.0f}", xp, yc, TFZ + 5.0, 4000, 18, sh=True)
light("castle_throne_dais", TT0 + 4.0, yc, TFZ + 3.0, 1500, 9, col=(1.0, 0.45, 0.3))
room("Throne Room", TT0, TX1, TY0, TY1, TFZ + 0.03, TH, note="liner room in the main block of the palace")

# secret stair: spiral (0.2 m steps) from the crypt floor (L-2) to the top tier of the dais, in a shaft of 1.6 m walls
# (the landscape is cut out over it: the walls hide the edge of that cut)
SW = 1.6
zb_, zt_ = U2F - 0.4, TFZ - 0.3
gR.wall("x", SPY - SPH - SW + T[1], SPY - SPH + T[1], SPX - SPH - SW + T[0], SPX + SPH + SW + T[0], zb_ + T[2], zt_ + T[2], "C2_Wall")
gR.wall("x", SPY + SPH + T[1], SPY + SPH + SW + T[1], SPX - SPH - SW + T[0], SPX + SPH + SW + T[0], zb_ + T[2], zt_ + T[2], "C2_Wall")
gR.wall("y", SPX - SPH - SW + T[0], SPX - SPH + T[0], SPY - SPH + T[1], SPY + SPH + T[1], zb_ + T[2], zt_ + T[2], "C2_Wall")
gR.wall("y", SPX + SPH + T[0], SPX + SPH + SW + T[0], SPY - SPH + T[1], SPY + SPH + T[1], zb_ + T[2], zt_ + T[2], "C2_Wall",
        holes=[(SPY - 0.75 + T[1], SPY + 0.75 + T[1], U2F + T[2], U2F + 2.6 + T[2])])             # foot: east, into the crypt
# 113 steps of 19.02 deg (3.8 m a turn): the first starts east of the core (entry from the east), the last ends east (panel)
spiral_stair(gR, SPX, SPY, 1.95, 0.3, U2F, DAIS, 19.02, 19.02)
for (a0, a1, b0, b1) in ((SPX - SPH, SPX + SPH, SPY - SPH - 0.2, SPY - SPH), (SPX - SPH, SPX + SPH, SPY + SPH, SPY + SPH + 0.2)):
    B(gF, a0, a1, b0, b1, DAIS, DAIS + 1.0, "LB_Stone")                                          # balustrade round the well
CUTS.append(dict(x=[SPX - SPH, SPX + SPH], y=[SPY - SPH, SPY + SPH], z=[U2F - 1.0, TFZ + 0.1], what="secret stair shaft"))
VOIDS.append([round(SPX - SPH - 0.8 + T[0], 2), round(SPX + SPH + 0.8 + T[0], 2), round(SPY - SPH - 0.8 + T[1], 2), round(SPY + SPH + 0.8 + T[1], 2), round(U2F - 0.18 + T[2], 2)])
for k_, zz in enumerate((3.0, 8.5, 14.0, 19.5)):                                                # candles in wall niches of the shaft
    light(f"castle_secret_stair_{k_}", SPX + (SPH - 0.15) * (1 if k_ % 2 else -1), SPY, zz, 700, 7, col=(1.0, 0.5, 0.25))
room("Secret stair chamber", TX0, TT0 - 0.4, SPY - SPH, SPY + SPH, DAIS, TH - 0.6, note="behind the throne: top of the spiral down to the crypt")


def tower_room(name, cx, cy, r, vol_floor, h, door, recipe):
    """Round tower room (the model's own interior): floor disc at the level of the ground outside its door, furniture
    by recipe, doorway cut toward the reachable outside point."""
    fz_ = round(max(vol_floor, ground_rel(*door["outside"])), 2)
    pts = [(cx + T[0] + (r - 0.3) * math.cos(a), cy + T[1] + (r - 0.3) * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)]
    gR.poly_prism(pts, fz_ - 0.25 + T[2], fz_ + 0.03 + T[2], "LB_WoodFloor")
    passage(name, door["inside"], door["outside"], door["axis"], fz_)
    recipe(cx, cy, r, fz_ + 0.03)
    room(name, cx - r * 0.6, cx + r * 0.6, cy - r * 0.6, cy + r * 0.6, fz_ + 0.03, h)
    return fz_


def library_recipe(cx, cy, r, fz):
    for k_ in range(7):                                                  # bookcases on chords of the round wall
        a = 2 * math.pi * k_ / 7 + 0.3
        if any(abs(((a - math.atan2(*(np.array(d_) - [cx, cy])[::-1])) + math.pi) % (2 * math.pi) - math.pi) < 0.5 for d_ in (LIB_DOOR,)):
            continue
        rr = r - 1.0
        kitbox("PF_LB_BookcaseTall", cx + rr * math.cos(a), cy + rr * math.sin(a), fz, math.degrees(a))
    kitbox("PF_LB_ReadingSet", cx, cy, fz, 0.0)
    kit("PF_LB_Chandelier", cx, cy, fz + 6.3, 0.0, 0.8)
    light("castle_library", cx, cy, fz + 3.0, 2500, 12, sh=True)


def apartments_recipe(cx, cy, r, fz):
    bx, by = cx - 2.0, cy + 1.5                                          # four-poster bed
    B(gF, bx - 1.1, bx + 1.1, by - 1.2, by + 1.2, fz, fz + 0.6, "LB_GlossyWood")
    B(gF, bx - 1.05, bx + 1.05, by - 1.15, by + 1.15, fz + 0.6, fz + 0.8, "GB_Detail")
    for sx_ in (-1, 1):
        for sy_ in (-1, 1):
            B(gF, bx + sx_ * 1.05 - 0.07, bx + sx_ * 1.05 + 0.07, by + sy_ * 1.15 - 0.07, by + sy_ * 1.15 + 0.07, fz, fz + 2.6, "LB_GlossyWood", False)
    B(gF, bx - 1.15, bx + 1.15, by - 1.25, by + 1.25, fz + 2.6, fz + 2.75, "GB_Detail", False)
    B(gF, bx - 1.1, bx + 1.1, by - 1.2, by + 1.2, fz, fz + 0.8, "GB_Stone", "only")
    kitbox("PF_LB_Bookcase", cx + r - 1.3, cy - 1.0, fz, 0.0)
    kitbox("PF_LB_ReadingSet", cx + 1.5, cy - 2.5, fz, 90.0)
    candelabrum(cx - 3.5, cy - 2.0, fz)
    light("castle_apartments", cx, cy, fz + 3.0, 1800, 10, sh=True)


def study_recipe(x0, x1, y0, y1, fz):
    kitbox("PF_LB_Bookcase", x1 - 0.05, (y0 + y1) / 2, fz, 0.0)
    kitbox("PF_LB_ReadingSet", (x0 + x1) / 2 - 0.5, (y0 + y1) / 2, fz, 0.0)
    candelabrum(x0 + 0.8, y0 + 0.8, fz)
    light("castle_study", (x0 + x1) / 2, (y0 + y1) / 2, fz + 2.8, 1500, 9, sh=True)


lib = RJ["Library"]; LIB_DOOR = lib["door"]["inside"]
tower_room("Library", 58.3, 73.6, 8.4, lib["floor"], 6.5, lib["door"], library_recipe)
ap = RJ["Lord's Apartments"]
tower_room("Lord's Apartments", -69.5, 61.0, 7.6, ap["floor"], 6.5, ap["door"], apartments_recipe)
st = RJ["Lord's Study"]; sx0, sx1, sy0, sy1 = st["rect"]; d_ = st["door"]
sfz = round(max(st["floor"], ground_rel(*d_["outside"])), 2)
B(gR, sx0, sx1, sy0, sy1, sfz - 0.25, sfz + 0.03, "LB_WoodFloor")
passage("Lord's Study", d_["inside"], d_["outside"], d_["axis"], sfz)
study_recipe(sx0, sx1, sy0, sy1, sfz + 0.03)
room("Lord's Study", sx0, sx1, sy0, sy1, sfz + 0.03, 4.5)

# Chapel: the model's pillared hall north of the palace court (six columns, open to the court by an arcade). Nave along
# X between the two rows of columns, altar at the north end against the wall of the throne block, pews facing it.
CHF = 21.4
CX0, CX1, CY0, CY1 = -38.0, -22.6, 45.8, 60.8
B(gR, -26.4, -22.5, 52.0, 56.4, CHF - 0.1, CHF + 0.2, "LB_Stone")                                 # sanctuary step
B(gR, -25.6, -22.5, 52.6, 55.8, CHF + 0.2, CHF + 0.45, "LB_Stone")
B(gF, -24.9, -23.9, 53.2, 55.2, CHF + 0.45, CHF + 1.45, "LB_Stone")                               # altar
B(gF, -24.95, -23.85, 53.1, 55.3, CHF + 1.45, CHF + 1.5, "GB_Detail", False)                       # altar cloth
B(gF, -22.75, -22.45, 52.4, 56.0, CHF + 0.45, CHF + 5.6, "LB_GlossyWood", False)                   # reredos
B(gF, -22.8, -22.75, 53.0, 55.4, CHF + 1.2, CHF + 5.0, "GB_Detail", False)
B(gF, -22.95, -22.8, 54.12, 54.28, CHF + 1.8, CHF + 4.6, "LB_Metal", False)                         # cross
B(gF, -22.95, -22.8, 53.55, 54.85, CHF + 3.7, CHF + 3.86, "LB_Metal", False)
B(gF, -24.95, -22.45, 52.4, 56.0, CHF + 0.45, CHF + 1.5, "GB_Stone", "only")
for yp in (52.9, 55.5):
    candelabrum(-25.2, yp, CHF + 0.45, 1.6)
for xr in (-37.3, -36.1, -34.0, -32.8, -31.6, -30.4, -28.2, -27.0):                                # pews (avoid the columns)
    for ya, yb in ((52.0, 53.7), (54.7, 56.4)):
        B(gF, xr - 0.2, xr + 0.2, ya, yb, CHF + 0.42, CHF + 0.48, "LB_GlossyWood", False)
        B(gF, xr - 0.24, xr - 0.18, ya, yb, CHF + 0.48, CHF + 1.0, "LB_GlossyWood", False)
        for yy in (ya + 0.05, yb - 0.11):
            B(gF, xr - 0.2, xr + 0.2, yy, yy + 0.06, CHF, CHF + 0.42, "LB_GlossyWood", False)
        B(gF, xr - 0.25, xr + 0.22, ya, yb, CHF, CHF + 1.0, "GB_Stone", "only")
kit("PF_LB_Chandelier", -31.5, 54.2, CHF + 9.0, 0.0, 1.2)
light("castle_chapel_altar", -25.5, 54.2, CHF + 2.6, 1500, 9, sh=True)
light("castle_chapel_nave", -31.5, 54.2, CHF + 5.0, 1800, 14)
light("castle_chapel_moon", -31.0, 47.5, CHF + 4.0, 700, 12, col=(0.55, 0.62, 0.9))
room("Chapel", CX0, CX1, CY0, CY1, CHF, 8.0, note="the model's pillared hall north of the palace court")

# War Room: liner inside the east-wing building (1700 of the covered-volume analysis), door from the east court up a stoop
WX0, WX1, WY0, WY1, WFZ, WH = 37.0, 43.8, -21.0, -6.6, 14.5, 6.0
CUTS.append(dict(x=[WX0, WX1], y=[WY0, WY1], z=[WFZ + 0.035, WFZ + WH], what="model clutter inside the War Room (to the lining)"))
liner(WX0, WX1, WY0, WY1, WFZ, WH, doors=[("n", -14.6, -12.9, 2.9)], mw="LB_Sandstone", mf="LB_WoodFloor", mc="LB_GlossyWood")
pb = passage("War Room", (WX1 - 0.2, -13.75), (WX1 + 1.8, -13.75), 0, WFZ, apron=False)
zc_ = ground_rel(pb[1] + 1.9, -13.75)
gR.stairs((pb[1] + 1.9 + T[0], -13.75 + T[1]), (-1, 0), 1.7, zc_ + T[2], WFZ + 0.03 + T[2], "LB_Stone", step_h=0.19)
B(gF, 38.9, 41.9, -16.3, -11.3, WFZ + 0.03, WFZ + 0.82, "LB_GlossyWood", False)                     # map table
B(gF, 39.0, 41.8, -16.2, -11.4, WFZ + 0.82, WFZ + 0.86, "GB_Plaster", False)                   # map
B(gF, 38.8, 42.0, -16.4, -11.2, WFZ + 0.03, WFZ + 0.86, "GB_Stone", "only")
for yy in (-15.4, -13.8, -12.2):
    chair(38.4, yy, WFZ + 0.03, (1, 0)); chair(42.4, yy, WFZ + 0.03, (-1, 0))
chair(40.4, -17.0, WFZ + 0.03, (0, 1), high=True)
for xx in np.arange(37.6, 43.4, 0.55):                                                             # spear rack, south wall
    B(gF, xx - 0.03, xx + 0.03, WY0 + 0.15, WY0 + 0.21, WFZ + 0.1, WFZ + 2.6, "LB_Metal", False)
B(gF, 37.4, 43.4, WY0 + 0.05, WY0 + 0.3, WFZ + 1.2, WFZ + 1.3, "LB_GlossyWood", False)
for xx in (38.4, 42.4):
    B(gF, xx - 0.8, xx + 0.8, WY1 - 0.07, WY1 - 0.01, WFZ + 2.0, WFZ + 5.0, "GB_Detail", False)  # banners, north wall
kitbox("PF_LB_Bookcase", WX0 + 0.05, -9.1, WFZ + 0.03, 180.0)
candelabrum(WX1 - 0.6, WY0 + 0.8, WFZ + 0.03); candelabrum(WX0 + 0.6, WY0 + 0.8, WFZ + 0.03)
kit("PF_LB_Chandelier", 40.4, -13.8, WFZ + WH - 0.05, 0.0, 0.8)
light("castle_war_room", 40.4, -13.8, WFZ + 3.6, 2200, 11, sh=True)
room("War Room", WX0, WX1, WY0, WY1, WFZ + 0.03, WH, note="liner in the east-wing building, door from the east court")

# ---------------------------------------------------------------- undercroft (under the terrain of the palace)
# Two levels below the landscape (no hole in it: only the two shafts cut it), rooms at the sizes of the design document.
# Grand stair: dog-leg with a central spine wall in the west aisle of the Great Hall, six flights of 3.5-3.7 m:
# hall -> L-1 (+7.0, Banquet Hall, Kitchen, Larder, cellar) -> L-2 (0.0, Crypt, Dungeon, start of the secret tunnel)
SX0, SX1, SY0, SY1 = -10.1, -5.3, 35.0, 47.5
FA, FB, SPN = (-10.1, -7.8), (-7.5, -5.3), (-7.8, -7.5)
YT = 37.0                                                                    # south landings: y SY0..YT
xa_, xb_ = sum(FA) / 2, sum(FB) / 2
LEVELS = [GHF] + [round(GHF - (GHF - U1F) * k / 4, 3) for k in (1, 2, 3)] + [U1F, round((U1F + U2F) / 2, 3), U2F]
north_z, south_z, runs = [], [], []
for k in range(6):
    za_, zb2 = LEVELS[k], LEVELS[k + 1]                                       # flight k goes down from za_ to zb2
    nst = int(round((za_ - zb2) / 0.195)); run_ = nst * 0.3; runs.append(run_)
    if k % 2 == 0:                                                           # on FA, heading north (+y), from YT
        gR.stairs((xa_ + T[0], YT + run_ + T[1]), (0, -1), FA[1] - FA[0], zb2 + T[2], za_ + T[2], "LB_Stone", step_h=(za_ - zb2) / nst)
        north_z.append((zb2, YT + run_))
    else:                                                                    # on FB, heading south (-y), to YT
        gR.stairs((xb_ + T[0], YT + T[1]), (0, 1), FB[1] - FB[0], zb2 + T[2], za_ + T[2], "LB_Stone", step_h=(za_ - zb2) / nst)
        south_z.append(zb2)
for zl, yl in north_z:                                                       # north landings
    B(gR, SX0, SX1, yl, SY1, zl - 0.4, zl, "C2_Floor")
for zl in south_z[:-1]:                                                      # south landing at L-1 (door)
    B(gR, SX0, SX1, SY0, YT, zl - 0.4, zl, "C2_Floor")
B(gR, SX0, SX1, SY0, SY1, U2F - 0.4, U2F, "C2_Floor")                                              # floor of the well (L-2)
YRUN = YT + max(runs)
B(gR, SPN[0], SPN[1], YT, YRUN, U2F - 0.4, GHF, "C2_Wall")                                         # spine wall
B(gR, SX0, SX1, SY0, YT, 21.4, 21.8, "C2_Wall")                                                    # under the hall floor
holes_e = [(SY0 + 0.2 + T[1], YT - 0.2 + T[1], z + T[2], z + 2.8 + T[2]) for z in (U1F, U2F)]
gR.wall("y", SX1 + T[0], SX1 + SW + T[0], SY0 - SW + T[1], SY1 + SW + T[1], U2F - 0.4 + T[2], 21.8 + T[2], "C2_Wall", holes_e)
gR.wall("y", SX0 - SW + T[0], SX0 + T[0], SY0 - SW + T[1], SY1 + SW + T[1], U2F - 0.4 + T[2], 21.8 + T[2], "C2_Wall")
gR.wall("x", SY0 - SW + T[1], SY0 + T[1], SX0 + T[0], SX1 + T[0], U2F - 0.4 + T[2], 21.8 + T[2], "C2_Wall")
gR.wall("x", SY1 + T[1], SY1 + SW + T[1], SX0 + T[0], SX1 + T[0], U2F - 0.4 + T[2], 21.8 + T[2], "C2_Wall")
CUTS.append(dict(x=[SX0, SX1], y=[YT, SY1], z=[GHF - 3.0, GHF + 0.6], what="Great Hall floor over the grand stair"))
CUTS.append(dict(x=[SX0, SX1], y=[SY0, SY1], z=[U2F - 1.0, GHF - 3.0], what="grand stair shaft"))
VOIDS.append([round(SX0 - 0.8 + T[0], 2), round(SX1 + 0.8 + T[0], 2), round(SY0 - 0.8 + T[1], 2), round(SY1 + 0.8 + T[1], 2), round(U2F - 0.18 + T[2], 2)])
for (a0, a1, b0, b1) in ((FB[0], SX1 + 0.2, YT - 0.2, YT), (SX1, SX1 + 0.2, YT, SY1 + 0.2), (SX0, SX1, SY1, SY1 + 0.2), (SPN[0], SPN[1], YT, YRUN)):
    B(gF, a0, a1, b0, b1, GHF, GHF + 1.0, "LB_Stone")                                              # balustrade round the well
for k_, (zl, yl) in enumerate(north_z):
    torch(f"castle_grand_stair_{k_}", SX0 + 0.12, (yl + SY1) / 2, zl + 2.2, (-1, 0), 1400, 10)
room("Grand stair (L-1 landing)", SX0, SX1, SY0, YT, U1F, 6.6, sealed=True)
room("Grand stair (L-2 landing)", SX0, SX1, SY0, YT, U2F, 6.6, sealed=True)

# L-1 (+7.0): Banquet Hall 36 x 14 x 12 (vaulted, two rows of piers), Kitchen 16 x 12 x 8, Larder 18 x 10 x 5,
# Wine and blood cellar 10 x 10 x 5
BX0, BX1, BY0, BY1, BH = SX1 + SW, SX1 + SW + 36.0, 35.0, 49.0, 12.0
liner(BX0, BX1, BY0, BY1, U1F - 0.03, BH, doors=[("e", 4.0, 6.5, 3.2)], mw="C2_Wall", mc="C2_Wall", thick=dict(s=0.0))
PXS = [BX0 + 6.0 * k for k in range(1, 6)]; PYS = [BY0 + 14.0 / 3, BY0 + 28.0 / 3]
for px in PXS:
    for py in PYS:
        pier(px, py, U1F, BH - 0.03, s=0.55)
    arch_y(px, BY0, PYS[0] - 0.55, U1F + 7.0, 4.3, w=0.6, d=0.55); arch_y(px, PYS[0] + 0.55, PYS[1] - 0.55, U1F + 7.0, 4.3, w=0.6, d=0.55)
    arch_y(px, PYS[1] + 0.55, BY1, U1F + 7.0, 4.3, w=0.6, d=0.55)
for py in PYS:
    xs_ = [BX0] + PXS + [BX1]
    for a_, b_ in zip(xs_[:-1], xs_[1:]):
        arch_x(py, a_ + (0.55 if a_ > BX0 else 0), b_ - (0.55 if b_ < BX1 else 0), U1F + 7.0, 4.3, w=0.6, d=0.55)
table((BX0 + BX1) / 2 + 1.0, (BY0 + BY1) / 2, U1F, 28.0, "x", w=1.5)
chair(BX0 + 1.4, (BY0 + BY1) / 2, U1F, (1, 0), high=True)
for k_, xx in enumerate(PXS[:-1]):
    kit("PF_LB_Chandelier", xx + 3.0, (BY0 + BY1) / 2, U1F + BH - 0.05, 0.0, 1.3)
    light(f"castle_banquet_{k_}", xx + 3.0, (BY0 + BY1) / 2, U1F + 5.5, 6000, 18, sh=k_ in (1, 3))
hearth(BX1 - 1.0, BX1, 39.5, 44.5, U1F, 2.8, U1F + BH, "n")                                         # great fireplace, east end
light("castle_banquet_fire", BX1 - 2.0, 42.0, U1F + 1.2, 4000, 14, col=(1.0, 0.45, 0.2), sh=True)
for xx in PXS:
    for yy in (BY0 + 0.8, BY1 - 0.8):
        candelabrum(xx, yy, U1F)
for xx in np.arange(BX0 + 3.0, BX1 - 2.0, 6.0):
    B(gF, xx - 0.8, xx + 0.8, BY0 + 0.01, BY0 + 0.07, U1F + 4.0, U1F + 7.5, "GB_Detail", False)     # banners
    B(gF, xx - 0.8, xx + 0.8, BY1 - 0.07, BY1 - 0.01, U1F + 4.0, U1F + 7.5, "GB_Detail", False)
room("Banquet Hall", BX0, BX1, BY0, BY1, U1F, BH - 0.03, sealed=True, note="vaulted hall of the undercroft (L-1), under the Great Hall")

KX0, KX1, KY0, KY1, KH = BX0, BX0 + 16.0, BY1 + 0.4, BY1 + 12.4, 8.0                               # Kitchen
liner(KX0, KX1, KY0, KY1, U1F - 0.03, KH, doors=[("n", 52.0, 54.0, 2.8)], mw="C2_Wall", mc="C2_Wall", thick=dict(w=0.0))
hearth(KX0, KX0 + 1.6, 53.0, 58.0, U1F, 2.6, U1F + KH, "s")                                        # hearth on the west wall
gF.cyl(KX0 + 0.8 + T[0], 55.5 + T[1], 0.5, U1F + 0.3 + T[2], U1F + 1.05 + T[2], "LB_Metal", 12, False)        # cauldron
B(gF, KX0 + 0.1, KX0 + 1.5, 55.45, 55.55, U1F + 1.4, U1F + 1.46, "LB_Metal", False)                          # spit
table(KX0 + 6.5, 55.4, U1F, 5.0, "y", w=1.2, seats=False)
table(KX0 + 11.0, 55.4, U1F, 5.0, "y", w=1.2, seats=False)
for xx in np.arange(KX0 + 3.0, KX1 - 0.8, 1.6):                                                    # shelves on the north side
    for zz in (1.0, 1.7, 2.4):
        B(gF, xx - 0.75, xx + 0.75, KY1 - 0.45, KY1 - 0.02, U1F + zz, U1F + zz + 0.05, "LB_GlossyWood", False)
    B(gF, xx - 0.8, xx + 0.8, KY1 - 0.5, KY1, U1F, U1F + 2.5, "GB_Stone", "only")
for xx, yy in ((KX1 - 0.6, KY0 + 0.6), (KX1 - 1.4, KY0 + 0.6), (KX1 - 0.6, KY0 + 1.4)):
    barrel_up(xx, yy, U1F)
light("castle_kitchen_fire", KX0 + 2.4, 55.5, U1F + 1.3, 4000, 12, col=(1.0, 0.45, 0.2), sh=True)
light("castle_kitchen", KX0 + 9.0, 55.4, U1F + 5.0, 4000, 14)
room("Kitchen", KX0, KX1, KY0, KY1, U1F, KH - 0.03, sealed=True)

LX0, LX1, LY0, LY1, LH = KX1 + 0.4, KX1 + 18.4, KY0, KY0 + 10.0, 5.0                              # Larder
liner(LX0, LX1, LY0, LY1, U1F - 0.03, LH, doors=[("n", 52.0, 54.0, 2.8)], mw="C2_Wall", mc="C2_Wall", thick=dict(w=0.0, s=0.0))
for xx in np.arange(LX0 + 1.0, LX1 - 0.5, 1.7):                                                    # shelves on both long walls
    for yy in (LY0 + 0.25, LY1 - 0.25):
        for zz in (0.6, 1.3, 2.0):
            B(gF, xx - 0.8, xx + 0.8, yy - 0.25, yy + 0.25, U1F + zz, U1F + zz + 0.05, "LB_GlossyWood", False)
        B(gF, xx - 0.85, xx + 0.85, yy - 0.3, yy + 0.3, U1F, U1F + 2.1, "GB_Stone", "only")
for yy in np.arange(LY0 + 2.2, LY1 - 1.5, 1.6):                                                    # hams and game on beams
    B(gF, LX0 + 1.5, LX1 - 1.5, yy - 0.03, yy + 0.03, U1F + 3.9, U1F + 3.96, "LB_GlossyWood", False)
    for xx in np.arange(LX0 + 2.0, LX1 - 1.5, 1.2):
        B(gF, xx - 0.12, xx + 0.12, yy - 0.15, yy + 0.15, U1F + 3.1, U1F + 3.9, "GB_Detail", False)
for xx, yy in (((LX0 + LX1) / 2, LY0 + 1.2), ((LX0 + LX1) / 2 + 0.8, LY0 + 1.2)):
    barrel_up(xx, yy, U1F)
light("castle_larder", (LX0 + LX1) / 2, (LY0 + LY1) / 2, U1F + 3.6, 2400, 12)
room("Larder", LX0, LX1, LY0, LY1, U1F, LH - 0.03, sealed=True)

CX0_, CX1_, CY0_, CY1_, CH = LX1 + 0.4, LX1 + 10.4, LY0, LY1, 5.0                                 # Wine and blood cellar
liner(CX0_, CX1_, CY0_, CY1_, U1F - 0.03, CH, mw="C2_Wall", mc="C2_Wall", thick=dict(s=0.0, w=0.0))
B(gR, BX1 + 0.4, CX1_ + 0.4, CY0_ - 0.4, CY0_, U1F - 0.43, U1F + CH + 0.4, "C2_Wall")
for xx in np.arange(CX0_ + 0.8, CX1_ - 0.5, 1.15):                                                 # casks along the north wall
    for zz in (0.55, 1.45):
        barrel_lying(xx, CY1_ - 0.6, U1F + zz, (0, 1))
    B(gF, xx - 0.5, xx + 0.5, CY1_ - 1.2, CY1_ - 0.05, U1F, U1F + 0.15, "LB_GlossyWood", False)
B(gF, CX0_ + 0.3, CX1_ - 0.2, CY1_ - 1.2, CY1_, U1F, U1F + 1.9, "GB_Stone", "only")
for k_, xx in enumerate((CX0_ + 2.4, CX1_ - 2.4)):                                                 # vats of blood
    gF.cyl(xx + T[0], CY0_ + 3.0 + T[1], 1.15, U1F + T[2], U1F + 2.1 + T[2], "LB_GlossyWood", 16, True)
    for zb in (0.3, 1.0, 1.75):
        gF.cyl(xx + T[0], CY0_ + 3.0 + T[1], 1.18, U1F + zb + T[2], U1F + zb + 0.08 + T[2], "LB_Metal", 16, False)
    gF.cyl(xx + T[0], CY0_ + 3.0 + T[1], 1.08, U1F + 2.04 + T[2], U1F + 2.08 + T[2], "GB_Detail", 16, False)
light("castle_cellar", (CX0_ + CX1_) / 2, (CY0_ + CY1_) / 2, U1F + 3.6, 2600, 12, col=(1.0, 0.45, 0.32))
room("Wine and blood cellar", CX0_, CX1_, CY0_, CY1_, U1F, CH - 0.03, sealed=True)
CUTS.append(dict(x=[BX0 - 0.5, CX1_ + 0.5], y=[BY0 - 0.5, KY1 + 0.5], z=[U1F - 0.6, U1F + BH + 0.5], what="undercroft L-1 (model foundations)"))

for nm_, (a0, a1, b0, b1, ztop) in {"Banquet Hall": (BX0, BX1, BY0, BY1, U1F + BH + 0.4), "Kitchen": (KX0, KX1, KY0, KY1, U1F + KH + 0.4),
                                    "Larder": (LX0, LX1, LY0, LY1, U1F + LH + 0.4), "cellar": (CX0_, CX1_, CY0_, CY1_, U1F + CH + 0.4)}.items():
    gg = [ground_rel(x_, y_) for x_ in np.arange(a0, a1, 1.0) for y_ in np.arange(b0, b1, 1.0)]
    print(f"  cover over {nm_}: {min(gg) - ztop:.2f} m (lowest ground {min(gg):.2f})")

# L-2 (0.0): corridor from the grand stair to the dungeon; Crypt 26 x 14 x 6 (spiral from the throne) and Dungeon
# (40 m corridor, 10 cells 3 x 3, guard room, interrogation room, pit cell); iron gate between crypt and dungeon
h_c = 4.0
QX0, QX1 = 7.4, 9.4                                                                                # north-south part of the corridor
RX0, RX1, RY0, RY1, RH = -19.6, 6.4, 48.6, 62.6, 6.0                                               # Crypt
DGY0, DGY1 = 49.6, 51.6                                                                            # dungeon corridor (y)
B(gR, SX1 + SW, QX1, SY0, YT, U2F - 0.4, U2F, "C2_Floor"); B(gR, QX0, QX1, YT, DGY0 - 0.4, U2F - 0.4, U2F, "C2_Floor")
B(gR, SX1 + SW, QX1 + 0.4, SY0 - 0.4, YT + 0.4, U2F + h_c, U2F + h_c + 0.4, "C2_Wall")
B(gR, QX0 - 0.4, QX1 + 0.4, YT, DGY0 - 0.4, U2F + h_c, U2F + h_c + 0.4, "C2_Wall")
B(gR, SX1 + SW, QX1 + 0.4, SY0 - 0.4, SY0, U2F - 0.4, U2F + h_c, "C2_Wall"); B(gR, QX1, QX1 + 0.4, SY0, DGY0 - 0.4, U2F - 0.4, U2F + h_c, "C2_Wall")
B(gR, SX1 + SW, QX0, YT, YT + 0.4, U2F - 0.4, U2F + h_c, "C2_Wall"); B(gR, QX0 - 0.4, QX0, YT, DGY0 - 0.4, U2F - 0.4, U2F + h_c, "C2_Wall")
torch("castle_corridor_l2", QX1 - 0.12, 41.0, U2F + 2.2, (1, 0), 500, 8)
room("Dungeon stair corridor", QX0, QX1, YT, DGY0 - 0.4, U2F, h_c, sealed=True)

liner(RX0, RX1, RY0, RY1, U2F - 0.03, RH, doors=[("n", DGY0, DGY1, 3.0), ("s", 52.0, 53.6, 2.8)], mw="C2_Wall", mc="C2_Wall",
      ceil=[(SPX - SPH, SPX + SPH, SPY - SPH, SPY + SPH)])
for px in (-10.0, -3.0, 4.0):
    for py in (53.2, 58.0):
        pier(px, py, U2F, RH - 0.03)
    arch_y(px, RY0, 52.75, U2F + 3.4, 2.3); arch_y(px, 53.65, 57.55, U2F + 3.4, 2.3); arch_y(px, 58.45, RY1, U2F + 3.4, 2.3)
sarcophagus(-6.5, 55.6, U2F, "x", 2.4, 1.1, lord=True)
for xx in (-12.5, -6.5, 0.5):
    sarcophagus(xx, RY0 + 0.6, U2F, "x")
for xx in (-6.5, 0.5):
    sarcophagus(xx, RY1 - 0.6, U2F, "x")
for xx in (-8.6, -4.4):
    for yy in (54.1, 57.1):
        candelabrum(xx, yy, U2F, 1.5)
light("castle_crypt_lord", -6.5, 55.6, U2F + 3.4, 2600, 12, sh=True, col=(1.0, 0.55, 0.3))
light("castle_crypt", -12.0, 52.0, U2F + 4.0, 1800, 14, col=(0.6, 0.68, 1.0))
light("castle_crypt_east", 2.5, 55.6, U2F + 4.0, 1400, 12, col=(0.6, 0.68, 1.0))
room("Crypt", RX0, RX1, RY0, RY1, U2F, RH, sealed=True, note="vaulted crypt (L-2) under the throne room; the secret spiral lands in it")
cg = G("SM_GB_Castle_CryptGate", "Environment/Castle")                                             # iron gate (open)
for yy in np.arange(DGY0 + 0.05, DGY1, 0.16):
    B(cg, RX1 + 0.15, RX1 + 0.2, yy - 0.025, yy + 0.025, U2F, U2F + 2.9, "GB_Metal")
MOVABLE.append(dict(name="SM_GB_Castle_CryptGate", pivot=W(RX1 + 0.2, DGY0, U2F), motion="hinge", note="iron gate crypt / dungeon"))

DX0_, DX1_, DH = RX1 + 0.4, RX1 + 40.4, 4.5                                                        # Dungeon corridor (40 m)
CW = 3.4                                                                                           # 5 cells each side, 3 x 3
cell_x = [DX0_ + 3.4 + CW * k for k in range(5)]
GX0, GX1 = cell_x[-1] + 3.4, cell_x[-1] + 3.4 + 10.0                                             # guard room (south), interrogation (north)
liner(DX0_, DX1_, DGY0, DGY1, U2F - 0.03, DH, mw="C2_Wall", mc="C2_Wall", thick=dict(s=0.0),
      doors=[("w", QX0, QX1, 2.8), ("w", GX0 + 3.5, GX0 + 6.5, 2.8), ("e", GX0 + 3.5, GX0 + 5.5, 2.8)]
      + [(sd, xa, xa + 3.0, 2.6) for xa in cell_x for sd in ("w", "e")])
for side, (ya, yb) in (("s", (DGY0 - 3.4, DGY0)), ("n", (DGY1, DGY1 + 3.4))):
    for k_, xa in enumerate(cell_x):
        xb = xa + 3.0
        y0c, y1c = (ya, ya + 3.0) if side == "s" else (yb - 3.0, yb)
        B(gR, xa, xb, y0c, y1c, U2F - 0.4, U2F, "C2_Floor")
        B(gR, xa - 0.4, xb + 0.4, (y0c - 0.4 if side == "s" else y1c), (y0c if side == "s" else y1c + 0.4), U2F - 0.4, U2F + 3.2, "C2_Wall")
        if k_ == 0:
            B(gR, xa - 0.4, xa, y0c, y1c, U2F - 0.4, U2F + 3.2, "C2_Wall")
        B(gR, xb, xb + 0.4, y0c, y1c, U2F - 0.4, U2F + 3.2, "C2_Wall")
        B(gR, xa - 0.4, xb + 0.4, min(y0c, y1c) - 0.4, max(y0c, y1c) + 0.4, U2F + 3.2, U2F + 3.6, "C2_Wall")
        xm = (xa + xb) / 2
        bars_y(xa, xb, (DGY0 - 0.2 if side == "s" else DGY1 + 0.2), U2F, 2.6, gaps=[(xm - 0.45, xm + 0.45)])
        yw = y0c + 0.05 if side == "s" else y1c - 0.09
        B(gF, xm - 0.8, xm - 0.76, yw, yw + 0.04, U2F + 0.8, U2F + 1.8, "LB_Metal", False)             # chains, straw
        B(gF, xm + 0.76, xm + 0.8, yw, yw + 0.04, U2F + 0.8, U2F + 1.8, "LB_Metal", False)
        B(gF, xa + 0.2, xb - 0.2, (y0c + 0.2 if side == "s" else y1c - 1.6), (y0c + 1.6 if side == "s" else y1c - 0.2), U2F, U2F + 0.08, "GB_Wood", False)
B(gR, GX0, GX1, DGY0 - 7.0, DGY0, U2F - 0.4, U2F, "C2_Floor"); B(gR, GX0, GX1, DGY1, DGY1 + 7.0, U2F - 0.4, U2F, "C2_Floor")
for (ya, yb) in ((DGY0 - 7.4, DGY0 - 7.0), (DGY1 + 7.0, DGY1 + 7.4)):
    B(gR, GX0 - 0.4, GX1 + 0.4, ya, yb, U2F - 0.4, U2F + DH, "C2_Wall")
for xw in (GX0 - 0.4, GX1):
    B(gR, xw, xw + 0.4, DGY0 - 7.0, DGY0, U2F - 0.4, U2F + DH, "C2_Wall"); B(gR, xw, xw + 0.4, DGY1, DGY1 + 7.0, U2F - 0.4, U2F + DH, "C2_Wall")
B(gR, GX0 - 0.4, GX1 + 0.4, DGY0 - 7.4, DGY0, U2F + DH, U2F + DH + 0.4, "C2_Wall"); B(gR, GX0 - 0.4, GX1 + 0.4, DGY1, DGY1 + 7.4, U2F + DH, U2F + DH + 0.4, "C2_Wall")
table((GX0 + GX1) / 2, DGY0 - 4.0, U2F, 3.0, "x", w=1.0)                                           # guard room
B(gF, GX1 - 0.3, GX1 - 0.05, DGY0 - 6.5, DGY0 - 2.5, U2F + 0.3, U2F + 2.4, "LB_GlossyWood", False)  # weapon rack
table((GX0 + GX1) / 2, DGY1 + 4.5, U2F, 2.4, "x", w=0.9, seats=False)                               # interrogation: the rack
for xx in (GX0 + 1.5, GX1 - 1.5):
    gF.cyl(xx + T[0], DGY1 + 6.2 + T[1], 0.35, U2F + T[2], U2F + 0.9 + T[2], "LB_Metal", 10, True)   # braziers
    B(gF, xx - 0.25, xx + 0.25, DGY1 + 5.95, DGY1 + 6.45, U2F + 0.9, U2F + 1.05, "GB_WinLit", False)
PX0 = GX1 + 0.4                                                                                    # pit cell (oubliette) at the end
B(gF, PX0 + 0.6, PX0 + 2.6, DGY0 + 0.1, DGY1 - 0.1, U2F, U2F + 0.04, "GB_Metal", False)
light("castle_guard_room", (GX0 + GX1) / 2, DGY0 - 3.5, U2F + 3.2, 900, 9)
light("castle_interrogation", (GX0 + GX1) / 2, DGY1 + 5.5, U2F + 1.6, 900, 8, col=(1.0, 0.4, 0.2))
for k_, xx in enumerate(np.arange(DX0_ + 4.0, DX1_, 9.0)):                                         # lanterns on chains
    ym = (DGY0 + DGY1) / 2
    B(gF, xx - 0.02, xx + 0.02, ym - 0.02, ym + 0.02, U2F + 3.3, U2F + DH, "LB_Metal", False)
    B(gF, xx - 0.13, xx + 0.13, ym - 0.13, ym + 0.13, U2F + 3.0, U2F + 3.3, "GB_WinLit", False)
    light(f"castle_dungeon_{k_}", xx, ym, U2F + 2.8, 600, 9, col=(1.0, 0.55, 0.25))
room("Dungeon", DX0_, DX1_, DGY0, DGY1, U2F, DH - 0.03, sealed=True, note="40 m corridor, 10 cells 3 x 3, guard room, interrogation room, pit cell")
room("Guard room", GX0, GX1, DGY0 - 7.0, DGY0, U2F, DH - 0.03, sealed=True)
room("Interrogation room", GX0, GX1, DGY1, DGY1 + 7.0, U2F, DH - 0.03, sealed=True)
CUTS.append(dict(x=[RX0 - 0.5, DX1_ + 0.5], y=[SY0 - 0.5, RY1 + 0.5], z=[U2F - 0.6, U2F + RH + 0.5], what="undercroft L-2 (model foundations)"))

# ---------------------------------------------------------------- secret tunnel: crypt -> foot of the south cliff
# three legs inside the crag (stairs 0.2 / 0.3, then level), always 3 m+ under the landscape; hidden door at the exit
TW, TH_, TT = 2.0, 4.0, 0.6
ZE = -86.0                                                                                         # last leg, under the cliff foot
tun = G("SM_GB_Castle_Tunnel", "Environment/Castle")


def sheared(g, xa, xb, ya, yb, za0, za1, zb0, zb1, mat, col=True):
    """Box between x = xa (z za0..za1) and x = xb (z zb0..zb1), y ya..yb: a sloped wall or vault slab (convex)."""
    v = [(xa, ya, za0), (xb, ya, zb0), (xb, yb, zb0), (xa, yb, za0), (xa, ya, za1), (xb, ya, zb1), (xb, yb, zb1), (xa, yb, za1)]
    g.add([(a + T[0], b + T[1], c + T[2]) for a, b, c in v], [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]], mat, col)


def tunnel_leg(p0, p1, z0, z1, y):
    """Straight leg along x from x=p0 (floor z0) to x=p1 (z1) at y: floor (stairs when sloped), walls and vault slab."""
    xa, xb = sorted((p0, p1)); za, zb = (z0, z1) if p0 < p1 else (z1, z0)
    if abs(z1 - z0) > 0.05:
        lo_end = p0 if z0 < z1 else p1; hi_end = p1 if z0 < z1 else p0
        tun.stairs((lo_end + T[0], y + T[1]), (np.sign(hi_end - lo_end), 0), TW, min(z0, z1) + T[2], max(z0, z1) + T[2], "C2_Floor",
                   step_h=0.2, run=0.3, solid=False)
    else:
        B(tun, xa, xb, y - TW / 2, y + TW / 2, z0 - 0.4, z0, "C2_Floor")
    for ya, yb in ((y - TW / 2 - TT, y - TW / 2), (y + TW / 2, y + TW / 2 + TT)):
        sheared(tun, xa, xb, ya, yb, za - 0.6, za + TH_, zb - 0.6, zb + TH_, "C2_Wall")
    sheared(tun, xa, xb, y - TW / 2 - TT, y + TW / 2 + TT, za + TH_, za + TH_ + 0.4, zb + TH_, zb + TH_ + 0.4, "LB_Stone")


def tunnel_turn(xa, xb, ya_leg, yb_leg, z, end_x):
    """Landing joining two legs (ya_leg, yb_leg: their axes) between x = xa and xb, closed at end_x."""
    y0, y1 = ya_leg - TW / 2, yb_leg + TW / 2
    B(tun, xa, xb, y0, y1, z - 0.4, z, "C2_Floor")
    B(tun, xa, xb, y0 - TT, y0, z - 0.6, z + TH_, "C2_Wall"); B(tun, xa, xb, y1, y1 + TT, z - 0.6, z + TH_, "C2_Wall")
    ex0, ex1 = (end_x - TT, end_x) if end_x <= xa + 1e-6 else (end_x, end_x + TT)
    B(tun, ex0, ex1, y0 - TT, y1 + TT, z - 0.6, z + TH_ + 0.4, "C2_Wall")
    B(tun, min(xa, ex0), max(xb, ex1), y0 - TT, y1 + TT, z + TH_, z + TH_ + 0.4, "LB_Stone")


Y1_, Y2_, Y3_ = 52.8, 56.1, 59.4
X_A, X_B = -23.6, -95.6
z_1 = U2F - (X_A - X_B) / 0.3 * 0.2                                                                # bottom of leg 1
X_C = X_B + (z_1 - ZE) / 0.2 * 0.3                                                                 # leg 2 climbs back to X_C
X_EX = -117.5                                                                                      # exit cell at the foot of the cliff
tunnel_leg(RX0 - 0.4, X_A, U2F, U2F, Y1_)
tunnel_leg(X_A, X_B, U2F, z_1, Y1_)
tunnel_turn(X_B - 3.4, X_B, Y1_, Y2_, z_1, X_B - 3.4)
tunnel_leg(X_B, X_C, z_1, ZE, Y2_)
tunnel_turn(X_C, X_C + 3.4, Y2_, Y3_, ZE, X_C + 3.4)
tunnel_leg(X_C, X_EX + SPH, ZE, ZE, Y3_)
# exit: a squat stone cell at the foot of the cliff (walls of 1.6 m: they hide the edge of the landscape cut over its
# stair), a spiral from the tunnel up to its floor, the hidden door (Movable, wood) on the valley side
GE = round(ground_rel(X_EX - SPH - SW - 1.0, Y3_), 2)                                              # ground at the door
ex0, ex1, ey0, ey1 = X_EX - SPH, X_EX + SPH, Y3_ - SPH, Y3_ + SPH
gt_ = GE + 3.4
tun.wall("x", ey0 - SW + T[1], ey0 + T[1], ex0 - SW + T[0], ex1 + SW + T[0], ZE - 0.4 + T[2], gt_ + T[2], "C2_Wall")
tun.wall("x", ey1 + T[1], ey1 + SW + T[1], ex0 - SW + T[0], ex1 + SW + T[0], ZE - 0.4 + T[2], gt_ + T[2], "C2_Wall")
tun.wall("y", ex0 - SW + T[0], ex0 + T[0], ey0 + T[1], ey1 + T[1], ZE - 0.4 + T[2], gt_ + T[2], "C2_Wall",
         holes=[(Y3_ - 0.7 + T[1], Y3_ + 0.7 + T[1], GE + T[2], GE + 2.5 + T[2])])                  # door (valley side)
tun.wall("y", ex1 + T[0], ex1 + SW + T[0], ey0 + T[1], ey1 + T[1], ZE - 0.4 + T[2], gt_ + T[2], "C2_Wall",
         holes=[(Y3_ - TW / 2 + T[1], Y3_ + TW / 2 + T[1], ZE + T[2], ZE + 3.0 + T[2])])            # from the tunnel
B(tun, ex0, ex1, ey0, ey1, ZE - 0.4, ZE, "C2_Floor")
B(tun, ex0 - SW - 0.3, ex1 + SW + 0.3, ey0 - SW - 0.3, ey1 + SW + 0.3, gt_, gt_ + 0.5, "LB_Stone")      # roof slab
tun.pyramid(ex0 - SW - 0.3 + T[0], ex1 + SW + 0.3 + T[0], ey0 - SW - 0.3 + T[1], ey1 + SW + 0.3 + T[1], gt_ + 0.5 + T[2], gt_ + 2.6 + T[2], "C2_Roof")
nst_ = int(round((GE - ZE) / 0.2)); th_ = (179.0 + 360.0) / (nst_ + 0.5)                            # enters from +x, ends at -x
spiral_stair(tun, X_EX, Y3_, 1.95, 0.3, ZE, GE, th_, th_)
B(tun, ex0 - SW - 1.6, ex0 - SW, Y3_ - 1.0, Y3_ + 1.0, GE - 0.4, GE + 0.03, "LB_Stone")              # doorstep
dr = G("SM_GB_Castle_TunnelDoor", "Environment/Castle")
B(dr, ex0 - SW + 0.15, ex0 - SW + 0.3, Y3_ - 0.68, Y3_ + 0.68, GE + 0.01, GE + 2.48, "FC_WoodPlanks")
MOVABLE.append(dict(name="SM_GB_Castle_TunnelDoor", pivot=W(ex0 - SW + 0.22, Y3_ - 0.68, GE), motion="hinge",
                    note="hidden door of the secret tunnel: stone cell at the foot of the south cliff; opens inward"))
VOIDS.append([round(ex0 - 0.8 + T[0], 2), round(ex1 + 0.8 + T[0], 2), round(ey0 - 0.8 + T[1], 2), round(ey1 + 0.8 + T[1], 2), round(ZE - 0.18 + T[2], 2)])
APRONS.append([round(ex0 - SW - 2.0 + T[0], 2), round(Y3_ + T[1], 2), round(GE + T[2], 2), 1.6, 4.0])
light("castle_tunnel_exit", X_EX, Y3_, GE - 1.0, 400, 8, col=(1.0, 0.5, 0.25))
for k_, xx in enumerate(np.arange(X_A - 10.0, X_B + 5.0, -24.0)):
    torch(f"castle_tunnel_a{k_}", xx, Y1_ + TW / 2 - 0.12, U2F - (X_A - xx) / 0.3 * 0.2 + 2.0, (0, 1), 350, 8)
for k_, xx in enumerate(np.arange(X_C + 0.0, X_EX + 6.0, -24.0)):
    torch(f"castle_tunnel_c{k_}", xx, Y3_ + TW / 2 - 0.12, ZE + 2.0, (0, 1), 350, 8)
room("Secret tunnel (head)", X_A - 3.0, RX0 - 0.4, Y1_ - TW / 2, Y1_ + TW / 2, U2F, TH_, sealed=True)
room("Secret tunnel (exit)", X_EX + SPH + SW, X_EX + SPH + SW + 8.0, Y3_ - TW / 2, Y3_ + TW / 2, ZE, TH_, sealed=True)
X_PORT = ex0 - SW
TUNNEL_LEN = round((RX0 - 0.4 - X_A) + math.hypot(X_A - X_B, U2F - z_1) + 3.4 + math.hypot(X_C - X_B, z_1 - ZE) + 3.4 + (X_C - X_EX), 1)
CUTS.append(dict(x=[X_A - 1.0, RX0], y=[Y1_ - 2.0, Y1_ + 2.0], z=[U2F - 1.0, U2F + TH_ + 1.0], what="tunnel head (model foundations)"))

# ---------------------------------------------------------------- walk-test triangles of the shell (cut boxes subtracted)
tri_src = f"{ROOT}/assets/castle20/tris.npz"
if os.path.exists(tri_src):
    TR = np.load(tri_src)["tris"].astype(np.float64)
    TR2, touched = subtract(TR, CUTS)
    np.savez_compressed(f"{ROOT}/assets/castle20/tris_world.npz", tris=(TR2 + T).astype(np.float32))
    print("shell triangles for the walk test:", len(TR2), "| triangles cut or clipped (gate leaves, doors, room clutter):", touched)

# ---------------------------------------------------------------- outputs
json.dump([g.to_json() for g in groups], open(f"{ROOT}/greybox/castle_groups.json", "w"))
meta = dict(rooms=ROOMS, voids=VOIDS, void_paths=[], void_discs=[], aprons=APRONS, movable=MOVABLE, lights=LIGHTS, piers=PIERS,
            tunnel_length_m=TUNNEL_LEN, tunnel_exit=W(X_PORT - 0.5, Y3_, GE),
            undercroft=dict(L1_floor=round(U1F + T[2], 2), L2_floor=round(U2F + T[2], 2), note="under the terrain of the palace (no landscape hole); voids only over the two shafts"),
            model=dict(name="Castle 2.0 (EldersCrawler)", scale=SC, origin=T.round(3).tolist(), gate=[round(v, 2) for v in gate_w],
                       gate_cut=GATE_CUT, cuts=CUTS),
            castle_plate=dict(origin=T.round(3).tolist(), file="data/castle20_plate.npz", min_rel=8.45, note="crag top = origin z + hill"),
            bridge=dict(start=[742.0, 80.0, z0], end=[round(RIM[0], 2), round(RIM[1], 2), round(z1, 2)], length_m=round(L, 1),
                        heading_deg=round(math.degrees(math.atan2(u[1], u[0])), 1)))
# hero views of the design document that framed the greybox castle, re-aimed at the model (render_hero.py applies them)
SPIRE = W(17.4, 60.6, 60.0)                                                  # palace tower (top of the model at +70.7)
meta["hero_views"] = {
    "V1": dict(look_at=SPIRE), "V5": dict(look_at=SPIRE),
    "V2": dict(name="Castle walls toward the city", camera=W(-97.0, 20.0, 20.1), look_at=[-320, -556, 80]),
    "V3": dict(camera=[*(BR0 + u * L * 0.45).round(2).tolist(), round(z0 + (z1 - z0) * 0.45 + 1.7, 2)], look_at=W(-0.3, -48.2, 12.0)),
    "V4": dict(camera=W(2.0, 29.0, 22.9), look_at=W(2.0, 50.0, 24.5)),
    "V6": dict(look_at=W(-3.0, -10.0, 30.0)), "V8": dict(look_at=W(0.0, 10.0, 40.0))}
# spawn marker of the design document in the castle: the court is now on the model's hill (11 m higher)
meta["spawn_overrides"] = {"castle_inner_ward": [728.0, 318.0, round(gz(728.0, 318.0) + 1.0, 2)]}
json.dump(meta, open(f"{ROOT}/greybox/castle_meta.json", "w"), indent=1)
json.dump(PL, open(f"{ROOT}/data/placements_castle.json", "w"), indent=0)
nav = dict(name="castle", bbox=[590, 840, 66, 385, 100, 300], groups=["greybox/castle_groups.json"], meta=["greybox/castle_meta.json"],
           meshes=["assets/castle20/tris_world.npz"], landscape_crust=1.0,
           exclude=["SM_GB_Castle_GateLeafW", "SM_GB_Castle_GateLeafE", "SM_GB_Castle_SecretPanel", "SM_GB_Castle_CryptGate", "SM_GB_Castle_TunnelDoor"],
           seeds=[[742.0, 88.0, 199.1]],
           probes={"bridge_mid": [*(BR0 + u * L * 0.5).round(2).tolist(), round(z0 + (z1 - z0) * 0.5, 2)],
                   "forecourt": [round(gate_w[0], 2), 215.0, round(gz(gate_w[0], 215.0), 2)],
                   "gate_passage": W(-0.3, -44.0, 8.5), "lower_court": W(0.0, -20.0, pz(0.0, -20.0)),
                   "palace_court": W(-30.0, 40.0, pz(-30.0, 40.0)),
                   "throne_dais": W(TT0 + 1.5, yc + 2.0, DAIS), "throne_door": W(2.25, 50.5, fz + 0.03),
                   "secret_stair_top": W(SPX + 1.2, SPY + 0.6, DAIS), "spiral_foot": W(SPX + SPH + SW + 0.8, SPY, U2F),
                   "grand_stair_mid": W(-6.4, 45.5, north_z[0][0]), "tunnel_turn_1": W(X_B - 1.7, (Y1_ + Y2_) / 2, z_1),
                   "tunnel_turn_2": W(X_C + 1.7, (Y2_ + Y3_) / 2, ZE), "tunnel_outside": W(X_PORT - 2.5, Y3_, GE), "exit_spiral_top": W(X_EX - 1.2, Y3_, GE)},
           levels={"courts": [200, 212], "palace": [212, 226]})
json.dump(nav, open(f"{ROOT}/greybox/nav_castle.json", "w"), indent=1)
print(f"castle: Castle 2.0 at {T.tolist()} (scale {SC:.0f}), gate {[round(float(v), 1) for v in gate_w]}, bridge {L:.0f} m "
      f"heading {meta['bridge']['heading_deg']} deg, {len(ROOMS)} rooms, {len(LIGHTS)} lights, tunnel {TUNNEL_LEN} m, "
      f"voids {len(VOIDS)}, aprons {len(APRONS)}, cuts {len(CUTS)}")
