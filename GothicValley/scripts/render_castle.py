# Blender (Cycles): the vampires' castle (Castle 2.0 on the crag) assembled like in Unreal: our geometry
# (export/castle.blend from gb_build), the pack meshes (export/kit.blend) instanced from data/placements_castle.json,
# the point lights of greybox/castle_meta.json, the terrain around the crag. World -> Blender: y = -Y.
# usage: blender -b --factory-startup --python render_castle.py -- ROOT OUTDIR [view,view,...]
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
ROOT, OUT = a[0], a[1]
ONLY = a[2].split(",") if len(a) > 2 else []
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
with bpy.data.libraries.load(f"{ROOT}/export/castle.blend", link=False) as (src, dst):
    dst.objects = [n for n in src.objects if not n.startswith("UCX_")]
for ob in dst.objects:
    if ob is not None and ob.type == "MESH":
        sc.collection.objects.link(ob)
with bpy.data.libraries.load(f"{ROOT}/export/kit.blend", link=False) as (src, dst):
    dst.meshes = list(src.meshes)
KIT = {m.name: m for m in dst.meshes if m is not None}
PL = json.load(open(f"{ROOT}/data/placements_castle.json"))
META = json.load(open(f"{ROOT}/greybox/castle_meta.json"))
for i, p in enumerate(PL):
    me = KIT.get(p["mesh"])
    if me is None:
        print("missing kit mesh", p["mesh"]); continue
    ob = bpy.data.objects.new(f"{p['mesh']}_{i}", me); sc.collection.objects.link(ob)
    x, y, z = p["loc"]
    ob.location = (x, -y, z); ob.rotation_euler = (0, 0, -math.radians(p["yaw"])); ob.scale = p["scale"]
for L in META["lights"]:
    ld = bpy.data.lights.new(L["name"], "POINT"); ld.energy = L["lumens"] / 12.0; ld.color = L["color"]
    ld.shadow_soft_size = 0.25; ld.use_shadow = True
    lo = bpy.data.objects.new(L["name"], ld); sc.collection.objects.link(lo)
    x, y, z = L["xyz"]; lo.location = (x, -y, z)
print("objects", len(sc.objects), "kit instances", len(PL), flush=True)

# terrain patch (0.75 m) around the crag, same splat-free grass/rock look as a quick read of the site
H = np.load(f"{ROOT}/terrain/H_4033.npy")
step = 3024.0 / (H.shape[0] - 1)
ox, oy = META["model"]["origin"][:2]
clamp = lambda i: min(max(i, 0), H.shape[0])
c0, c1 = clamp(int((ox - 420 + 1512) / step)), clamp(int((ox + 260 + 1512) / step))
r0, r1 = clamp(int((oy - 330 + 1512) / step)), clamp(int((oy + 260 + 1512) / step))
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

O = META["model"]["origin"]
cx = lambda x, y, z: (O[0] + x, O[1] + y, O[2] + z)
RM = {r["name"]: r for r in META["rooms"]}
def rc(n, fx=0.5, fy=0.5, dz=1.7):
    r = RM[n]; return (r["x0"] + (r["x1"] - r["x0"]) * fx, r["y0"] + (r["y1"] - r["y0"]) * fy, r["z0"] + dz)
VIEWS = [  # id, name, camera (world), target (world), lens, exposure
    ("C1", "Castle from the Great Bridge", (744.0, 96.0, 202.0), (716.0, 260.0, 222.0), 24, 0.4),
    ("C2", "Castle on its crag from the city side", (520.0, 120.0, 260.0), (715.0, 300.0, 215.0), 30, 0.3),
    ("C3", "Forecourt and gate", (718.5, 205.0, 205.6), (718.7, 245.0, 208.0), 22, 0.5),
    ("C4", "Inner court toward the palace", cx(-6.0, -28.0, 12.5), cx(0.0, 30.0, 26.0), 20, 0.5),
    ("C5", "Great Hall", rc("Great Hall", 0.5, 0.08), rc("Great Hall", 0.5, 0.95, 2.5), 16, 1.2),
    ("C6", "Throne Room", rc("Throne Room", 0.93, 0.5), rc("Throne Room", 0.0, 0.5, 2.0), 16, 1.2),
    ("C7", "Library tower", rc("Library", 0.15, 0.2), rc("Library", 0.85, 0.8, 1.2), 14, 1.3),
    ("C8", "Lord's apartments", rc("Lord's Apartments", 0.85, 0.2), rc("Lord's Apartments", 0.1, 0.8, 1.0), 14, 1.3),
    ("C9", "Chapel", cx(-37.2, 54.2, 23.1), cx(-23.0, 54.2, 23.4), 18, 1.2),
    ("C10", "War Room", cx(43.2, -19.8, 16.2), cx(38.0, -9.0, 15.2), 16, 1.2),
    ("C11", "Banquet Hall (undercroft)", rc("Banquet Hall", 0.97, 0.12, 1.8), rc("Banquet Hall", 0.0, 0.7, 3.5), 15, 1.3),
    ("C12", "Kitchen", rc("Kitchen", 0.95, 0.9, 1.7), rc("Kitchen", 0.05, 0.4, 1.0), 15, 1.3),
    ("C13", "Wine and blood cellar", rc("Wine and blood cellar", 0.95, 0.08, 1.7), rc("Wine and blood cellar", 0.1, 0.7, 1.0), 15, 1.3),
    ("C14", "Crypt", rc("Crypt", 0.95, 0.15, 1.7), rc("Crypt", 0.4, 0.55, 1.0), 15, 1.4),
    ("C15", "Dungeon", rc("Dungeon", 0.01, 0.5, 1.7), rc("Dungeon", 1.0, 0.5, 1.2), 18, 1.4),
    ("C16", "Grand stair from the Great Hall", cx(-4.6, 47.3, 23.4), cx(-8.6, 37.5, 12.0), 15, 1.8),
    ("C17", "Foot of the secret spiral (crypt)", cx(-8.5, 55.5, 1.8), cx(-14.5, 59.0, 1.8), 16, 1.8),
    ("C18", "Secret tunnel, last leg", cx(-60.0, 59.4, -84.3), cx(-115.0, 59.4, -84.6), 20, 1.6),
    ("C19", "Hidden door at the foot of the cliff", cx(-133.0, 67.0, -78.0), cx(-117.5, 59.4, -79.5), 26, 0.6),
    ("C20", "Secret panel behind the throne", cx(-8.0, 53.2, 23.7), cx(-15.0, 59.0, 23.6), 16, 1.2),
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
    tob.hide_render = False
    fn = f"{OUT}/{vid}_{name.replace(' ', '_')}.png"
    sc.render.filepath = fn
    bpy.ops.render.render(write_still=True)
    unmirror(fn)
    LOG.append(dict(id=vid, name=name, camera=c, target=t, file=os.path.basename(fn)))
    print("rendered", fn, flush=True)
json.dump(LOG, open(f"{OUT}/castle_views.json", "w"), indent=1)
