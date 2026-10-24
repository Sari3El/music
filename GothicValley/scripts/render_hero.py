# Blender (Cycles): textured hero views V1-V8 of the design document + an overview, terrain at 2.25 m with the same splat
# layering as the Unreal landscape material, river and fen water, physical sky with a low autumn sun.
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
# pack meshes (castle model, lodge, kit pieces) instanced from the placement files, as in Unreal
if os.path.exists(f"{ROOT}/export/kit.blend"):
    with bpy.data.libraries.load(f"{ROOT}/export/kit.blend", link=False) as (src, dst):
        dst.meshes = list(src.meshes)
    KITM = {m.name: m for m in dst.meshes if m is not None}
    for pf in sorted(f for f in os.listdir(f"{ROOT}/data") if f.startswith("placements_")):
        for i, p in enumerate(json.load(open(f"{ROOT}/data/{pf}"))):
            me = KITM.get(p["mesh"])
            if me is None:
                continue
            ob = bpy.data.objects.new(f"{p['mesh']}_{i}", me); sc.collection.objects.link(ob)
            x, y, z = p["loc"]
            ob.location = (x, -y, z); ob.rotation_euler = (0, 0, -math.radians(p["yaw"])); ob.scale = p["scale"]
print("objects", len(sc.objects), flush=True)

# ------------------------------------------------------------------ terrain + water
H = np.load(f"{ROOT}/terrain/H_4033.npy")
DEP = np.load(f"{ROOT}/terrain/river_depth.npy").astype(np.float32)
TEX = f"{ROOT}/textures"
ST = 3
Hs, Ds = H[::ST, ::ST], DEP[::ST, ::ST]
n = Hs.shape[0]
ax = np.linspace(-1512.0, 1512.0, H.shape[0])[::ST]
Xg, Yg = np.meshgrid(ax, ax)                     # arrays are [row = Y, col = X]


def grid_mesh(name, Z, mask_faces, mat, uvs=()):
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
    for uname, U, V in uvs:                                                      # per-vertex UVs spread to the loops
        lay = me.uv_layers.new(name=uname)
        lay.data.foreach_set("uv", np.stack([U.ravel()[quads.ravel()], V.ravel()[quads.ravel()]], 1).ravel().astype(np.float32))
    me.materials.append(mat)
    me.update(); me.validate()
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    return ob


def img_node(nt, path, colour, uvnode):
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
    t.image.colorspace_settings.name = "sRGB" if colour else "Non-Color"
    t.image.alpha_mode = "CHANNEL_PACKED"
    nt.links.new(uvnode.outputs["UV"], t.inputs["Vector"])
    return t


