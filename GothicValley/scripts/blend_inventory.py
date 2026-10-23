# Blender: list the mesh objects of a .blend (world bounds, tris, materials) as JSON next to it.
import bpy, sys, os, json
import numpy as np
f = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.open_mainfile(filepath=f)
rows = []
for o in bpy.data.objects:
    if o.type != "MESH" or not len(o.data.vertices):
        continue
    co = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    M = np.array(o.matrix_world); w = co @ M[:3, :3].T + M[:3, 3]
    rows.append(dict(name=o.name, mats=[m.name for m in o.data.materials if m], lo=w.min(0).round(2).tolist(), hi=w.max(0).round(2).tolist(),
                     tris=sum(len(p.vertices) - 2 for p in o.data.polygons)))
json.dump(rows, open(os.path.splitext(f)[0] + "_inventory.json", "w"), indent=0)
print("ROWS", len(rows))
