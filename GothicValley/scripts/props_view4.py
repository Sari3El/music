# Blender: views of prefabs from four sides (front = +X first, then left, back, right), true handedness, for checks.
# usage: blender -b PROPS_BLEND --python props_view4.py -- OUT_DIR NAME [NAME ...]
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
OUT, NAMES = a[0], a[1:]
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "TEXTURE"; sh.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 300
wo = bpy.data.worlds.new("w"); wo.color = (0.55, 0.58, 0.62); sc.world = wo
cd = bpy.data.cameras.new("c"); cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
for o in sc.objects:
    o.hide_render = True
views = []
for n in NAMES:
    o = bpy.data.objects["PF_PR_" + n]; o.hide_render = False; o.scale = (1, -1, 1)
    co = np.array([v.co[:] for v in o.data.vertices]) * [1, -1, 1]; lo, hi = co.min(0), co.max(0)
    c = Vector(((lo + hi) / 2).tolist()); R = float(np.linalg.norm(hi - lo)) * 1.3 + 0.05
    for k, az in enumerate((0, 90, 180, 270)):                 # world azimuth from +X toward +Y (east)
        A = math.radians(az); el = math.radians(20)
        d = Vector((math.cos(A) * math.cos(el), -math.sin(A) * math.cos(el), math.sin(el)))   # Blender y = -world Y
        cam.location = c + d * R; cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
        cd.lens = 40; cd.clip_start = R * 0.01; cd.clip_end = R * 10
        f = os.path.join(OUT, f"{n}_{az}.png"); sc.render.filepath = f; bpy.ops.render.render(write_still=True)
        views.append([f"{n} from {['+X front', '+Y east', '-X back', '-Y west'][k]}", f])
    o.hide_render = True; o.scale = (1, 1, 1)
json.dump(views, open(os.path.join(OUT, "views.json"), "w"))
