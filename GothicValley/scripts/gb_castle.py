# Castle greybox (section 5 + Appendix A4). World metres, +X north, +Y east. L-2 188, L-1 196, L0 204, L1 218, L2 226.
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gb_lib import Group, rect_minus, ground_snap
from tlib import sample
from castle_shape import rim_sd as _rim_sd

ROOT = sys.argv[1]
HN = f"{ROOT}/terrain/H_natural_4033.npy"                         # terrain before the greybox voids
H = np.load(HN if os.path.exists(HN) else f"{ROOT}/terrain/H_4033.npy")
M = json.load(open(f"{ROOT}/data/layout_manifest.json"))
L2_, L1_, L0, Lp1, Lp2 = 188.0, 196.0, 204.0, 218.0, 226.0
ROOMS, VOIDS, VOID_PATHS, VOID_DISCS, APRONS, DOORS_MOVABLE, PANELS = [], [], [], [], [], [], []
gz = lambda x, y: float(sample(H, x, y)[0])


def R(name, x0, x1, y0, y1, z0, h, core=None):
    r = dict(name=name, x0=x0, x1=x1, y0=y0, y1=y1, z0=z0, z1=z0 + h)
    if core:
        r["core_id"] = core
    ROOMS.append(r)
    return r


# ====================================================================== interiors
pal = Group("SM_GB_Castle_Palace", "Environment/Castle")

# ---- L0: Great Hall, Throne Room, Banquet, Kitchen, servery, antechamber, robing room, portal porch
hall = R("Great Hall", 664, 684, 314, 346, L0, 16, 1)
thr = R("Throne Room", 619, 664, 320, 340, L0, 20, 2)
ban = R("Banquet Hall", 643, 657, 272, 308, L0, 12, 3)
kit = R("Kitchen", 645, 657, 253, 269, L0, 8, 8)
serv = R("Servery", 645, 657, 269, 272, L0, 4.5)
ante = R("Antechamber", 650, 684, 308, 314, L0, 6)
rob = R("Robing room", 636, 649, 340.5, 350, L0, 5)
porch = R("Portal porch", 684, 688, 324, 336, L0, 10)
pas_e = R("East passage", 649, 684, 346, 354, L0, 4.5)
D = lambda u0, u1, v0, v1, side: (side, u0, u1, v0, v1)

pal.room(hall, doors=[D(327, 333, L0, L0 + 9, "n"),                 # main portal 6 x 9
                      D(327.5, 332.5, L0, L0 + 8, "s"),             # throne doors 5 x 8
                      D(672, 675, L0, L0 + 4.5, "w"),               # antechamber (main door 3 x 4.5)
                      D(668, 671, L0, L0 + 3.2, "e"),               # east passage (under the grand stair)
                      D(664.5, 667.5, Lp1, Lp1 + 4.5, "e")])        # gallery at the top of the grand staircase
# grand staircase, 5 m wide, along the east wall, open underneath (steps 20 cm)
pal.stairs((683.3, 343.1), (-1, 0), 5.0, L0, Lp1, "GB_Stone", 0.2, 0.25, solid=False)
pal.box(664.4, 665.9, 340.6, 345.6, Lp1 - 0.3, Lp1, "GB_Stone")                  # top landing
pal.box(665.9, 683.4, 340.3, 340.6, L0, L0 + 0.1, "GB_Stone", col=False)        # stair string marker
for xf in (668.0, 680.0):                                                       # two fireplaces (west wall)
    pal.box(xf - 2, xf + 2, 314.4, 315.6, L0, L0 + 3.5, "GB_Detail")
pal.room(thr, doors=[D(327.5, 332.5, L0, L0 + 8, "n"),
                     D(640.5, 643.5, L0, L0 + 3, "e"),              # hidden door to the robing room
                     D(628.0, 630.0, L0, L0 + 3, "e"),              # panel behind the dais -> private stair
                     D(628.2, 631.8, L0, L0 + 4.5, "w")],           # loggia -> balcony
         windows=[D(327.5, 332.5, L0 + 4, L0 + 18, "s")])           # 14 m lancet facing the city
for k in range(7):                                                              # 7-step dais at the south end
    pal.box(619.4, 627.0 - 0.6 * k, 320.4, 339.6, L0, L0 + 0.2 * (k + 1), "GB_Stone")
pal.box(620.0, 621.6, 329.2, 330.8, L0 + 1.4, L0 + 4.6, "GB_Detail")            # throne block
for yc in (326.5, 333.5):                                                       # two rows of six columns
    for i in range(6):
        pal.cyl(628.5 + i * 6.0, yc, 0.75, L0, L0 + 20, "GB_Stone", 12)
pal.box(619.8, 625.0, 304.0, 319.6, L0 - 0.6, L0, "GB_Stone")                   # inner half of the balcony (loggia floor)
pal.box(613.0, 618.2, 304.0, 319.6, L0 - 1.4, L0 - 0.8, "GB_Stone")             # outer half, 0.8 m lower: the city shows over
pal.stairs((617.8, 311.75), (1, 0), 14.4, L0 - 0.8, L0, "GB_Stone", 0.2, 0.5)   # 4 steps down through the facade
lg = R("Throne balcony loggia", 619, 632, 304, 320, L0, 8)
pal.room(lg, walls=("n", "w"), mat_wall="GB_Interior", floor=False)
for (a, b, c, d) in ((613.0, 613.5, 304.0, 319.6), (613.0, 618.2, 304.0, 304.5), (613.0, 618.2, 319.1, 319.6)):
    pal.box(a, b, c, d, L0 - 0.8, L0 + 0.3, "GB_Stone")                         # 1.1 m parapets
pal.room(ban, doors=[D(650, 654, L0, L0 + 4.5, "e"), D(650, 653, L0, L0 + 3, "w")])
pal.box(643.4, 646.0, 272.4, 307.6, L0, L0 + 0.6, "GB_Stone")                  # high-table dais (south end)
pal.box(649.0, 651.0, 276.0, 304.0, L0, L0 + 0.8, "GB_Detail", col=False)      # long table footprint (40 seats)
pal.room(serv, doors=[D(650, 653, L0, L0 + 3, "w"), D(650, 653, L0, L0 + 3, "e")], ceil=True)
pal.room(kit, doors=[D(650, 653, L0, L0 + 3, "e"), D(258, 261, L0, L0 + 3, "n")],
         holes_floor=[(645.4, 648.2, 255.8, 266.8)])
