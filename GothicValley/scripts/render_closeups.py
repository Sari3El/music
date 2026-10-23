# Blender (Workbench): close-up renders of listed spots straight from the greybox JSON (no FBX build needed), with the
# full-resolution landscape around each spot. Used to review the audit findings by eye.
# usage: blender -b --factory-startup --python render_closeups.py -- ROOT OUTDIR targets.json
#        targets.json: [{"name", "at": [x, y, z], "dist": m, "azim": deg, "elev": deg}]
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
ROOT, OUT, TG = a[0], a[1], json.load(open(a[2]))
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
COL = {"GB_Stone": (0.55, 0.53, 0.5), "GB_Church": (0.66, 0.63, 0.58), "GB_Interior": (0.72, 0.7, 0.66), "GB_Floor": (0.45, 0.42, 0.38),
       "GB_Wood": (0.42, 0.3, 0.2), "GB_Timber": (0.3, 0.21, 0.14), "GB_Tile": (0.45, 0.2, 0.15), "GB_Roof": (0.25, 0.27, 0.3),
       "GB_Metal": (0.2, 0.2, 0.22), "GB_Plaster": (0.8, 0.76, 0.66), "GB_Detail": (0.6, 0.15, 0.15), "GB_Ground": (0.32, 0.24, 0.16),
       "GB_Hedge": (0.12, 0.25, 0.12)}
MATS = {}


def mat(name):
    if name not in MATS:
        m = bpy.data.materials.new(name); m.use_nodes = False
        m.diffuse_color = (*COL.get(name, (0.8, 0.0, 0.8)), 1.0); MATS[name] = m
    return MATS[name]


verts, faces, fmat, names = [], [], [], []
for part in ("castle", "city", "sites"):
    for g in json.load(open(f"{ROOT}/greybox/{part}_groups.json")):
        for p in g["prims"]:
            if p["col"] == "only":
                continue
            o = len(verts)
            verts += [(x, -y, z) for x, y, z in p["v"]]                    # Blender view: world Y flipped (right-handed)
            for f in p["f"]:
                faces.append([o + i for i in f][::-1]); fmat.append(p["m"])
me = bpy.data.meshes.new("gb"); me.from_pydata(verts, [], faces)
ml = sorted(set(fmat)); [me.materials.append(mat(m)) for m in ml]
me.polygons.foreach_set("material_index", [ml.index(m) for m in fmat]); me.update()
sc.collection.objects.link(bpy.data.objects.new("gb", me))
H = np.load(f"{ROOT}/terrain/H_4033.npy")
grass = mat("T_Grass"); grass.diffuse_color = (0.25, 0.3, 0.17, 1)
sc.render.engine = "BLENDER_WORKBENCH"
wo = bpy.data.worlds.new("sky"); wo.color = (0.62, 0.68, 0.76); sc.world = wo
sc.render.resolution_x, sc.render.resolution_y = 800, 450
sh = sc.display.shading
sh.light = "STUDIO"; sh.color_type = "MATERIAL"; sh.show_shadows = True; sh.shadow_intensity = 0.5
sh.show_cavity = True; sh.cavity_type = "BOTH"; sh.background_type = "VIEWPORT"; sh.background_color = (0.62, 0.68, 0.76)
sc.display.light_direction = (0.45, -0.35, 0.82); sc.display.render_aa = "8"; sc.view_settings.view_transform = "Standard"
cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 28; cam_d.clip_start = 0.1; cam_d.clip_end = 3000
cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
for t in TG:
    x, y, z = t["at"]
    c0, r0 = int((x + 1512) / 0.75), int((y + 1512) / 0.75); R = 110
    rs, cs = slice(max(r0 - R, 0), r0 + R), slice(max(c0 - R, 0), c0 + R)
    Hs = H[rs, cs]; ny_, nx_ = Hs.shape
    xs = -1512 + 0.75 * np.arange(cs.start, cs.start + nx_); ys = -1512 + 0.75 * np.arange(rs.start, rs.start + ny_)
    X, Y = np.meshgrid(xs, ys)
    tv = np.stack([X.ravel(), -Y.ravel(), Hs.ravel()], 1)
    i0 = (np.arange(ny_ - 1)[:, None] * nx_ + np.arange(nx_ - 1)[None, :]).ravel()
    tf = np.stack([i0, i0 + 1, i0 + nx_ + 1, i0 + nx_], 1)
    tm = bpy.data.meshes.new("t"); tm.from_pydata(tv.tolist(), [], tf.tolist()); tm.materials.append(grass); tm.update()
    to = bpy.data.objects.new("t", tm); sc.collection.objects.link(to)
    az, el, d = math.radians(t.get("azim", 225)), math.radians(t.get("elev", 25)), t.get("dist", 14)
    loc = Vector((x + d * math.cos(el) * math.cos(az), -(y + d * math.cos(el) * math.sin(az)), z + d * math.sin(el)))
    cam.location = loc; cam.rotation_euler = (Vector((x, -y, z)) - loc).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = f"{OUT}/{t['name']}.png"
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(to); bpy.data.meshes.remove(tm)
    print("closeup", t["name"], flush=True)
