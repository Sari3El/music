# Geometry audit of the greybox: every visible piece must rest on something. For each primitive, the bottom of its hull
# is sampled; a sample is supported when the landscape reaches it, or when another primitive lies just under it or
# around it. Free-standing pieces (nothing touching their sides) with unsupported samples are reported: a pillar half
# over a stair opening, a post floating above a slope, a wall stub over a void. Also reported: landscape poking through
# room floors, and room floors left hanging above the landscape with no slab under them.
# usage: gb_audit.py ROOT  ->  greybox/audit.json (+ summary on stdout)
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tlib import sample

ROOT = sys.argv[1]
H = np.load(f"{ROOT}/terrain/H_4033.npy")
P, PF = [], []                                           # (group, index, mat, col, V, planes, lo, hi), faces
for part in [p for p in ("castle", "city", "sites", "lodge") if os.path.exists(f"{ROOT}/greybox/{p}_groups.json")]:
    for g in json.load(open(f"{ROOT}/greybox/{part}_groups.json")):
        for i, p in enumerate(g["prims"]):
            V = np.asarray(p["v"], float); c = V.mean(0); pl = []
            for f in p["f"]:
                a, b, cc = V[f[0]], V[f[1]], V[f[2]]
                n = np.cross(b - a, cc - a); ln = np.linalg.norm(n)
                if ln < 1e-9:
                    continue
                n /= ln; d = n @ a
                if n @ c > d:
                    n, d = -n, -d
                pl.append([*n, d])
            P.append((g["name"], i, p["m"], p["col"], V, np.array(pl), V.min(0), V.max(0))); PF.append(p["f"])
LO = np.array([p[6] for p in P]); HI = np.array([p[7] for p in P])
print("prims", len(P), flush=True)


def inside(k, Q, tol=0.03):
    pl = P[k][5]
    return np.all(Q @ pl[:, :3].T <= pl[:, 3] + tol, axis=1)


def column_range(k, x, y):
    """Bottom and top of hull k along the vertical lines through (x, y) (NaN where the line misses the hull)."""
    pl = P[k][5]
    zb = np.full(len(x), -np.inf); zt = np.full(len(x), np.inf); ok = np.ones(len(x), bool)
    for nx, ny, nz, d in pl:
        r = d - nx * x - ny * y
        if abs(nz) < 1e-6:
            ok &= r >= -1e-6
        elif nz < 0:
            zb = np.maximum(zb, r / nz)
        else:
            zt = np.minimum(zt, r / nz)
    ok &= zb <= zt + 1e-6
    return np.where(ok, zb, np.nan), np.where(ok, zt, np.nan)


def near(k, pad):
    m = np.all((LO <= P[k][7] + pad) & (HI >= P[k][6] - pad), axis=1)
    m[k] = False
    return np.nonzero(m)[0]