pal.box(652.0, 656.6, 253.4, 258.0, L0, L0 + 2.2, "GB_Detail")                 # walk-in hearth
pal.room(ante, doors=[D(650, 654, L0, L0 + 4.5, "w"), D(672, 675, L0, L0 + 4.5, "e")], walls=("n", "s", "e", "w"))
pal.room(rob, doors=[D(640.5, 643.5, L0, L0 + 3, "w"), D(343.5, 346.5, L0, L0 + 3, "s"), D(346.5, 349.5, L0, L0 + 3, "n")])
pal.room(porch, doors=[D(327, 333, L0, L0 + 9, "s"), D(327, 333, L0, L0 + 9, "n")], walls=("n", "e", "w"))
pal.room(pas_e, doors=[D(668, 671, L0, L0 + 3.2, "w"), D(346.5, 349.5, L0, L0 + 3, "s")])

# ---- private spiral stair (4 m across) in a 10 x 10 m tower behind the dais: L-2 crypt, L0 throne, L1 study, L2 apartments
TX0, TX1, TY0, TY1 = 626.0, 636.0, 340.0, 350.0
SCX, SCY = 631.0, 345.0
RSP = 0.45 + 2.2                                             # spirals: 2.2 m treads (MUST)
segs = [(L2_, L0, 90.0, 15.75), (L0, Lp1, 270.0, 15.4286), (Lp1, Lp2, 0.0, 18.0)]   # (z0, z1, start angle, deg/step)
for z0, z1, a0, dps in segs:
    pal.spiral(SCX, SCY, RSP, z0, z1, "GB_Stone", 0.2, dps, a0, shaft=False)
tower = dict(x0=TX0, x1=TX1, y0=TY0, y1=TY1, z0=L2_, z1=Lp2 + 4.5)
pal.room(tower, doors=[D(628.0, 630.0, L0, L0 + 3, "w"),         # throne panel (west = y0 side)
                       D(343.5, 346.5, L0, L0 + 3, "n"),         # robing room
                       D(346.5, 349.5, Lp1, Lp1 + 3, "n"),       # L1 passage to the study
                       D(343.0, 346.0, Lp2, Lp2 + 3, "n"),       # L2 corridor to the apartments
                       D(628.0, 631.0, L2_, L2_ + 3, "e")],      # crypt vestibule
         mat_wall="GB_Interior", t=0.8, floor_t=0.3)
for z in (L0, Lp1, Lp2):                                     # landing rings around the spiral at each level
    pal.floor_ring(TX0 + 0.4, TX1 - 0.4, TY0 + 0.4, TY1 - 0.4, z, (SCX - RSP - 0.1, SCX + RSP + 0.1, SCY - RSP - 0.1, SCY + RSP + 0.1))

# ---- L1: gallery (U around the hall), War Room, Study, passages, Library (+ mezzanine)
war = R("War Room", 645, 657, 280, 296, Lp1, 7, 4)
stu = R("Lord's Study", 640, 649, 350, 362, Lp1, 6, 5)
lib = R("Library", 660, 674, 371, 395, Lp1, 9, 9)
gw = R("Gallery (west wing)", 645, 684, 296, 314, Lp1, 5.5)
gn = R("Gallery (north)", 684, 688, 296, 354, Lp1, 5.5)
ge = R("Gallery (east wing)", 649, 684, 346, 354, Lp1, 5.5)
p1 = R("Study passage", 636, 640, 346, 354, Lp1, 5.5)
c1a = R("Library corridor", 643, 664, 362, 368, Lp1, 5.5)
c1b = R("Library corridor (b)", 658, 664, 368, 371, Lp1, 5.5)
pal.room(war, doors=[D(649, 652, Lp1, Lp1 + 4.5, "e")])
pal.box(649.0, 653.0, 285.0, 291.0, Lp1, Lp1 + 1.0, "GB_Detail")                # map table with the valley model
pal.room(gw, doors=[D(649, 652, Lp1, Lp1 + 4.5, "w")], walls=("s", "w", "e"))
pal.room(gn, walls=("n",))
pal.room(ge, doors=[D(664.5, 667.5, Lp1, Lp1 + 4.5, "w"), D(350.4, 353.6, Lp1, Lp1 + 4.5, "s")], walls=("s", "w", "e"))
pal.box(684.0, 688.0, 295.6, 296.4, Lp1 - 0.3, Lp1 + 5.8, "GB_Interior")       # closing walls of the U
pal.box(684.0, 688.0, 353.6, 354.4, Lp1 - 0.3, Lp1 + 5.8, "GB_Interior")
pal.box(683.6, 684.4, 314.0, 346.0, Lp1 - 0.3, Lp1 + 5.8, "GB_Interior")       # north strip, above the hall's north wall
pal.room(stu, doors=[D(350.4, 353.6, Lp1, Lp1 + 4.5, "n"), D(350.4, 353.0, Lp1, Lp1 + 3, "s"), D(644, 647, Lp1, Lp1 + 4.5, "e")])
pal.room(p1, doors=[D(346.5, 349.5, Lp1, Lp1 + 3, "s"), D(350.4, 353.0, Lp1, Lp1 + 3, "n")])
pal.room(c1a, doors=[D(644, 647, Lp1, Lp1 + 4.5, "w")], walls=("s", "w", "n"))
pal.box(643.0, 658.0, 367.6, 368.4, Lp1 - 0.3, Lp1 + 5.8, "GB_Interior")
pal.room(c1b, doors=[D(660.5, 663.5, Lp1, Lp1 + 4.5, "e")], walls=("s", "n", "e"))
pal.room(lib, doors=[D(660.5, 663.5, Lp1, Lp1 + 4.5, "w")])
pal.box(671.0, 673.6, 371.4, 394.6, Lp1 + 4.4 - 0.3, Lp1 + 4.4, "GB_Wood")     # mezzanine (two tiers of shelves)
pal.box(671.0, 671.2, 371.4, 389.0, Lp1 + 4.4, Lp1 + 5.5, "GB_Wood")          # railing, gap at the stair head
pal.spiral(668.4, 391.4, RSP, Lp1, Lp1 + 4.4, "GB_Wood", 0.2, 20, 280, shaft=False)   # arrives at 0 deg -> mezzanine
for yy in range(373, 394, 4):
    pal.box(673.0, 673.6, yy, yy + 3, Lp1, Lp1 + 4.2, "GB_Wood", col=False)      # shelves (lower tier)

