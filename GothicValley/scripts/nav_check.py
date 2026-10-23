# Walkability test: voxelise the greybox collision hulls (inflated by the capsule radius) + the landscape, extract the
# standing cells of a Nanos World character capsule (r 0.35 m, 1.8 m tall, step 0.4 m, slopes up to ~39 deg) and flood
# fill from the seeds. Reports every listed room (reached or not), fall-through leaks into covered voids, and level maps.
# usage: nav_check.py ROOT config.json      config: {name, bbox:[x0,x1,y0,y1,z0,z1], groups:[json], meta:[json],
#                                                    exclude:[group names left open], seeds:[[x,y,z]], probes:{name:[x,y,z]}}
import sys, os, json, math
import numpy as np
from numba import njit
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tlib import sample

ROOT, CFG = sys.argv[1], json.load(open(sys.argv[2]))
DX, DZ, RAD, HB, STEP = 0.5, 0.1, 0.35, 18, 4
x0, x1, y0, y1, z0, z1 = CFG["bbox"]
nx, ny, nz = int((x1 - x0) / DX), int((y1 - y0) / DX), int((z1 - z0) / DZ)
xs = x0 + (np.arange(nx) + 0.5) * DX
ys = y0 + (np.arange(ny) + 0.5) * DX

# ---------------------------------------------------------------- collision hulls -> half-spaces
planes, starts, boxes = [], [0], []
for fn in CFG["groups"]:
    for g in json.load(open(f"{ROOT}/{fn}")):
        if g["name"] in CFG.get("exclude", []):
            continue
        for p in g["prims"]:
            if p["col"] is False:
                continue
            v = np.asarray(p["v"], float); c = v.mean(0)
            for f in p["f"]:
                a, b, cc = v[f[0]], v[f[1]], v[f[2]]
                n = np.cross(b - a, cc - a); ln = np.linalg.norm(n)
                if ln < 1e-9:
                    continue
                n /= ln; d = n @ a
                if n @ c > d:
                    n, d = -n, -d
                planes.append([n[0], n[1], n[2], d + RAD * math.hypot(n[0], n[1])])   # capsule-radius inflation
            lo, hi = v.min(0), v.max(0)
            planes.append([0.0, 0.0, 1.0, hi[2]])                                     # z caps: the capsule sweep is
            planes.append([0.0, 0.0, -1.0, -lo[2]])                                   # horizontal, heights never grow
            starts.append(len(planes))
            boxes.append([lo[0] - RAD, hi[0] + RAD, lo[1] - RAD, hi[1] + RAD, lo[2], hi[2]])
planes, starts, boxes = np.array(planes), np.array(starts, np.int64), np.array(boxes)
H = np.load(f"{ROOT}/terrain/H_4033.npy")
Xc, Yc = np.meshgrid(xs, ys, indexing="ij")
HC = sample(H, Xc.ravel(), Yc.ravel()).reshape(nx, ny)


CRUST = float(CFG.get("landscape_crust", 1e6))          # only this thickness under the surface is solid (sealed rooms below)


@njit(cache=True)
def voxelise(planes, starts, boxes, HC, nx, ny, nz, x0, y0, z0, DX, DZ, CRUST):
    S = np.zeros((nx, ny, nz), np.uint8)
    for i in range(nx):
        for j in range(ny):
            kt = int(math.floor((HC[i, j] - z0) / DZ - 0.5))
            kb = max(0, int(math.floor((HC[i, j] - CRUST - z0) / DZ - 0.5)))
            for k in range(kb, min(kt + 1, nz)):
                S[i, j, k] = 2                                               # 2 = landscape
    for p in range(len(starts) - 1):
        bx = boxes[p]
        i0 = max(0, int(math.ceil((bx[0] - x0) / DX - 0.5))); i1 = min(nx - 1, int(math.floor((bx[1] - x0) / DX - 0.5)))
        j0 = max(0, int(math.ceil((bx[2] - y0) / DX - 0.5))); j1 = min(ny - 1, int(math.floor((bx[3] - y0) / DX - 0.5)))
        for i in range(i0, i1 + 1):
            x = x0 + (i + 0.5) * DX
            for j in range(j0, j1 + 1):
                y = y0 + (j + 0.5) * DX
                lo, hi, ok = -1e9, 1e9, True
                for q in range(starts[p], starts[p + 1]):
                    a = planes[q, 2]; b = planes[q, 3] - planes[q, 0] * x - planes[q, 1] * y
                    if a > 1e-6:
                        hi = min(hi, b / a)
                    elif a < -1e-6:
                        lo = max(lo, b / a)
                    elif b < 0:
                        ok = False
                        break
                if not ok or lo >= hi:
                    continue
                k0 = max(0, int(math.ceil((lo - z0) / DZ - 0.5))); k1 = min(nz - 1, int(math.floor((hi - z0) / DZ - 0.5)))
                for k in range(k0, k1 + 1):
                    S[i, j, k] = 1
    return S


