# The hunters' lodge (Fantasy Castle shell, Hawtor Studio) at the far south-west of the valley, its secret stair and
# the underground library (Classic Library kit, denniswoo1993, architecture scaled x1.5). World metres, +X north, +Y east.
# Our geometry (floors, partitions, the stair tunnel, the library walls, galleries and grand stair) and the invisible
# collision of every kit piece go to greybox/lodge_groups.json; the kit pieces themselves (mesh, position, yaw, scale)
# to data/placements_lodge.json; rooms, pad, voids, movable pieces and lights to greybox/lodge_meta.json.
#
# Lodge frame: origin at the shell centre (O) on the pad (P), axes = world axes; the main door is on +X (north, facing
# the valley), the library lies to +Y (east). Library frame: u = x - X0 (across), v = y - Y0 (along), w = z - F.
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gb_lib import Group, rect_minus
from tlib import sample

ROOT = sys.argv[1]
HN = f"{ROOT}/terrain/H_natural_4033.npy"
H = np.load(HN if os.path.exists(HN) else f"{ROOT}/terrain/H_4033.npy")
KIT = json.load(open(f"{ROOT}/data/kit_library.json"))
gz = lambda x, y: float(sample(H, np.atleast_1d(float(x)), np.atleast_1d(float(y)))[0])

O = np.array([-1400.0, -700.0]); P = 81.0           # lodge: shell centre, pad level
FL = 0.08                                           # lodge floor (top), lodge frame
S = 1.5                                             # library architecture scale (15 m bays, 12 m columns, vault apex 28 m)
BAY, NB = 15.0, 8
F = 40.0                                            # library floor (world z)
LV = [0.0, 5.1, 10.2]                               # library levels (w): floor, first and second gallery
groups, PL, ROOMS, LIGHTS, MOVABLE, VOIDS = [], [], [], [], [], []


def G(name, folder, frame):
    g = Group(name, folder); g.frame = frame; groups.append(g)
    return g


def R(frame, name, x0, x1, y0, y1, z0, h, **kw):
    ox, oy, oz = frame
    ROOMS.append(dict(name=name, x0=round(x0 + ox, 2), x1=round(x1 + ox, 2), y0=round(y0 + oy, 2), y1=round(y1 + oy, 2),
                      z0=round(z0 + oz, 2), z1=round(z0 + h + oz, 2), **kw))


def light(frame, name, x, y, z, lm, radius, color=(1.0, 0.72, 0.45), shadows=False):
    ox, oy, oz = frame
    LIGHTS.append(dict(name=name, xyz=[round(x + ox, 2), round(y + oy, 2), round(z + oz, 2)], lumens=lm, radius=radius,
                       color=list(color), shadows=shadows))


def rot(yaw):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    return np.array([[c, -s], [s, c]])


def place(frame, key, x, y, z, yaw=0.0, s=1.0, col=None, gcol=None, folder="Props/LibraryKit"):
    """Kit piece `key` (PF_LB_* in the kit file) -> placement of SM_LB_*; col='box' adds its bounding box (rotated) to
    the collision group, col='treads' one hull per step (spiral stair)."""
    ox, oy, oz = frame
    sc = np.array([s, s, s] if np.isscalar(s) else s, float)
    PL.append(dict(mesh=key.replace("PF_", "SM_"), folder=folder, loc=[round(x + ox, 3), round(y + oy, 3), round(z + oz, 3)],
                   yaw=round(yaw, 2), scale=sc.round(4).tolist()))
    if col is None or gcol is None:
        return
    k = KIT[key]; Rm = rot(yaw)
    if col == "box":
        lo, hi = np.array(k["lo"]) * sc, np.array(k["hi"]) * sc
        pts = [Rm @ p + [x, y] for p in ([lo[0], lo[1]], [hi[0], lo[1]], [hi[0], hi[1]], [lo[0], hi[1]])]
        gcol.poly_prism([tuple(p) for p in pts], z + lo[2], z + hi[2], "GB_Stone", "only")
    elif col == "treads":                                  # spiral: helical ramp (one sloped hull per step) + platform
        steps = [t for t in k["treads"] if t["area"] < 0.3]
        ang = [math.degrees(math.atan2(*np.mean(t["poly"], 0)[::-1])) for t in steps]
        ang = np.unwrap(np.radians(ang)); zs = [t["z"] for t in steps]
        da = ang[1] - ang[0]
        ang = np.concatenate([[ang[0] - da], ang, [ang[-1] + da]]); zs = [0.0] + zs + [k["treads"][-1]["z"]]
        for a0, a1, z0_, z1_ in zip(ang[:-1], ang[1:], zs[:-1], zs[1:]):
            am = (a0 + a1) / 2
            out0, out1 = 1.6 * np.array([math.cos(a0), math.sin(a0)]), 1.6 * np.array([math.cos(a1), math.sin(a1)])
            inn = 0.18 * np.array([math.cos(am), math.sin(am)])
            # top plane through the two outer corners (z0_, z1_) and the inner point at mid height: all corners on it
            A = np.array([[*out0, 1], [*out1, 1], [*inn, 1]]); cz = np.linalg.solve(A, [z0_, z1_, (z0_ + z1_) / 2])
            inn0, inn1 = 0.18 * np.array([math.cos(a0), math.sin(a0)]), 0.18 * np.array([math.cos(a1), math.sin(a1)])
            quad = [inn0, out0, out1, inn1]
            top = [(*(Rm @ (q * sc[:2]) + [x, y]), z + (cz[0] * q[0] + cz[1] * q[1] + cz[2]) * sc[2]) for q in quad]
            bot = [(a_, b_, c_ - 0.35) for a_, b_, c_ in top]
            gcol.add(bot + top, [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]], "GB_Stone", "only")
        t = k["treads"][-1]                                # top platform
        pts = [tuple(Rm @ (np.array(p) * sc[:2]) + [x, y]) for p in t["poly"]]
        gcol.poly_prism(pts, z + t["z"] * sc[2] - 0.3, z + t["z"] * sc[2], "GB_Stone", "only")
        gcol.cyl(x, y, 0.16, z, z + k["hi"][2] * sc[2], "GB_Stone", 8, "only")