# ---- L2: corridor from the spiral, antechamber, Lord's Apartments, covered bridge to the keep
c2a = R("Lord's corridor", 636, 650, 343, 348, Lp2, 4.5)
c2b = R("Lord's corridor (b)", 646, 650, 348, 370, Lp2, 4.5)
ant2 = R("Apartments antechamber", 646, 654, 370, 376, Lp2, 6)
apt = R("Lord's Apartments", 646, 656, 376, 390, Lp2, 6, 11)
c2c = R("Bridge corridor", 648, 653, 390, 396, Lp2, 4.5)
pal.room(c2a, doors=[D(343.0, 346.0, Lp2, Lp2 + 3, "s"), D(646.5, 649.5, Lp2, Lp2 + 3, "e")], walls=("s", "w", "e", "n"))
pal.room(c2b, doors=[D(646.5, 649.5, Lp2, Lp2 + 3, "e")], walls=("s", "e", "n"))
pal.room(ant2, doors=[D(646.5, 649.5, Lp2, Lp2 + 3, "w"), D(648.5, 651.5, Lp2, Lp2 + 3, "e")])
pal.room(apt, doors=[D(648.5, 651.5, Lp2, Lp2 + 3, "w"), D(649.0, 652.0, Lp2, Lp2 + 3, "e")])
pal.box(651.5, 655.6, 384.0, 389.6, Lp2, Lp2 + 0.6, "GB_Detail", col=False)    # canopy bed footprint
pal.room(c2c, doors=[D(649.0, 652.0, Lp2, Lp2 + 3, "w"), D(649.0, 652.0, Lp2, Lp2 + 3, "e")])
lnd = R("Bridge landing", 648, 653, 396.8, 400.4, Lp2, 4.0)                    # outside the east wall, turns into the bridge
pal.room(lnd, walls=("s", "e"), t=0.6, mat_wall="GB_Wood")

# ---- underground: service stair, Larder (L-1), wine and blood cellar, Crypt (L-2), gate corridor, Dungeon (L-2)
lar = R("Larder", 626, 636, 252, 270, L1_, 5, 7)
cel = R("Wine and blood cellar", 626, 636, 271, 289, L1_, 5)
svs = R("Service stair", 636, 648.6, 252.6, 258, L1_, 8)
pal.stairs((646.8, 255.8), (0, 1), 2.6, L1_, L0, "GB_Stone", 0.2, 0.27)        # L-1 (y 255.8) -> kitchen floor (y 266.6)
pal.box(645.4, 648.2, 252.6, 255.6, L1_ - 0.3, L1_, "GB_Stone")
pal.room(svs, doors=[D(254.0, 257.0, L1_, L1_ + 3, "s"), D(645.3, 648.3, L1_, L0 + 0.3, "e")], ceil=False)
pal.box(645.0, 645.8, 255.6, 267.0, L1_ - 0.3, L0 + 1.1, "GB_Interior")              # stair well sides (rails above L0)
pal.box(648.2, 649.0, 255.6, 267.0, L1_ - 0.3, L0 + 1.1, "GB_Interior")
pal.box(645.0, 649.0, 266.8, 267.6, L1_ - 0.3, L0 - 0.3, "GB_Interior")              # end wall under the kitchen floor
pal.box(645.4, 648.6, 255.3, 255.6, L0, L0 + 1.1, "GB_Wood")                          # rail at the low end of the opening
pal.room(lar, doors=[D(254.0, 257.0, L1_, L1_ + 3, "n"), D(629.0, 632.0, L1_, L1_ + 3, "e")])
pal.room(cel, doors=[D(629.0, 632.0, L1_, L1_ + 3, "w")])
cry = R("Crypt", 620, 634, 352, 378, L2_, 6, 10)
vest = R("Crypt vestibule", 627, 632, 350, 352, L2_, 4)
pal.room(cry, doors=[D(628.0, 631.0, L2_, L2_ + 3, "w"),                 # vestibule from the private stair
                     D(352.6, 355.4, L2_, L2_ + 3, "n"),                 # gate corridor stub (iron gate)
                     D(624.5, 627.5, L2_, L2_ + 3, "e")])                # secret tunnel
pal.room(vest, doors=[D(628.0, 631.0, L2_, L2_ + 3, "w"), D(628.0, 631.0, L2_, L2_ + 3, "e")])
for i in range(6):                                                       # sarcophagi in wall niches + the lord's on a dais
    pal.box(620.6, 622.6, 355 + i * 3.8, 357.2 + i * 3.8, L2_, L2_ + 1.0, "GB_Detail")
pal.box(629.0, 633.4, 371.0, 376.0, L2_, L2_ + 0.6, "GB_Stone"); pal.box(630.2, 632.2, 372.5, 374.5, L2_ + 0.6, L2_ + 1.6, "GB_Detail")
gc1 = R("Gate corridor (a)", 637, 640, 259, 356, L2_, 4)
gc2 = R("Gate corridor (b)", 637, 684, 256, 259, L2_, 4)
gcs = R("Gate corridor (iron gate)", 634, 637, 352, 356, L2_, 4)
pal.room(gc1, doors=[D(637.2, 639.8, L2_, L2_ + 3, "w"), D(352.6, 355.4, L2_, L2_ + 3, "s")])
pal.room(gc2, doors=[D(256.4, 258.6, L2_, L2_ + 3, "n"), D(637.2, 639.8, L2_, L2_ + 3, "e")])
pal.room(gcs, doors=[D(352.6, 355.4, L2_, L2_ + 3, "s"), D(352.6, 355.4, L2_, L2_ + 3, "n")], walls=("w", "e"))
# hidden panels of the throne room (separate meshes, the doc asks for it): private stair + robing room
for nm, (y0_, y1_, x0_, x1_) in (("SM_GB_Castle_HiddenPanel", (339.7, 340.3, 628.0, 630.0)), ("SM_GB_Castle_RobingPanel", (339.7, 340.3, 640.5, 643.5))):
    hp = Group(nm, "Environment/Castle")
    hp.box(x0_, x1_, y0_, y1_, L0, L0 + 3.0, "GB_Interior")
    DOORS_MOVABLE.append(dict(name=nm, pivot=[x0_, (y0_ + y1_) / 2, L0]))
    PANELS.append(hp)
# iron gate (separate mesh, scripted later)
gate_iron = Group("SM_GB_Castle_IronGate", "Environment/Castle")
gate_iron.box(635.4, 635.6, 352.6, 355.4, L2_, L2_ + 3.0, "GB_Metal")
DOORS_MOVABLE.append(dict(name="SM_GB_Castle_IronGate", pivot=[635.5, 352.6, L2_]))

dun = R("Dungeon", 684, 708, 220, 260, L2_, 4.5, 6)
pal_d = Group("SM_GB_Castle_Dungeon", "Environment/Castle")
pal_d.room(dun, doors=[D(256.4, 258.6, L2_, L2_ + 3, "s")], holes_floor=[(688.8, 691.2, 242.8, 245.2)],
           holes_ceil=[(701.6, 708.0, 229.8, 245.0)])
