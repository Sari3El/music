# Blender: Castle 2.0 face table (object, normal, area, centre, UV centre / extent / area) -> npz, for rebuilding its materials.
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=a[0])
rows = {k: [] for k in ("obj", "n", "area", "c", "uvc", "uvs", "uva", "nv")}
names = []
LV, LU, LF = [], [], []                                    # per loop: global vertex id, uv, face id
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    m = o.data; M = np.array(o.matrix_world)
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", co); co = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
    uv = np.empty(len(m.loops) * 2); m.uv_layers.active.data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
    ls = np.empty(len(m.polygons), np.int32); m.polygons.foreach_get("loop_start", ls)
    lt = np.empty(len(m.polygons), np.int32); m.polygons.foreach_get("loop_total", lt)
    vi = np.empty(len(m.loops), np.int32); m.loops.foreach_get("vertex_index", vi)
    voff = sum(len(bpy.data.objects[nm].data.vertices) for nm in names)
    foff = len(rows["obj"])
    LV.append(vi + voff); LU.append(uv); LF.append(np.repeat(np.arange(len(ls)) + foff, lt))
    for s, t in zip(ls, lt):
        P = co[vi[s:s + t]]; U = uv[s:s + t]
        n = np.zeros(3); ua = 0.0
        for k in range(1, t - 1):
            n += np.cross(P[k] - P[0], P[k + 1] - P[0])
            e1, e2 = U[k] - U[0], U[k + 1] - U[0]; ua += abs(e1[0] * e2[1] - e1[1] * e2[0]) / 2
        ar = np.linalg.norm(n) / 2
        rows["obj"].append(len(names)); rows["n"].append(n / (np.linalg.norm(n) + 1e-12)); rows["area"].append(ar)
        rows["c"].append(P.mean(0)); rows["uvc"].append(U.mean(0)); rows["uvs"].append(U.max(0) - U.min(0)); rows["uva"].append(ua); rows["nv"].append(t)
    names.append(o.name)
np.savez_compressed(a[1], names=np.array(names), loop_v=np.concatenate(LV), loop_uv=np.concatenate(LU).astype(np.float32),
                    loop_f=np.concatenate(LF), **{k: np.array(v) for k, v in rows.items()})
print("FACES", len(rows["obj"]))
