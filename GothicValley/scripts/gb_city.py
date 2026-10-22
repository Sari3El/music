# City greybox (section 6 + Appendix A city): ring wall, 16 towers, 4 gates (North double gate + barbican), Great Church,
# Noble Manor, town hall, guild hall, watch barracks, market, covered stairs, 295 plots from the city plan (closed modular
# houses, 16 variants) and the enterable interiors. World metres, +X north, +Y east.
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gb_lib import Group, rect_minus
from tlib import sample

ROOT = sys.argv[1]
HN = f"{ROOT}/terrain/H_natural_4033.npy"
H = np.load(HN if os.path.exists(HN) else f"{ROOT}/terrain/H_4033.npy")
M = json.load(open(f"{ROOT}/data/layout_manifest.json"))
C = M["city"]
gz = lambda x, y: float(sample(H, x, y)[0])
CX, CY = C["wall_ellipse"]["centre"]
RA, RB = C["wall_ellipse"]["radii_ns_ew"]
ROOMS, VOIDS, MOVABLE, ENTER = [], [], [], []
F = "Environment/City"
RSP = 0.45 + 2.2                                                  # spiral stairs: 2.2 m treads


def R(name, x0, x1, y0, y1, z0, h, kind=None):
    r = dict(name=name, x0=x0, x1=x1, y0=y0, y1=y1, z0=z0, z1=z0 + h)
    if kind:
        r["interior"] = kind
    ROOMS.append(r)
    return r


def obox(g, c, t, ht, hn, z0, z1, mat, col=True):
    """Box oriented along unit tangent t (half-lengths ht along t, hn across)."""
    t = np.array(t, float) / np.linalg.norm(t); n = np.array([-t[1], t[0]])
    c = np.array(c, float)
    pts = [c - t * ht - n * hn, c + t * ht - n * hn, c + t * ht + n * hn, c - t * ht + n * hn]
    if (pts[1] - pts[0])[0] * (pts[3] - pts[0])[1] - (pts[1] - pts[0])[1] * (pts[3] - pts[0])[0] < 0:
        pts = pts[::-1]
    g.poly_prism([tuple(p) for p in pts], z0, z1, mat, col)


def ell(th):
    return np.array([CX + RA * math.cos(th), CY + RB * math.sin(th)])


def ell_th(x, y):
    return math.atan2((y - CY) / RB, (x - CX) / RA)


def ell_dist(x, y):
    """Approximate distance (m) from (x, y) inward to the wall centre line (positive inside)."""
    er = math.hypot((x - CX) / RA, (y - CY) / RB)
    th = ell_th(x, y)
    rad = math.hypot(RA * math.cos(th), RB * math.sin(th))
    return (1 - er) * rad


# ====================================================================== ring wall, wall-walk, towers, gates
walls = Group("SM_GB_City_Walls", F)
GATES = {k: v for k, v in C["gates"].items()}
GATE_TH = {k: ell_th(v[0], v[1]) for k, v in GATES.items()}
GATE_HALF = {"north": 9.0, "east": 8.0, "west": 8.0, "water": 5.0}           # half-width of each gatehouse along the wall
NSEG = 160
th = np.linspace(0, 2 * math.pi, NSEG + 1)
P = np.array([ell(t) for t in th])
G = np.array([gz(*p) for p in P])
Gs = np.convolve(np.concatenate([G[-4:-1], G, G[1:4]]), np.ones(7) / 7, mode="valid")   # smoothed ground along the wall
WALL_H = 10.5                                                                    # 9-12 m
TOP = Gs + WALL_H


def near_gate(p, extra=0.0):
    for k, (gx, gy, _) in GATES.items():
        if math.hypot(p[0] - gx, p[1] - gy) < GATE_HALF[k] + extra:
            return k
    return None


def clip_gates(a, b, za, zb):
    """Pieces of segment a-b outside the gatehouses (each gate removes a disc of radius half-width - 0.4)."""
    pieces = [(0.0, 1.0)]
    for k, (gx, gy, _) in GATES.items():
        r = GATE_HALF[k] - 0.4
        d = b - a; f = a - np.array([gx, gy])
        A_, B_, C_ = d @ d, 2 * f @ d, f @ f - r * r
        disc = B_ * B_ - 4 * A_ * C_
        if disc <= 0:
            continue
        t0, t1 = (-B_ - math.sqrt(disc)) / (2 * A_), (-B_ + math.sqrt(disc)) / (2 * A_)
        pieces = [q for (p0, p1) in pieces for q in ((p0, min(p1, t0)), (max(p0, t1), p1)) if q[1] - q[0] > 1e-3]
    return [(a + (b - a) * p0, a + (b - a) * p1, za + (zb - za) * p0, za + (zb - za) * p1) for p0, p1 in pieces]


# 16 towers spread along the perimeter, clear of the gates
cands = [i for i in range(NSEG) if near_gate(P[i], 30.0) is None]
TW = [cands[int(round(k))] for k in np.linspace(0, len(cands) - 1, 17)[:-1]]
STAIR_SEG = {TW[k] + 3: k for k in (1, 5, 9, 13)}
TWC = []                                                                         # tower centres (1 m outside the line)
for i in TW:
    tt = (P[i + 1] - P[i - 1]); tt /= np.linalg.norm(tt); no = np.array([tt[1], -tt[0]])
    if np.dot(no, P[i] - np.array([CX, CY])) < 0:
        no = -no
    TWC.append(P[i] + no * 1.0)


def clip_towers(a, b, za, zb, r=3.9):
    pieces = [(0.0, 1.0)]
    for cxy in TWC:
        d = b - a; f = a - cxy
        A_, B_, C_ = d @ d, 2 * f @ d, f @ f - r * r
        disc = B_ * B_ - 4 * A_ * C_
        if disc <= 0:
            continue
        t0, t1 = (-B_ - math.sqrt(disc)) / (2 * A_), (-B_ + math.sqrt(disc)) / (2 * A_)
        pieces = [q for (p0, p1) in pieces for q in ((p0, min(p1, t0)), (max(p0, t1), p1)) if q[1] - q[0] > 1e-3]
    return [(a + (b - a) * p0, a + (b - a) * p1, za + (zb - za) * p0, za + (zb - za) * p1) for p0, p1 in pieces]
for i in range(NSEG):
  for a, b, za, zb in clip_gates(P[i], P[i + 1], TOP[i], TOP[i + 1]):
    mid = (a + b) / 2
    t = (b - a) / np.linalg.norm(b - a); n_out = np.array([t[1], -t[0]])          # outward normal
    if np.dot(n_out, mid - np.array([CX, CY])) < 0:
        n_out = -n_out
    gmin = min(G[i], G[i + 1]) - 2.0
    walls.ramp(tuple(a), tuple(b), 2.6, za, zb, max(za, zb) - gmin, "GB_Stone")                  # wall 2.5 m
    walls.ramp(tuple(a - n_out * 1.75), tuple(b - n_out * 1.75), 1.0, za, zb, 0.5, "GB_Timber")   # corbelled walk (3.2 m)
    for a2, b2, za2, zb2 in clip_towers(a, b, za, zb):                                            # parapets stop at towers
        walls.ramp(tuple(a2 + n_out * 1.1), tuple(b2 + n_out * 1.1), 0.4, za2 + 1.1, zb2 + 1.1, 1.1, "GB_Stone")
        L2 = np.linalg.norm(b2 - a2)
        for s_ in np.arange(1.0, L2 - 1.0, 2.6):                                                 # merlons
            p_ = a2 + t * s_ + n_out * 1.1
            obox(walls, p_, t, 0.6, 0.2, za2 + (zb2 - za2) * s_ / L2 + 1.1, za2 + (zb2 - za2) * s_ / L2 + 2.1, "GB_Stone")
        if i not in STAIR_SEG:
            walls.ramp(tuple(a2 - n_out * 2.1), tuple(b2 - n_out * 2.1), 0.3, za2 + 1.1, zb2 + 1.1, 1.1, "GB_Timber")  # inner rail
    if i in STAIR_SEG:                                                                            # stair landing, no rail
        walls.ramp(tuple(a - n_out * 3.6), tuple(b - n_out * 3.6), 3.2, za, zb, 0.4, "GB_Timber")
        walls.ramp(tuple(a - n_out * 5.35), tuple(b - n_out * 5.35), 0.3, za + 1.1, zb + 1.1, 1.1, "GB_Timber")
        obox(walls, b - n_out * 3.75 - t * 0.15, t, 0.15, 1.5, zb, zb + 1.1, "GB_Timber")
    if i % 9 == 4:                                                                                # timber hoardings
        walls.ramp(tuple(a + n_out * 1.9), tuple(b + n_out * 1.9), 1.2, za + 3.2, zb + 3.2, 0.2, "GB_Timber", col=False)
        walls.ramp(tuple(a + n_out * 2.5), tuple(b + n_out * 2.5), 0.15, za + 3.2, zb + 3.2, 3.2, "GB_Timber", col=False)