for xw in (694.5, 697.5):                                                      # corridor walls with barred cell doors
    holes = [(221.8 + 4 * i, 223.4 + 4 * i, L2_, L2_ + 2.6) for i in range(5)] + [(242.0, 247.0, L2_, L2_ + 3.0)]
    pal_d.wall("y", xw - 0.3, xw + 0.3, 220.4, 247.6, L2_, L2_ + 4.5, "GB_Interior", holes=holes)
for i in range(6):                                                             # partitions: five 3 x 3 cells each side
    y = 220.6 + 4 * i
    pal_d.box(690.6, 694.2, y - 0.3, y + 0.3, L2_, L2_ + 4.5, "GB_Interior")
    pal_d.box(697.8, 701.4, y - 0.3, y + 0.3, L2_, L2_ + 4.5, "GB_Interior")
pal_d.box(690.3, 690.9, 220.4, 240.9, L2_, L2_ + 4.5, "GB_Interior"); pal_d.box(701.1, 701.7, 220.4, 240.9, L2_, L2_ + 4.5, "GB_Interior")
pal_d.wall("x", 247.3, 247.9, 684.4, 707.6, L2_, L2_ + 4.5, "GB_Interior", holes=[(694.6, 697.4, L2_, L2_ + 3.0), (688.0, 690.4, L2_, L2_ + 3.0), (700.0, 702.4, L2_, L2_ + 3.0)])
pal_d.wall("y", 692.2, 692.8, 247.9, 259.6, L2_, L2_ + 4.5, "GB_Interior", holes=[(250.0, 252.4, L2_, L2_ + 3.0)])   # interrogation room
pal_d.wall("y", 697.7, 698.3, 247.9, 259.6, L2_, L2_ + 4.5, "GB_Interior", holes=[(250.0, 252.4, L2_, L2_ + 3.0)])   # guard room
for (a, b, c, d) in ((688.8, 691.2, 242.6, 242.8), (688.8, 691.2, 245.2, 245.4), (688.6, 688.8, 242.6, 245.4), (691.2, 691.4, 242.6, 245.4)):
    pal_d.box(a, b, c, d, L2_ - 4.0, L2_, "GB_Interior")                       # pit cell walls
pal_d.box(688.8, 691.2, 242.8, 245.2, L2_ - 4.3, L2_ - 4.0, "GB_Stone")
# guard stair: outer-ward guard room (L0) -> dungeon (L-2), dog-leg in the guard room's east end
gr = R("Guard room", 690, 708, 224, 246, L0, 5)
VOIDS.append([682.8, 709.2, 218.8, 261.2, 186.0])                            # dungeon under the outer ward
for (a0, a1, b0, b1) in rect_minus((682.0, 710.0, 218.0, 262.0), [(701.6, 708.0, 230.2, 245.0)]):
    pal_d.box(a0, a1, b0, b1, L0 - 0.35, L0 - 0.05, "GB_Stone")                   # paving over the dungeon void
pal_d.stairs((706.35, 233.2), (0, 1), 2.5, L0 - 8.0, L0, "GB_Stone", 0.2, 0.27)  # upper flight: landing -> guard room
pal_d.box(702.0, 707.6, 230.6, 233.2, L0 - 8.3, L0 - 8.0, "GB_Stone")           # landing
pal_d.stairs((703.25, 244.0), (0, -1), 2.5, L2_, L0 - 8.0, "GB_Stone", 0.2, 0.27)  # lower flight: dungeon -> landing
pal_d.room(dict(x0=701.6, x1=708.0, y0=230.2, y1=245.0, z0=L2_ + 4.5, z1=L0), walls=("n", "s", "e", "w"), floor=False, ceil=False)

# ---- secret tunnel: crypt -> head passage -> spiral shaft -> winding gallery under the palace -> straight run out
# through the south cliff -> hidden door at its foot [574, 384, 118]. The whole run lies in a landscape void (terrain
# lowered under its floor) so no landscape surface ever crosses it; outside the palace a talus mass covers it.
tun = Group("SM_GB_Castle_SecretTunnel", "Environment/Castle")
t1 = R("Secret tunnel (head)", 624.5, 627.5, 378, 386, L2_, 4)
tun.room(t1, doors=[D(624.5, 627.5, L2_, L2_ + 2.6, "w"), D(625.0, 627.0, L2_, L2_ + 2.6, "e")])
TSX, TSY, TZ0 = 626.0, 389.9, 124.0
tun.spiral(TSX, TSY, RSP, TZ0, L2_, "GB_Stone", 0.2, 16, 190, shaft=True, shaft_mat="GB_Interior",
           openings=[(270.0, L2_, 2.2, 3.2), (0.0, TZ0, 2.2, 3.2)])          # top: head passage, bottom: gallery
tun.cyl(TSX, TSY, RSP + 0.75, TZ0 - 0.4, TZ0, "GB_Stone", 20)                   # shaft floor
tun.box(625.0, 627.0, 386.0, 387.4, L2_ - 0.3, L2_, "GB_Stone")                 # threshold through the shaft wall
tun.box(TSX + RSP - 0.2, TSX + RSP + 1.0, TSY - 1.2, TSY + 1.2, TZ0 - 0.4, TZ0, "GB_Stone")
TXY = [(TSX + RSP + 0.05, TSY), (668.0, TSY), (668.0, 378.0), (632.0, 378.0), (632.0, 384.0), (574.0, 384.0)]
_l = np.concatenate([[0], np.cumsum([math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(TXY[:-1], TXY[1:])])])
TPATH = [(x, y, TZ0 - 6.0 * l / _l[-1]) for (x, y), l in zip(TXY, _l)]
for k, ((xa, ya, za), (xb, yb, zb)) in enumerate(zip(TPATH[:-1], TPATH[1:])):
    d = np.array([xb - xa, yb - ya]); Lg = np.linalg.norm(d); d /= Lg; n = np.array([-d[1], d[0]])
    tun.ramp((xa, ya), (xb, yb), 2.4, za, zb, 0.4, "GB_Stone")
    ta = 1.8 if k > 0 else 0.0; tb = 1.8 if k < len(TPATH) - 2 else 0.0      # walls stop where a corner block takes over
    wa, wb = za + (zb - za) * ta / Lg, zb - (zb - za) * tb / Lg
    for sgn in (-1, 1):                                                       # walls + roof of the gallery
        p0 = np.array([xa, ya]) + d * ta + n * sgn * 1.5; p1 = np.array([xb, yb]) - d * tb + n * sgn * 1.5
        tun.ramp(tuple(p0), tuple(p1), 0.6, wa + 4.0, wb + 4.0, 4.4, "GB_Interior")      # 4 m clear (camera rule)
    tun.ramp((xa, ya), (xb, yb), 3.6, za + 4.4, zb + 4.4, 0.4, "GB_Interior")