def rail_x(g, gc, frame, y, xa, xb, z, h=1.2):
    """Wooden balustrade along X from xa to xb at y (kit railing, stretched to the length) + its collision."""
    L = abs(xb - xa); n = max(1, int(round(L / 5.1)))
    for i in range(n):
        cx = min(xa, xb) + L * (i + 0.5) / n
        place(frame, "PF_LB_RailingWood", cx, y, z, 0.0, (L / n / 5.11, 1.0, 1.0))
    gc.box(min(xa, xb), max(xa, xb), y - 0.12, y + 0.12, z, z + h, "GB_Stone", "only")


def rail_y(g, gc, frame, x, ya, yb, z, h=1.2):
    L = abs(yb - ya); n = max(1, int(round(L / 5.1)))
    for i in range(n):
        cy = min(ya, yb) + L * (i + 0.5) / n
        place(frame, "PF_LB_RailingWood", x, cy, z, 90.0, (L / n / 5.11, 1.0, 1.0))
    gc.box(x - 0.12, x + 0.12, min(ya, yb), max(ya, yb), z, z + h, "GB_Stone", "only")


def rail_slope(g, gc, p0, p1, z0, z1, mat="LB_GlossyWood"):
    """Handrail on posts along a flight edge (p0 at z0 -> p1 at z1), with a sloped collision wall."""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    L = np.linalg.norm(p1 - p0); n = max(2, int(L / 1.5) + 1)
    for i in range(n):
        t = i / (n - 1); p = p0 + (p1 - p0) * t; zz = z0 + (z1 - z0) * t
        g.box(p[0] - 0.06, p[0] + 0.06, p[1] - 0.06, p[1] + 0.06, zz - 0.05, zz + 1.0, mat, False)
    g.ramp(p0, p1, 0.12, z0 + 1.05, z1 + 1.05, 0.1, mat, col=False)
    gc.ramp(p0, p1, 0.2, z0 + 1.15, z1 + 1.15, 1.45, "GB_Stone", col=True, visible=False)


# =====================================================================================================================
# 1. the lodge (shell + interiors), lodge frame
LF = (O[0], O[1], P)
place(LF, "SM_FC_Lodge", 0, 0, 0, folder="Environment/Lodge")
PL[-1]["mesh"] = "SM_FC_Lodge"
gI = G("SM_GB_Lodge_Interior", "Environment/Lodge", LF)
gC = G("SM_GB_Lodge_Collision", "Environment/Lodge", LF)
# solid masses of the shell that are not visited (the shell itself has no collision in Unreal)
gC.box(-21.3, 6.5, -15.2, 0.0, 0, 18, "GB_Stone", "only")                     # courtyard block (closed courtyard)
gC.box(-17.0, 1.5, 0.0, 5.0, 0, 18, "GB_Stone", "only")                       # north block
gC.box(1.5, 6.5, 0.0, 16.6, 0, 26, "GB_Stone", "only")                        # keep
for cx, cy, r in ((-21.25, -15.2, 1.4), (-21.3, 0.0, 1.3), (6.3, -15.2, 1.3), (3.8, 3.4, 3.65), (9.0, 6.5, 3.25)):
    gC.cyl(cx, cy, r, 0, 24, "GB_Stone", 16, "only")
# hall wing: walls 0.5 m behind the shell faces, door opening on the east gable (x 22.3, y -2.7 .. -0.45)
gC.box(6.5, 22.8, -7.2, -6.7, 0, 8, "GB_Stone", "only")
gC.box(6.5, 22.8, 3.9, 4.4, 0, 8, "GB_Stone", "only")
gC.box(22.3, 22.8, -7.2, -2.7, 0, 8, "GB_Stone", "only")
gC.box(22.3, 22.8, -0.45, 4.4, 0, 8, "GB_Stone", "only")
gC.box(21.8, 22.8, -2.7, -0.45, 3.3, 8, "GB_Stone", "only")
gC.box(6.5, 22.8, -7.2, 4.4, 7.3, 7.8, "GB_Stone", "only")
gC.box(21.79, 22.8, -2.8, -0.35, FL - 0.4, FL, "GB_Stone", "only")             # door sill
# floors: stone tiles in the hall, oak boards in the study; the hidden room is a stair well
HR = (7.5, 10.9, -0.2, 3.2)                                                     # hidden room (interior)
for a in rect_minus((12.4, 22.3, -6.7, 3.9), []):
    gI.box(*a, FL - 0.35, FL, "FC_StoneTiles")
for a in rect_minus((6.5, 12.0, -6.7, 3.9), [(HR[0] - 0.3, HR[1] + 0.3, HR[2] - 0.3, HR[3] + 0.3)]):
    gI.box(*a, FL - 0.35, FL, "LB_WoodFloor")
gI.box(12.0, 12.4, -6.7, 3.9, FL - 0.35, FL, "FC_StoneTiles")
# partition hall | study (door y -5.4..-4.2), study ceiling (oak boards on beams)
gI.wall("y", 12.0, 12.4, -6.7, 3.9, FL, 7.3, "FC_StoneBrickWall", holes=[(-5.4, -4.2, FL, FL + 2.4)])
gI.box(11.9, 12.5, -5.5, -4.1, FL + 2.4, FL + 2.7, "LB_Stone")                   # lintel
gI.box(6.5, 12.0, -6.7, 3.9, 4.8, 5.0, "FC_WoodPlanks")
for bx in (7.6, 9.3, 11.0):
    gI.box(bx - 0.15, bx + 0.15, -6.7, 3.9, 4.45, 4.8, "LB_GlossyWood", False)
