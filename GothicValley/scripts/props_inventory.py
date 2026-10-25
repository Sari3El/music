# Blender: inventory of a prop pack FBX (objects, world size in metres as imported, materials, triangle counts) -> json,
# plus a labelled overview render (Workbench) to read the pieces.
# usage: blender -b --factory-startup --python props_inventory.py -- FBX OUT_JSON OUT_PNG
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
FBX, OJ, OP = a[0], a[1], a[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX)
obs = [o for o in bpy.data.objects if o.type == "MESH"]
rows = []
for o in obs:
    n = len(o.data.vertices)
    if not n:
        continue
    co = np.empty(n * 3); o.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    M = np.array(o.matrix_world); w = co @ M[:3, :3].T + M[:3, 3]
    o.data.calc_loop_triangles()
    mats = sorted({s.material.name for s in o.material_slots if s.material})
    rows.append(dict(name=o.name, parent=o.parent.name if o.parent else None, lo=w.min(0).round(3).tolist(), hi=w.max(0).round(3).tolist(),
                     size=(w.max(0) - w.min(0)).round(3).tolist(), tris=len(o.data.loop_triangles), mats=mats))
lo = np.min([r["lo"] for r in rows], 0); hi = np.max([r["hi"] for r in rows], 0)
json.dump(dict(fbx=os.path.basename(FBX), objects=rows, lo=lo.tolist(), hi=hi.tolist(), size=(hi - lo).tolist()), open(OJ, "w"), indent=1)
print("INV", os.path.basename(FBX), "objects", len(rows), "size", (hi - lo).round(2).tolist())
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "RANDOM"; sh.show_cavity = True
sc.render.resolution_x, sc.render.resolution_y = 1200, 800
cd = bpy.data.cameras.new("c"); cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector(((lo + hi) / 2).tolist()); R = float(np.linalg.norm(hi - lo)) * 1.1 + 0.1
d = Vector((math.cos(math.radians(-60)) * math.cos(math.radians(35)), math.sin(math.radians(-60)) * math.cos(math.radians(35)), math.sin(math.radians(35))))
cam.location = c + d * R; cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler(); cd.lens = 35; cd.clip_end = R * 10
sc.render.filepath = OP; bpy.ops.render.render(write_still=True)
