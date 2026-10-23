# The hunters' track: a 3 m track from the fen path (same bank of the river) up to the lodge door, routed as a least-cost
# path on the natural terrain (grade penalty, hard cap 16 %, no water), smoothed, then given a graded profile (<= 14 %).
# Adds / replaces "hunters_track" in data/roads_final.json (terrain_gv grades its bed and marks it in the road mask).
# usage: track_lodge.py ROOT
import sys, os, json, heapq, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tlib import sample

ROOT = sys.argv[1]
H = np.load(f"{ROOT}/terrain/H_natural_4033.npy")
DEP = np.load(f"{ROOT}/terrain/river_depth.npy").astype(np.float32)
RF = json.load(open(f"{ROOT}/data/roads_final.json"))
LM = json.load(open(f"{ROOT}/greybox/lodge_meta.json"))
door = np.array(LM["lodge"]["door"][:2]) + [4.5, 0.0]                  # in front of the door, on the pad
ZEND = LM["lodge"]["origin"][2]
fen = RF["fen_path"]; FXY = np.array(fen["xy"]); FZ = np.array(fen["z"])
STEP = 4.0
x0, x1, y0, y1 = -1430.0, -560.0, -1240.0, -640.0
xs = np.arange(x0, x1, STEP); ys = np.arange(y0, y1, STEP)
X, Y = np.meshgrid(xs, ys, indexing="ij")
Z = sample(H, X.ravel(), Y.ravel()).reshape(X.shape)
W = sample(DEP, X.ravel(), Y.ravel()).reshape(X.shape)
bad = (W > 0.05) | (Z < 3.2)                                            # river channel, fen pools
lx, ly, lr = LM["lodge"]["origin"][0], LM["lodge"]["origin"][1], 30.0
bad |= (np.hypot(X - lx, Y - ly) < lr) & (X < door[0] - 6)              # do not cross the lodge itself
nx, ny = X.shape
INF = 1e18
dist = np.full((nx, ny), INF); prev = np.full((nx, ny, 2), -1, np.int32)
pq = []
for i in range(30, len(FXY)):                                          # any point of the fen path can be the junction
    a, b = int(round((FXY[i, 0] - x0) / STEP)), int(round((FXY[i, 1] - y0) / STEP))
    if 0 <= a < nx and 0 <= b < ny and not bad[a, b]:
        dist[a, b] = 0.0; heapq.heappush(pq, (0.0, a, b))
ta, tb = int(round((door[0] - x0) / STEP)), int(round((door[1] - y0) / STEP))
NB = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1), (2, 1), (1, 2), (-2, 1), (-1, 2), (2, -1), (1, -2), (-2, -1), (-1, -2)]
while pq:
    d, a, b = heapq.heappop(pq)
    if d > dist[a, b]:
        continue
    if (a, b) == (ta, tb):
        break
    for da, db in NB:
        c, e = a + da, b + db
        if not (0 <= c < nx and 0 <= e < ny) or bad[c, e]:
            continue
        L = STEP * math.hypot(da, db); g = abs(Z[c, e] - Z[a, b]) / L
        cost = L * (1 + 40 * g * g) + (1e4 if g > 0.16 else 0.0)
        if d + cost < dist[c, e]:
            dist[c, e] = d + cost; prev[c, e] = (a, b); heapq.heappush(pq, (d + cost, c, e))
path = [(ta, tb)]
while prev[path[-1]][0] >= 0:
    path.append(tuple(prev[path[-1]]))
path = path[::-1]
P = np.array([[xs[a], ys[b]] for a, b in path])
j = int(np.argmin(np.hypot(FXY[:, 0] - P[0, 0], FXY[:, 1] - P[0, 1])))
P = np.vstack([FXY[j], P[1:], door])
for _ in range(4):                                                     # Chaikin smoothing (keeps both ends)
    Q = [P[0]]
    for p, q in zip(P[:-1], P[1:]):
        Q += [0.75 * p + 0.25 * q, 0.25 * p + 0.75 * q]
    Q.append(P[-1]); P = np.array(Q)
seg = np.hypot(*np.diff(P, axis=0).T); s = np.concatenate([[0], np.cumsum(seg)])
S = np.arange(0, s[-1], 10.0); S = np.append(S, s[-1])
XY = np.stack([np.interp(S, s, P[:, 0]), np.interp(S, s, P[:, 1])], 1)
zt = sample(H, XY[:, 0], XY[:, 1])
zt = np.convolve(np.pad(zt, 2, mode="edge"), np.ones(5) / 5, mode="valid")
zt[0], zt[-1] = FZ[j], ZEND
G = 0.14
for _ in range(50):                                                    # grade cap, both directions, ends fixed
    for k in range(1, len(S)):
        zt[k] = np.clip(zt[k], zt[k - 1] - G * (S[k] - S[k - 1]), zt[k - 1] + G * (S[k] - S[k - 1]))
    for k in range(len(S) - 2, -1, -1):
        zt[k] = np.clip(zt[k], zt[k + 1] - G * (S[k + 1] - S[k]), zt[k + 1] + G * (S[k + 1] - S[k]))
    zt[0], zt[-1] = FZ[j], ZEND
grade = np.abs(np.diff(zt)) / np.diff(S)
RF["hunters_track"] = dict(type="track", width_m=3, s=np.round(S, 2).tolist(), xy=np.round(XY, 2).tolist(), z=np.round(zt, 2).tolist(),
                           max_grade=round(float(grade.max()), 4), rule=0.35, rule_met=bool(grade.max() <= 0.35),
                           max_dev_from_appendix_m=None, note="added for the hunters' lodge (not in appendix A); branches off the fen path")
crossings = RF.pop("_crossings"); RF["_crossings"] = crossings                 # keep "_crossings" last
json.dump(RF, open(f"{ROOT}/data/roads_final.json", "w"), indent=1)
print(f"hunters_track: {s[-1]:.0f} m from the fen path at ({FXY[j, 0]:.0f}, {FXY[j, 1]:.0f}) z {FZ[j]:.1f} to the lodge door z {ZEND}, "
      f"max grade {grade.max() * 100:.1f} %, cut/fill max {np.abs(zt - sample(H, XY[:, 0], XY[:, 1])).max():.1f} m")