for i in range(1, len(TPATH) - 1):                                            # corner blocks: floor, roof, outer walls
    (xa, ya, _), (xc, yc, zc), (xb, yb, _) = TPATH[i - 1], TPATH[i], TPATH[i + 1]
    din = np.array([xc - xa, yc - ya]); din /= np.linalg.norm(din)
    dout = np.array([xb - xc, yb - yc]); dout /= np.linalg.norm(dout)
    tun.box(xc - 1.8, xc + 1.8, yc - 1.8, yc + 1.8, zc - 0.4, zc, "GB_Stone")
    tun.box(xc - 1.8, xc + 1.8, yc - 1.8, yc + 1.8, zc + 4.0, zc + 4.4, "GB_Interior")
    for dv, off in ((din, (1.2, 1.8)), (dout, (-1.8, -1.2))):
        c0 = np.array([xc, yc]) + dv * off[0]; c1 = np.array([xc, yc]) + dv * off[1]
        lo, hi = np.minimum(c0, c1), np.maximum(c0, c1)
        if abs(dv[0]) > 0.5:
            tun.box(lo[0], hi[0], yc - 1.8, yc + 1.8, zc - 0.4, zc + 4.0, "GB_Interior")
        else:
            tun.box(xc - 1.8, xc + 1.8, lo[1], hi[1], zc - 0.4, zc + 4.0, "GB_Interior")
tun.box(571.6, 574.0, 382.6, 385.4, 117.6, 118.0, "GB_Stone")                  # sill outside the hidden door
seg_len = float(_l[-1])
spiral_len = (L2_ - TZ0) / 0.2 * math.radians(16) * (0.45 + RSP) / 2           # walking line at mid-tread
TUNNEL_LEN = (386 - 378) + spiral_len + seg_len
hidden = Group("SM_GB_Castle_TunnelExitDoor", "Environment/Castle")
hidden.box(573.6, 574.0, 382.8, 385.2, 118.0, 121.0, "GB_Wood")
DOORS_MOVABLE.append(dict(name="SM_GB_Castle_TunnelExitDoor", pivot=[573.8, 382.8, 118.0]))
# talus mass over the run outside the palace (x 574 -> 619): side and top blocks, top follows the natural cliff
talus = Group("SM_GB_Castle_TunnelTalus", "Environment/Castle")
for xa in np.arange(574.0, 619.0, 2.0):
    xb = min(xa + 2.0, 619.8)
    zf = TZ0 - 6.0 * (_l[-1] - (xa - 574.0)) / _l[-1]                          # floor level at xa
    hs = [gz(x, y) for x in (xa, xb) for y in (379.8, 384.0, 388.2)]
    top = max(max(hs) + 0.3, zf + 4.4 + 1.6)
    bot = min(min(hs) - 1.0, zf - 3.0)
    for y0_, y1_ in ((379.8, 382.2), (385.8, 388.2)):
        talus.box(xa, xb, y0_, y1_, bot, top, "GB_Rock")
    talus.box(xa, xb, 382.2, 385.8, zf + 4.4, top, "GB_Rock")
    talus.box(xa, xb, 382.2, 385.8, bot, zf - 0.4, "GB_Rock")
VOID_PATHS.append(dict(pts=[[round(x, 2), round(y, 2), round(z - 0.45, 2)] for x, y, z in TPATH], half=2.6,
                       note="secret tunnel: landscape kept just under the gallery floor"))
VOID_DISCS.append([TSX, TSY, RSP + 0.75 + 0.8, TZ0 - 0.5])
APRONS.append([566.0, 384.0, 117.8, 7.0, 22.0])                               # spoil heap in front of the door

# ====================================================================== exterior volumes
ext = Group("SM_GB_Castle_Exterior", "Environment/Castle")
# palace envelope (walls to +26 m), openings for the portal, service gate, throne window, balcony door
PX0, PX1, PY0, PY1 = 619.0, 688.0, 250.0, 396.0
TE, PH = 1.6, 29.0
ext.wall("y", PX1 - TE / 2, PX1 + TE / 2, PY0 - TE / 2, PY1 + TE / 2, L0 - 0.3, L0 + PH, "GB_Stone", holes=[(327, 333, L0, L0 + 9), (260, 264, L0, L0 + 4.5)])
ext.wall("y", PX0 - TE / 2, PX0 + TE / 2, PY0 - TE / 2, PY1 + TE / 2, L0 - 1.6, L0 + PH, "GB_Stone", holes=[(327.5, 332.5, L0 + 4, L0 + 18), (304.5, 319.0, L0 - 0.8, L0 + 6)])
ext.wall("x", PY0 - TE / 2, PY0 + TE / 2, PX0 + TE / 2, PX1 - TE / 2, L0 - 0.3, L0 + PH, "GB_Stone")
ext.wall("x", PY1 - TE / 2, PY1 + TE / 2, PX0 + TE / 2, PX1 - TE / 2, L0 - 0.3, L0 + PH, "GB_Stone", holes=[(649.0, 652.0, Lp2, Lp2 + 3)])
# under the palace the landscape is lowered to +186 (a covered void): every underground room and shaft sits inside it, so
# no landscape surface cuts a room; the envelope walls (1.6 m) hide the void edge, the L0 slab covers it
VOIDS.append([PX0, PX1, PY0, PY1, 186.0])
for (a0, a1, b0, b1) in rect_minus((PX0, PX1, PY0, PY1), [(645.4, 648.2, 255.8, 266.8), (TX0, TX1, TY0, TY1), (PX0, 619.8, 304.5, 319.0)]):
    pal.box(a0, a1, b0, b1, L0 - 0.4, L0 - 0.05, "GB_Floor")                    # L0 structural slab (holes: two shafts)
pal.box(PX1 - 1.2, PX1 + 1.4, 326.6, 333.4, L0 - 0.3, L0, "GB_Stone")           # thresholds over the void edge
pal.box(PX1 - 1.2, PX1 + 1.4, 259.6, 264.4, L0 - 0.3, L0, "GB_Stone")
pal.box(PX0 - 1.4, PX0 + 1.2, 304.4, 319.6, L0 - 1.4, L0 - 0.8, "GB_Stone")     # under the balcony steps
# roofs (55 deg slate) per block -> palace ridge ~ +38 m
ROOFB = [(619, 664, 318, 342, L0 + 22, "x"), (662, 688, 312, 348, L0 + 18, "y"), (641, 659, 250, 312, L0 + 23, "y"),
         (619, 641, 250, 318, L0 + 22, "y"), (619, 688, 342, 396, L0 + 26, "x"), (659, 688, 296, 314, L0 + 22, "x")]