issues = []
for k, (gn, gi, mat, col, V, pl, lo, hi) in enumerate(P):
    if col == "only" or len(pl) < 4:
        continue
    h = hi[2] - lo[2]
    area = (hi[0] - lo[0]) * (hi[1] - lo[1])
    s = max(0.15, math.sqrt(area / 160.0))
    gx, gy = np.meshgrid(np.arange(lo[0] + s / 2, hi[0], s), np.arange(lo[1] + s / 2, hi[1], s))
    x, y = gx.ravel(), gy.ravel()
    if len(x) == 0:
        x, y = np.array([(lo[0] + hi[0]) / 2]), np.array([(lo[1] + hi[1]) / 2])
    zb, zt = column_range(k, x, y)
    m = np.isfinite(zb)
    if m.sum() == 0:
        continue
    x, y, zb = x[m], y[m], zb[m]
    sup = sample(H, x, y) >= zb - 0.25                                          # the landscape carries it
    nb = near(k, 0.3)
    for q in nb:
        if sup.all():
            break
        r = ~sup
        Q = np.stack([x[r], y[r], zb[r] - 0.08], 1); Q2 = Q.copy(); Q2[:, 2] += 0.16
        sup[r] = inside(q, Q) | inside(q, Q2)                                    # under it, or embedded in it
    frac = 1.0 - sup.mean()
    if frac < 0.1:
        continue
    # side contact, face by face: points 6 cm outside each lateral face (landscape counts as contact)
    faces = []
    for f in [ff for ff in PF[k]]:
        Vf = V[f]; n = np.cross(Vf[1] - Vf[0], Vf[2] - Vf[0]); ln = np.linalg.norm(n)
        if ln < 1e-9:
            continue
        n /= ln
        if n @ (Vf.mean(0) - V.mean(0)) < 0:
            n = -n
        if abs(n[2]) > 0.5:
            continue
        pts = []
        for t in range(1, len(Vf) - 1):                                   # fan triangles, barycentric grid
            A_, B_, C_ = Vf[0], Vf[t], Vf[t + 1]
            for u in np.linspace(0.05, 0.95, 7):
                for w in np.linspace(0.05, 0.95, 7):
                    if u + w < 0.97:
                        pts.append(A_ + u * (B_ - A_) + w * (C_ - A_))
        if not pts:
            continue
        Q = np.array(pts) + n * 0.06
        hit = sample(H, Q[:, 0], Q[:, 1]) >= Q[:, 2]
        for q in near(k, 0.2):
            if hit.all():
                break
            hit |= inside(q, Q)
        faces.append((n, float(hit.mean())))
    touched = [(n, c) for n, c in faces if c > 0.05]
    opposite = any(n1 @ n2 < -0.5 for i1, (n1, _) in enumerate(touched) for n2, _ in touched[i1 + 1:])
    kind = "spanning" if opposite else ("cantilever" if touched else "free")
    issues.append(dict(group=gn, prim=gi, mat=mat, col=col, unsupported=round(float(frac), 2),
                       kind=kind, faces_touched=len(touched),
                       height=round(float(h), 2), size=[round(float(v), 2) for v in hi[:2] - lo[:2]],
                       lo=[round(float(v), 2) for v in lo], hi=[round(float(v), 2) for v in hi],
                       terrain_gap=round(float(np.nanmin(zb - sample(H, x, y))), 2)))
    if k % 1000 == 0:
        print(k, len(issues), flush=True)

# landscape through room floors / floors hanging over air (rooms of the three metas)
rooms = []
for part in ("castle", "city", "sites", "lodge"):
    if os.path.exists(f"{ROOT}/greybox/{part}_meta.json"):
        rooms += json.load(open(f"{ROOT}/greybox/{part}_meta.json")).get("rooms", [])
room_issues = []
for r in rooms:
    xs, ys = np.meshgrid(np.linspace(r["x0"] + 0.9, r["x1"] - 0.9, 12), np.linspace(r["y0"] + 0.9, r["y1"] - 0.9, 12))   # inside the walls
    t = sample(H, xs.ravel(), ys.ravel())
    if r.get("sealed"):                                    # under the landscape: the rock must stay above the ceiling
        if r["interior"] == "library" and float(t.min()) < r["z1"] + 1.0:
            room_issues.append(dict(room=r["name"], z1=r["z1"], rock_cover_m=round(float(t.min() - r["z1"]), 2)))
        continue
    over = float((t > r["z0"] + 0.05).mean())
    if over > 0.02:
        room_issues.append(dict(room=r["name"], z0=r["z0"], terrain_above_floor_frac=round(over, 2), max_excess=round(float((t - r["z0"]).max()), 2)))
free = [i for i in issues if i["kind"] == "free" and i["mat"] not in ("GB_Tile", "GB_Roof")]
json.dump(dict(free_standing_unsupported=free, all_unsupported=issues, rooms=room_issues), open(f"{ROOT}/greybox/audit.json", "w"), indent=1)
print("unsupported pieces", len(issues), "| free-standing", len(free),
      "| cantilevers", sum(i["kind"] == "cantilever" for i in issues), "| rooms with landscape above the floor", len(room_issues))
