# Blender (Cycles): the hunters' lodge, its secret stair and the underground library, assembled like in Unreal: our
# geometry (export/lodge.blend from gb_build), the pack meshes (export/kit.blend) instanced from data/placements_lodge.json,
# the point lights of greybox/lodge_meta.json, a terrain patch around the lodge. World -> Blender: y = -Y.
# usage: blender -b --factory-startup --python render_lodge.py -- ROOT OUTDIR [view,view,...]
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
ROOT, OUT = a[0], a[1]
ONLY = a[2].split(",") if len(a) > 2 else []
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
with bpy.data.libraries.load(f"{ROOT}/export/lodge.blend", link=False) as (src, dst):
    dst.objects = [n for n in src.objects if not n.startswith("UCX_")]
for ob in dst.objects:
    if ob is not None and ob.type == "MESH":
        sc.collection.objects.link(ob)
with bpy.data.libraries.load(f"{ROOT}/export/kit.blend", link=False) as (src, dst):
    dst.meshes = list(src.meshes)
KIT = {m.name: m for m in dst.meshes if m is not None}
PL = json.load(open(f"{ROOT}/data/placements_lodge.json"))
META = json.load(open(f"{ROOT}/greybox/lodge_meta.json"))
for i, p in enumerate(PL):
    me = KIT.get(p["mesh"])
    if me is None:
        print("missing kit mesh", p["mesh"]); continue
    ob = bpy.data.objects.new(f"{p['mesh']}_{i}", me); sc.collection.objects.link(ob)
    x, y, z = p["loc"]
    ob.location = (x, -y, z); ob.rotation_euler = (0, 0, -math.radians(p["yaw"])); ob.scale = p["scale"]
WIDE = os.environ.get("GV_WARDROBE_OPEN", "1") == "1"
if WIDE:                                                       # show the passage: the wardrobe slid aside
    for mv in META["movable"]:
        if mv.get("motion") == "slide" and mv["name"] in bpy.data.objects:
            o = bpy.data.objects[mv["name"]]; d = mv["offset"]
            o.location = (o.location.x + d[0], o.location.y - d[1], o.location.z + d[2])
for L in META["lights"]:
    ld = bpy.data.lights.new(L["name"], "POINT"); ld.energy = L["lumens"] / 12.0; ld.color = L["color"]
    ld.shadow_soft_size = 0.25; ld.use_shadow = True
    lo = bpy.data.objects.new(L["name"], ld); sc.collection.objects.link(lo)
    x, y, z = L["xyz"]; lo.location = (x, -y, z)
print("objects", len(sc.objects), "kit instances", len(PL), flush=True)

# terrain patch (0.75 m) around the lodge, same splat-free grass/rock look as a quick read of the site
H = np.load(f"{ROOT}/terrain/H_4033.npy")
step = 3024.0 / (H.shape[0] - 1)
ox, oy = META["lodge"]["origin"][:2]
clamp = lambda i: min(max(i, 0), H.shape[0])
c0, c1 = clamp(int((ox - 260 + 1512) / step)), clamp(int((ox + 260 + 1512) / step))
r0, r1 = clamp(int((oy - 220 + 1512) / step)), clamp(int((oy + 300 + 1512) / step))
Z = H[r0:r1, c0:c1]
xs = -1512 + np.arange(c0, c1) * step; ys = -1512 + np.arange(r0, r1) * step
Xg, Yg = np.meshgrid(xs, ys)
ny_, nx_ = Z.shape
verts = np.stack([Xg.ravel(), -Yg.ravel(), Z.ravel()], 1).astype(np.float32)
rr, cc = np.mgrid[0:ny_ - 1, 0:nx_ - 1]; i0 = (rr * nx_ + cc).ravel()
quads = np.stack([i0, i0 + 1, i0 + nx_ + 1, i0 + nx_], 1)
me = bpy.data.meshes.new("terrain")
me.vertices.add(len(verts)); me.vertices.foreach_set("co", verts.ravel())
me.loops.add(len(quads) * 4); me.loops.foreach_set("vertex_index", quads.ravel().astype(np.int32))
me.polygons.add(len(quads)); me.polygons.foreach_set("loop_start", (np.arange(len(quads)) * 4).astype(np.int32))
me.polygons.foreach_set("loop_total", np.full(len(quads), 4, np.int32))
uv = me.uv_layers.new(name="tile")
uv.data.foreach_set("uv", np.stack([Xg.ravel()[quads.ravel()] / 4.0, Yg.ravel()[quads.ravel()] / 4.0], 1).ravel().astype(np.float32))
me.update(); me.validate()
tm = bpy.data.materials.new("terrain"); tm.use_nodes = True; nt = tm.node_tree; b = nt.nodes["Principled BSDF"]
TEX = f"{ROOT}/textures"
uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map = "tile"
def img(path, colour):
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
    t.image.colorspace_settings.name = "sRGB" if colour else "Non-Color"; nt.links.new(uvn.outputs["UV"], t.inputs["Vector"]); return t