# hidden room: false walls (brick like the shell), shaft down to -4.72 with the tunnel opening on +Y
SB = FL - 4.8                                                                   # shaft bottom = spiral base
gI.wall("x", HR[2] - 0.3, HR[2], HR[0] - 0.3, HR[1] + 0.3, SB - 0.4, 4.8, "FC_StoneBrickWall", holes=[(9.3, 10.7, FL, FL + 2.2)])
gI.box(9.2, 10.8, HR[2] - 0.35, HR[2] + 0.05, FL + 2.2, FL + 2.45, "LB_GlossyWood")  # door lintel behind the wardrobe
gI.wall("y", HR[0] - 0.3, HR[0], HR[2] - 0.3, HR[3] + 0.3, SB - 0.4, 4.8, "FC_StoneBrickWall")
gI.wall("y", HR[1], HR[1] + 0.3, HR[2] - 0.3, HR[3] + 0.3, SB - 0.4, 4.8, "FC_StoneBrickWall")
gI.wall("x", HR[3], HR[3] + 0.3, HR[0] - 0.3, HR[1] + 0.3, SB - 0.4, 4.8, "FC_StoneBrickWall", holes=[(7.9, 9.9, SB, SB + 2.7)])
gI.box(HR[0] - 0.3, HR[1] + 0.3, HR[2] - 0.3, HR[3] + 0.3, SB - 0.45, SB, "LB_Stone")
SP = (9.2, 1.5)                                                                 # spiral centre, yaw 90: top platform
place(LF, "PF_LB_SpiralStair", SP[0], SP[1], SB, 90.0, col="treads", gcol=gC)  # toward -Y (the door), foot toward +Y
gC.box(9.2, 10.8, HR[2] - 0.32, HR[2] + 0.02, FL - 0.3, FL, "GB_Stone", "only")    # threshold
VOIDS.append([round(O[0] + HR[0] - 0.5, 2), round(O[0] + HR[1] + 0.5, 2), round(O[1] + HR[2] - 0.5, 2), round(O[1] + HR[3] + 0.5, 2),
              round(P + SB - 0.7, 2)])
# the wardrobe in front of the hidden door (slides 2 m toward -X: a ScriptedDoor in Unreal)
gW = G("SM_GB_Lodge_SecretWardrobe", "Environment/Lodge", LF)
WX0, WX1, WY0, WY1 = 9.0, 11.0, -1.25, -0.52
gW.box(WX0, WX1, WY0, WY1, FL + 0.12, FL + 2.38, "LB_GlossyWood")
gW.box(WX0 - 0.05, WX1 + 0.05, WY0 - 0.07, WY1, FL + 2.38, FL + 2.55, "LB_GlossyWood")
gW.box(WX0 + 0.02, WX1 - 0.02, WY0 - 0.02, WY1, FL, FL + 0.12, "LB_GlossyWood")
for x_a, x_b in ((WX0 + 0.08, (WX0 + WX1) / 2 - 0.02), ((WX0 + WX1) / 2 + 0.02, WX1 - 0.08)):
    gW.box(x_a, x_b, WY0 - 0.04, WY0, FL + 0.25, FL + 2.28, "FC_WoodPlanks", False)
gW.box((WX0 + WX1) / 2 - 0.12, (WX0 + WX1) / 2 - 0.06, WY0 - 0.08, WY0 - 0.04, FL + 1.1, FL + 1.4, "LB_Metal", False)
gW.box((WX0 + WX1) / 2 + 0.06, (WX0 + WX1) / 2 + 0.12, WY0 - 0.08, WY0 - 0.04, FL + 1.1, FL + 1.4, "LB_Metal", False)
MOVABLE.append(dict(name="SM_GB_Lodge_SecretWardrobe", pivot=[round(O[0] + WX0, 2), round(O[1] + WY1, 2), round(P + FL, 2)],
                    motion="slide", offset=[-2.0, 0.0, 0.0], note="slides 2 m along the false wall, uncovering the hidden door"))
# study furniture: bookcase on the west wall, reading table
place(LF, "PF_LB_Bookcase", 6.78, -3.8, FL, 180.0, col="box", gcol=gC)
place(LF, "PF_LB_ReadingSet", 9.4, -4.05, FL, 0.0, col="box", gcol=gC)
R(LF, "Lodge study", 6.6, 12.0, -6.6, -0.5, FL, 4.7, interior="lodge")
R(LF, "Lodge hidden stair (top platform)", 9.25, 10.8, -0.1, 1.4, FL, 4.7, interior="lodge", sealed=True)
light(LF, "lodge_study", 9.4, -4.0, 3.4, 1500, 9, shadows=True)
light(LF, "lodge_hidden_room", 9.2, 1.5, 2.6, 250, 6)
light(LF, "lodge_shaft_bottom", 8.9, 3.0, SB + 2.3, 400, 6)
# great hall: fireplace on the partition, beams, banquet table, chandeliers, chests, rug, open double door
gI.box(12.4, 12.6, -0.6, 2.6, FL, 7.3, "LB_Stone")                               # chimney breast: back,
gI.wall("y", 12.6, 13.3, -0.6, 2.6, FL, 7.3, "LB_Stone", holes=[(0.1, 1.9, FL, FL + 1.75)])   # front with the firebox
gI.box(12.6, 13.25, 0.1, 1.9, FL + 1.75, FL + 1.95, "GB_WinDark", False)        # soot under the hood
gI.box(12.6, 12.66, 0.1, 1.9, FL, FL + 1.75, "GB_WinDark", False)               # fire back
gI.box(12.4, 13.5, -0.9, 2.9, FL + 2.3, FL + 2.65, "LB_Stone")                  # mantel
gI.box(13.3, 13.9, -1.0, 3.0, FL, FL + 0.12, "LB_Stone")                        # hearth stone
gI.box(12.66, 13.2, 0.3, 1.7, FL, FL + 0.08, "GB_WinLit", False)                # embers
for k_, (y_a, y_b) in enumerate(((0.35, 1.55), (0.5, 1.7), (0.42, 1.62))):     # logs on the fire dogs
    xx = 12.8 + 0.13 * k_; zz = FL + 0.1 + (0.12 if k_ == 2 else 0.0)
    gI.box(xx - 0.07, xx + 0.07, y_a, y_b, zz, zz + 0.14, "FC_WoodPlanks", False)
