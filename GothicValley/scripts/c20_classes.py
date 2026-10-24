# Castle 2.0: the rip lost which of the four texture sets each face used (one material on 13 arbitrary chunks).
# Faces are grouped into UV islands (faces sharing a vertex with the same UV); each island takes the class of most of its
# area by orientation: walls (vertical / overhanging) -> WallStoneMix, sloped -> RoofsDetails (tiles), flat up -> FloorStone.
# The ground plate (mesh14) is FloorStone. Output: assets/castle20/classes.npz (class per face, in import order).
# usage: python3 c20_classes.py ROOT
import sys
import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import connected_components

ROOT = sys.argv[1]
d = np.load(f"{ROOT}/assets/castle20/faces.npz")
lv, luv, lf = d["loop_v"], d["loop_uv"], d["loop_f"]
nf = len(d["obj"])
key = np.stack([lv, np.round(luv[:, 0] * 2048).astype(np.int64), np.round(luv[:, 1] * 2048).astype(np.int64)], 1)
_, kid = np.unique(key, axis=0, return_inverse=True)
kid = kid.ravel()
A = sparse.csr_matrix((np.ones(len(lf)), (lf, kid)), shape=(nf, kid.max() + 1))
G = sparse.bmat([[None, A], [A.T, None]]).tocsr()
ncomp, lab = connected_components(G, directed=False)
isl = lab[:nf]
nz = d["n"][:, 2]; area = d["area"]
cls = np.where(nz > 0.9, 2, np.where(nz > 0.25, 1, 0))                     # 0 wall, 1 roof, 2 floor
vote = np.zeros((isl.max() + 1, 3))
np.add.at(vote, (isl, cls), area)
icl = vote.argmax(1)
out = icl[isl]
names = d["names"]
plate = np.array([names[o] == "mesh14" for o in d["obj"]])
out[plate] = 2
sizes = np.bincount(isl)
print("islands", ncomp, "faces per island median", int(np.median(sizes[np.unique(isl)])), "largest", sizes.max())
for k, nm in enumerate(("wall", "roof", "floor")):
    print(nm, "faces", int((out == k).sum()), "area share", round(float(area[out == k].sum() / area.sum()), 3),
          "changed by island vote", int(((cls == k) != (out == k)).sum()))
np.savez_compressed(f"{ROOT}/assets/castle20/classes.npz", cls=out.astype(np.int8), island=isl)