@njit(cache=True)
def nodes_of(S, HB):
    nx, ny, nz = S.shape
    cnt = np.zeros(nx * ny + 1, np.int64)
    out = np.empty((nx * ny * 6, 3), np.int32)
    n = 0
    for i in range(nx):
        for j in range(ny):
            run = 0
            tmp = np.empty(64, np.int32); m = 0
            for k in range(nz - 1, 0, -1):                                   # free run above k, scanned top-down
                if S[i, j, k] == 0:
                    run += 1
                    if S[i, j, k - 1] != 0 and run >= HB and m < 64:
                        tmp[m] = k; m += 1
                else:
                    run = 0
            for t in range(m - 1, -1, -1):                                   # ascending k
                if n < len(out):
                    out[n, 0] = i; out[n, 1] = j; out[n, 2] = tmp[t]; n += 1
            cnt[i * ny + j + 1] = n
    return out[:n], cnt


@njit(cache=True)
def flood(N, cnt, ny, seeds, STEP):
    lab = np.full(len(N), -1, np.int32)
    q = np.empty(len(N), np.int64)
    for s in seeds:
        if s < 0 or lab[s] >= 0:
            continue
        h, t = 0, 0
        q[t] = s; t += 1; lab[s] = 1
        while h < t:
            a = q[h]; h += 1
            i, j, k = N[a, 0], N[a, 1], N[a, 2]
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ii, jj = i + di, j + dj
                if ii < 0 or jj < 0 or jj >= ny or ii * ny + jj + 1 >= len(cnt):
                    continue
                c = ii * ny + jj
                for b in range(cnt[c], cnt[c + 1]):
                    if abs(N[b, 2] - k) <= STEP and lab[b] < 0:
                        lab[b] = 1; q[t] = b; t += 1
    return lab


S = voxelise(planes, starts, boxes, HC, nx, ny, nz, x0, y0, z0, DX, DZ, CRUST)
N, cnt = nodes_of(S, HB)
NZ = z0 + N[:, 2] * DZ                                                       # standing height of each node
NXw, NYw = x0 + (N[:, 0] + 0.5) * DX, y0 + (N[:, 1] + 0.5) * DX


def nearest(p, tol_xy=1.5, tol_z=0.8):
    d = np.hypot(NXw - p[0], NYw - p[1]); dz = np.abs(NZ - p[2])
    m = np.nonzero((d < tol_xy) & (dz < tol_z))[0]
    return int(m[np.argmin(d[m] + dz[m])]) if len(m) else -1


seeds = np.array([nearest(s, 3.0, 1.5) for s in CFG["seeds"]], np.int64)
lab = flood(N, cnt, ny, seeds, STEP)
reach = lab >= 0
rep = dict(name=CFG["name"], cells=[nx, ny, nz], hulls=int(len(starts) - 1), nodes=int(len(N)), reached=int(reach.sum()),
           seeds=[[*s, bool(k >= 0)] for s, k in zip(CFG["seeds"], seeds)], rooms=[], probes={}, leaks=[])
rooms = []
for fn in CFG["meta"]:
    rooms += json.load(open(f"{ROOT}/{fn}")).get("rooms", [])
for r in rooms:
    m = ((NXw > r["x0"] + 0.3) & (NXw < r["x1"] - 0.3) & (NYw > r["y0"] + 0.3) & (NYw < r["y1"] - 0.3)
         & (NZ > r["z0"] - 0.35) & (NZ < r["z0"] + 1.6))
    tot, ok = int(m.sum()), int((m & reach).sum())
    rep["rooms"].append(dict(name=r["name"], z=r["z0"], floor_cells=tot, reached_cells=ok,
                             reached=ok > 0, share=round(ok / max(tot, 1), 2)))
