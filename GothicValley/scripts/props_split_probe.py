# Blender: split a prop pack whose pieces are merged into a few meshes: loose parts of every object, joined into pieces
# when their bounding boxes touch (union-find), skipping showcase objects (floor, walls). Writes the pieces (bbox,
# member parts, triangle count) to json for identification. usage: ... -- FBX SCALE OUT_JSON [skip,names]
import bpy, sys, json
import numpy as np
a = sys.argv[sys.argv.index("--") + 1:]
FBX, SC, OJ = a[0], float(a[1]), a[2]
SKIP = a[3].split(",") if len(a) > 3 else []
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX)
obs = [o for o in bpy.data.objects if o.type == "MESH" and not any(s in o.name for s in SKIP)]
parts = []
for o in obs:
    me = o.data; n = len(me.vertices)
    co = np.empty(n * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    M = np.array(o.matrix_world); w = (co @ M[:3, :3].T + M[:3, 3]) * SC
    # loose parts by vertex connectivity through faces
    par = np.arange(n)
    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for p in me.polygons:
        vs = list(p.vertices); r0 = find(vs[0])
        for v in vs[1:]:
            r1 = find(v)
            if r1 != r0:
                par[r1] = r0
    roots = np.array([find(i) for i in range(n)])
    for r in np.unique(roots):
        m = roots == r
        parts.append(dict(obj=o.name, lo=w[m].min(0), hi=w[m].max(0), nv=int(m.sum())))
N = len(parts)
par = list(range(N))
def f(i):
    while par[i] != i:
        par[i] = par[par[i]]; i = par[i]
    return i
LO = np.array([p["lo"] for p in parts]) - 0.01; HI = np.array([p["hi"] for p in parts]) + 0.01
for i in range(N):
    ov = np.nonzero((LO[i] <= HI).all(1) & (HI[i] >= LO).all(1))[0]
    for j in ov:
        ri, rj = f(i), f(j)
        if ri != rj:
            par[rj] = ri
groups = {}
for i in range(N):
    groups.setdefault(f(i), []).append(i)
out = []
for k, idx in enumerate(sorted(groups.values(), key=lambda g: -sum(parts[i]["nv"] for i in g))):
    lo = np.min([parts[i]["lo"] for i in idx], 0); hi = np.max([parts[i]["hi"] for i in idx], 0)
    out.append(dict(id=k, lo=lo.round(3).tolist(), hi=hi.round(3).tolist(), size=(hi - lo).round(3).tolist(),
                    nv=int(sum(parts[i]["nv"] for i in idx)), objs=sorted({parts[i]["obj"] for i in idx})))
json.dump(out, open(OJ, "w"), indent=1)
print("PIECES", len(out), "from", N, "loose parts")
