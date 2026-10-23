# Blender: dump the world-space triangles of a .blend's meshes to an .npz (tris (n,3,3), object index, object names).
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
T, I, names = [], [], []
for o in bpy.data.objects:
    if o.type != "MESH" or not len(o.data.polygons):
        continue
    m = o.data; m.calc_loop_triangles()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    M = np.array(o.matrix_world); w = co @ M[:3, :3].T + M[:3, 3]
    lt = np.empty(len(m.loop_triangles) * 3, np.int32); m.loop_triangles.foreach_get("vertices", lt)
    T.append(w[lt.reshape(-1, 3)]); I.append(np.full(len(lt) // 3, len(names))); names.append(o.name)
np.savez_compressed(a[1], tris=np.concatenate(T).astype(np.float32), obj=np.concatenate(I), names=np.array(names))
print("TRIS", sum(len(t) for t in T))