for x0, x1, y0, y1, ze, ax in ROOFB:                       # 55 deg slate, eaves +29, ridge line held at +38 (silhouette)
    ext.box(x0, x1, y0, y1, L0 + PH - 0.4, L0 + PH, "GB_Stone")
    ext.roof_trunc(x0, x1, y0, y1, L0 + PH, L0 + 38.0, 55.0, "GB_Roof", ax)
for xc, yc in ((619, 250), (619, 396), (688, 250), (688, 396), (619, 318), (619, 342)):  # pinnacles on the corners
    ext.box(xc - 0.9, xc + 0.9, yc - 0.9, yc + 0.9, L0 + PH, L0 + PH + 4, "GB_Stone"); ext.pyramid(xc - 0.9, xc + 0.9, yc - 0.9, yc + 0.9, L0 + PH + 4, L0 + PH + 8, "GB_Roof")
# flying buttresses on the valley side: piers corbelled out of the cliff face (the facade continues the cliff)
for yb in np.arange(262, 392, 13):
    if 302 < yb < 334:
        continue                                                                # balcony and the 14 m lancet
    ext.box(616.6, PX0 - TE / 2, yb - 0.9, yb + 0.9, L0 - 22.0, L0, "GB_Stone")
    xo = PX0 - TE / 2                                                           # corbel: the pier widens 1.4 m over 3 m
    ext.add([(616.6, yb - 0.9, L0 - 3.0), (xo, yb - 0.9, L0 - 3.0), (xo, yb + 0.9, L0 - 3.0), (616.6, yb + 0.9, L0 - 3.0),
             (615.2, yb - 0.9, L0), (xo, yb - 0.9, L0), (xo, yb + 0.9, L0), (615.2, yb + 0.9, L0)],
            [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]], "GB_Stone")
    ext.box(615.2, PX0 - TE / 2, yb - 0.9, yb + 0.9, L0, L0 + 14.0, "GB_Stone")
    ext.cone(616.7, yb, 1.1, L0 + 14.0, L0 + 19.0, "GB_Roof", 8)
    ext.ramp((616.0, yb), (PX0, yb), 1.0, L0 + 13.0, L0 + 24.0, 1.6, "GB_Stone")
# service court (open, north of the kitchen) paved over the void
pal.box(657.0, PX1, PY0, 296.0, L0 - 0.3, L0, "GB_Stone")
pal.box(656.6, 657.4, PY0, 253.4, L0, L0 + 8.0, "GB_Stone")                      # court walls
pal.box(657.0, PX1, 295.6, 296.4, L0, L0 + 8.0, "GB_Stone")

# curtain wall around the crag rim (palace stretch excluded), 3 m thick, 15-20 m on the gate side, 8-10 m on the cliffs
def rim_sd(x, y):
    return float(_rim_sd(x, y))


poly = []
for a in np.radians(np.arange(0, 360, 4.0)):
    lo, hi = 0.0, 200.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if rim_sd(715 + mid * math.cos(a), 308 + mid * math.sin(a)) < -3.0:
            lo = mid
        else:
            hi = mid
    poly.append((715 + lo * math.cos(a), 308 + lo * math.sin(a)))
in_palace = lambda p: PX0 - 4 < p[0] < PX1 + 2 and PY0 - 2 < p[1] < PY1 + 2
NP = len(poly)
side_h = [17.0 if (p[1] < 260 and p[0] > 690) else 9.0 for p in poly]      # gate side 15-20 m, cliffs 8-10 m
cand = [i for i, p in enumerate(poly) if not in_palace(p) and not (abs(p[0] - 742) < 20 and p[1] < 218)
        and not in_palace(poly[(i - 1) % NP]) and not in_palace(poly[(i + 1) % NP])]
TW_IDX = [cand[k] for k in np.linspace(0, len(cand) - 1, 12).round().astype(int)[1:-1]]
walk_h = list(side_h)
tw_sorted = sorted(TW_IDX)
for ta, tb in zip(tw_sorted, tw_sorted[1:] + [tw_sorted[0] + NP]):          # ramps half-way between towers
    ha, hb = side_h[ta % NP], side_h[tb % NP]
    run = list(range(ta, tb + 1))
    for j, v in enumerate(run):
        mid = len(run) / 2
        walk_h[v % NP] = ha if j < mid - 1 else (hb if j > mid + 1 else ha + (hb - ha) * (j - (mid - 1)) / 2)
TOWERS = []


def clip_discs(a, b, za, zb, discs):
    """Pieces of segment a-b (with heights) outside the given discs (cx, cy, r)."""
    pieces = [(0.0, 1.0)]
    for cx_, cy_, r in discs:
        d = b - a; f = a - np.array([cx_, cy_])
        A2, B2, C2 = d @ d, 2 * f @ d, f @ f - r * r
        disc = B2 * B2 - 4 * A2 * C2
        if disc <= 0:
            continue
        t0, t1 = (-B2 - math.sqrt(disc)) / (2 * A2), (-B2 + math.sqrt(disc)) / (2 * A2)
        pieces = [q for (p0, p1) in pieces for q in ((p0, min(p1, t0)), (max(p0, t1), p1)) if q[1] - q[0] > 1e-3]
    return [(a + (b - a) * p0, a + (b - a) * p1, za + (zb - za) * p0, za + (zb - za) * p1) for p0, p1 in pieces]


TW_DISCS = [(poly[i][0], poly[i][1], 4.5) for i in TW_IDX]
for i in range(NP):
  (xa, ya), (xb, yb) = poly[i], poly[(i + 1) % NP]
  if in_palace((xa, ya)) or in_palace((xb, yb)):
      continue
  for A_, B_, za, zb in clip_discs(np.array([xa, ya]), np.array([xb, yb]), L0 + walk_h[i], L0 + walk_h[(i + 1) % NP], TW_DISCS):
    d = B_ - A_; Lg = np.linalg.norm(d); d /= Lg; nrm = np.array([d[1], -d[0]])
    ext.ramp(tuple(A_), tuple(B_), 3.0, za, zb, max(za, zb) - (L0 - 1.0), "GB_Stone")                   # wall, 3 m thick
    ext.ramp(tuple(A_ + nrm * 1.25), tuple(B_ + nrm * 1.25), 0.5, za + 1.1, zb + 1.1, 1.1, "GB_Stone")   # outer parapet
    ext.ramp(tuple(A_ - nrm * 1.3), tuple(B_ - nrm * 1.3), 0.4, za + 1.1, zb + 1.1, 1.1, "GB_Stone")     # inner parapet
    for k in np.arange(1.0, Lg - 0.8, 2.2):                                    # merlons on the outer parapet
        p = A_ + d * k + nrm * 1.25; zk = za + (zb - za) * k / Lg
        q = [p - d * 0.4 - nrm * 0.25, p - d * 0.4 + nrm * 0.25, p + d * 0.4 + nrm * 0.25, p + d * 0.4 - nrm * 0.25]
        ext.poly_prism([tuple(v) for v in q], zk + 1.1, zk + 2.0, "GB_Stone")                  # sits on the 0.5 m parapet
