# Blender: probe the Fantasy Castle shell: horizontal rays along X and Y at a few heights -> hit list (pos, facing), plus
# an orthographic plan render with a 5 m grid.
import bpy, sys, os, bmesh, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); OUT = a[1]
obs = [o for o in bpy.data.objects if o.type == "MESH" and not o.name.endswith(("Glass_0", "Back_0"))]
bm = bmesh.new()
for o in obs:
    t = bmesh.new(); t.from_mesh(o.data); t.transform(o.matrix_world); m = bpy.data.meshes.new("t"); t.to_mesh(m); bm.from_mesh(m); t.free()
tree = BVHTree.FromBMesh(bm)
def ray(o, d, far=80):
    out = []; p = Vector(o)
    while True:
        h = tree.ray_cast(p, Vector(d), far)
        if h[0] is None: break
        out.append((round((h[0] - Vector(o)).length, 2), "in" if h[1].dot(Vector(d)) > 0 else "out"))
        p = h[0] + Vector(d) * 0.01
    return out
for z in (1.5, 6.0, 11.0):
    for y in (-12, -6, 0, 6, 12):
        print(f"X-ray z{z} y{y}:", ray((-40, y, z), (1, 0, 0)))
    for x in (-18, -10, 0, 10, 18):
        print(f"Y-ray z{z} x{x}:", ray((x, -40, z), (0, 1, 0)))
# vertical rays: roof / floor levels on a 4 m grid
for x in range(-20, 24, 4):
    row = []
    for y in range(-14, 18, 4):
        h = tree.ray_cast(Vector((x, y, 60)), Vector((0, 0, -1)), 100)
        row.append(f"{h[0].z:5.1f}" if h[0] else "  -  ")
    print(f"top x{x:3d}", " ".join(row))