geo = nt.nodes.new("ShaderNodeNewGeometry"); sepn = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Normal"], sepn.inputs["Vector"])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.93; mr.inputs["From Max"].default_value = 0.8
nt.links.new(sepn.outputs["Z"], mr.inputs["Value"])
mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; nt.links.new(mr.outputs["Result"], mix.inputs["Factor"])
nt.links.new(img(f"{TEX}/T_L_Grass_D.jpg", True).outputs["Color"], mix.inputs[6]); nt.links.new(img(f"{TEX}/T_L_Rock_D.jpg", True).outputs["Color"], mix.inputs[7])
nt.links.new(mix.outputs[2], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.9
me.materials.append(tm)
tob = bpy.data.objects.new("terrain", me); sc.collection.objects.link(tob)

# render: Cycles, night sky with a low moon, interiors lit by their candles / chandeliers / torches
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("GV_SAMPLES", "64")); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.cycles.max_bounces = 5; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 2; sc.cycles.transmission_bounces = 2
sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.cycles.light_sampling_threshold = 0.01
wo = bpy.data.worlds.new("sky"); wo.use_nodes = True; sc.world = wo
sky = wo.node_tree.nodes.new("ShaderNodeTexSky"); sky.sky_type = "NISHITA"
sky.sun_elevation = math.radians(7.0); sky.sun_rotation = math.radians(250.0); sky.sun_disc = False; sky.air_density = 2.0; sky.dust_density = 5.0
bg = wo.node_tree.nodes["Background"]; bg.inputs["Strength"].default_value = 0.25
wo.node_tree.links.new(sky.outputs["Color"], bg.inputs["Color"])
sun_d = bpy.data.lights.new("sun", "SUN"); sun_d.energy = 1.6; sun_d.color = (1.0, 0.72, 0.55); sun_d.angle = math.radians(2)
sun = bpy.data.objects.new("sun", sun_d); sc.collection.objects.link(sun)
sun.rotation_euler = (math.radians(90 - 7.0), 0.0, math.radians(250.0 - 90.0))
sc.render.resolution_x, sc.render.resolution_y = 1600, 900
sc.render.resolution_percentage = int(os.environ.get("GV_SCALE", "100"))
sc.view_settings.view_transform = "AgX"
try:
    sc.view_settings.look = "AgX - Medium High Contrast"
except Exception:
    pass
cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 20; cam_d.clip_start = 0.1; cam_d.clip_end = 5000
cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam

O = META["lodge"]["origin"]; LB = META["library"]["origin"]; LV = META["library"]["levels"]
lx = lambda x, y, z: (O[0] + x, O[1] + y, O[2] + z)
bx = lambda u, v, w: (LB[0] + u, LB[1] + v, LB[2] + w)
VIEWS = [  # id, name, camera (world), target (world), lens, exposure
    ("L1", "Lodge from the valley track", lx(62, 30, 9), lx(4, -2, 8), 26, 0.6),
    ("L2", "Great hall", lx(21.6, 2.9, 1.7), lx(12.6, -2.5, 1.9), 16, 1.0),
    ("L3", "Study and the wardrobe moved aside", lx(11.6, -6.2, 1.7), lx(8.6, -0.6, 1.3), 16, 1.3),
    ("L4", "Secret stair", lx(8.9, 6.2, -3.0), lx(8.9, 30.0, -14.0), 18, 1.6),
    ("B1", "Library from the balcony", bx(0.0, 2.5, LV[2] - LB[2] + 1.7), bx(0.0, 100.0, 6.0), 18, 1.0),
    ("B2", "Library nave and the grand stair", bx(4.0, 52.0, 1.7), bx(0.0, 10.0, 8.0), 18, 1.0),
    ("B3", "East aisle, second gallery", bx(7.4, 34.2, LV[2] - LB[2] + 1.7), bx(12.5, 70.0, LV[2] - LB[2] + 1.0), 18, 1.2),
    ("B4", "Great window", bx(-6.0, 80.0, 1.7), bx(0.0, 120.0, 12.0), 18, 1.0),
]
def unmirror(fn):
    """The scene is built in Blender axes (y = -Y east), i.e. mirrored: flip the image back to the real view."""
    im = bpy.data.images.load(fn, check_existing=False)
    w, h = im.size
    px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px)
    im.pixels.foreach_set(np.ascontiguousarray(px.reshape(h, w, 4)[:, ::-1]).ravel())
    im.filepath_raw = fn; im.file_format = "PNG"; im.save()
    bpy.data.images.remove(im)


LOG = []
for vid, name, c, t, lens, ex in VIEWS:
    if ONLY and vid not in ONLY:
        continue
    loc = Vector((c[0], -c[1], c[2])); tgt = Vector((t[0], -t[1], t[2]))
    cam.location = loc; cam.rotation_euler = (tgt - loc).to_track_quat("-Z", "Y").to_euler()
    cam_d.lens = lens; sc.view_settings.exposure = ex
    tob.hide_render = vid[0] == "B" or vid == "L4"
    fn = f"{OUT}/{vid}_{name.replace(' ', '_')}.png"
    sc.render.filepath = fn
    bpy.ops.render.render(write_still=True)
    unmirror(fn)
    LOG.append(dict(id=vid, name=name, camera=c, target=t, file=os.path.basename(fn)))
    print("rendered", fn, flush=True)
json.dump(LOG, open(f"{OUT}/lodge_views.json", "w"), indent=1)
