# Blender (Workbench): greybox hero views V1-V8 of the design document + an overview, terrain at 2.25 m, river and fen water.
# usage: blender -b --factory-startup --python render_hero.py -- ROOT OUTDIR castle.blend city.blend sites.blend
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
ROOT, OUT, BLENDS = a[0], a[1], a[2:]
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
for bp in BLENDS:
    with bpy.data.libraries.load(bp, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if not n.startswith("UCX_")]
    for ob in dst.objects:
        if ob is not None and ob.type == "MESH":
            sc.collection.objects.link(ob)
print("objects", len(sc.objects), flush=True)

# ------------------------------------------------------------------ terrain + water
H = np.load(f"{ROOT}/terrain/H_4033.npy")
DEP = np.load(f"{ROOT}/terrain/river_depth.npy").astype(np.float32)
RM = np.load(f"{ROOT}/terrain/road_mask.npy")
ST = 3
Hs, Ds, Rs = H[::ST, ::ST], DEP[::ST, ::ST], RM[::ST, ::ST]
n = Hs.shape[0]
ax = np.linspace(-1512.0, 1512.0, H.shape[0])[::ST]
Xg, Yg = np.meshgrid(ax, ax)                     # arrays are [row = Y, col = X]


def grid_mesh(name, Z, mask_faces, mats, mat_index):
    verts = np.stack([Xg.ravel(), -Yg.ravel(), Z.ravel()], 1).astype(np.float32)
    r, c = np.nonzero(mask_faces)
    i0 = r * n + c
    quads = np.stack([i0, i0 + n, i0 + n + 1, i0 + 1], 1)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(verts)); me.vertices.foreach_set("co", verts.ravel())
    me.loops.add(len(quads) * 4); me.loops.foreach_set("vertex_index", quads.ravel().astype(np.int32))
    me.polygons.add(len(quads))
    me.polygons.foreach_set("loop_start", (np.arange(len(quads)) * 4).astype(np.int32))
    me.polygons.foreach_set("loop_total", np.full(len(quads), 4, np.int32))
    for m in mats:
        me.materials.append(m)
    me.polygons.foreach_set("material_index", mat_index[r, c].astype(np.int32))
    me.update(); me.validate()
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    return ob


def mat(name, rgb, rough=0.9):
    m = bpy.data.materials.new(name); m.use_nodes = False
    m.diffuse_color = (*rgb, 1.0); m.roughness = rough
    return m


gy, gx = np.gradient(Hs, ax[1] - ax[0])
slope = np.degrees(np.arctan(np.hypot(gx, gy)))[:-1, :-1]
idx = np.where(slope > 38, 1, 0)
idx = np.where((Rs[:-1, :-1] > 0) & (Rs[:-1, :-1] < 5), 2, idx)
idx = np.where(Hs[:-1, :-1] > 390, 3, idx)
TM = [mat("T_Grass", (0.22, 0.26, 0.15)), mat("T_Rock", (0.34, 0.33, 0.32)), mat("T_Road", (0.45, 0.40, 0.32)), mat("T_Snow", (0.85, 0.86, 0.88))]
grid_mesh("Terrain", Hs, np.ones((n - 1, n - 1), bool), TM, idx)
wet = Ds > 0.05
fen = (np.hypot(Xg + 1230, Yg + 1230) < 270) & (Hs < 3.0)
WZ = np.where(wet, Hs + Ds - 0.6, np.where(fen, 3.0, Hs - 5))
wm = (wet | fen)
wf = wm[:-1, :-1] & wm[1:, :-1] & wm[:-1, 1:] & wm[1:, 1:]
grid_mesh("Water", WZ.astype(np.float32), wf, [mat("T_Water", (0.12, 0.20, 0.26), 0.05)], np.zeros((n - 1, n - 1), int))

# ------------------------------------------------------------------ render settings
sc.render.engine = "BLENDER_WORKBENCH"
wo = bpy.data.worlds.new("sky"); wo.color = (0.58, 0.64, 0.72); sc.world = wo
sc.render.resolution_x, sc.render.resolution_y = 1600, 900
sc.display.shading.light = "STUDIO"
sc.display.shading.color_type = "MATERIAL"
sc.display.shading.show_shadows = True
sc.display.shading.shadow_intensity = 0.55
sc.display.shading.show_cavity = True
sc.display.shading.cavity_type = "BOTH"
sc.display.shading.show_specular_highlight = False
sc.display.shading.background_type = "VIEWPORT"
sc.display.shading.background_color = (0.58, 0.64, 0.72)
sc.display.light_direction = (0.45, -0.35, 0.82)
sc.display.render_aa = "8"
sc.view_settings.view_transform = "Standard"
cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 24; cam_d.clip_start = 0.3; cam_d.clip_end = 20000
cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
M = json.load(open(f"{ROOT}/data/layout_manifest.json"))


def ground(x, y):
    c = int(round((x + 1512) / (3024 / (H.shape[0] - 1)))); r = int(round((y + 1512) / (3024 / (H.shape[0] - 1))))
    return float(H[min(max(r, 0), H.shape[0] - 1), min(max(c, 0), H.shape[0] - 1)])


FIX = {"V3": 201.9 + 1.7, "V5": 80.0 + 1.7}                       # deck of the Great Bridge, floor of the bell chamber
views = [dict(v) for v in M["hero_views"]] + [dict(id="V0", name="Valley overview", camera=[-1450, -1650, 950], look_at=[200, -100, 60])]
LOG = []
for v in views:
    cx, cy, cz = v["camera"]
    cz = FIX.get(v["id"], max(cz, ground(cx, cy) + 1.6))
    tx, ty, tz = v["look_at"]
    loc = Vector((cx, -cy, cz)); tgt = Vector((tx, -ty, tz))
    cam.location = loc
    cam.rotation_euler = (tgt - loc).to_track_quat("-Z", "Y").to_euler()
    cam_d.lens = 18 if v["id"] in ("V4", "V5", "V2") else 24
    fn = f"{OUT}/{v['id']}_{v['name'].replace(' ', '_')}.png"
    sc.render.filepath = fn
    bpy.ops.render.render(write_still=True)
    LOG.append(dict(id=v["id"], name=v["name"], camera_used=[cx, cy, round(cz, 2)], look_at=v["look_at"], file=os.path.basename(fn)))
    print("rendered", fn, flush=True)
json.dump(LOG, open(f"{OUT}/hero_views.json", "w"), indent=1)
