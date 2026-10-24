# Castle 2.0 rooms: for each chosen covered volume (assets/castle20/interiors_covered_lab.npz), the usable floor
# rectangle (largest empty rectangle at 0.5-2 m above its floor) and, when the volume has no reachable opening, the
# place where a door is cut: the nearest reachable outdoor point of the walk test at the same level, the doorway joining
# them through the wall. Output in the centred model frame -> data/castle20_rooms.json (read by gb_castle2.py).
# usage: c20_rooms2.py ROOT NAV_DUMP.npz
import sys, os, json
import numpy as np
from scipy import ndimage

ROOT, NAVD = sys.argv[1], sys.argv[2]
L = np.load(f"{ROOT}/assets/castle20/interiors_covered_lab.npz"); lab = L["lab"]; BB = L["bbox"]; DX = float(L["dx"])
INFO = {r["id"]: r for r in json.load(open(f"{ROOT}/assets/castle20/interiors_covered.json"))}
CM = json.load(open(f"{ROOT}/greybox/castle_meta.json")); T = np.array(CM["model"]["origin"])
N = np.load(NAVD)
nx_, ny_, nz_ = N["x"] - T[0], N["y"] - T[1], N["z"] - T[2]
PICK = {"Great Hall": 1114, "Throne Room": 861, "Banquet Hall": 475, "Chapel": 286, "Library": 1817, "Kitchen": 297,
        "Lord's Apartments": 190, "War Room": 1460, "Lord's Study": 2219}
cell = lambda v, a: int((v - BB[a * 2]) / DX)


def max_rect(M):
    """Largest all-True axis-aligned rectangle in a 2-D boolean grid -> (i0, i1, j0, j1) half-open."""
    best = (0, 0, 0, 0, 0); h = np.zeros(M.shape[1], int)
    for i in range(M.shape[0]):
        h = np.where(M[i], h + 1, 0)
        st = []
        for j in range(M.shape[1] + 1):
            cur = h[j] if j < M.shape[1] else 0
            start = j
            while st and st[-1][1] >= cur:
                s_, hh = st.pop()
                area = hh * (j - s_)
                if area > best[0]:
                    best = (area, i - hh + 1, i + 1, s_, j)
                start = s_
            st.append((start, cur))
    return best[1:]


out = {}
for name, cid in PICK.items():
    r = INFO[cid]
    comp = lab == cid
    anyc = comp.any(axis=2)
    lf = np.where(anyc, comp.argmax(axis=2), -1)                         # lowest free cell of every column
    vals, cnt = np.unique(lf[anyc], return_counts=True)
    kf = int(vals[np.argmax(cnt)])                                       # the main floor level of the volume
    fl = BB[4] + (kf - 1) * DX                                           # (the closing ate one cell: give it back)
    k0, k1 = kf, kf + 3
    foot = (np.abs(lf - kf) <= 1) & comp[:, :, k0:k1 + 1].all(axis=2)   # on that level, free for 2 m
    i0, i1, j0, j1 = max_rect(foot)
    rect = [BB[0] + i0 * DX, BB[0] + i1 * DX, BB[2] + j0 * DX, BB[2] + j1 * DX]
    zz = np.nonzero(comp[(i0 + i1) // 2, (j0 + j1) // 2])[0]
    ceiling = BB[4] + (zz.max() + 2) * DX if len(zz) else fl + r["height"]
    # reachable walk-test points inside the volume (standing at its floor): if none, find where to cut a door
    ii = ((nx_ - BB[0]) / DX).astype(int); jj = ((ny_ - BB[2]) / DX).astype(int); kk = ((nz_ + 0.6 - BB[4]) / DX).astype(int)
    ok = (ii >= 0) & (ii < lab.shape[0]) & (jj >= 0) & (jj < lab.shape[1]) & (kk >= 0) & (kk < lab.shape[2])
    inside = np.zeros(len(ii), bool); inside[ok] = lab[ii[ok], jj[ok], kk[ok]] == cid
    reached_in = int((inside & N["r"]).sum())
    door = None
    if reached_in < 20:
        fp = comp[:, :, k0:k1 + 1].any(axis=2)
        ring = ndimage.binary_dilation(fp, iterations=8) & ~fp
        cand = N["r"] & ok & (np.abs(nz_ - fl) < 0.7)
        cand[ok] &= ring[ii[ok], jj[ok]]
        if cand.any():
            dist = ndimage.distance_transform_edt(~fp) * DX
            c_ = np.nonzero(cand)[0]
            dd = dist[ii[c_], jj[c_]]
            k = c_[np.argmin(dd)]
            p_out = np.array([nx_[k], ny_[k]])
            # nearest footprint cell to the outdoor point
            fi, fj = np.nonzero(fp)
            cx = BB[0] + (fi + 0.5) * DX; cy = BB[2] + (fj + 0.5) * DX
            m_ = np.argmin(np.hypot(cx - p_out[0], cy - p_out[1]))
            p_in = np.array([cx[m_], cy[m_]])
            d = p_out - p_in; Ld = float(np.linalg.norm(d))
            axis = 0 if abs(d[0]) > abs(d[1]) else 1                    # doorway square to the nearest axis
            door = dict(inside=p_in.round(2).tolist(), outside=p_out.round(2).tolist(), axis=axis, length=round(Ld, 2),
                        floor=round(float(fl), 2), outside_z=round(float(nz_[k]), 2))
    out[name] = dict(id=cid, floor=round(float(fl), 2), ceiling=round(float(ceiling), 2), rect=[round(v, 2) for v in rect],
                     size=[round(rect[1] - rect[0], 1), round(rect[3] - rect[2], 1)], reached_inside=reached_in, door=door)
    print(f"{name:18s} floor {fl + T[2]:6.1f} ceiling {ceiling - fl:5.1f} m  rect {rect[1] - rect[0]:5.1f} x {rect[3] - rect[2]:5.1f}  "
          f"reached inside {reached_in:4d}  door {door}")
json.dump(out, open(f"{ROOT}/data/castle20_rooms.json", "w"), indent=1)