for k, p in CFG.get("probes", {}).items():
    a = nearest(p)
    rep["probes"][k] = dict(at=p, found=a >= 0, reached=bool(a >= 0 and reach[a]), z=round(float(NZ[a]), 2) if a >= 0 else None)
# leaks: reachable standing cells on the landscape inside a covered void (the player fell under the buildings)
onland = S[N[:, 0], N[:, 1], np.maximum(N[:, 2] - 1, 0)] == 2
for fn in CFG["meta"]:
    mm = json.load(open(f"{ROOT}/{fn}"))
    for vx0, vx1, vy0, vy1, vz in mm.get("voids", []):
        m = reach & onland & (NXw > vx0) & (NXw < vx1) & (NYw > vy0) & (NYw < vy1) & (NZ < vz + 3)
        if m.any():
            idx = np.nonzero(m)[0][:5]
            rep["leaks"].append(dict(void=[vx0, vx1, vy0, vy1], cells=int(m.sum()),
                                     examples=[[round(float(NXw[i]), 1), round(float(NYw[i]), 1), round(float(NZ[i]), 1)] for i in idx]))
os.makedirs(f"{ROOT}/greybox/nav", exist_ok=True)
json.dump(rep, open(f"{ROOT}/greybox/nav/nav_{CFG['name']}.json", "w"), indent=1)
# level maps: reached cells coloured by height inside each band, unreached floor cells in red
for lv, (za, zb) in CFG.get("levels", {}).items():
    img = np.full((nx, ny, 3), 18, np.uint8)
    m = (NZ >= za) & (NZ < zb)
    t = np.clip((NZ[m] - za) / max(zb - za, 1e-3), 0, 1)
    col = np.where(reach[m][:, None], np.stack([60 + 120 * t, 200 - 60 * t, 90 + 150 * t], 1), [[230, 40, 40]]).astype(np.uint8)
    img[N[m, 0], N[m, 1]] = col
    Image.fromarray(img[::-1]).resize((ny * 2, nx * 2), Image.NEAREST).save(f"{ROOT}/greybox/nav/{CFG['name']}_{lv}.png")
bad = [r for r in rep["rooms"] if not r["reached"]]
print(f"nodes {len(N)} reached {reach.sum()}  rooms {len(rep['rooms']) - len(bad)}/{len(rep['rooms'])} reached, leaks {len(rep['leaks'])}")
for r in bad:
    print("  NOT REACHED:", r["name"], r["z"], "floor cells", r["floor_cells"])
for k, v in rep["probes"].items():
    print("  probe", k, v)
for l in rep["leaks"]:
    print("  LEAK", l)
if os.environ.get("NAV_DEBUG"):
    qx, qy, qr = map(float, os.environ["NAV_DEBUG"].split(","))
    m = np.hypot(NXw - qx, NYw - qy) < qr
    zz = np.round(NZ[m], 1); rr = reach[m]
    import collections
    hist = collections.defaultdict(lambda: [0, 0])
    for z_, r_ in zip(zz, rr):
        hist[round(z_)][int(r_)] += 1
    for z_ in sorted(hist):
        print("  z", z_, "unreached", hist[z_][0], "reached", hist[z_][1])
    if os.environ.get("NAV_DEBUG_Z"):
        za_, zb_ = map(float, os.environ["NAV_DEBUG_Z"].split(","))
        mm = m & (NZ >= za_) & (NZ <= zb_)
        ii, jj = N[mm, 0], N[mm, 1]
        grid_ = {}
        for i_, j_, z_, r_ in zip(ii, jj, NZ[mm], reach[mm]):
            grid_.setdefault((i_, j_), []).append(f"{z_ - za_:.1f}{'*' if r_ else ''}")
        for i_ in range(ii.max(), ii.min() - 1, -1):
            print("  " + " ".join(f"{'/'.join(grid_.get((i_, j_), ['.'])):>9s}" for j_ in range(jj.min(), jj.max() + 1)))
if os.environ.get("NAV_DUMP"):
    np.savez_compressed(os.environ["NAV_DUMP"], x=NXw, y=NYw, z=NZ, r=reach)