for yy in (0.4, 1.6):
    gI.box(13.0, 13.08, yy - 0.04, yy + 0.04, FL, FL + 0.3, "LB_Metal", False)
gC.box(12.4, 13.9, -1.0, 3.0, FL, 7.3, "GB_Stone", "only")
for bx in (14.5, 16.6, 18.7, 20.8):
    gI.box(bx - 0.17, bx + 0.17, -6.7, 3.9, 6.85, 7.3, "FC_WoodPlanks", False)
place(LF, "PF_LB_ReadingSet", 17.2, -1.4, FL, 90.0, col="box", gcol=gC)
gI.box(14.6, 19.8, -2.9, 0.1, FL, FL + 0.015, "LB_Leather", False)              # rug
for cx in (16.6, 18.7):                                                           # hung from the beams
    place(LF, "PF_LB_Chandelier", cx, -1.4, 6.85)
    light(LF, f"lodge_hall_chandelier_{cx:.0f}", cx, -1.4, 3.6, 2500, 11, shadows=cx < 17)
light(LF, "lodge_hall_fire", 13.6, 1.0, 0.9, 3500, 9, color=(1.0, 0.55, 0.25), shadows=True)
for cx in (14.7, 16.75, 18.8, 20.85):                                            # chests under the windows
    for cy, dy in ((-6.7, 1), (3.9, -1)):
        y_a, y_b = sorted((cy + dy * 0.05, cy + dy * 0.65))
        gI.box(cx - 0.55, cx + 0.55, y_a, y_b, FL, FL + 0.62, "LB_GlossyWood")
        gI.box(cx - 0.58, cx + 0.58, y_a - 0.02, y_b + 0.02, FL + 0.62, FL + 0.7, "FC_WoodPlanks")
for cy0, cy1 in ((-6.2, -3.1), (0.6, 3.4)):                                       # weapon racks flanking the door
    gI.box(21.95, 22.25, cy0, cy1, FL, FL + 0.25, "LB_GlossyWood")
    gI.box(21.95, 22.25, cy0, cy1, FL + 1.75, FL + 1.9, "LB_GlossyWood")
    for k in range(6):
        yy = cy0 + 0.25 + k * (cy1 - cy0 - 0.5) / 5
        gI.box(22.02, 22.08, yy - 0.02, yy + 0.02, FL + 0.25, FL + 1.75, "LB_Metal", False)
    gC.box(21.9, 22.3, cy0, cy1, FL, FL + 1.9, "GB_Stone", "only")
for side, yh in (("L", -2.7), ("R", -0.45)):                                     # door leaves, open inward
    gD = G(f"SM_GB_Lodge_Door{side}", "Environment/Lodge", LF)
    sgn = 1 if side == "L" else -1
    gD.box(20.7, 21.78, yh + sgn * 0.0 - (0.1 if sgn < 0 else 0), yh + (0.1 if sgn > 0 else 0), FL, FL + 3.05, "FC_WoodPlanks")
    MOVABLE.append(dict(name=f"SM_GB_Lodge_Door{side}", pivot=[round(O[0] + 21.78, 2), round(O[1] + yh, 2), round(P + FL, 2)],
                        motion="hinge", note="open (90 deg); closes to the door plane"))
R(LF, "Lodge great hall", 13.9, 22.2, -6.6, 3.8, FL, 7.2, interior="lodge")
light(LF, "lodge_porch", 23.5, -1.6, 3.6, 800, 8)

# =====================================================================================================================
# 2. the secret stair: shaft foot (SB) -> long stone stair toward +Y -> the library balcony (F + LV[2]), lodge frame
gT = G("SM_GB_Lodge_SecretStair", "Environment/Lodge", LF)
TX, TW = 8.9, 2.0                                     # axis x and clear width
xa, xb = TX - TW / 2, TX + TW / 2
z_end = F + LV[2] - P                                 # balcony level in the lodge frame
drop = SB - z_end
nr = int(math.ceil(drop / 0.17)); rh = drop / nr; RUN = 0.32; PER = 16; LAND = 1.6
y = HR[3] + 0.3                                       # leaves the shaft through its north wall
segs = [("flat", y, y + 2.2, SB)]
y += 2.2; z = SB; left = nr; k = 0
while left > 0:
    m = min(PER, left)
    segs.append(("flight", y, y + m * RUN, z, z - m * rh)); y += m * RUN; z -= m * rh; left -= m; k += 1
    if left > 0:
        segs.append(("flat", y, y + LAND, z)); y += LAND
