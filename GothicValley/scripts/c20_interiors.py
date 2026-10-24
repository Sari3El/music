# Castle 2.0: find the enclosed interiors of its buildings. The shell is voxelised (0.5 m), the hill (ground plate) is
# solid, small openings are closed by a one-cell dilation, then the outside air is flood-filled from the sky and the
# map edges: the free space it never reaches is made of closed volumes = building interiors. Each one is reported with
# its floor, height, footprint and bounding box (centred model frame, scale 160).  -> assets/castle20/interiors.json
# usage: c20_interiors.py ROOT
import sys, os, json
import numpy as np
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meshvox import voxelise

ROOT = sys.argv[1]
T = np.load(f"{ROOT}/assets/castle20/tris.npz")["tris"].astype(np.float64)
G = np.load(f"{ROOT}/assets/castle20/ground.npz")
DX = DZ = 0.5
BB = (-104.0, 104.0, -88.0, 88.0, 0.0, 76.0)
S = voxelise(T, BB, DX, DZ).astype(bool)
nx, ny, nz = S.shape
xs = BB[0] + (np.arange(nx) + 0.5) * DX; ys = BB[2] + (np.arange(ny) + 0.5) * DX; zs = BB[4] + (np.arange(nz) + 0.5) * DZ
# hill: plate heights on the voxel columns (outside the plate: its edge value)
gi = np.clip(np.searchsorted(G["xs"], xs), 0, len(G["xs"]) - 1); gj = np.clip(np.searchsorted(G["ys"], ys), 0, len(G["ys"]) - 1)
P = np.nan_to_num(G["plate"], nan=np.nanmin(G["plate"]))[np.ix_(gi, gj)]
ground = zs[None, None, :] < P[:, :, None]
solid = S | ground
closed = ndimage.binary_dilation(solid, iterations=1)                     # shut windows and slits < ~1 m
free = ~closed
seed = np.zeros_like(free)
seed[:, :, -1] = True; seed[0] = seed[-1] = True; seed[:, 0] = seed[:, -1] = True
outside = ndimage.binary_propagation(seed & free, mask=free)            # 6-connected flood of the open air
covered = free & (np.flip(np.logical_or.accumulate(np.flip(closed, 2), 2), 2) & ~closed)   # a solid somewhere above
covered &= ~ground
inside = (free & ~outside) | covered if os.environ.get("COVERED") else free & ~outside
lab, n = ndimage.label(inside)
sizes = ndimage.sum(inside, lab, index=np.arange(1, n + 1))
rooms = []
for k in np.nonzero(sizes * DX * DX * DZ >= float(os.environ.get("MINVOL", "60")))[0] + 1:
    idx = np.argwhere(lab == k)
    i0, j0, k0 = idx.min(0); i1, j1, k1 = idx.max(0)
    foot = np.unique(idx[:, :2], axis=0)
    floor = float(BB[4] + k0 * DZ - DZ)                                 # the closing ate one cell: give it back
    enclosed = bool((~outside[tuple(idx.T)]).all())
    rooms.append(dict(id=int(k), enclosed=enclosed, volume_m3=round(float(len(idx) * DX * DX * DZ), 0), floor=round(floor, 2),
                      top=round(float(BB[4] + (k1 + 1) * DZ + DZ), 2), height=round(float((k1 - k0 + 1) * DZ + 2 * DZ), 2),
                      area_m2=round(float(len(foot) * DX * DX), 1),
                      x=[round(float(BB[0] + i0 * DX - DX), 1), round(float(BB[0] + (i1 + 1) * DX + DX), 1)],
                      y=[round(float(BB[2] + j0 * DX - DX), 1), round(float(BB[2] + (j1 + 1) * DX + DX), 1)],
                      centre=[round(float(xs[idx[:, 0]].mean()), 1), round(float(ys[idx[:, 1]].mean()), 1)],
                      plate=round(float(P[int(idx[:, 0].mean()), int(idx[:, 1].mean())]), 2)))
rooms.sort(key=lambda r: -r["volume_m3"])
TAG = "_covered" if os.environ.get("COVERED") else ""
json.dump(rooms, open(f"{ROOT}/assets/castle20/interiors{TAG}.json", "w"), indent=1)
np.savez_compressed(f"{ROOT}/assets/castle20/interiors{TAG}_lab.npz", lab=lab.astype(np.int32), bbox=np.array(BB), dx=DX)
print("enclosed volumes", n, "| kept (>= 60 m3)", len(rooms))
for r in rooms[:40]:
    print(f"#{r['id']:4d} {'E' if r['enclosed'] else 'o'} vol {r['volume_m3']:7.0f} m3  area {r['area_m2']:6.1f} m2  floor {r['floor']:5.1f} (hill {r['plate']:5.1f}) "
          f"h {r['height']:5.1f}  x {r['x']} y {r['y']} c {r['centre']}")
