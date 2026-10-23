# Blender: Fantasy Castle check views (textured exterior from 4 sides + views from inside the east hall).
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asset_lib import quick_views, bounds
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); OUT = a[1]
obs = [o for o in bpy.data.objects if o.type == "MESH"]
views = []
views += quick_views(obs, OUT, "ext", views=((0, 15), (90, 15), (180, 15), (270, 15)), res=(900, 650))
sc = bpy.context.scene; sc.display.shading.show_backface_culling = False
cam = sc.camera; cam.data.lens = 16
for k, (p, t) in enumerate([((20.5, 0, 2.0), (6, 0, 3)), ((8, 4, 2.0), (22, -4, 3)), ((14, 5.0, 2.0), (14, -6, 3))]):
    cam.location = Vector(p); cam.rotation_euler = (Vector(t) - Vector(p)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(OUT, f"hall_{k}.png"); bpy.ops.render.render(write_still=True); views.append(sc.render.filepath)
import json; json.dump([[os.path.basename(v), v] for v in views], open(os.path.join(OUT, "views.json"), "w"))