# ten round towers (11 m wide, 30-35 m, conical slate roofs), hollow at walk level so the wall-walk runs through them;
# two of them carry a spiral stair from the ward to the walk (outer ward on the gate side, inner ward on the cliffs)
STAIR_TW = [min(TW_IDX, key=lambda i: math.hypot(poly[i][0] - 706, poly[i][1] - 210)),
            min(TW_IDX, key=lambda i: math.hypot(poly[i][0] - 812, poly[i][1] - 330))]
for k, i in enumerate(TW_IDX):
    x, y = poly[i]
    ht = 30.0 + (k % 3) * 2.5
    hv = L0 + walk_h[i]
    angs = [math.degrees(math.atan2(poly[j % NP][1] - y, poly[j % NP][0] - x)) for j in (i - 1, i + 1)]
    ops = [(a_, hv, 3.0, 3.2) for a_ in angs]
    stair = i in STAIR_TW
    if stair:
        ang_in = math.degrees(math.atan2(308 - y, 715 - x))                    # door towards the ward
        ops.append((ang_in, L0, 3.0, 3.6))
    ext.ring_wall(x, y, 4.3, 5.5, L0 - 3.0, L0 + ht, "GB_Stone", ops)
    if stair:
        ext.cyl(x, y, 4.4, L0 - 3.0, L0, "GB_Stone", 20)
        ext.spiral(x, y, RSP, L0, hv, "GB_Stone", 0.2, 18.0, ang_in - 9.0, shaft=False)    # first step faces the door
        ext.annulus(x, y, RSP + 0.1, 4.35, hv, sides=24)
        pass
    else:
        ext.cyl(x, y, 4.4, L0 - 3.0, hv - 0.3, "GB_Stone", 20)
        ext.cyl(x, y, 4.4, hv - 0.3, hv, "GB_Floor", 20)
    ext.cyl(x, y, 5.5, L0 + ht, L0 + ht + 0.4, "GB_Stone", 20)
    ext.cone(x, y, 6.2, L0 + ht + 0.4, L0 + ht + 11, "GB_Roof", 16)
    TOWERS.append([round(x, 1), round(y, 1), ht, round(hv, 1), stair])
# gatehouse (twin round towers 13 m wide, 28 m), passage, portcullis slot, machicolations
ext.wall("y", 732.0, 734.0, 192.0, 212.0, L0, L0 + 22, "GB_Stone")
ext.wall("y", 750.0, 752.0, 192.0, 212.0, L0, L0 + 22, "GB_Stone")
ext.box(734.0, 750.0, 192.0, 212.0, L0 + 6.0, L0 + 22.0, "GB_Stone")
ext.box(734.0, 739.0, 192.0, 212.0, L0, L0 + 6.0, "GB_Stone"); ext.box(745.0, 750.0, 192.0, 212.0, L0, L0 + 6.0, "GB_Stone")
ext.box(738.8, 745.2, 191.0, 192.0, L0 + 22, L0 + 24, "GB_Stone")
for xc in (733.0, 751.0):
    ext.cyl(xc, 197.0, 6.5, L0 - 4, L0 + 28, "GB_Stone", 20)
    ext.cone(xc, 197.0, 7.0, L0 + 28, L0 + 38, "GB_Roof", 20)
portc = Group("SM_GB_Castle_Portcullis", "Environment/Castle")
portc.box(739.0, 745.0, 196.0, 196.3, L0, L0 + 5.8, "GB_Metal")
DOORS_MOVABLE.append(dict(name="SM_GB_Castle_Portcullis", pivot=[742.0, 196.15, L0]))
# inner wall + inner gatehouse between the outer and inner wards
ext.wall("x", 268.0, 270.5, 688.0, 812.0, L0, L0 + 10, "GB_Stone", holes=[(718.0, 722.0, L0, L0 + 5)])
ext.box(714.0, 726.0, 266.0, 274.0, L0 + 5.5, L0 + 14.0, "GB_Stone")
ext.box(714.0, 718.0, 266.0, 274.0, L0, L0 + 5.5, "GB_Stone"); ext.box(722.0, 726.0, 266.0, 274.0, L0, L0 + 5.5, "GB_Stone")
# outer-ward buildings: barracks, armory, stables (closed), guard room (enterable, dungeon stair)
for name, (x0, x1, y0, y1), h, door in (("barracks", (768, 786, 212, 246), 9, ("s", 226, 229)),
                                       ("armory", (766, 786, 249, 265), 7, ("s", 255, 258)),
                                       ("stables", (660, 676, 212, 250), 6, ("n", 228, 233)),
                                       ("guard_room", (690, 708, 224, 246), 5, ("w", 694, 697))):
    side, u0, u1 = door
    ext.room(dict(x0=x0, x1=x1, y0=y0, y1=y1, z0=L0, z1=L0 + h), doors=[(side, u0, u1, L0, L0 + 3.2)], t=1.0,
             mat_wall="GB_Stone", floor=False, ceil=True)
    span = min(x1 - x0, y1 - y0)
    ext.gable(x0, x1, y0, y1, L0 + h + 0.3, L0 + h + 0.3 + span / 2 * 1.2, "GB_Roof", "x" if (x1 - x0) > (y1 - y0) else "y")
ext.cyl(720.0, 240.0, 1.4, L0, L0 + 1.0, "GB_Stone", 12)                       # well
ext.cyl(744.0, 336.0, 4.0, L0, L0 + 0.8, "GB_Stone", 20)                       # dry fountain, statue torn down (off the spawn)
ext.box(743.0, 745.0, 335.0, 337.0, L0 + 0.8, L0 + 2.2, "GB_Stone")

# keep: 22 x 22, 75 m to the spire tip, eyrie at +65 with a balcony, spiral stair, bridge door at L2
keep = Group("SM_GB_Castle_Keep", "Environment/Castle")
K = dict(x0=771.5, x1=790.5, y0=371.5, y1=390.5, z0=L0, z1=L0 + 69)
keep.room(K, doors=[("s", 375.0, 378.0, L0, L0 + 4.5), ("e", 772.5, 775.5, Lp2, Lp2 + 3.0), ("n", 379.0, 383.0, L0 + 65, L0 + 68)],
          t=3.0, mat_wall="GB_Stone", ceil=True)
