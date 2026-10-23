# Shared helpers for the asset phase (Blender): import a pack FBX, rebuild its PBR materials from the pack textures
# (the FBX references were lost), apply a uniform scale, and render quick checks.
import bpy, os, re, glob, math
from mathutils import Vector


def tex(folder, key):
    """Pack texture whose name (after the 32-hex prefix) matches `key` (case-insensitive regex)."""
    for f in sorted(glob.glob(os.path.join(folder, "*"))):
        name = re.sub(r"^[0-9a-f]{32}_", "", os.path.basename(f))
        if re.search(key, name, re.I):
            return f
    return None


def pbr(name, color=None, normal=None, rough=None, metal=None, ao=None, tint=(0.5, 0.5, 0.5), rough_value=0.8,
        metallic=0.0, emission=0.0, alpha=None, normal_gl=True):
    """Principled material from texture files (any can be None)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    b.inputs["Base Color"].default_value = (*tint, 1)
    b.inputs["Roughness"].default_value = rough_value
    b.inputs["Metallic"].default_value = metallic

    def img(path, colour):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(path, check_existing=True)
        t.image.colorspace_settings.name = "sRGB" if colour else "Non-Color"
        return t
    if color:
        c = img(color, True)
        if ao:
            mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0
            nt.links.new(c.outputs["Color"], mix.inputs[6]); nt.links.new(img(ao, False).outputs["Color"], mix.inputs[7])
            nt.links.new(mix.outputs[2], b.inputs["Base Color"])
        else:
            nt.links.new(c.outputs["Color"], b.inputs["Base Color"])
        if alpha == "color":
            nt.links.new(c.outputs["Alpha"], b.inputs["Alpha"])
    if rough:
        nt.links.new(img(rough, False).outputs["Color"], b.inputs["Roughness"])
    if metal:
        nt.links.new(img(metal, False).outputs["Color"], b.inputs["Metallic"])
    if normal:
        nm = nt.nodes.new("ShaderNodeNormalMap")
        t = img(normal, False)
        if normal_gl:
            nt.links.new(t.outputs["Color"], nm.inputs["Color"])
        else:                                                    # DirectX map: flip green
            sep = nt.nodes.new("ShaderNodeSeparateColor"); comb = nt.nodes.new("ShaderNodeCombineColor")
            inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
            nt.links.new(t.outputs["Color"], sep.inputs["Color"])
            nt.links.new(sep.outputs["Green"], inv.inputs[1])
            nt.links.new(sep.outputs["Red"], comb.inputs["Red"]); nt.links.new(inv.outputs["Value"], comb.inputs["Green"])
            nt.links.new(sep.outputs["Blue"], comb.inputs["Blue"])
            nt.links.new(comb.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    if emission:
        b.inputs["Emission Strength"].default_value = emission
        if color:
            nt.links.new(nt.nodes[[n.name for n in nt.nodes if n.type == "TEX_IMAGE"][0]].outputs["Color"], b.inputs["Emission Color"])
        else:
            b.inputs["Emission Color"].default_value = (*tint, 1)
    m["textures"] = {k: v for k, v in dict(D=color, N=normal, R=rough, M=metal, AO=ao).items() if v}
    return m


def import_fbx(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    return [o for o in bpy.data.objects if o not in before and o.type == "MESH"]


def bounds(obs):
    """World bounds from the vertices themselves (bound_box is stale right after mesh edits)."""
    import numpy as np
    lo = np.full(3, 1e18); hi = np.full(3, -1e18)
    for o in obs:
        n = len(o.data.vertices)
        if n == 0:
            continue
        co = np.empty(n * 3); o.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
        M = np.array(o.matrix_world)
        w = co @ M[:3, :3].T + M[:3, 3]
        lo = np.minimum(lo, w.min(0)); hi = np.maximum(hi, w.max(0))
    return Vector(lo), Vector(hi)


def normalise(obs, scale, floor_to_zero=True, centre=True):
    """Apply transforms, scale uniformly about the origin, then put the footprint centre at x = y = 0 and the base at z = 0."""
    bpy.ops.object.select_all(action="DESELECT")
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")           # FBX empties carry the unit scale
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in obs:
        o.data.transform(__import__("mathutils").Matrix.Scale(scale, 4))
        o.data.update()
    lo, hi = bounds(obs)
    off = Vector(((lo.x + hi.x) / 2 if centre else 0, (lo.y + hi.y) / 2 if centre else 0, lo.z if floor_to_zero else 0))
    for o in obs:
        o.data.transform(__import__("mathutils").Matrix.Translation(-off))
        o.data.update()
    return bounds(obs)


def quick_views(obs, out, prefix, views=((30, 25), (120, 25), (210, 25), (300, 60)), res=(900, 600), engine="WORKBENCH",
                target=None, radius=None, lens=35):
    sc = bpy.context.scene
    if engine == "WORKBENCH":
        sc.render.engine = "BLENDER_WORKBENCH"
        sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "TEXTURE"; sh.show_cavity = True; sh.show_shadows = True
    else:
        sc.render.engine = "CYCLES"; sc.cycles.samples = 24; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = res
    wo = bpy.data.worlds.get("chk") or bpy.data.worlds.new("chk"); wo.color = (0.62, 0.66, 0.72); sc.world = wo
    lo, hi = bounds(obs)
    c = target if target is not None else (lo + hi) / 2
    R = radius or (hi - lo).length * 0.85
    cam_d = bpy.data.cameras.get("chk") or bpy.data.cameras.new("chk"); cam_d.lens = lens
    cam_d.clip_start = max(0.01, R * 0.002); cam_d.clip_end = R * 20
    cam = bpy.data.objects.get("chk") or bpy.data.objects.new("chk", cam_d)
    if cam.name not in sc.collection.objects:
        sc.collection.objects.link(cam)
    sc.camera = cam
    files = []
    for k, (az, el) in enumerate(views):
        d = Vector((math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(az)) * math.cos(math.radians(el)),
                    math.sin(math.radians(el))))
        cam.location = c + d * R
        cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(out, f"{prefix}_{k}.png")
        bpy.ops.render.render(write_still=True)
        files.append(sc.render.filepath)
    return files