TOWERS = []
for k, i in enumerate(TW):
    c = P[i]; t = (P[i + 1] - P[i - 1]); t /= np.linalg.norm(t)
    n_out = np.array([t[1], -t[0]])
    if np.dot(n_out, c - np.array([CX, CY])) < 0:
        n_out = -n_out
    c = c + n_out * 1.0                                                              # towers project outside the wall
    ht = 18.0 + (k * 7 % 8)                                                          # 18-25 m
    zf = TOP[i]
    g0 = gz(*c) - 2.0
    # hollow square tower 8 x 8: walls 1 m, a room at wall-walk level with doors on both wall-walk sides
    for s_ in (-1, 1):
        obox(walls, c + n_out * 3.5 * s_, t, 4.0, 0.5, g0, zf + ht - (zf - Gs[i]), "GB_Stone")   # outer / inner faces
    for s_ in (-1, 1):                                                               # side walls cross the walk: doors
        cc = c + t * 3.5 * s_
        obox(walls, cc, t, 0.5, 3.0, g0, zf - 0.3, "GB_Stone")
        obox(walls, cc, t, 0.5, 3.0, zf + 3.2, Gs[i] + ht, "GB_Stone")                        # door 3.2 m high
        obox(walls, cc + n_out * 1.65, t, 0.5, 1.35, zf - 0.3, zf + 3.2, "GB_Stone")             # outer jamb (walk side open)
    obox(walls, c, t, 3.0, 3.0, zf - 0.3, zf, "GB_Floor")                                        # floor at walk level
    obox(walls, c, t, 4.0, 4.0, Gs[i] + ht, Gs[i] + ht + 0.4, "GB_Stone")
    pyr = [tuple(c + t * 4.4 * a_ + n_out * 4.4 * b_) for a_, b_ in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    xs_, ys_ = [p[0] for p in pyr], [p[1] for p in pyr]
    walls.add([(*p, Gs[i] + ht + 0.4) for p in pyr] + [(c[0], c[1], Gs[i] + ht + 7.0)],
              [[0, 1, 2, 3][::-1] if (pyr[1][0] - pyr[0][0]) * (pyr[3][1] - pyr[0][1]) - (pyr[1][1] - pyr[0][1]) * (pyr[3][0] - pyr[0][0]) > 0 else [0, 1, 2, 3],
               [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]], "GB_Tile")
    TOWERS.append(dict(xy=[round(float(c[0]), 1), round(float(c[1]), 1)], height=ht, walk_z=round(float(zf), 2)))
# wall-walk stairs (2.5 m, along the inner face) near four towers
WALK_STAIRS = []
for k in (1, 5, 9, 13):
    i = TW[k] + 3
    a = P[i]; t = (P[i + 1] - P[i - 1]); t /= np.linalg.norm(t)
    n_out = np.array([t[1], -t[0]])
    if np.dot(n_out, a - np.array([CX, CY])) < 0:
        n_out = -n_out
    top = TOP[i]; foot = gz(*(a - n_out * 4.0))
    for _ in range(2):
        run = (top - foot) / 0.2 * 0.3
        start = a - n_out * 3.85 - t * run
        foot = gz(*start)
    walls.stairs(tuple(start), tuple(t), 2.5, foot, top, "GB_Stone", 0.2, 0.3)
    WALK_STAIRS.append([round(float(start[0]), 1), round(float(start[1]), 1), round(float(foot), 1)])

# gatehouses
gates = Group("SM_GB_City_Gates", F)
GATE_INFO = {}
for k, (gx, gy, gzz) in GATES.items():
    thg = GATE_TH[k]
    c = ell(thg)
    t = np.array([-RA * math.sin(thg), RB * math.cos(thg)]); t /= np.linalg.norm(t)
    n_out = np.array([t[1], -t[0]])
    if np.dot(n_out, c - np.array([CX, CY])) < 0:
        n_out = -n_out
    z = gz(gx, gy)
    i = int(round(thg % (2 * math.pi) / (2 * math.pi) * NSEG)) % NSEG
    walk = TOP[i]
    hw = GATE_HALF[k]
    pw = 2.5 if k == "water" else 3.0                                         # passage half-width (5-6 m)
    ph = 4.5 if k == "water" else 6.0
    depth = 7.0 if k == "water" else 9.0
    tower_h = {"north": 30.0, "east": 20.0, "west": 20.0, "water": 14.0}[k]
    for s_ in (-1, 1):                                                         # side blocks of the gatehouse
        cc = c + t * s_ * (pw + (hw - pw) / 2)
        obox(gates, cc, t, (hw - pw) / 2, depth, z - 2.0, z + tower_h, "GB_Stone")
    obox(gates, c, t, pw, depth, z + ph, z + tower_h, "GB_Stone")             # over the passage
    obox(gates, c, t, hw + 0.4, depth + 0.4, z + tower_h, z + tower_h + 0.4, "GB_Stone")
    pyr = [tuple(c + t * (hw + 0.6) * a_ + n_out * (depth + 0.6) * b_) for a_, b_ in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    gates.add([(*p, z + tower_h + 0.4) for p in pyr] + [(c[0], c[1], z + tower_h + 9.0)],
              [[3, 2, 1, 0], [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]], "GB_Tile")
    zi, zo = gz(*(c - n_out * (depth + 0.5))), gz(*(c + n_out * (depth + 0.5)))
    gates.ramp(tuple(c - n_out * (depth + 0.6)), tuple(c + n_out * (depth + 0.6)), 2 * pw + 0.4, zi + 0.05, zo + 0.05, 1.2, "GB_Stone")  # passage floor follows the slope
    dv = Group(f"SM_GB_City_GateDoors_{k.capitalize()}", F)                    # iron-studded doors (movable)
    obox(dv, c - n_out * (depth - 1.0), t, pw, 0.15, z, z + ph - 0.2, "GB_Wood")
    MOVABLE.append(dict(name=dv.name, pivot=[round(float(c[0]), 2), round(float(c[1]), 2), round(z, 2)]))
    GATE_INFO[k] = dict(centre=[round(float(c[0]), 1), round(float(c[1]), 1), round(z, 1)], tower_m=tower_h, passage_w=2 * pw,
                        passage_h=ph, doors=dv)
    if k == "north":                                                           # double gate: portcullis + outer barbican
        pc = Group("SM_GB_City_NorthPortcullis", F)
        obox(pc, c + n_out * (depth - 1.5), t, pw, 0.1, z, z + ph - 0.2, "GB_Metal")
        MOVABLE.append(dict(name=pc.name, pivot=[round(float(c[0]), 2), round(float(c[1]), 2), round(z, 2)]))
        GATE_INFO[k]["portcullis"] = pc
        for s_ in (-1, 1):                                                     # barbican side walls 26 m, 9 m high
            cc = c + n_out * (depth + 13.0) + t * s_ * (pw + 4.5)
            obox(gates, cc, t, 1.25, 13.0, z - 2.0, z + 9.0, "GB_Stone")
        cc = c + n_out * (depth + 26.0)
        for s_ in (-1, 1):
            obox(gates, cc + t * s_ * (pw + 2.6), t, 2.6, 2.0, z - 2.0, z + 14.0, "GB_Stone")
        obox(gates, cc, t, pw + 5.2, 2.0, z + ph, z + 14.0, "GB_Stone")
        bd = Group("SM_GB_City_GateDoors_Barbican", F)
        obox(bd, cc - n_out * 1.0, t, pw, 0.15, z, z + ph - 0.2, "GB_Wood")
        MOVABLE.append(dict(name=bd.name, pivot=[round(float(cc[0]), 2), round(float(cc[1]), 2), round(z, 2)]))
        GATE_INFO[k]["barbican_doors"] = bd
    if k == "east":                                                            # toll booth outside the gate
        tb = c + n_out * (depth + 7.0) + t * (pw + 5.0)
        obox(gates, tb, t, 2.5, 2.0, gz(*tb) - 0.5, gz(*tb) + 3.0, "GB_Wood")
        obox(gates, tb, t, 3.0, 2.5, gz(*tb) + 3.0, gz(*tb) + 3.3, "GB_Roof")

# ====================================================================== Great Church (Appendix boxes, floor +35)
ch = C["great_church"]
ZC = float(ch["floor_z"])
church = Group("SM_GB_Church_GreatChurch", "Environment/Church")
nv, cr, tw_ = ch["nave"], ch["choir"], ch["tower"]
NX0, NX1, NY0, NY1 = nv["x"][0], nv["x"][1], nv["y"][0], nv["y"][1]
CX0, CX1, CY0, CY1 = cr["x"][0], cr["x"][1], cr["y"][0], cr["y"][1]
TX0, TX1, TY0, TY1 = tw_["x"][0], tw_["x"][1], tw_["y"][0], tw_["y"][1]
VAULT = float(nv["vault_m"])
EAVE = ZC + VAULT + 2.0
nave = R("Church nave (hall)", NX0, NX1, NY0, NY1, ZC, VAULT, "church")
choir = R("Church choir", CX0, CX1, CY0, CY1, ZC, VAULT, "church")
# nave walls: south porch door, north portal, west wall opens to the tower hall, east wall = triumphal arch to the choir
church.wall("y", NX0 - 0.8, NX0 + 0.8, NY0 - 0.8, NY1 + 0.8, ZC - 0.3, EAVE, "GB_Church", holes=[(-526.0, -522.0, ZC, ZC + 5.0)] +
            [(y, y + 2.4, ZC + 6, ZC + 18) for y in (-546.0, -538.0, -522.0, -515.0)])
church.wall("y", NX1 - 0.8, NX1 + 0.8, NY0 - 0.8, NY1 + 0.8, ZC - 0.3, EAVE, "GB_Church", holes=[(-526.0, -522.0, ZC, ZC + 5.0)] +
            [(y, y + 2.4, ZC + 6, ZC + 18) for y in (-546.0, -538.0, -522.0, -515.0)])
church.wall("x", NY0 - 0.8, NY0 + 0.8, NX0 + 0.8, NX1 - 0.8, ZC - 0.3, EAVE, "GB_Church", holes=[(-322.0, -318.0, ZC, ZC + 6.0)])
church.wall("x", NY1 - 0.8, NY1 + 0.8, NX0 + 0.8, NX1 - 0.8, ZC - 0.3, EAVE, "GB_Church", holes=[(CX0 + 1.2, CX1 - 1.2, ZC, ZC + 19.0)])
# choir walls (open to the nave), polygonal apse to the east
church.wall("y", CX0 - 0.8, CX0 + 0.8, CY0, CY1, ZC - 0.3, EAVE, "GB_Church", holes=[(y, y + 2.2, ZC + 6, ZC + 18) for y in (-505.0, -495.0, -487.0)])
church.wall("y", CX1 - 0.8, CX1 + 0.8, CY0, CY1, ZC - 0.3, EAVE, "GB_Church", holes=[(-505.5, -503.5, ZC, ZC + 3.0)] + [(y, y + 2.2, ZC + 6, ZC + 18) for y in (-495.0, -487.0)])
APX, APY, APR = (CX0 + CX1) / 2, CY1, (CX1 - CX0) / 2
for k in range(4):                                                               # 5/8 apse wall panels
    a0, a1 = math.radians(-90 + 45 * k), math.radians(-90 + 45 * (k + 1))
    q0 = np.array([APX - APR * math.cos(a0 + math.pi / 2), APY + APR * math.sin(a0 + math.pi / 2)])
    q1 = np.array([APX - APR * math.cos(a1 + math.pi / 2), APY + APR * math.sin(a1 + math.pi / 2)])
    mid = (q0 + q1) / 2; tt = q1 - q0; L = np.linalg.norm(tt)
    nn = mid - np.array([APX, APY]); nn /= np.linalg.norm(nn)
    obox(church, mid + nn * 0.0, tt, L / 2 + 0.6, 0.8, ZC - 0.3, EAVE, "GB_Church")
    obox(church, mid - nn * 0.0, tt, L / 2 * 0.25, 0.85, ZC + 6, ZC + 18, "GB_Detail", col=False)   # tall window marker
apse_pts = [(APX - APR * math.cos(math.radians(-90 + 45 * k) + math.pi / 2), APY + APR * math.sin(math.radians(-90 + 45 * k) + math.pi / 2)) for k in range(5)]
church.poly_prism(apse_pts if (apse_pts[1][0] - apse_pts[0][0]) * (apse_pts[2][1] - apse_pts[0][1]) - (apse_pts[1][1] - apse_pts[0][1]) * (apse_pts[2][0] - apse_pts[0][0]) > 0 else apse_pts[::-1], ZC - 0.4, ZC, "GB_Floor")
# floors (church floor slab over the crypt void), pillars, altar, pulpit, font, seats footprint, organ loft
CRX0, CRX1, CRY0, CRY1, ZCR = CX0 + 1.0, CX1 - 1.0, CY0 + 1.0, CY1 - 1.0, ZC - 5.0
for (a0, a1, b0, b1) in rect_minus((NX0 - 0.8, NX1 + 0.8, NY0 - 0.8, NY1 + 0.8), []):
    church.box(a0, a1, b0, b1, ZC - 0.35, ZC, "GB_Floor")
for (a0, a1, b0, b1) in rect_minus((CX0 - 0.8, CX1 + 0.8, CY0, CY1 + 0.1), [(CX1 - 4.2, CX1 - 1.6, CY0 + 6.2, CY0 + 13.1)]):
    church.box(a0, a1, b0, b1, ZC - 0.35, ZC, "GB_Floor")
for xr in (NX0 + (NX1 - NX0) / 3, NX0 + 2 * (NX1 - NX0) / 3):
    for k in range(5):
        church.cyl(xr, NY0 + 4.0 + k * 7.5, 0.9, ZC, ZC + VAULT, "GB_Church", 12)
church.box(CX0 + 7.0, CX1 - 7.0, CY1 - 3.0, CY1 - 1.0, ZC, ZC + 1.2, "GB_Stone")     # high altar
church.box(CX0 + 6.0, CX1 - 6.0, CY1 - 1.2, CY1 - 0.9, ZC + 1.2, ZC + 7.0, "GB_Detail", col=False)   # winged altarpiece
church.box(CX0 + 4.0, CX1 - 4.0, CY1 - 6.0, CY1 - 0.9, ZC, ZC + 0.6, "GB_Stone")     # sanctuary step
church.cyl(NX1 - 3.0, -520.0, 0.8, ZC, ZC + 3.0, "GB_Wood", 8)                       # pulpit
church.cyl(-320.0, NY0 + 3.0, 0.7, ZC, ZC + 1.0, "GB_Stone", 8)                      # font
for k in range(10):                                                                  # pews (300 seats), visual only
    for xa, xb in ((NX0 + 2.0, -323.0), (-317.0, NX1 - 2.0)):
        church.box(xa, xb, NY0 + 9.0 + k * 2.6, NY0 + 9.6 + k * 2.6, ZC, ZC + 0.9, "GB_Wood", col=False)
# organ loft over the west portal (+9 m), reached by a stair along the north wall
church.box(NX0 + 0.8, NX1 - 0.8, NY0 + 0.8, NY0 + 6.0, ZC + 8.7, ZC + 9.0, "GB_Wood")
church.box(NX0 + 0.8, NX1 - 3.5, NY0 + 5.9, NY0 + 6.2, ZC + 9.0, ZC + 10.1, "GB_Wood")                  # loft rail
church.box(-326.0, -314.0, NY0 + 0.9, NY0 + 3.0, ZC + 9.0, ZC + 15.0, "GB_Detail", col=False)   # organ case
church.stairs((NX1 - 2.15, NY0 + 6.2 + 12.0), (0, -1), 2.5, ZC, ZC + 9.0, "GB_Wood", 0.2, 0.27)
# sacristy north of the choir
sac = R("Sacristy", CX1, CX1 + 8.0, -510.0, -500.0, ZC, 5.0, "church")
church.room(sac, doors=[("s", -505.5, -503.5, ZC, ZC + 3.0)], walls=("n", "e", "w"), mat_wall="GB_Church", t=1.2)
# crypt under the choir (relics, ossuary): stair from the choir along its north wall
crypt = R("Church crypt", CRX0, CRX1, CRY0, CRY1, ZCR, 4.5, "church")
church.room(crypt, mat_wall="GB_Stone", t=1.2, ceil=False, holes_floor=[])
church.stairs((CX1 - 2.9, CY0 + 13.0), (0, -1), 2.5, ZCR, ZC, "GB_Stone", 0.2, 0.27)   # crypt floor -> choir (rises to -Y)
church.box(CX1 - 4.3, CX1 - 4.0, CY0 + 7.0, CY0 + 13.1, ZC, ZC + 1.1, "GB_Wood")         # rail beside the stair opening
church.box(CX1 - 4.3, CX1 - 1.6, CY0 + 13.1, CY0 + 13.4, ZC, ZC + 1.1, "GB_Wood")
for k in range(6):
    church.box(CRX0 + 0.4, CRX0 + 1.4, CRY0 + 2.0 + k * 4.0, CRY0 + 4.5 + k * 4.0, ZCR, ZCR + 2.2, "GB_Detail")   # ossuary shelves
church.box(-322.0, -318.0, -498.0, -492.0, ZCR, ZCR + 1.0, "GB_Stone")                # reliquary
VOIDS.append([CX0 - 0.8, CX1 + 0.8, CY0 - 0.8, CY1 + 0.8, ZCR - 1.5])
# west tower 72 m: hall at the base (west portal 4 x 6 m), spiral to the bell chamber at +45 m (+80), spire to +72 m
TCX, TCY = (TX0 + TX1) / 2, (TY0 + TY1) / 2
BELL = ZC + 45.0
church.room(dict(x0=TX0, x1=TX1, y0=TY0, y1=TY1, z0=ZC, z1=BELL),
            doors=[("w", -322.0, -318.0, ZC, ZC + 6.0), ("e", -322.0, -318.0, ZC, ZC + 6.0)], mat_wall="GB_Church", t=1.6, ceil=False)
R("Church tower hall", TX0, TX1, TY0, TY1, ZC, 6.0, "church")
R("Bell chamber", TX0, TX1, TY0, TY1, BELL, 8.0, "church")
church.spiral(TCX, TCY, RSP, ZC, BELL, "GB_Stone", 0.2, 15.0, 0.0, shaft=False)        # 225 steps of 20 cm
church.floor_ring(TX0 + 0.8, TX1 - 0.8, TY0 + 0.8, TY1 - 0.8, BELL, (TCX - RSP - 0.1, TCX + RSP + 0.1, TCY - RSP - 0.1, TCY + RSP + 0.1))
# octagonal bell stage on the square shaft, faces at 0, 45, ... deg with one opening each: the north-east face looks
# straight at the castle keep (V5 "tower faces tower"; on a square chamber that line ran into the corner)
A_OUT, A_IN, OW, T8 = (TX1 - TX0) / 2 + 0.8, (TX1 - TX0) / 2 - 0.8, 3.0, math.tan(math.radians(22.5))


def ccw(pts):
    c = np.mean(pts, 0)
    return sorted(pts, key=lambda q: math.atan2(q[1] - c[1], q[0] - c[0]))


for k8 in range(8):
    u8 = np.array([math.cos(math.radians(45 * k8)), math.sin(math.radians(45 * k8))]); v8 = np.array([-u8[1], u8[0]])
    P8 = lambda a, s_: tuple(np.array([TCX, TCY]) + u8 * a + v8 * s_)
    for sg in (-1, 1):                                                                   # piers either side of the opening
        church.poly_prism(ccw([P8(A_IN, sg * A_IN * T8), P8(A_OUT, sg * A_OUT * T8), P8(A_OUT, sg * OW / 2), P8(A_IN, sg * OW / 2)]),
                          BELL - 0.3, BELL + 8.0, "GB_Church")
    mid = ccw([P8(A_IN, -OW / 2), P8(A_OUT, -OW / 2), P8(A_OUT, OW / 2), P8(A_IN, OW / 2)])
    church.poly_prism(mid, BELL - 0.3, BELL + 1.1, "GB_Church")                          # sill (1.1 m)
    church.poly_prism(mid, BELL + 5.0, BELL + 8.0, "GB_Church")                          # lintel over the 3.9 m opening
    for k in range(2, 5):
        church.poly_prism(mid, BELL + 1.6 + k * 0.75, BELL + 1.75 + k * 0.75, "GB_Wood", False)   # louvres above eye level
church.cyl(TCX, TCY, 1.2, BELL + 5.0, BELL + 6.6, "GB_Metal", 12, col=False)           # bell (hung above the stair head)
R8 = (A_OUT + 0.6) / math.cos(math.radians(22.5))
church.poly_prism([(TCX + R8 * math.cos(math.radians(22.5 + 45 * k)), TCY + R8 * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)],
                  BELL + 8.0, BELL + 8.6, "GB_Church")                                   # octagonal cornice
church.cone(TCX, TCY, 7.6, BELL + 8.6, ZC + 72.0, "GB_Church", 8)                      # stone spire to +72 m
# roofs: steep glazed tile, hall roof over the nave, lower roof over the choir, porch
church.gable(NX0, NX1, NY0, NY1, EAVE, EAVE + (NX1 - NX0) / 2 * math.tan(math.radians(58)), "GB_Tile", "y", overhang=0.8)
church.gable(CX0, CX1, CY0, CY1 + APR, EAVE, EAVE + (CX1 - CX0) / 2 * math.tan(math.radians(58)), "GB_Tile", "y", overhang=0.8)
for yb in np.arange(NY0 + 4.0, CY1, 8.0):                                               # buttresses
    if -530.0 < yb < -517.0 or -512.0 < yb < -497.0:
        continue                                                                         # porch, north portal, sacristy
    for xb, sgn in ((NX0 if yb < NY1 else CX0, -1), (NX1 if yb < NY1 else CX1, 1)):
        church.box(min(xb, xb + sgn * 2.5), max(xb, xb + sgn * 2.5), yb - 0.7, yb + 0.7, ZC - 1.0, EAVE - 3.0, "GB_Church")
porch = R("Church south porch", NX0 - 6.0, NX0, -527.0, -521.0, ZC, 6.0, "church")
church.room(porch, doors=[("s", -525.5, -522.5, ZC, ZC + 4.5)], walls=("s", "w", "e"), mat_wall="GB_Church", t=1.0)
church.gable(NX0 - 6.5, NX0, -527.5, -520.5, ZC + 6.3, ZC + 10.0, "GB_Tile", "x")
church.box(NX0 - 7.0, NX0 - 0.8, -527.5, -520.5, ZC - 0.35, ZC, "GB_Floor")
church.box(NX1 - 0.8, NX1 + 1.5, -526.4, -521.6, ZC - 0.35, ZC, "GB_Floor")             # north portal threshold
church.box(TX0 - 0.8, TX1 + 0.8, TY0 - 2.0, TY0 + 0.8, ZC - 0.35, ZC, "GB_Floor")        # west portal threshold
church.box(TX0 + 0.8, TX1 - 0.8, TY0 + 0.8, TY1 - 0.8, ZC - 0.35, ZC, "GB_Floor")

# churchyard: 1.2 m wall, graves (visual), mausolea, charnel house, lime tree, parish house on the west side
cy_ = ch["churchyard"]
yard = Group("SM_GB_Church_Churchyard", "Environment/Church")
YX0, YX1, YY0, YY1 = cy_["x"][0], cy_["x"][1], cy_["y"][0], cy_["y"][1]
gaps = {"s": [(-505.0, -495.0)], "e": [(-345.0, -339.0)], "n": [(-532.0, -526.0)], "w": [(-325.0, -315.0)]}
for side, (fixed, a0, a1, ax) in {"s": (YX0, YY0, YY1, "y"), "n": (YX1, YY0, YY1, "y"), "w": (YY0, YX0, YX1, "x"), "e": (YY1, YX0, YX1, "x")}.items():
    segs = [(a0, a1)]
    for g0, g1 in gaps[side]:
        segs = [s for seg in segs for s in ((seg[0], min(seg[1], g0)), (max(seg[0], g1), seg[1])) if s[1] - s[0] > 0.5]
    for s0, s1 in segs:
        for u in np.arange(s0, s1, 6.0):
            u1 = min(u + 6.0, s1)
            if ax == "y":
                zz = min(gz(fixed, u), gz(fixed, u1))
                yard.box(fixed - 0.3, fixed + 0.3, u, u1, zz - 0.8, zz + 1.2, "GB_Stone")
            else:
                zz = min(gz(u, fixed), gz(u1, fixed))
                yard.box(u, u1, fixed - 0.3, fixed + 0.3, zz - 0.8, zz + 1.2, "GB_Stone")
rng = np.random.default_rng(7)
for k in range(140):
    x, y = rng.uniform(YX0 + 3, YX1 - 3), rng.uniform(YY0 + 3, YY1 - 3)
    if (NX0 - 8 < x < NX1 + 8 and TY0 - 8 < y < CY1 + APR + 8) or (-345 < x < -339 and y > -480):
        continue
    z = gz(x, y)
    yard.box(x - 0.08, x + 0.08, y - 0.35, y + 0.35, z - 0.3, z + 0.9, "GB_Stone", col=False)
for (x, y) in ((-362.0, -588.0), (-280.0, -590.0), (-285.0, -470.0)):                     # mausolea (hiding spots)
    z = gz(x, y)
    yard.box(x - 2.5, x + 2.5, y - 3.0, y + 3.0, z - 0.5, z + 3.5, "GB_Stone")
    yard.gable(x - 2.5, x + 2.5, y - 3.0, y + 3.0, z + 3.5, z + 5.5, "GB_Stone", "y")
z = gz(-280.0, -560.0)
yard.box(-284.0, -276.0, -566.0, -556.0, z - 0.5, z + 4.0, "GB_Stone")                   # charnel house
yard.gable(-284.0, -276.0, -566.0, -556.0, z + 4.0, z + 7.0, "GB_Tile", "y")
z = gz(-300.0, -580.0)
yard.cyl(-300.0, -580.0, 0.9, z - 0.5, z + 7.0, "GB_Wood", 10)                           # old lime tree
yard.cone(-300.0, -580.0, 8.0, z + 5.0, z + 16.0, "GB_Hedge", 12, col=False)
ENTER_SPECS = []
ENTER_SPECS.append(dict(name="Parish house", rect=(-352.0, -334.0, -618.0, -604.0), front="+y", kind="parish", storeys=2))

# ====================================================================== Noble Manor (compound 110 x 90, 4 m wall)
nm = C["noble_manor"]
man = Group("SM_GB_Manor_NobleManor", "Environment/Manor")
MX0, MX1, MY0, MY1 = nm["compound"]["x"][0], nm["compound"]["x"][1], nm["compound"]["y"][0], nm["compound"]["y"][1]
ZM = round(max(gz(x, y) for x in (MX0, MX1) for y in (MY0, MY1)) * 2) / 2 + 0.2         # court level (flat platform)
ZLOW = min(gz(x, y) for x in (MX0, MX1) for y in (MY0, MY1)) - 1.5
GH = (-362.0, -350.0)                                                                       # gatehouse passage (x) on the west wall
for side, (fixed, a0, a1, ax, holes) in {"w": (MY0, MX0, MX1, "x", [(GH[0] + 2.5, GH[1] - 2.5)]), "e": (MY1, MX0, MX1, "x", []),
                                          "s": (MX0, MY0, MY1, "y", []), "n": (MX1, MY0, MY1, "y", [])}.items():
    segs = [(a0, a1)]
    for g0, g1 in holes:
        segs = [s_ for seg in segs for s_ in ((seg[0], min(seg[1], g0)), (max(seg[0], g1), seg[1])) if s_[1] - s_[0] > 0.3]
    for s0, s1 in segs:
        if ax == "x":
            man.box(s0, s1, fixed - 0.4, fixed + 0.4, ZLOW, ZM + 4.0, "GB_Stone")
        else:
            man.box(fixed - 0.4, fixed + 0.4, s0, s1, ZLOW, ZM + 4.0, "GB_Stone")
for (a0, a1, b0, b1) in rect_minus((MX0 + 0.4, MX1 - 0.4, MY0 + 0.4, MY1 - 0.4), [(-345.5, -299.5, -420.5, -403.5), (-300.5, -281.5, -420.5, -371.5)]):
    man.box(a0, a1, b0, b1, ZLOW, ZM - 0.05, "GB_Ground")                                       # level court platform (not under the house)
# gatehouse with the blank coat of arms, approach ramp from Gate Street
gh = R("Manor gatehouse", GH[0], GH[1], MY0 - 2.0, MY0 + 6.0, ZM, 4.5, "manor")
man.room(gh, doors=[("w", GH[0] + 2.5, GH[1] - 2.5, ZM, ZM + 4.5), ("e", GH[0] + 2.5, GH[1] - 2.5, ZM, ZM + 4.5)],
         mat_wall="GB_Stone", t=1.2, floor=True)
man.box(GH[0] - 0.6, GH[1] + 0.6, MY0 - 2.6, MY0 + 6.6, ZM + 4.8, ZM + 8.5, "GB_Stone")
man.box(GH[0] + 4.5, GH[1] - 4.5, MY0 - 2.8, MY0 - 2.6, ZM + 5.2, ZM + 7.6, "GB_Detail", col=False)   # blank coat of arms
man.gable(GH[0] - 0.6, GH[1] + 0.6, MY0 - 2.6, MY0 + 6.6, ZM + 8.5, ZM + 12.0, "GB_Tile", "x")
gd = Group("SM_GB_Manor_GateDoors", "Environment/Manor")
gd.box(GH[0] + 2.5, GH[1] - 2.5, MY0 - 1.6, MY0 - 1.4, ZM, ZM + 4.3, "GB_Wood")
MOVABLE.append(dict(name=gd.name, pivot=[GH[0] + 2.5, MY0 - 1.5, ZM]))
zst = gz((GH[0] + GH[1]) / 2, -436.0)
man.ramp(((GH[0] + GH[1]) / 2, -437.0), ((GH[0] + GH[1]) / 2, MY0 - 2.4), 7.0, zst, ZM, 1.5, "GB_Stone")
# main house: wing_b (west range 45 x 16) + wing_a (north range 18 x 48), two storeys of 5 m + roofs
wa, wb = nm["wing_a"], nm["wing_b"]
Z1M = ZM + 5.0
T = 1.0
TWX0, TWX1, TWY0, TWY1 = -291.0, -282.0, -420.0, -411.0                                     # corner tower 25 m
TCXm, TCYm = (TWX0 + TWX1) / 2, (TWY0 + TWY1) / 2
G0 = dict(E=R("Manor entrance hall", -345.0, -333.0, -420.0, -404.0, ZM, 4.7, "manor"),
          GC=R("Manor great chamber", -333.0, -313.0, -420.0, -410.0, ZM, 4.7, "manor"),
          CO=R("Manor ground corridor", -333.0, -300.0, -410.0, -404.0, ZM, 4.7, "manor"),
          GR=R("Manor guard room", -313.0, -300.0, -420.0, -410.0, ZM, 4.7, "manor"),
          LB=R("Manor lobby", -300.0, -282.0, -411.0, -404.0, ZM, 4.7, "manor"),
          MU=R("Manor muniment room", -300.0, -291.0, -420.0, -411.0, ZM, 4.7, "manor"),
          DI=R("Manor dining room", -300.0, -282.0, -404.0, -390.0, ZM, 4.7, "manor"),
          KI=R("Manor kitchen", -300.0, -282.0, -390.0, -372.0, ZM, 4.7, "manor"))
pw_ = "GB_Plaster"
man.room(G0["E"], doors=[("e", -341.5, -338.5, ZM, ZM + 4.5), ("n", -417.0, -414.0, ZM, ZM + 4.5), ("n", -409.0, -406.0, ZM, ZM + 3.2)], mat_wall=pw_, t=T,
         holes_ceil=[(-344.4, -341.5, -412.8, -405.6)])
man.room(G0["GC"], doors=[("s", -417.0, -414.0, ZM, ZM + 4.5), ("e", -324.5, -321.5, ZM, ZM + 4.5)], mat_wall=pw_, t=T)
man.box(-317.5, -313.6, -419.4, -410.6, ZM, ZM + 0.6, "GB_Stone")                          # dais with the ruler's seat
man.box(-315.6, -314.2, -415.8, -414.2, ZM + 0.6, ZM + 2.6, "GB_Detail")
man.room(G0["CO"], doors=[("s", -409.0, -406.0, ZM, ZM + 3.2), ("w", -324.5, -321.5, ZM, ZM + 4.5), ("w", -308.0, -305.0, ZM, ZM + 3.2),
                          ("n", -409.0, -406.0, ZM, ZM + 3.2), ("e", -320.0, -317.0, ZM, ZM + 4.5)], mat_wall=pw_, t=T)
man.room(G0["GR"], doors=[("e", -308.0, -305.0, ZM, ZM + 3.2)], mat_wall=pw_, t=T)
man.room(G0["LB"], doors=[("s", -409.0, -406.0, ZM, ZM + 3.2), ("w", -288.0, -285.0, ZM, ZM + 3.2), ("w", -297.0, -294.0, ZM, ZM + 3.2),
                          ("e", -294.0, -291.0, ZM, ZM + 3.2)], mat_wall=pw_, t=T)
man.room(G0["MU"], doors=[("e", -297.0, -294.0, ZM, ZM + 3.2)], mat_wall=pw_, t=T)
man.room(G0["DI"], doors=[("w", -294.0, -291.0, ZM, ZM + 3.2), ("e", -294.0, -291.0, ZM, ZM + 3.2)], mat_wall=pw_, t=T)
man.box(-296.0, -286.0, -400.0, -394.0, ZM, ZM + 0.8, "GB_Wood", col=False)                 # dining table
man.room(G0["KI"], doors=[("w", -294.0, -291.0, ZM, ZM + 3.2), ("s", -386.0, -383.0, ZM, ZM + 3.2)], mat_wall=pw_, t=T,
         holes_floor=[(-285.2, -282.5, -387.3, -380.4)])
man.box(-299.4, -297.0, -389.4, -383.0, ZM, ZM + 1.6, "GB_Stone")                           # kitchen hearth
cel = R("Manor cellar strongroom", -300.0, -282.0, -390.0, -372.0, ZM - 5.0, 4.6, "manor")
man.room(cel, mat_wall="GB_Stone", t=T, ceil=False)
man.stairs((-283.85, -380.5), (0, -1), 2.5, ZM - 5.0, ZM, "GB_Stone", 0.2, 0.27)            # cellar -> kitchen (rises to -Y)
man.box(-285.5, -285.2, -387.3, -381.0, ZM, ZM + 1.1, "GB_Wood")                            # rail beside the opening
man.box(-296.0, -292.0, -388.0, -386.0, ZM - 5.0, ZM - 3.8, "GB_Metal")                       # strongbox
VOIDS.append([-301.0, -281.0, -391.0, -371.0, ZM - 6.5])
# entrance-hall stair (2.5 m) to the upper floor, arrives in the study
man.stairs((-342.95, -406.0), (0, -1), 2.5, ZM, Z1M, "GB_Stone", 0.2, 0.27)
G1 = dict(ST=R("Manor study (city records)", -345.0, -333.0, -420.0, -404.0, Z1M, 4.5, "manor"),
          B1=R("Manor bedchamber (lord)", -333.0, -313.0, -420.0, -404.0, Z1M, 4.5, "manor"),
          B2=R("Manor bedchamber (lady)", -313.0, -300.0, -420.0, -404.0, Z1M, 4.5, "manor"),
          UH=R("Manor upper hall", -300.0, -282.0, -411.0, -404.0, Z1M, 4.5, "manor"),
          SO=R("Manor solar", -300.0, -282.0, -404.0, -390.0, Z1M, 4.5, "manor"))
man.room(G1["ST"], doors=[("n", -417.0, -414.0, Z1M, Z1M + 3.2)], mat_wall=pw_, t=T, holes_floor=[(-344.4, -341.5, -412.8, -405.6)])
man.box(-341.5, -341.2, -412.0, -405.3, Z1M, Z1M + 1.1, "GB_Wood")                         # rails at the stair head
man.box(-344.5, -341.2, -405.6, -405.3, Z1M, Z1M + 1.1, "GB_Wood")
man.room(G1["B1"], doors=[("s", -417.0, -414.0, Z1M, Z1M + 3.2), ("n", -417.0, -414.0, Z1M, Z1M + 3.2)], mat_wall=pw_, t=T)
man.room(G1["B2"], doors=[("s", -417.0, -414.0, Z1M, Z1M + 3.2), ("n", -409.0, -406.0, Z1M, Z1M + 3.2)], mat_wall=pw_, t=T)
man.room(G1["UH"], doors=[("s", -409.0, -406.0, Z1M, Z1M + 3.2), ("w", -288.0, -285.0, Z1M, Z1M + 3.2), ("e", -294.0, -291.0, Z1M, Z1M + 3.2)],
         mat_wall=pw_, t=T)
man.room(G1["SO"], doors=[("w", -294.0, -291.0, Z1M, Z1M + 3.2)], mat_wall=pw_, t=T)
for k, (bx0, bx1) in enumerate(((-331.0, -326.0), (-311.0, -307.0))):
    man.box(bx0, bx1, -419.4, -415.0, Z1M, Z1M + 0.7, "GB_Wood", col=False)                 # beds
# corner tower: base, upper door, spiral to the top room (+20 m) with windows towards the castle
R("Manor tower base", TWX0, TWX1, TWY0, TWY1, ZM, 4.7, "manor")
R("Manor tower top room", TWX0, TWX1, TWY0, TWY1, ZM + 20.0, 4.5, "manor")
man.room(dict(x0=TWX0, x1=TWX1, y0=TWY0, y1=TWY1, z0=ZM, z1=ZM + 24.5),
         doors=[("e", -288.0, -285.0, ZM, ZM + 3.2), ("e", -288.0, -285.0, Z1M, Z1M + 3.2)],
         windows=[("n", -418.0, -413.0, ZM + 21.1, ZM + 23.6), ("e", -289.5, -284.5, ZM + 21.1, ZM + 23.6)], mat_wall="GB_Stone", t=T)
man.spiral(TCXm, TCYm, RSP, ZM, ZM + 20.0, "GB_Stone", 0.2, 18.0, 90.0, shaft=False)
for zr in (Z1M, ZM + 20.0):
    man.floor_ring(TWX0 + 0.5, TWX1 - 0.5, TWY0 + 0.5, TWY1 - 0.5, zr, (TCXm - RSP - 0.1, TCXm + RSP + 0.1, TCYm - RSP - 0.1, TCYm + RSP + 0.1))
man.box(TWX0 - 0.5, TWX1 + 0.5, TWY0 - 0.5, TWY1 + 0.5, ZM + 24.8, ZM + 25.1, "GB_Stone")
man.pyramid(TWX0 - 0.5, TWX1 + 0.5, TWY0 - 0.5, TWY1 + 0.5, ZM + 25.1, ZM + 31.0, "GB_Tile")
# roofs (55 deg tile)
man.box(-345.5, -299.5, -420.5, -403.5, Z1M + 4.7, Z1M + 5.0, "GB_Stone")
man.gable(-345.0, -300.0, -420.0, -404.0, Z1M + 5.0, Z1M + 5.0 + 8.0 * math.tan(math.radians(55)), "GB_Tile", "x")
for (a0, a1, b0, b1) in rect_minus((-300.5, -281.5, -420.5, -389.5), [(TWX0, TWX1 + 0.5, TWY0 - 0.5, TWY1)]):
    man.box(a0, a1, b0, b1, Z1M + 4.7, Z1M + 5.0, "GB_Stone")                               # (the tower rises clear)
man.gable(-300.0, -282.0, -411.0, -372.0, Z1M + 5.0, Z1M + 5.0 + 9.0 * math.tan(math.radians(55)), "GB_Tile", "y")
man.gable(-300.0, -291.0, -420.0, -411.0, Z1M + 5.0, Z1M + 5.0 + 4.5 * math.tan(math.radians(55)), "GB_Tile", "x")
man.box(-300.5, -281.5, -390.5, -371.5, ZM + 4.7, Z1M + 4.7, "GB_Plaster")                  # closed loft over the kitchen
# arcaded loggia on the court side of wing_b
for xc in np.arange(-343.0, -300.0, 4.0):
    if abs(xc + 318.5) < 2.2 or abs(xc + 340.0) < 2.2:
        continue
    man.cyl(xc, -401.6, 0.35, ZM, ZM + 4.4, "GB_Stone", 8)
man.box(-345.0, -300.0, -404.6, -400.8, ZM + 4.4, ZM + 4.9, "GB_Stone")
# stables + carriage house (south strip), private chapel, well, walled garden with fountain and pavilion
stb = R("Manor stables", MX0 + 1.0, MX0 + 12.0, -362.0, -322.0, ZM, 5.0, "manor")
man.room(stb, doors=[("n", -350.0, -346.0, ZM, ZM + 4.0), ("n", -336.0, -332.0, ZM, ZM + 4.0)], mat_wall="GB_Timber", t=0.6)
man.gable(MX0 + 1.0, MX0 + 12.0, -362.0, -322.0, ZM + 5.3, ZM + 9.5, "GB_Tile", "y")
chp = R("Manor private chapel", -345.0, -333.0, -372.0, -364.0, ZM, 7.0, "manor")
man.room(chp, doors=[("w", -341.0, -338.0, ZM, ZM + 4.5)], mat_wall="GB_Stone", t=1.0)
man.gable(-345.0, -333.0, -372.0, -364.0, ZM + 7.3, ZM + 11.5, "GB_Tile", "x")
man.cyl(-325.0, -385.0, 1.3, ZM, ZM + 1.0, "GB_Stone", 12)                                  # court well
gx0, gx1, gy0, gy1 = nm["garden"]["x"][0], nm["garden"]["x"][1], nm["garden"]["y"][0], nm["garden"]["y"][1]
for (a0, a1, b0, b1) in rect_minus((gx0, gx1, gy0 - 0.3, gy0 + 0.3), [(-322.0, -318.0, gy0 - 1, gy0 + 1)]):
    man.box(a0, a1, b0, b1, ZM, ZM + 2.5, "GB_Stone")                                         # garden wall + gate
man.cyl((gx0 + gx1) / 2, (gy0 + gy1) / 2, 3.0, ZM, ZM + 0.8, "GB_Stone", 16)                # fountain
man.cyl((gx0 + gx1) / 2, (gy0 + gy1) / 2, 0.4, ZM + 0.8, ZM + 2.4, "GB_Stone", 8)
pav = (gx1 - 8.0, gy1 - 8.0)
for dx in (-2.5, 2.5):
    for dy in (-2.5, 2.5):
        man.cyl(pav[0] + dx, pav[1] + dy, 0.25, ZM, ZM + 3.2, "GB_Stone", 8)
man.pyramid(pav[0] - 3.2, pav[0] + 3.2, pav[1] - 3.2, pav[1] + 3.2, ZM + 3.2, ZM + 5.5, "GB_Tile")
for k in range(6):
    for j in range(4):
        man.box(gx0 + 6 + k * 9, gx0 + 12 + k * 9, gy0 + 6 + j * 9, gy0 + 9 + j * 9, ZM, ZM + 0.5, "GB_Hedge", col=False)
man.box(gx1 - 6.0, gx1 - 0.6, gy0 + 2.0, gy1 - 2.0, ZM, ZM + 0.6, "GB_Stone")                 # garden terrace facing the castle
man.ramp((gx1 - 9.0, gy0 + 6.0), (gx1 - 6.0, gy0 + 6.0), 3.0, ZM, ZM + 0.6, 0.6, "GB_Stone")
# ground slab under the whole house (covers the cellar void edge)
for (a0, a1, b0, b1) in rect_minus((-345.5, -281.5, -420.5, -403.5), [(-344.4, -341.5, -412.8, -405.6)]):
    man.box(a0, a1, b0, b1, ZM - 0.4, ZM - 0.05, "GB_Floor")
for (a0, a1, b0, b1) in rect_minus((-300.5, -281.5, -403.5, -371.5), [(-285.2, -282.5, -387.3, -380.4)]):
    man.box(a0, a1, b0, b1, ZM - 0.4, ZM - 0.05, "GB_Floor")

# ====================================================================== town hall (45 m clock tower), guild hall, barracks
pub = Group("SM_GB_City_TownHall", F)
th_ = C["town_hall"]
HX0, HX1, HY0, HY1 = th_["x"][0], th_["x"][1], th_["y"][0], th_["y"][1]
ZH = round(gz((HX0 + HX1) / 2, HY1) + 0.3, 1)
th0 = R("Town hall: archive", HX0, HX0 + 20.0, HY0, HY1, ZH, 5.0, "town_hall")
th1 = R("Town hall: holding cells", HX0 + 20.0, HX1 - 10.0, HY0, HY1, ZH, 5.0, "town_hall")
th2 = R("Town hall: council chamber", HX0, HX1 - 10.0, HY0, HY1, ZH + 5.3, 6.0, "town_hall")
th2_hole = (HX0 + 16.7, HX0 + 19.4, HY1 - 9.0, HY1 - 1.6)
pub.room(th0, doors=[("e", HX0 + 8.0, HX0 + 11.0, ZH, ZH + 4.5), ("n", HY0 + 4.0, HY0 + 7.0, ZH, ZH + 3.0)], mat_wall="GB_Stone", t=1.2,
         holes_ceil=[th2_hole])
pub.room(th1, doors=[("e", HX1 - 16.0, HX1 - 13.0, ZH, ZH + 4.5), ("s", HY0 + 4.0, HY0 + 7.0, ZH, ZH + 3.0)], mat_wall="GB_Stone", t=1.2)
for k in range(3):                                                                        # three cells with barred fronts
    yb = HY0 + 1.0 + k * 4.0
    pub.box(HX1 - 17.0, HX1 - 16.6, yb, yb + 3.4, ZH, ZH + 3.0, "GB_Metal")
pub.stairs((HX0 + 18.05, HY1 - 2.0), (0, -1), 2.5, ZH, ZH + 5.3, "GB_Stone", 0.2, 0.27)  # archive (NE corner) -> council
pub.room(th2, doors=[], mat_wall="GB_Stone", t=1.2, holes_floor=[th2_hole])
pub.box(th2_hole[0] - 0.3, th2_hole[0], th2_hole[2] + 0.4, th2_hole[3] + 0.3, ZH + 5.3, ZH + 6.4, "GB_Wood")     # rails
pub.box(th2_hole[1], th2_hole[1] + 0.3, th2_hole[2] + 0.4, th2_hole[3] + 0.3, ZH + 5.3, ZH + 6.4, "GB_Wood")
pub.box(th2_hole[0], th2_hole[1], th2_hole[3], th2_hole[3] + 0.3, ZH + 5.3, ZH + 6.4, "GB_Wood")
pub.gable(HX0, HX1, HY0, HY1, ZH + 11.6, ZH + 11.6 + (HY1 - HY0) / 2 * math.tan(math.radians(55)), "GB_Tile", "x")
CTX0, CTX1, CTY0, CTY1 = HX1 - 10.0, HX1, HY1 - 10.0, HY1                                 # clock tower, square corner
pub.room(dict(x0=CTX0, x1=CTX1, y0=CTY0, y1=CTY1, z0=ZH, z1=ZH + 38.0), doors=[("e", CTX0 + 3.5, CTX0 + 6.5, ZH, ZH + 4.5)],
         mat_wall="GB_Stone", t=1.4)
pub.box(CTX0, CTX1, HY0, CTY0, ZH - 0.3, ZH + 11.6, "GB_Stone")                          # closed corner behind the tower
R("Town hall: clock tower base", CTX0, CTX1, CTY0, CTY1, ZH, 5.0, "town_hall")
for s_ in range(4):
    pub.cyl(*(((CTX0 + CTX1) / 2 + 5.2, (CTY0 + CTY1) / 2), ((CTX0 + CTX1) / 2 - 5.2, (CTY0 + CTY1) / 2),
              ((CTX0 + CTX1) / 2, (CTY0 + CTY1) / 2 + 5.2), ((CTX0 + CTX1) / 2, (CTY0 + CTY1) / 2 - 5.2))[s_], 1.6, ZH + 30.0, ZH + 33.2,
            "GB_Detail", 12, col=False)                                                    # clock faces (markers)
pub.box(CTX0 - 0.4, CTX1 + 0.4, CTY0 - 0.4, CTY1 + 0.4, ZH + 38.0, ZH + 38.5, "GB_Stone")
pub.pyramid(CTX0 - 0.4, CTX1 + 0.4, CTY0 - 0.4, CTY1 + 0.4, ZH + 38.5, ZH + 45.0, "GB_Tile")
pub.box(HX0 - 0.6, HX1 + 0.6, HY0 - 0.6, HY1 + 0.6, ZH - 1.5, ZH - 0.05, "GB_Stone")
gup = Group("SM_GB_City_GuildHall", F)
gu = C["guild_hall"]
UX0, UX1, UY0, UY1 = gu["x"][0], gu["x"][1], gu["y"][0], gu["y"][1]
ZU = round(gz(UX1, (UY0 + UY1) / 2) + 0.3, 1)
gh_ = R("Guild hall", UX0, UX1, UY0, UY1, ZU, 9.0, "guild_hall")
gup.room(gh_, doors=[("n", -456.5, -453.5, ZU, ZU + 4.5), ("n", -470.0, -467.0, ZU, ZU + 4.5)], mat_wall="GB_Stone", t=1.2)
gup.box(UX0 + 1.0, UX0 + 3.5, UY0 + 4.0, UY1 - 4.0, ZU, ZU + 0.6, "GB_Stone")                # masters' bench
gup.box(UX0 - 0.6, UX1 + 0.6, UY0 - 0.6, UY1 + 0.6, ZU - 1.5, ZU - 0.05, "GB_Stone")
gup.gable(UX0, UX1, UY0, UY1, ZU + 9.6, ZU + 9.6 + (UX1 - UX0) / 2 * math.tan(math.radians(55)), "GB_Tile", "y")
bkp = Group("SM_GB_City_Barracks", F)
wb_ = C["watch_barracks"]
BX0, BX1, BY0, BY1 = wb_["x"][0], wb_["x"][1], wb_["y"][0], wb_["y"][1]
# the Appendix box pokes ~10 m out through the ring wall: slide it inwards until the 5 m ring street is clear
dvec = np.array([CX - (BX0 + BX1) / 2, CY - (BY0 + BY1) / 2]); dvec /= np.linalg.norm(dvec)
BARRACKS_SHIFT = 0.0
while min(ell_dist(x, y) for x in (BX0, BX1) for y in (BY0, BY1)) < 6.5:
    BX0, BX1, BY0, BY1 = BX0 + dvec[0] * 0.5, BX1 + dvec[0] * 0.5, BY0 + dvec[1] * 0.5, BY1 + dvec[1] * 0.5
    BARRACKS_SHIFT += 0.5
BX0, BX1, BY0, BY1 = (round(v, 1) for v in (BX0, BX1, BY0, BY1))
ZB = round(gz(BX0, (BY0 + BY1) / 2) + 0.3, 1)
b0 = R("Watch barracks: guard hall", BX0, BX0 + 14.0, BY0, BY1, ZB, 5.0, "barracks")
b1 = R("Watch barracks: dormitory", BX0 + 14.0, BX1, BY0, BY0 + 30.0, ZB, 5.0, "barracks")
b2 = R("Watch barracks: lock-up", BX0 + 14.0, BX1, BY0 + 30.0, BY1, ZB, 5.0, "barracks")
bkp.room(b0, doors=[("s", BY1 - 23.5, BY1 - 20.5, ZB, ZB + 4.5), ("n", BY0 + 10.0, BY0 + 13.0, ZB, ZB + 3.0), ("n", BY1 - 12.0, BY1 - 9.0, ZB, ZB + 3.0)],
         mat_wall="GB_Stone", t=1.2)
bkp.room(b1, doors=[("s", BY0 + 10.0, BY0 + 13.0, ZB, ZB + 3.0)], mat_wall="GB_Stone", t=1.2)
bkp.room(b2, doors=[("s", BY1 - 12.0, BY1 - 9.0, ZB, ZB + 3.0)], mat_wall="GB_Stone", t=1.2)
for k in range(4):
    bkp.box(BX1 - 4.0, BX1 - 3.7, BY0 + 31.0 + k * 4.5, BY0 + 34.5 + k * 4.5, ZB, ZB + 3.0, "GB_Metal")
for k in range(8):
    bkp.box(BX0 + 15.0 + (k % 2) * 7.5, BX0 + 21.5 + (k % 2) * 7.5, BY0 + 2.0 + (k // 2) * 7.0, BY0 + 4.0 + (k // 2) * 7.0, ZB, ZB + 0.7, "GB_Wood", col=False)
bkp.box(BX0 - 0.6, BX1 + 0.6, BY0 - 0.6, BY1 + 0.6, ZB - 1.5, ZB - 0.05, "GB_Stone")
bkp.gable(BX0, BX1, BY0, BY1, ZB + 5.6, ZB + 5.6 + (BX1 - BX0) / 2 * math.tan(math.radians(52)), "GB_Tile", "y")

# market square: well, pillory, stalls; covered stairs from the square to the churchyard
mk = C["market_square"]
mkt = Group("SM_GB_City_Market", F)
QX0, QX1, QY0, QY1 = mk["x"][0], mk["x"][1], mk["y"][0], mk["y"][1]
qc = (QX0 + 17.0, QY0 + 20.0)                                       # well kept off the square's spawn point (centre)
z = gz(*qc)
mkt.cyl(qc[0], qc[1], 2.2, z - 0.5, z + 1.0, "GB_Stone", 16)
mkt.box(qc[0] - 0.3, qc[0] + 0.3, qc[1] - 2.0, qc[1] - 1.4, z + 1.0, z + 3.6, "GB_Wood")
mkt.box(QX0 + 8.0, QX0 + 9.0, QY1 - 14.0, QY1 - 13.0, gz(QX0 + 8, QY1 - 14) - 0.3, gz(QX0 + 8, QY1 - 14) + 2.8, "GB_Wood")   # pillory
for k in range(10):
    sx, sy = QX0 + 10.0 + (k % 5) * 10.0, QY0 + 12.0 + (k // 5) * 52.0
    zs = gz(sx, sy)
    mkt.box(sx - 1.5, sx + 1.5, sy - 1.0, sy + 1.0, zs, zs + 0.9, "GB_Wood")
    mkt.gable(sx - 1.8, sx + 1.8, sy - 1.4, sy + 1.4, zs + 2.4, zs + 3.0, "GB_Roof", "x", col=False)
stp = C["streets"]["church_stairs"]["points_xy"]
for (xa, ya), (xb, yb) in zip(stp[:-1], stp[1:]):
    za, zb = gz(xa, ya), gz(xb, yb)
    d = np.array([xb - xa, yb - ya], float); L = np.linalg.norm(d); d /= L; n = np.array([-d[1], d[0]])
    nst = max(1, int(abs(zb - za) / 0.2))
    mkt.ramp((xa, ya), (xb, yb), 4.0, za + 0.05, zb + 0.05, 1.2, "GB_Stone")                  # stepped walkway (collision ramp)
    for s in np.arange(0, L, 4.0):
        p = np.array([xa, ya]) + d * s; zp = za + (zb - za) * s / L
        for q in (-1, 1):
            mkt.cyl(*(p + n * q * 2.3), 0.15, zp, zp + 3.2, "GB_Wood", 6)
    mkt.ramp(tuple(np.array([xa, ya]) - d * 0.5), tuple(np.array([xb, yb]) + d * 0.5), 5.4, za + 3.5, zb + 3.5, 0.25, "GB_Roof", col=False)

# ====================================================================== plots -> houses (16 variants) and interiors
raw = json.load(open(f"{ROOT}/data/city_plots_raw.json"))
SPECIAL = [(QX0, QX1, QY0, QY1), (HX0, HX1, HY0, HY1), (UX0, UX1, UY0, UY1), (YX0, YX1, YY0, YY1), (MX0, MX1, MY0 - 3, MY1),
           (BX0, BX1, BY0, BY1), (-352.0, -334.0, -618.0, -604.0)]


def seg_dist(px, py, a, b):
    a, b = np.array(a, float), np.array(b, float); ab = b - a
    t = np.clip(((px - a[0]) * ab[0] + (py - a[1]) * ab[1]) / (ab @ ab), 0, 1)
    return math.hypot(px - a[0] - t * ab[0], py - a[1] - t * ab[1])


def rect_hits_street(x0, x1, y0, y1):
    for sid, s in C["streets"].items():
        pts = s["points_xy"]; hw = s["width_m"] / 2 + 0.5
        for a, b in zip(pts[:-1], pts[1:]):
            for px in np.linspace(x0, x1, 5):
                for py in np.linspace(y0, y1, 5):
                    if seg_dist(px, py, a, b) < hw:
                        return sid
    return None


plots, dropped = [], {}
for x0, x1, y0, y1, _ in raw:
    cx_, cy_ = (x0 + x1) / 2, (y0 + y1) / 2
    if math.hypot((cx_ - CX) / RA, (cy_ - CY) / RB) >= 1.0:
        continue
    why = None
    if min(ell_dist(x, y) for x in (x0, x1) for y in (y0, y1)) < 1.3 + 5.0:
        why = "ring street"
    elif any(not (x1 < a0 - 1 or x0 > a1 + 1 or y1 < b0 - 1 or y0 > b1 + 1) for a0, a1, b0, b1 in SPECIAL):
        why = "landmark"
    else:
        why = rect_hits_street(x0, x1, y0, y1)
    if why:
        # try shrinking the plot by up to 3 m on the offending side(s) before dropping it
        ok = False
        for sh in (1.0, 2.0, 3.0):
            for (a, b, c, d) in ((x0 + sh, x1, y0, y1), (x0, x1 - sh, y0, y1), (x0, x1, y0 + sh, y1), (x0, x1, y0, y1 - sh)):
                if (b - a) < 9 or (d - c) < 8:
                    continue
                if (min(ell_dist(x, y) for x in (a, b) for y in (c, d)) >= 6.3 and not rect_hits_street(a, b, c, d)
                        and not any(not (b < a0 - 1 or a > a1 + 1 or d < b0 - 1 or c > b1 + 1) for a0, a1, b0, b1 in SPECIAL)):
                    x0, x1, y0, y1, ok = a, b, c, d, True
                    break
            if ok:
                break
        if not ok:
            dropped[why] = dropped.get(why, 0) + 1
            continue
    plots.append([x0, x1, y0, y1])
plots = np.array(plots)
# V1 (market square -> keep): drop the few plots whose roofs would hide the keep, so it reads framed between roofs
v1 = [v for v in M["hero_views"] if v["id"] == "V1"][0]
c1 = np.array(v1["camera"], float); c1[2] = max(c1[2], gz(c1[0], c1[1]) + 1.6)
t1 = np.array(v1["look_at"], float)
az = math.atan2(t1[1] - c1[1], t1[0] - c1[0]); el = math.atan2(t1[2] - c1[2], math.hypot(*(t1 - c1)[:2]))
keep_mask, V1_DROPPED = [], 0
for x0, x1, y0, y1 in plots:
    hit = False
    for (px_, py_) in ((x0, y0), (x0, y1), (x1, y0), (x1, y1), ((x0 + x1) / 2, (y0 + y1) / 2)):
        dx_, dy_ = px_ - c1[0], py_ - c1[1]
        dist_ = math.hypot(dx_, dy_)
        daz = abs((math.atan2(dy_, dx_) - az + math.pi) % (2 * math.pi) - math.pi)
        top = gz(px_, py_) + 4.0 + 3.4 * 3 + 7.0
        if dist_ > 6 and daz < math.radians(4.0) and math.atan2(top - c1[2], dist_) > el - math.radians(1.0):
            hit = True
    keep_mask.append(not hit)
    V1_DROPPED += hit
plots = plots[np.array(keep_mask)]
# close tiny gaps between row neighbours (gaps under 2.5 m become party walls, alleys stay >= 2.5 m)
for i in range(len(plots)):
    for j in range(len(plots)):
        if i == j:
            continue
        a, b = plots[i], plots[j]
        ov_x = min(a[1], b[1]) - max(a[0], b[0]); ov_y = min(a[3], b[3]) - max(a[2], b[2])
        if ov_x > 4 and 0 < b[2] - a[3] < 2.5:
            m = (a[3] + b[2]) / 2; plots[i][3] = m; plots[j][2] = m
        if ov_y > 4 and 0 < b[0] - a[1] < 2.5:
            m = (a[1] + b[0]) / 2; plots[i][1] = m; plots[j][0] = m


def district(x, y):
    if x > -380 and y < -470:
        return "upper" if y > -620 else "poor"
    if x > -380 and y > -330:
        return "guard"
    if x > -400:
        return "upper"
    if x > -440 and y < -560:
        return "poor"
    if x < -585:
        return "river"
    if y > -400:
        return "merchant"
    if y < -520:
        return "artisan"
    return "market"


obstacles = [tuple(p) for p in plots] + SPECIAL


def clearance(i, side):
    x0, x1, y0, y1 = plots[i]
    cx_, cy_ = (x0 + x1) / 2, (y0 + y1) / 2
    best = 0.0
    for dd in np.arange(0.5, 14.0, 0.5):
        px, py = {"+x": (x1 + dd, cy_), "-x": (x0 - dd, cy_), "+y": (cx_, y1 + dd), "-y": (cx_, y0 - dd)}[side]
        if ell_dist(px, py) < 1.3:
            return dd
        hit = False
        for k, (a0, a1, b0, b1) in enumerate(obstacles):
            if k != i and a0 - 0.01 <= px <= a1 + 0.01 and b0 - 0.01 <= py <= b1 + 0.01:
                hit = True
                break
        if hit:
            return dd
        best = dd
    return 14.0


VARIANTS = [dict(st=s, pitch=p, jetty=j, upper=u, ridge=r) for s, p, j, u, r in
            [(2, 52, False, "GB_Plaster", "street"), (2, 58, True, "GB_Timber", "street"), (3, 55, True, "GB_Timber", "eaves"),
             (3, 50, False, "GB_Plaster", "street"), (4, 56, True, "GB_Timber", "street"), (2, 60, False, "GB_Timber", "eaves"),
             (3, 58, False, "GB_Stone", "street"), (4, 52, False, "GB_Plaster", "eaves"), (3, 60, True, "GB_Plaster", "street"),
             (2, 55, True, "GB_Plaster", "eaves"), (3, 52, True, "GB_Timber", "street"), (4, 58, True, "GB_Plaster", "street"),
             (2, 50, False, "GB_Stone", "street"), (3, 56, False, "GB_Timber", "eaves"), (4, 60, False, "GB_Stone", "eaves"),
             (2, 57, True, "GB_Timber", "street")]]

# enterable interiors on chosen plots (closest plot to each anchor, by district role)
ANCHORS = [("Main inn", "inn", (-440.0, -395.0), 3, True), ("Tavern at the East Gate", "tavern", (-450.0, -190.0), 2, False),
           ("Tavern in the River Quarter", "tavern", (-650.0, -470.0), 2, False), ("Blacksmith", "smith", (-470.0, -690.0), 2, False),
           ("Apothecary", "shop", (-425.0, -370.0), 2, False), ("Bakery", "bakery", (-505.0, -560.0), 2, False),
           ("Butcher", "shop", (-560.0, -520.0), 2, False), ("Cloth merchant and tailor", "shop", (-490.0, -340.0), 2, False),
           ("General store", "shop", (-430.0, -300.0), 2, False), ("Bathhouse", "bath", (-640.0, -410.0), 2, True),
           ("Barber-surgeon", "shop", (-515.0, -410.0), 2, False), ("Scribe and notary", "shop", (-500.0, -520.0), 2, False),
           ("Poor house 1", "house_poor", (-340.0, -660.0), 2, False), ("Poor house 2", "house_poor", (-380.0, -700.0), 2, False),
           ("Artisan house 1", "house", (-560.0, -640.0), 2, False), ("Artisan house 2", "house", (-610.0, -560.0), 2, False),
           ("Merchant house 1", "house_rich", (-500.0, -260.0), 3, False), ("Merchant house 2", "house_rich", (-545.0, -300.0), 3, False)]
used = set()
for name, kind, (ax_, ay_), st, merge in ANCHORS:
    d = [(math.hypot((p[0] + p[1]) / 2 - ax_, (p[2] + p[3]) / 2 - ay_), i) for i, p in enumerate(plots) if i not in used
         and min(p[1] - p[0], p[3] - p[2]) >= 9.5 and max(p[1] - p[0], p[3] - p[2]) >= 14.0]
    _, i = min(d)
    used.add(i)
    rect = list(plots[i])
    if merge:                                                    # merge with the touching neighbour along the frontage
        for j, q in enumerate(plots):
            if j in used:
                continue
            if abs(q[0] - rect[0]) < 3 and abs(q[1] - rect[1]) < 3 and (abs(q[2] - rect[3]) < 0.6 or abs(q[3] - rect[2]) < 0.6):
                rect = [min(rect[0], q[0]), max(rect[1], q[1]), min(rect[2], q[2]), max(rect[3], q[3])]
                used.add(j)
                break
    ENTER_SPECS.append(dict(name=name, rect=tuple(rect), front=None, kind=kind, storeys=st, plot=i))

# ---------------------------------------------------------------- closed houses
house_groups = {}
HOUSES = []
for i, (x0, x1, y0, y1) in enumerate(plots):
    if i in used:
        continue
    dist_ = district((x0 + x1) / 2, (y0 + y1) / 2)
    g = house_groups.setdefault(dist_, Group(f"SM_GB_City_Houses_{dist_.capitalize()}", F))
    sides = ["+x", "-x"] if (x1 - x0) >= (y1 - y0) else ["+y", "-y"]          # frontage = short side
    cl = {s: clearance(i, s) for s in ("+x", "-x", "+y", "-y")}
    front = max(sides, key=lambda s: cl[s])
    if cl[front] < 2.4:
        front = max(cl, key=cl.get)
    corner = sum(v >= 2.5 for v in cl.values()) >= 3
    v = VARIANTS[(i * 7 + len(dist_)) % 16]
    if dist_ == "poor":
        v = dict(v, st=2, upper="GB_Timber")
    if dist_ == "upper":
        v = dict(v, upper="GB_Stone" if i % 2 else v["upper"])
    fx, fy = {"+x": (x1, (y0 + y1) / 2), "-x": (x0, (y0 + y1) / 2), "+y": ((x0 + x1) / 2, y1), "-y": ((x0 + x1) / 2, y0)}[front]
    zf = gz(fx, fy) + 0.15
    zmin = min(gz(x, y) for x in (x0, x1) for y in (y0, y1))
    g.box(x0, x1, y0, y1, zmin - 0.8, zf, "GB_Stone")                          # plinth
    j = 0.6 if v["jetty"] else 0.0
    gx0, gx1, gy0, gy1 = x0, x1, y0, y1
    if j:                                                                      # ground floor set back under the jetty
        gx0 += j if front == "-x" else 0; gx1 -= j if front == "+x" else 0
        gy0 += j if front == "-y" else 0; gy1 -= j if front == "+y" else 0
    g.box(gx0, gx1, gy0, gy1, zf, zf + 4.0, "GB_Stone")                        # stone ground floor
    ze = zf + 4.0 + 3.4 * (v["st"] - 1)
    g.box(x0, x1, y0, y1, zf + 4.0, ze, v["upper"])
    ax = ("y" if front in ("+x", "-x") else "x") if v["ridge"] == "eaves" else ("x" if front in ("+x", "-x") else "y")
    span = (y1 - y0) if ax == "x" else (x1 - x0)
    if corner:
        g.pyramid(x0 - 0.4, x1 + 0.4, y0 - 0.4, y1 + 0.4, ze, ze + min(x1 - x0, y1 - y0) / 2 * math.tan(math.radians(v["pitch"])), "GB_Tile")
    else:
        g.gable(x0, x1, y0, y1, ze, ze + span / 2 * math.tan(math.radians(v["pitch"])), "GB_Tile", ax)
    # closed door + windows on the street front (lit or dark), chimney
    W_ = (y1 - y0) if front in ("+x", "-x") else (x1 - x0)
    c0 = np.array([fx, fy], float)
    nrm = {"+x": (1, 0), "-x": (-1, 0), "+y": (0, 1), "-y": (0, -1)}[front]
    tng = np.array([-nrm[1], nrm[0]], float)
    obox(g, c0 + np.array(nrm) * (0.05 - j), tng, 0.9, 0.08, zf, zf + 2.6, "GB_Wood", col=False)
    for k in range(1, v["st"]):
        for u in (-W_ / 3, 0.0, W_ / 3):
            lit = (i * 3 + k * 5 + int(u)) % 3 == 0
            obox(g, c0 + np.array(nrm) * 0.06 + tng * u, tng, 0.6, 0.06, zf + 4.0 + 3.4 * (k - 1) + 1.0,
                 zf + 4.0 + 3.4 * (k - 1) + 2.4, "GB_WinLit" if lit else "GB_WinDark", col=False)
    ccx, ccy = (x0 + x1) / 2 + tng[0] * W_ / 4, (y0 + y1) / 2 + tng[1] * W_ / 4
    g.box(ccx - 0.5, ccx + 0.5, ccy - 0.5, ccy + 0.5, ze, ze + span / 2 * math.tan(math.radians(v["pitch"])) * 0.8 + 1.2, "GB_Stone", col=False)
    HOUSES.append(dict(i=i, rect=[round(float(a), 2) for a in (x0, x1, y0, y1)], district=dist_, front=front, floor_z=round(zf, 2),
                       variant=(i * 7 + len(dist_)) % 16, storeys=v["st"], corner=corner))


# ---------------------------------------------------------------- enterable buildings (generic layout)
def L2W(rect, front, u, v):
    x0, x1, y0, y1 = rect
    return {"-x": (x0 + v, y0 + u), "+x": (x1 - v, y1 - u), "-y": (x1 - u, y0 + v), "+y": (x0 + u, y1 - v)}[front]


def lrect(rect, front, u0, u1, v0, v1):
    a, b = L2W(rect, front, u0, v0), L2W(rect, front, u1, v1)
    return min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1])


def ldir(front, du, dv):
    a, b = L2W((0, 0, 0, 0), front, 0, 0), L2W((0, 0, 0, 0), front, du, dv)
    return (b[0] - a[0], b[1] - a[1])


def ldoor(rect, front, room_w, side_pts, z0, z1):
    """Door given by two local points on a room boundary -> world (side, u0, u1, v0, v1) for Group.room."""
    (pa, pb) = [L2W(rect, front, *p) for p in side_pts]
    x0, x1, y0, y1 = room_w
    mx, my = (pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2
    d = {"n": abs(mx - x1), "s": abs(mx - x0), "e": abs(my - y1), "w": abs(my - y0)}
    side = min(d, key=d.get)
    if side in ("n", "s"):
        return (side, min(pa[1], pb[1]), max(pa[1], pb[1]), z0, z1)
    return (side, min(pa[0], pb[0]), max(pa[0], pb[0]), z0, z1)


PROPS = {"inn": "counter + 6 tables", "tavern": "counter + 4 tables", "smith": "forge + anvil", "bakery": "two bread ovens",
         "shop": "counter + shelves", "bath": "four tubs", "house_poor": "hearth + pallets", "house": "workbench + hearth",
         "house_rich": "table + hearth", "parish": "table + armoury racks"}
interiors = []
for spec in ENTER_SPECS:
    rect = spec["rect"]
    x0, x1, y0, y1 = rect
    if spec["front"] is None:
        i = spec["plot"]
        cl = {s: clearance(i, s) for s in ("+x", "-x", "+y", "-y")}
        sides = ["+x", "-x"] if (x1 - x0) <= (y1 - y0) else ["+y", "-y"]
        sides = ["+x", "-x", "+y", "-y"]
        spec["front"] = max(sides, key=lambda s: cl[s])
    front = spec["front"]
    W = (y1 - y0) if front in ("+x", "-x") else (x1 - x0)
    D = (x1 - x0) if front in ("+x", "-x") else (y1 - y0)
    fx, fy = L2W(rect, front, W / 2, 0)
    z0 = round(gz(fx, fy) + 0.2, 2)
    g = Group("SM_GB_City_Int_" + "".join(ch_ for ch_ in spec["name"].title() if ch_.isalnum()), F)
    zmin = min(gz(x, y) for x in (x0, x1) for y in (y0, y1))
    g.box(x0, x1, y0, y1, zmin - 0.8, z0 - 0.3, "GB_Stone")
    st = spec["storeys"]
    hz = [z0] + [z0 + 5.0 + 4.6 * k for k in range(st - 1)]                    # ground 5.0 m (4.7 clear), uppers 4.6 m
    t = 0.6
    big = spec["kind"] in ("inn", "tavern", "bath", "smith")
    dw = 3.0 if big else 2.4
    dh = 4.5 if big else 3.2
    wm = "GB_Stone"
    # stair flights against the back wall, alternating direction; landings at both ends
    run = 22 * 0.27
    flights = []
    for k in range(st - 1):
        rise = hz[k + 1] - hz[k]
        n = int(round(rise / 0.2)); rr = n * 0.27
        if k % 2 == 0:
            ua, ub, du = 1.6, 1.6 + rr, 1.0
        else:
            ua, ub, du = W - 1.6, W - 1.6 - rr, -1.0
        vb = D - 0.3 - 1.25 - (2.8 if k % 2 else 0.0)
        flights.append((ua, ub, du, vb, hz[k], hz[k + 1]))
        g.stairs(L2W(rect, front, ua, vb), ldir(front, du, 0), 2.5, hz[k], hz[k + 1], "GB_Wood", 0.2, 0.27)
    for k in range(st):
        zf = hz[k]; zc = hz[k + 1] - 0.3 if k + 1 < st else zf + 4.7
        rw = lrect(rect, front, 0, W, 0, D)
        holes_f = []
        if k > 0:                                                               # hole above the flight arriving here
            ua, ub, du, vb, _, _ = flights[k - 1]
            holes_f.append(lrect(rect, front, min(ua, ub) - 0.1, max(ua, ub), vb - 1.35, vb + 1.35))
        doors = []
        if k == 0:
            doors.append(ldoor(rect, front, rw, [(W / 2 - dw / 2, 0), (W / 2 + dw / 2, 0)], zf, zf + dh))
        R_ = dict(x0=rw[0] + t / 2, x1=rw[1] - t / 2, y0=rw[2] + t / 2, y1=rw[3] - t / 2, z0=zf, z1=zc)
        g.room(R_, doors=doors, mat_wall=wm if k == 0 else "GB_Plaster", t=t, holes_floor=holes_f, ceil=(k == st - 1))
        rname = f"{spec['name']}: {'ground floor' if k == 0 else f'floor {k}'}"
        R(rname, R_["x0"], R_["x1"], R_["y0"], R_["y1"], zf, zc - zf, spec["kind"])
        # partition between the front room and the back strip (stairs, landings); one 3.4 m opening by the stair
        vp = D - 0.3 - 2.8 * (2 if st > 2 else 1) - 0.2
        if st > 1:
            if k == 0:
                gap = (0.4, 3.8)                                                # at the foot of the first flight
            else:
                ua, ub, du, vb, _, _ = flights[k - 1]
                gap = (min(ub, W - 3.8), min(ub, W - 3.8) + 3.4) if du > 0 else (max(ub - 3.4, 0.4), max(ub - 3.4, 0.4) + 3.4)
            for (p0_, p1_) in ((0.3, gap[0]), (gap[1], W - 0.3)):
                if p1_ - p0_ > 0.2:
                    b_ = lrect(rect, front, p0_, p1_, vp - 0.15, vp + 0.15)
                    g.box(b_[0], b_[1], b_[2], b_[3], zf, zc, "GB_Plaster")
        if k > 0:                                                               # rails around the stairwell (1.1 m)
            ua, ub, du, vb, _, _ = flights[k - 1]
            lo_, hi_ = min(ua, ub), max(ua, ub)
            for rr_ in (lrect(rect, front, lo_ - 0.1, hi_ - 0.1, vb - 1.5, vb - 1.35),
                        lrect(rect, front, (lo_ - 0.4) if du > 0 else (hi_ + 0.1), (lo_ - 0.1) if du > 0 else (hi_ + 0.4), vb - 1.5, vb + 1.25)):
                g.box(rr_[0], rr_[1], rr_[2], rr_[3], zf, zf + 1.1, "GB_Wood")
        if k > 0 and spec["kind"] == "inn":                                     # 3 m corridor + 3 bedrooms per upper floor
            vc = vp - 3.0
            nrooms = 3
            for r_ in range(nrooms):
                u0r, u1r = W * r_ / nrooms, W * (r_ + 1) / nrooms
                dm = (u0r + u1r) / 2
                for (p0_, p1_) in ((u0r, dm - 1.0), (dm + 1.0, u1r)):
                    b_ = lrect(rect, front, max(p0_, 0.3), min(p1_, W - 0.3), vc - 0.15, vc + 0.15)
                    g.box(b_[0], b_[1], b_[2], b_[3], zf, zc, "GB_Plaster")
                g.box(*lrect(rect, front, dm - 1.0, dm + 1.0, vc - 0.15, vc + 0.15)[:4], zf + 3.0, zc, "GB_Plaster")   # over the door
                if r_ > 0:
                    b_ = lrect(rect, front, u0r - 0.15, u0r + 0.15, 0.3, vc)
                    g.box(b_[0], b_[1], b_[2], b_[3], zf, zc, "GB_Plaster")
                R(f"{spec['name']}: bedroom {r_ + 1 + (k - 1) * nrooms}", *lrect(rect, front, u0r + 0.3, u1r - 0.3, 0.3, vc - 0.2), zf, zc - zf, "inn")
    # props (furniture hugging the walls, 60 % of the floor kept clear)
    kind = spec["kind"]
    zf = hz[0]
    if kind in ("inn", "tavern", "shop", "bath", "bakery", "smith"):
        a = lrect(rect, front, 0.8, W * 0.45, D * 0.35, D * 0.35 + 1.0)
        g.box(a[0], a[1], a[2], a[3], zf, zf + 1.1, "GB_Wood")                 # counter / workbench
    if kind == "smith":
        a = lrect(rect, front, W - 3.2, W - 0.8, 1.0, 3.4); g.box(a[0], a[1], a[2], a[3], zf, zf + 1.0, "GB_Stone")   # forge
        a = lrect(rect, front, W / 2, W / 2 + 0.8, 2.0, 2.6); g.box(a[0], a[1], a[2], a[3], zf, zf + 0.8, "GB_Metal")  # anvil
    if kind == "bakery":
        for uo in (0.8, 3.6):
            a = lrect(rect, front, uo, uo + 2.4, D * 0.5, D * 0.5 + 2.4); g.box(a[0], a[1], a[2], a[3], zf, zf + 1.8, "GB_Stone")
    if kind == "bath":
        for k in range(4):
            a = lrect(rect, front, 1.0 + k * (W - 2.0) / 4, 1.0 + k * (W - 2.0) / 4 + 2.0, 1.0, 3.0)
            g.box(a[0], a[1], a[2], a[3], zf, zf + 0.8, "GB_Wood")
    # roof
    ze = hz[-1] + 5.0
    ax = "x" if front in ("+x", "-x") else "y"
    span = (y1 - y0) if ax == "x" else (x1 - x0)
    g.box(x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, ze - 0.3, ze, "GB_Stone")
    g.gable(x0, x1, y0, y1, ze, ze + span / 2 * math.tan(math.radians(55)), "GB_Tile", ax)
    interiors.append(g)
    ENTER.append(dict(name=spec["name"], kind=kind, props=PROPS.get(kind, ""), rect=[round(float(a), 2) for a in rect], front=front,
                      floor_z=hz, door_w=dw, door_h=dh, group=g.name))

# ---------------------------------------------------------------- outputs
groups = [walls, gates] + [v["doors"] for v in GATE_INFO.values()] + [GATE_INFO["north"]["portcullis"], GATE_INFO["north"]["barbican_doors"],
          church, yard, man, gd, pub, gup, bkp, mkt] + list(house_groups.values()) + interiors
json.dump([g.to_json() for g in groups], open(f"{ROOT}/greybox/city_groups.json", "w"))
n_bld = len(HOUSES) + len(interiors) - 1 + 4                                     # + town hall, guild hall, barracks, church
meta = dict(rooms=ROOMS, voids=VOIDS, movable=MOVABLE, towers=TOWERS, wall_stairs=WALK_STAIRS,
            gates={k: {kk: vv for kk, vv in v.items() if kk not in ("doors", "portcullis", "barbican_doors")} for k, v in GATE_INFO.items()},
            houses=HOUSES, interiors=ENTER, plots_from_plan=len(plots) + sum(dropped.values()) + V1_DROPPED, plots_dropped=dict(dropped, v1_sightline=V1_DROPPED),
            buildings_inside_walls=n_bld + 1, manor_court_z=ZM, barracks_rect=[BX0, BX1, BY0, BY1], barracks_shift_m=BARRACKS_SHIFT, church_floor_z=ZC, bell_chamber_z=BELL)
json.dump(meta, open(f"{ROOT}/greybox/city_meta.json", "w"), indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
print("city groups", len(groups), "houses", len(HOUSES), "interiors", len(interiors), "dropped", dropped,
      "buildings inside", meta["buildings_inside_walls"], "towers", len(TOWERS))
print("districts", {k: len(g.prims) for k, g in house_groups.items()})