keep.spiral(781.0, 381.0, RSP, L0, L0 + 65, "GB_Stone", 0.2, 15.0, 270.0, shaft=False)
keep.floor_ring(772.0, 790.0, 372.0, 390.0, L0 + 65.0, (778.25, 783.75, 378.25, 383.75))   # eyrie floor around the stair
keep.box(790.5, 794.5, 377.0, 385.0, L0 + 64.6, L0 + 65.0, "GB_Stone")       # eyrie balcony
keep.box(794.0, 794.5, 377.0, 385.0, L0 + 65, L0 + 66.1, "GB_Stone")
keep.floor_ring(772.0, 790.0, 372.0, 390.0, Lp2, (778.25, 783.75, 378.25, 383.75))           # bridge level
keep.pyramid(770.0, 792.0, 370.0, 392.0, L0 + 69.3, L0 + 75.0, "GB_Roof")
# covered bridge apartments (L2) -> keep, on piers over the ward
br = Group("SM_GB_Castle_CoveredBridge", "Environment/Castle")
cb = dict(x0=653.0, x1=776.0, y0=396.4, y1=400.4, z0=Lp2, z1=Lp2 + 4.0)
br.room(cb, doors=[("s", 396.6, 399.6, Lp2, Lp2 + 3), ("w", 772.5, 775.5, Lp2, Lp2 + 3)], t=0.6, mat_wall="GB_Wood")
br.room(dict(x0=771.5, x1=776.0, y0=392.0, y1=396.4, z0=Lp2, z1=Lp2 + 4.0), doors=[("e", 772.5, 775.5, Lp2, Lp2 + 3), ("w", 772.5, 775.5, Lp2, Lp2 + 3)],
        t=0.6, mat_wall="GB_Wood")
br.gable(653.0, 776.0, 396.0, 400.8, Lp2 + 4.3, Lp2 + 6.5, "GB_Roof", "x")
for xp in np.arange(690, 770, 16):
    br.box(xp - 1, xp + 1, 397.4, 399.4, L0, Lp2 - 0.3, "GB_Stone")
# chapel: 32 x 12 x 15, apse east, spire to +40 m
chap = Group("SM_GB_Castle_Chapel", "Environment/Castle")
ch = R("Chapel", 772, 784, 296, 328, L0, 15, 12)
chap.room(ch, doors=[("s", 310.0, 313.0, L0, L0 + 4.5), ("w", 776.5, 779.5, L0, L0 + 5)], t=1.2, mat_wall="GB_Stone")
chap.poly_prism([(772.6, 328.0), (784.0 - 0.6, 328.0), (781.0, 333.5), (775.6, 333.5)], L0, L0 + 15, "GB_Stone")
chap.gable(772.0, 784.0, 296.0, 328.0, L0 + 15.3, L0 + 23.6, "GB_Roof", "y")
chap.pyramid(775.0, 781.0, 296.5, 302.5, L0 + 23.6, L0 + 40.0, "GB_Roof")
chap.box(773.0, 783.0, 323.0, 327.4, L0, L0 + 0.6, "GB_Stone")              # altar platform (toppled altar later)
chap.box(774.0, 782.0, 321.8, 323.0, L0, L0 + 0.3, "GB_Stone")              # step

# ====================================================================== approach: barbican, Great Bridge, drawbridge
app = Group("SM_GB_Castle_Approach", "Environment/Castle")
app.wall("y", 729.0, 731.0, 74.0, 100.0, 199.0, 213.0, "GB_Stone")
app.wall("y", 753.0, 755.0, 74.0, 100.0, 199.0, 213.0, "GB_Stone")
app.box(731.0, 753.0, 74.0, 100.0, 207.0, 213.0, "GB_Stone")
for xc in (730.0, 754.0):
    app.cyl(xc, 97.0, 5.0, 196.0, 219.0, "GB_Stone", 16); app.cone(xc, 97.0, 5.6, 219.0, 227.0, "GB_Roof", 16)
BR0, BR1 = (742.0, 80.0, 199.1), (742.0, 182.0, 203.85)   # deck starts at the terrace level inside the barbican
app.ramp((742.0, BR0[1]), (742.0, BR1[1]), 6.0, BR0[2], BR1[2], 2.0, "GB_Stone")
for s in (-1, 1):
    app.ramp((742.0 + s * 3.25, BR0[1]), (742.0 + s * 3.25, BR1[1]), 0.5, BR0[2] + 1.1, BR1[2] + 1.1, 1.1, "GB_Stone")
PIERS = []
for yp in (112.0, 129.0, 145.0, 162.0):
    zt = BR0[2] + (BR1[2] - BR0[2]) * (yp - BR0[1]) / (BR1[1] - BR0[1]) - 2.0
    zb = min(gz(x, y) for x in (739, 745) for y in (yp - 2.5, yp + 2.5)) - 1.0
    app.box(739.0, 745.0, yp - 2.5, yp + 2.5, zb, zt, "GB_Stone")
    PIERS.append(dict(y=yp, bottom=round(zb, 1), top=round(zt, 1), height=round(zt - zb, 1)))
draw = Group("SM_GB_Castle_Drawbridge", "Environment/Castle")
draw.box(739.0, 745.0, 182.0, 192.0, 203.3, 204.0, "GB_Wood")
DOORS_MOVABLE.append(dict(name="SM_GB_Castle_Drawbridge", pivot=[742.0, 192.0, 204.0], note="hinge at the gatehouse"))

groups = [pal, pal_d, gate_iron, tun, hidden, talus, ext, portc, keep, br, chap, app, draw] + PANELS
print("ground-snapped pieces", ground_snap(groups, H, sample))
json.dump([g.to_json() for g in groups], open(f"{ROOT}/greybox/castle_groups.json", "w"))
meta = dict(rooms=ROOMS, voids=VOIDS, void_paths=VOID_PATHS, void_discs=VOID_DISCS, aprons=APRONS, movable=DOORS_MOVABLE, towers=TOWERS, piers=PIERS,
            tunnel_length_m=round(TUNNEL_LEN, 1), rim_polygon=[[round(x, 1), round(y, 1)] for x, y in poly])
json.dump(meta, open(f"{ROOT}/greybox/castle_meta.json", "w"), indent=1)
print("castle groups", [(g.name, len(g.prims)) for g in groups])
print("towers", len(TOWERS), "piers", PIERS, "tunnel length", round(TUNNEL_LEN))