def terrain_material():
    """Same layering as the Unreal landscape material: grass, then mud, road, paving, rock and snow by the splat maps."""
    m = bpy.data.materials.new("T_Terrain"); m.use_nodes = True
    nt = m.node_tree; bsdf = nt.nodes["Principled BSDF"]
    uvt = nt.nodes.new("ShaderNodeUVMap"); uvt.uv_map = "tile"
    uvs = nt.nodes.new("ShaderNodeUVMap"); uvs.uv_map = "splat"
    sp = img_node(nt, f"{TEX}/T_GV_Splat.png", False, uvs)
    sep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(sp.outputs["Color"], sep.inputs["Color"])
    sp2 = img_node(nt, f"{TEX}/T_GV_Splat2.png", False, uvs)
    sep2 = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(sp2.outputs["Color"], sep2.inputs["Color"])
    w = {"L_Mud": sep.outputs["Blue"], "L_Road": sep.outputs["Green"], "L_Paving": sep2.outputs["Red"], "L_Rock": sep.outputs["Red"],
         "L_Snow": sp.outputs["Alpha"]}
    outs = {}
    for k, colour in (("D", True), ("R", False), ("N", False)):
        ext = "png" if k == "N" else "jpg"
        cur = img_node(nt, f"{TEX}/T_L_Grass_{k}.{ext}", colour, uvt).outputs["Color"]
        for layer in ("L_Mud", "L_Road", "L_Paving", "L_Rock", "L_Snow"):
            mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
            nt.links.new(w[layer], mix.inputs["Factor"]); nt.links.new(cur, mix.inputs[6])
            nt.links.new(img_node(nt, f"{TEX}/T_{layer}_{k}.{ext}", colour, uvt).outputs["Color"], mix.inputs[7])
            cur = mix.outputs[2]
        outs[k] = cur
    macro = nt.nodes.new("ShaderNodeTexNoise"); macro.inputs["Scale"].default_value = 0.004   # large-scale tone variation
    tc = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tc.outputs["Object"], macro.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeMapRange"); ramp.inputs["To Min"].default_value = 0.75; ramp.inputs["To Max"].default_value = 1.2
    nt.links.new(macro.outputs["Fac"], ramp.inputs["Value"])
    mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"; mul.inputs["Factor"].default_value = 1.0
    nt.links.new(outs["D"], mul.inputs[6]); nt.links.new(ramp.outputs["Result"], mul.inputs[7])
    nt.links.new(mul.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(outs["R"], bsdf.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 0.7
    nt.links.new(outs["N"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return m


TERR = terrain_material()
grid_mesh("Terrain", Hs, np.ones((n - 1, n - 1), bool), TERR,
          uvs=[("tile", Xg / 4.0, Yg / 4.0), ("splat", (Xg + 1512.0) / 3024.0, 1.0 - (Yg + 1512.0) / 3024.0)])
wet = Ds > 0.05
fen = (np.hypot(Xg + 1230, Yg + 1230) < 270) & (Hs < 3.0)
WZ = np.where(wet, Hs + Ds - 0.6, np.where(fen, 3.0, Hs - 5))
wm = (wet | fen)
wf = wm[:-1, :-1] & wm[1:, :-1] & wm[:-1, 1:] & wm[1:, 1:]
water = bpy.data.materials.new("T_Water"); water.use_nodes = True
wb = water.node_tree.nodes["Principled BSDF"]
wb.inputs["Base Color"].default_value = (0.012, 0.018, 0.02, 1); wb.inputs["Roughness"].default_value = 0.04
grid_mesh("Water", WZ.astype(np.float32), wf, water)

# ------------------------------------------------------------------ render settings: Cycles, physical sky, low sun
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = int(os.environ.get("GV_SAMPLES", "48"))
sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True
sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.cycles.max_bounces = 4; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2; sc.cycles.transmission_bounces = 2
sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
wo = bpy.data.worlds.new("sky"); wo.use_nodes = True; sc.world = wo
sky = wo.node_tree.nodes.new("ShaderNodeTexSky"); sky.sky_type = "NISHITA"
sky.sun_elevation = math.radians(16.0); sky.sun_rotation = math.radians(215.0); sky.sun_disc = False
sky.air_density = 1.6; sky.dust_density = 4.0
bg = wo.node_tree.nodes["Background"]; bg.inputs["Strength"].default_value = 0.35
wo.node_tree.links.new(sky.outputs["Color"], bg.inputs["Color"])
sun_d = bpy.data.lights.new("sun", "SUN"); sun_d.energy = 2.6; sun_d.angle = math.radians(1.5); sun_d.color = (1.0, 0.86, 0.70)
sun = bpy.data.objects.new("sun", sun_d); sc.collection.objects.link(sun)
sun.rotation_euler = (math.radians(90 - 16.0), 0.0, math.radians(215.0 - 90.0))
sc.render.resolution_x, sc.render.resolution_y = 1600, 900
sc.view_settings.view_transform = "AgX"
try:
    sc.view_settings.look = "AgX - Medium High Contrast"
except Exception:
    pass
sc.view_settings.exposure = 0.3
cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 24; cam_d.clip_start = 0.3; cam_d.clip_end = 20000
cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
torch_d = bpy.data.lights.new("torch", "POINT"); torch_d.energy = 1500.0; torch_d.color = (1.0, 0.62, 0.32); torch_d.shadow_soft_size = 0.3
torch = bpy.data.objects.new("torch", torch_d); sc.collection.objects.link(torch)
M = json.load(open(f"{ROOT}/data/layout_manifest.json"))


def ground(x, y):
    c = int(round((x + 1512) / (3024 / (H.shape[0] - 1)))); r = int(round((y + 1512) / (3024 / (H.shape[0] - 1))))
    return float(H[min(max(r, 0), H.shape[0] - 1), min(max(c, 0), H.shape[0] - 1)])


FIX = {"V3": 201.9 + 1.7, "V5": 80.0 + 1.7}                       # deck of the Great Bridge, floor of the bell chamber
CMH = json.load(open(f"{ROOT}/greybox/castle_meta.json")).get("hero_views", {})     # re-aimed at the castle model
views = [dict(v, **CMH.get(v["id"], {})) for v in M["hero_views"]]
FIX = {k: v for k, v in FIX.items() if k not in CMH or "camera" not in CMH[k]}
views = views + [dict(id="V0", name="Valley overview", camera=[-1450, -1650, 950], look_at=[200, -100, 60])]
def unmirror(fn):
    """The scene is built in Blender axes (y = -Y east), i.e. mirrored: flip the image back to the real view."""
    im = bpy.data.images.load(fn, check_existing=False)
    w, h = im.size
    px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px)
    im.pixels.foreach_set(np.ascontiguousarray(px.reshape(h, w, 4)[:, ::-1]).ravel())
    im.filepath_raw = fn; im.file_format = "PNG"; im.save()
    bpy.data.images.remove(im)


LOG = []
ONLY = [x for x in os.environ.get("GV_VIEWS", "").split(",") if x]
sc.render.resolution_percentage = int(os.environ.get("GV_SCALE", "100"))
for v in [v for v in views if not ONLY or v["id"] in ONLY]:
    cx, cy, cz = v["camera"]
    cz = FIX.get(v["id"], max(cz, ground(cx, cy) + 1.6))
    tx, ty, tz = v["look_at"]
    loc = Vector((cx, -cy, cz)); tgt = Vector((tx, -ty, tz))
    cam.location = loc
    cam.rotation_euler = (tgt - loc).to_track_quat("-Z", "Y").to_euler()
    cam_d.lens = 18 if v["id"] in ("V4", "V5", "V2") else 24
    sc.view_settings.exposure = {"V4": 2.4, "V5": 1.4}.get(v["id"], 0.3)       # interiors lit only through their openings
    torch.hide_render = v["id"] not in ("V4", "V5")                              # + a warm hand-held light (phase 7 will add torches)
    torch.location = loc + (tgt - loc).normalized() * 1.5 + Vector((0, 0, 0.6))
    fn = f"{OUT}/{v['id']}_{v['name'].replace(' ', '_')}.png"
    sc.render.filepath = fn
    bpy.ops.render.render(write_still=True)
    unmirror(fn)
    LOG.append(dict(id=v["id"], name=v["name"], camera_used=[cx, cy, round(cz, 2)], look_at=v["look_at"], file=os.path.basename(fn)))
    print("rendered", fn, flush=True)
json.dump(LOG, open(f"{OUT}/hero_views.json", "w"), indent=1)