segs.append(("flat", y, y + 2.6, z, 4.3)); y += 2.6                          # taller vestibule at the library door
Y_END = y                                             # lodge frame y where the tunnel meets the library's west wall
HEAD = 3.0
clear = []
for s in segs:
    if s[0] == "flat":
        y0, y1, zz = s[1:4]; hd = s[4] if len(s) > 4 else HEAD
        gT.box(xa - 0.5, xb + 0.5, y0, y1, zz - 0.45, zz, "LB_Stone")
        gT.box(xa - 0.5, xb + 0.5, y0, y1, zz + hd, zz + hd + 0.4, "LB_Sandstone")
        for xw in ((xa - 0.5, xa), (xb, xb + 0.5)):
            gT.box(*xw, y0, y1, zz - 0.45, zz + hd + 0.4, "LB_Sandstone")
        gT.box(xa - 0.5, xb + 0.5, y0 + (y1 - y0) / 2 - 0.25, y0 + (y1 - y0) / 2 + 0.25, zz + hd - 0.35, zz + hd, "LB_Stone", False)
        lo_, hi_ = zz, zz
    else:
        _, y0, y1, za, zb = s
        n = int(round((za - zb) / rh))
        for i in range(n):                                                    # descending steps (solid)
            ys0, ys1 = y0 + i * RUN, y0 + (i + 1) * RUN
            gT.box(xa, xb, ys0, ys1, zb - 0.45, za - (i + 1) * rh, "LB_Stone", False)
        gT.ramp((TX, y0 - 0.05), (TX, y1), TW, za, zb, 0.45, "LB_Stone", col=True, visible=False)
        gT.ramp((TX, y0), (TX, y1), TW + 1.0, za + HEAD + 0.4, zb + HEAD + 0.4, 0.4, "LB_Sandstone")
        for xw in ((xa - 0.5, xa), (xb, xb + 0.5)):
            gT.box(*xw, y0, y1, zb - 0.45, za + HEAD + 0.4, "LB_Sandstone")
        rail_slope(gT, gT, (xa + 0.12, y0), (xa + 0.12, y1), za, zb, "LB_Metal")
        lo_, hi_ = zb, za
    for yy in np.arange(s[1], s[2] + 0.01, 1.0):                             # terrain cover over the vault
        top = (hi_ if s[0] == "flat" else s[3] - (yy - s[1]) / RUN * rh) + HEAD + 0.4
        clear.append((round(yy, 1), round(gz(O[0] + TX, O[1] + yy) - (P + top), 2)))
landings = [s for s in segs if s[0] == "flat"]
for i, s in enumerate(landings):
    if i % 2 == 0 or i == len(landings) - 1:                                  # torches on every other landing
        ym = (s[1] + s[2]) / 2
        gT.box(xb - 0.05, xb, ym - 0.15, ym + 0.15, s[3] + 1.9, s[3] + 2.3, "LB_Metal", False)
        gT.box(xb - 0.25, xb - 0.05, ym - 0.06, ym + 0.06, s[3] + 2.25, s[3] + 2.45, "GB_WinLit", False)
        light(LF, f"stair_torch_{i}", xb - 0.4, ym, s[3] + 2.3, 700, 9, color=(1.0, 0.6, 0.3), shadows=i % 4 == 0)
cover = min(c for yy, c in clear if yy > 10)            # past the hall wing the vault is under the landscape
R(LF, "Secret stair, foot of the spiral", xa, xb, HR[3] + 0.35, HR[3] + 2.4, SB, 3.0, interior="lodge", sealed=True)
mid = landings[len(landings) // 2]
R(LF, "Secret stair, middle landing", xa, xb, mid[1], mid[2], mid[3], 3.0, interior="lodge", sealed=True)

# =====================================================================================================================
# 3. the library, library frame (u across = x, v along = y, w up)
X0, Y0 = O[0] + TX, O[1] + Y_END + 1.0
LBF = (X0, Y0, F)
W2, LEN = 22.5, BAY * NB
gLW = G("SM_GB_Library_Walls", "Environment/Library", LBF)
gLF = G("SM_GB_Library_Floors", "Environment/Library", LBF)
gLS = G("SM_GB_Library_GrandStair", "Environment/Library", LBF)
gLC = [G(f"SM_GB_Library_Collision{i}", "Environment/Library", LBF) for i in range(4)]
gc_of = lambda u, l: gLC[(0 if u < 0 else 1) + 2 * (l >= 1)]
TOPW = 29.5
# shell: walls (door on the west wall at the balcony, the great window in the nave bay of the east wall), roof, floor
gLW.wall("x", -1.0, 0.0, -W2 - 1, W2 + 1, -0.6, TOPW, "LB_Sandstone", holes=[(-1.0, 1.0, LV[2], LV[2] + 4.3)])
gLW.wall("x", LEN, LEN + 1.0, -W2 - 1, W2 + 1, -0.6, TOPW, "LB_Sandstone", holes=[(-7.5, 7.5, -0.6, 26.9)])
gLW.box(-7.5, 7.5, LEN + 0.6, LEN + 1.6, -0.6, 26.95, "LB_Sandstone")          # backing behind the window wall
gLW.wall("y", W2, W2 + 1.0, -1.0, LEN + 1.0, -0.6, TOPW, "LB_Sandstone")
gLW.wall("y", -W2 - 1.0, -W2, -1.0, LEN + 1.0, -0.6, TOPW, "LB_Sandstone")
gLW.box(-W2 - 1, W2 + 1, -1.0, LEN + 1.6, TOPW, TOPW + 0.5, "LB_Sandstone", False)
gLF.box(-W2, W2, 0.0, LEN, -0.5, 0.0, "LB_WoodFloor")
gLF.box(-W2, W2, 0.0, 0.6, 0.0, 0.25, "LB_Stone", False)                      # skirting stones
# columns, vaults and ribs of the kit (x1.5); free-standing columns get a collision box
for u in (-W2, -7.5, 7.5, W2):
    for kk in range(NB + 1):
        v = BAY * kk
        place(LBF, "PF_LB_Column", u, v, 0.0, 0.0, S, col="box", gcol=gc_of(u, 0))
for iu, u in enumerate((-15.0, 0.0, 15.0)):
    for kk in range(NB):
        place(LBF, "PF_LB_Vault", u, BAY * kk + 7.5, 12.0, 0.0, S)
    for kk in range(NB + 1):
        place(LBF, "PF_LB_Rib", u, BAY * kk, 12.0, 0.0, S)
for u in (-W2, -7.5, 7.5, W2):
    for kk in range(NB):
        place(LBF, "PF_LB_Rib", u, BAY * kk + 7.5, 12.0, 90.0, S)
# the great window (east wall, nave bay) with its stained glass, and a dais with the reading table in front of it
place(LBF, "PF_LB_WindowWall", 0.0, LEN, 0.0, 90.0, S, col="box", gcol=gLC[1])
place(LBF, "PF_LB_StainedGlass", 0.0, LEN, 0.0, 90.0, S)
light(LBF, "library_window_glow", 0.0, LEN - 4.0, 11.0, 9000, 30, color=(0.75, 0.55, 0.95))
for i, (h_, d_) in enumerate(((0.15, 9.0), (0.3, 8.6), (0.45, 8.2))):
    gLF.box(-6.5 + 0.4 * i, 6.5 - 0.4 * i, LEN - d_, LEN - 0.6, 0.0, h_, "LB_Stone")
place(LBF, "PF_LB_ReadingSet", 0.0, LEN - 4.6, 0.45, 90.0, col="box", gcol=gLC[1])
R(LBF, "Library, dais under the great window", -5.5, 5.5, LEN - 7.6, LEN - 6.6, 0.45, 4.0, interior="library", sealed=True)
# west door: the kit's stone arch at the balcony, door leaves folded back against the wall
place(LBF, "PF_LB_DoorArch", 0.0, -0.15, LV[2], 90.0, 1.25)
for sgn in (-1, 1):
    gLS.box(sgn * 1.5 - (0.0 if sgn > 0 else 0.1), sgn * 1.5 + (0.1 if sgn > 0 else 0.0), 0.0, 1.5, LV[2], LV[2] + 3.9, "LB_GlossyWood")
light(LBF, "library_balcony_door", 0.0, 2.0, LV[2] + 3.2, 1500, 10, shadows=True)

# galleries: two wooden floors in each side aisle (5.1 / 10.2), slab edge at |u| = 6.2 (inside the column line)
SPIRALS = {(1, 0): 6, (1, 1): 5, (-1, 0): 6, (-1, 1): 5}                      # (side, level) -> bay of the spiral
SPU = 8.4                                                                       # |u| of the spiral centres
for s in (-1, 1):
    for l in (1, 2):
        wl = LV[l]
        holes = []
        k_sp = SPIRALS.get((s, l - 1))
        if k_sp is not None:
            vc = BAY * k_sp + 7.5
            holes.append((min(s * (SPU - 1.72), s * (SPU + 1.72)), max(s * (SPU - 1.72), s * (SPU + 1.72)), vc - 1.72, vc + 1.72))
        ua, ub = sorted((s * 6.2, s * W2))
        for a in rect_minus((ua, ub, 0.0, LEN), holes):
            gLF.box(*a, wl - 0.3, wl, "LB_WoodFloor")
        gLF.box(min(s * 6.2, s * 6.45), max(s * 6.2, s * 6.45), 0.0, LEN, wl - 0.65, wl, "LB_GlossyWood", False)   # fascia
        for vb in np.arange(1.875, LEN, 3.75):                                                                    # joists
            if any(h[2] - 0.3 < vb < h[3] + 0.3 for h in holes):
                continue
            gLF.box(ua, ub, vb - 0.14, vb + 0.14, wl - 0.62, wl - 0.3, "LB_GlossyWood", False)
        # balustrade along the nave, between the columns; open where the landing (L1) or the balcony (L2) joins
        for kk in range(NB):
            va, vb_ = BAY * kk + 1.6, BAY * (kk + 1) - 1.6
            if l == 1 and kk in (0, 1):
                segs_ = [(va, 14.6), (19.6, vb_)] if kk == 1 else [(va, vb_)]
                segs_ = [(max(a_, va), min(b_, vb_)) for a_, b_ in segs_ if min(b_, vb_) - max(a_, va) > 0.5]
            elif l == 2 and kk == 0:
                segs_ = [(5.0, vb_)]
            else:
                segs_ = [(va, vb_)]
            for a_, b_ in segs_:
                rail_y(gLF, gc_of(s, l), LBF, s * 6.35, a_, b_, wl)
        if k_sp is not None:                                                  # railings round the spiral well
            vc = BAY * k_sp + 7.5; uo, ui = s * (SPU + 1.72), s * (SPU - 1.72)
            rail_y(gLF, gc_of(s, l), LBF, uo, vc - 1.72, vc + 1.72, wl)
            vfar = vc + s * 1.72; vnear = vc - s * 1.72
            rail_x(gLF, gc_of(s, l), LBF, vfar, ui, uo, wl)
            rail_y(gLF, gc_of(s, l), LBF, ui, vc, vfar, wl)
            rail_x(gLF, gc_of(s, l), LBF, vnear, s * SPU, uo, wl)
# spiral stairs (kit, x1) on 0.3 m plinths: floor -> gallery 1 (bay 6), gallery 1 -> gallery 2 (bay 5)
for (s, l), k_sp in SPIRALS.items():
    vc = BAY * k_sp + 7.5; base = LV[l] + 0.3
    gLF.box(s * SPU - 1.7, s * SPU + 1.7, vc - 1.7, vc + 1.7, LV[l], base, "LB_Stone")
    place(LBF, "PF_LB_SpiralStair", s * SPU, vc, base, 0.0 if s > 0 else 180.0, col="treads", gcol=gc_of(s, l))
# balcony (L2) over the nave at the west end, on two piers; landing L1 (solid) and the grand stair
gLS.box(-6.2, 6.2, 0.0, 5.0, LV[2] - 0.5, LV[2], "LB_WoodFloor")
gLS.box(-6.2, 6.2, 4.75, 5.0, LV[2] - 1.0, LV[2], "LB_Stone", False)
for sgn in (-1, 1):
    gLS.box(sgn * 4.0 - 0.6, sgn * 4.0 + 0.6, 3.6, 4.8, 0.0, LV[2] - 0.5, "LB_Stone")
    rail_x(gLS, gLC[1], LBF, 5.0 + 0.12, sgn * 2.6, sgn * 6.2, LV[2])
gLS.stairs((0.0, 14.6), (0.0, -1.0), 5.0, LV[1], LV[2], "LB_Stone", step_h=0.17, run=0.32)
gLS.box(-2.5, 2.5, 5.0, 14.6, 0.0, LV[1] - 0.2, "LB_Sandstone")
gLS.box(-6.2, 6.2, 14.6, 19.6, 0.0, LV[1], "LB_Sandstone")
gLS.box(-6.4, 6.4, 14.4, 19.8, LV[1] - 0.35, LV[1], "LB_Stone", False)
for sgn in (-1, 1):
    rail_slope(gLS, gLC[1], (sgn * 2.62, 14.6), (sgn * 2.62, 5.0), LV[1], LV[2])
    gLS.stairs((sgn * 4.4, 29.2), (0.0, -1.0), 2.8, 0.0, LV[1], "LB_Stone", step_h=0.17, run=0.32)
    for ue_ in (sgn * 3.0 + sgn * 0.12 * -1, sgn * 5.8 + sgn * 0.12):
        rail_slope(gLS, gLC[1], (ue_, 29.2), (ue_, 19.6), 0.0, LV[1])
    rail_x(gLS, gLC[1], LBF, 14.6 - 0.12, sgn * 2.62, sgn * 6.2, LV[1])                 # L1 west edge (drop)
    rail_x(gLS, gLC[1], LBF, 19.6 + 0.12, sgn * 5.85, sgn * 6.2, LV[1])
rail_x(gLS, gLC[1], LBF, 19.6 + 0.12, -2.95, 2.95, LV[1])                                # between the side flights
R(LBF, "Library balcony (arrival of the secret stair)", -5.5, 5.5, 0.6, 4.4, LV[2], 4.0, interior="library", sealed=True)
R(LBF, "Library landing L1", -5.8, 5.8, 15.0, 19.2, LV[1], 4.0, interior="library", sealed=True)
for s in (-1, 1):
    for l in range(3):
        ua, ub = sorted((s * 10.5, s * 20.0))
        R(LBF, f"Library {'east' if s > 0 else 'west'} aisle, level {l}", ua, ub, 30.0, 100.0, LV[l], 4.6, interior="library", sealed=True)
R(LBF, "Library nave floor", -5.5, 5.5, 32.0, 110.0, 0.0, 10.0, interior="library", sealed=True)

# bookcases: tall units against the outer and end walls on the three levels, double stacks across the aisles
for s in (-1, 1):
    for l in range(3):
        key = "PF_LB_BookcaseTallUpper" if l == 2 else "PF_LB_BookcaseTall"
        hgt = KIT[key]["hi"][2]
        gc = gc_of(s, l)
        for kk in range(NB):
            for dv in (-2.5, 2.5):                                            # outer wall
                place(LBF, key, s * W2, BAY * kk + 7.5 + dv, LV[l], 0.0 if s > 0 else 180.0, col="box", gcol=gc)
            for vv in (BAY * kk + 7.5 - 5.0, BAY * kk + 7.5 + 5.0):           # end panels of each pair (cut units)
                ua, ub = sorted((s * W2, s * (W2 - 0.7)))
                gLF.box(ua, ub, vv - 0.04, vv + 0.04, LV[l], LV[l] + hgt, "LB_GlossyWood", False)
            k_sp = SPIRALS.get((s, l))
            for dv in (3.75, 7.5, 11.25):                                     # stacks
                if k_sp == kk and dv == 7.5:
                    continue
                if l == 2 and kk == 0 and dv == 3.75:
                    continue
                for uc in (12.735, 17.785):
                    place(LBF, "PF_LB_BookcaseDouble", s * uc, BAY * kk + dv, LV[l], 0.0, col="box", gcol=gc)
            light(LBF, f"library_aisle_{'e' if s > 0 else 'w'}{l}_{kk}", s * 14.0, BAY * kk + 7.5, LV[l] + 3.6, 2400, 13,
                  shadows=(kk % 3 == 1))
        for vwall, yaw in ((0.0, -90.0), (LEN, 90.0)):                         # end walls of the aisles
            for uc in (s * 12.5, s * 17.5):
                place(LBF, key, uc, vwall, LV[l], yaw, col="box", gcol=gc)
# nave: reading tables down the middle, great chandeliers under the vault keys
for kk in range(2, NB):                                                            # reading tables, four per bay
    for uc in (-3.2, 3.2):
        for dv in (3.9, 11.1):
            place(LBF, "PF_LB_ReadingSet", uc, BAY * kk + dv, 0.0, 0.0, col="box", gcol=gc_of(uc, 0))
place(LBF, "PF_LB_BookcaseTall", 0.0, 19.6, 0.0, -90.0, col="box", gcol=gLC[1])     # face of the landing, between the flights
for vv in (-2.5, 2.5):
    gLS.box(vv - 0.04, vv + 0.04, 19.6, 20.3, 0.0, KIT["PF_LB_BookcaseTall"]["hi"][2], "LB_GlossyWood", False)
for kk in range(1, NB):
    place(LBF, "PF_LB_ChandelierLong", 0.0, BAY * kk + 7.5, 12.0 + 10.714 * S, 0.0, 1.4)
    light(LBF, f"library_nave_{kk}", 0.0, BAY * kk + 7.5, 10.5, 7000, 24, shadows=(kk % 2 == 1))
for s in (-1, 1):
    for kk in range(NB):
        place(LBF, "PF_LB_ChandelierLong", s * 15.0, BAY * kk + 7.5, 12.0 + 10.714 * S, 0.0, 1.0)

# =====================================================================================================================
# 4. frames -> world, outputs
for g in groups:
    ox, oy, oz = g.frame
    for p in g.prims:
        p["v"] = np.round(np.asarray(p["v"]) + [ox, oy, oz], 3).tolist()
# collision-only groups ride on a visible mesh (Unreal needs render triangles to hold the UCX hulls)
HOST = {"SM_GB_Lodge_Collision": "SM_GB_Lodge_Interior", "SM_GB_Library_Collision0": "SM_GB_Library_Floors",
        "SM_GB_Library_Collision1": "SM_GB_Library_Walls", "SM_GB_Library_Collision2": "SM_GB_Library_GrandStair",
        "SM_GB_Library_Collision3": "SM_GB_Library_Floors"}
byname = {g.name: g for g in groups}
for src_, dst_ in HOST.items():
    byname[dst_].prims += byname[src_].prims
    groups.remove(byname[src_])
json.dump([g.to_json() for g in groups], open(f"{ROOT}/greybox/lodge_groups.json", "w"))
lib_box = [X0 - W2 - 1, X0 + W2 + 1, Y0 - 1, Y0 + LEN + 1.6]
lib_cover = float(min(gz(x, y) for x in np.linspace(lib_box[0], lib_box[1], 12) for y in np.linspace(lib_box[2], lib_box[3], 40))) - (F + TOPW + 0.5)
meta = dict(rooms=ROOMS, voids=VOIDS, pads=[[float(O[0]), float(O[1]), P, 40.0, "hunters_lodge"]], movable=MOVABLE, lights=LIGHTS,
            lodge=dict(origin=[float(O[0]), float(O[1]), P], floor=P + FL, door=[O[0] + 22.3, O[1] - 1.58, P + FL]),
            library=dict(origin=[X0, Y0, F], levels=[F + l for l in LV], size=[2 * W2, LEN], vault_apex=F + 12 + 10.714 * S,
                         rock_cover_min_m=round(lib_cover, 1)),
            secret_stair=dict(risers=nr, riser_m=round(rh, 4), tread_m=RUN, flights=k, length_m=round(Y_END - HR[3], 1),
                              drop_m=round(drop, 2), rock_cover_min_m=cover),
            sealed_note="rooms flagged sealed lie under the landscape: no terrain cut, the audit checks the rock above them")
json.dump(meta, open(f"{ROOT}/greybox/lodge_meta.json", "w"), indent=1)
json.dump(PL, open(f"{ROOT}/data/placements_lodge.json", "w"), indent=0)
nav = dict(name="lodge", bbox=[round(X0 - 32), round(X0 + 34), round(O[1] - 26), round(Y0 + LEN + 6), 34, 100], landscape_crust=1.0,
           groups=["greybox/lodge_groups.json"], meta=["greybox/lodge_meta.json"],
           exclude=["SM_GB_Lodge_SecretWardrobe", "SM_GB_Lodge_DoorL", "SM_GB_Lodge_DoorR"],
           seeds=[[float(O[0] + 25.0), float(O[1] - 1.6), P + FL]],
           probes={"hall": [O[0] + 17.0, O[1] + 1.8, P + FL], "study": [O[0] + 11.3, O[1] - 2.0, P + FL],
                   "spiral_top": [O[0] + 10.1, O[1] + 0.5, P + FL], "spiral_foot": [O[0] + 8.9, O[1] + 4.5, P + SB],
                   "balcony": [X0, Y0 + 2.5, F + LV[2]], "landing_L1": [X0, Y0 + 17.0, F + LV[1]],
                   "nave_floor": [X0, Y0 + 60.0, F], "east_aisle_L2": [X0 + 9.0, Y0 + 60.0, F + LV[2]],
                   "west_aisle_L2": [X0 - 9.0, Y0 + 60.0, F + LV[2]], "dais": [X0, Y0 + LEN - 7.0, F + 0.45]},
           levels={"lodge": [P - 1, P + 3], "library_floor": [F - 0.5, F + 2.5], "library_L1": [F + 4.6, F + 7], "library_L2": [F + 9.7, F + 12]})
json.dump(nav, open(f"{ROOT}/greybox/nav_lodge.json", "w"), indent=1)
print(f"lodge at {O.tolist()} +{P} | secret stair {nr} risers x {rh:.3f} m in {k} flights, {Y_END - HR[3]:.1f} m, "
      f"rock over its vault >= {cover:.1f} m | library {2 * W2:.0f} x {LEN:.0f} m, floor {F}, origin ({X0:.1f}, {Y0:.1f}), "
      f"rock above >= {lib_cover:.1f} m | {len(PL)} kit placements, {sum(len(g.prims) for g in groups)} prims, {len(LIGHTS)} lights")
