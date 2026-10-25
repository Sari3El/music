# Blender: the commissioner's prop packs (props_defs.PACKS) -> one prefab per prop, in world axes like the library kit
# (+X north, +Y east: Blender y is mirrored to -Y; export_kit mirrors it back), front turned to +X, origin at the centre
# of the footprint on the floor (furniture: the floor of its showcase room; chandelier: the top of its chain). Pieces the
# commissioner asked to leave out are removed here (throne: its stone base and the candles on the floor in front, left).
# Writes assets/props/props.blend (PF_PR_* objects with materials built from the pack textures, for the renders),
# assets/props/props.json (size, triangles, materials of each prefab) and contact sheet tiles.
# usage: blender -b --factory-startup --python prep_props.py -- PACKS_DIR OUT_DIR [SHEET_DIR]
import bpy, bmesh, sys, os, glob, json, math, re
import numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from props_defs import PACKS, MATS, FURN
import asset_lib as AL

a = sys.argv[sys.argv.index("--") + 1:]
PK, OUT = os.path.abspath(a[0]), os.path.abspath(a[1])
SHEET = a[2] if len(a) > 2 else None
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
MIRROR = Matrix.Scale(-1, 4, (0, 1, 0))
PREF = {}


def pack_dir(key):
    return glob.glob(os.path.join(PK, PACKS[key]["dir"]))[0]


def tex(key, rx):
    if rx is None or rx == "D":
        return None
    f = AL.tex(pack_dir(MATS[key]["pack"]), rx)
    if f is None:
        raise SystemExit(f"missing texture {rx} for {key}")
    return f


def material(name):
    """Principled material from the pack textures (renders); Unreal builds its own from textures/T_<name>_*."""
    m = bpy.data.materials.get(name)
    if m is not None:
        return m
    s = MATS[name]
    d = tex(name, s["D"])
    m = AL.pbr(name, color=d, normal=tex(name, s.get("N")), rough=None if s.get("rough_from_spec") else tex(name, s.get("R")),
               metal=tex(name, s.get("metal_map")), ao=tex(name, s.get("ao")), tint=s["col"], rough_value=s.get("rough", 0.8),
               metallic=s.get("metal", 0.0), alpha="color" if s.get("alpha") == "D" else None, normal_gl=not s.get("dxn"))
    nt = m.node_tree; b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    dn = next((n for n in nt.nodes if n.type == "TEX_IMAGE" and d and n.image.filepath == d), None)
    def img(path):
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(path, check_existing=True)
        t.image.colorspace_settings.name = "Non-Color"
        return t
    if s.get("rough_from_spec"):
        inv = nt.nodes.new("ShaderNodeInvert"); nt.links.new(img(tex(name, s["R"])).outputs["Color"], inv.inputs["Color"])
        nt.links.new(inv.outputs["Color"], b.inputs["Roughness"])
    if s.get("alpha") and s["alpha"] != "D":
        nt.links.new(img(tex(name, s["alpha"])).outputs["Color"], b.inputs["Alpha"])
    if s.get("emit"):
        src = dn if s["emit"] == "D" else img(tex(name, s["emit"]))
        if s["emit"] != "D":
            src.image.colorspace_settings.name = "sRGB"
        nt.links.new(src.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 4.0
    if dn is not None:
        nt.nodes.active = dn                                   # Workbench "texture" colour shows the base colour
    m.use_backface_culling = False
    return m


def import_pack(key):
    """Pack FBX -> mesh objects with their transforms (and the pack scale) applied, in Blender axes (metres)."""
    P = PACKS[key]
    fbx = [f for f in glob.glob(os.path.join(pack_dir(key), "*")) if f.lower().endswith(".fbx")][0]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=fbx)
    new = [o for o in bpy.data.objects if o not in before]
    obs = [o for o in new if o.type == "MESH" and len(o.data.vertices)
           and not any(s in o.name for s in P.get("skip_objects", []) + P.get("drop_objects", []))]
    bpy.context.view_layer.update()
    MW = {o.name: o.matrix_world.copy() for o in obs}            # before the parents (FBX unit scale, axes) go
    for o in new:
        if o not in obs:
            bpy.data.objects.remove(o)
    for o in obs:
        o.data = o.data.copy()
        M = MW[o.name]
        o.parent = None; o.matrix_world = Matrix.Identity(4)
        o.data.transform(M)
        if M.determinant() < 0:
            o.data.flip_normals()
        # material from the object name (packs whose slots all carry one name) or the slot name; "" = any
        mats = P["mats"]
        def pick(label):
            for k, v in mats.items():
                if k and k.lower() in label.lower():
                    return v
            return mats.get("")
        names = [pick(o.name) or pick(s.material.name if s.material else "") for s in o.material_slots] or [pick(o.name)]
        o.data.materials.clear()
        for n_ in names:
            o.data.materials.append(material(n_))
        with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o], selected_editable_objects=[o]):
            bpy.ops.mesh.customdata_custom_splitnormals_clear()
    return obs


def verts(o):
    co = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get("co", co)
    return co.reshape(-1, 3)


def join(obs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    if len(obs) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = o.data.name = name
    return o


def loose_parts(o):
    """Vertex index -> loose part id (connected through faces)."""
    n = len(o.data.vertices); par = np.arange(n)
    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for p in o.data.polygons:
        vs = list(p.vertices); r0 = find(vs[0])
        for v in vs[1:]:
            r1 = find(v)
            if r1 != r0:
                par[r1] = r0
    return np.array([find(i) for i in range(n)])


def keep_faces(o, keep, name):
    """Copy of `o` with only the faces whose index is in `keep`."""
    c = o.copy(); c.data = o.data.copy(); c.name = c.data.name = name
    sc.collection.objects.link(c)
    bm = bmesh.new(); bm.from_mesh(c.data); bm.faces.ensure_lookup_table()
    k = set(keep)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in k], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(c.data); bm.free()
    return c


def clusters(o, tol=0.01):
    """Faces of `o` grouped into pieces: loose parts joined when their boxes touch (as props_split_probe)."""
    lp = loose_parts(o); co = verts(o)
    roots, inv = np.unique(lp, return_inverse=True)
    lo = np.array([co[inv == i].min(0) for i in range(len(roots))]); hi = np.array([co[inv == i].max(0) for i in range(len(roots))])
    nv = np.bincount(inv)
    par = list(range(len(roots)))
    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    L, H = lo - tol, hi + tol
    for i in range(len(roots)):
        for j in np.nonzero((L[i] <= H).all(1) & (H[i] >= L).all(1))[0]:
            ri, rj = f(i), f(int(j))
            if ri != rj:
                par[rj] = ri
    groups = {}
    for i in range(len(roots)):
        groups.setdefault(f(i), []).append(i)
    face_part = np.array([inv[p.vertices[0]] for p in o.data.polygons])
    out = []
    for g in sorted(groups.values(), key=lambda g: -sum(nv[i] for i in g)):
        gs = set(g)
        out.append(dict(lo=lo[g].min(0), hi=hi[g].max(0), faces=[k for k, p in enumerate(face_part) if p in gs]))
    return out


def drop_boxes(o, boxes):
    lp = loose_parts(o); co = verts(o)
    kill = set()
    for r in np.unique(lp):
        m = lp == r; l_, h_ = co[m].min(0), co[m].max(0)
        for b in boxes:
            if l_[0] >= b[0] and h_[0] <= b[1] and l_[1] >= b[2] and h_[1] <= b[3] and l_[2] >= b[4] and h_[2] <= b[5]:
                kill |= set(np.nonzero(m)[0].tolist())
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in kill], context="VERTS")
    bm.to_mesh(o.data); bm.free()
    print("dropped", len(kill), "vertices from", o.name)


def finish(o, name, key, front=(0.0, -1.0, 0.0), anchor="floor", yaw_fix=0.0, floor_z=0.0):
    """Blender axes -> world axes (mirror y), front -> +X, origin per anchor; register the prefab."""
    P = PACKS[key]
    me = o.data
    me.transform(MIRROR); me.flip_normals()
    fw = Vector((front[0], -front[1], front[2]))
    ang = -math.atan2(fw.y, fw.x) + math.radians(yaw_fix)
    me.transform(Matrix.Rotation(ang, 4, "Z"))
    co = verts(o); lo, hi = co.min(0), co.max(0)
    z0 = {"floor": lo[2], "floor0": floor_z, "ceiling": hi[2]}[anchor]
    me.transform(Matrix.Translation((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -z0)))
    me.update()
    o.name = o.data.name = "PF_PR_" + name
    co = verts(o)
    me.calc_loop_triangles()
    PREF[o.name] = dict(pack=key, folder=P["folder"], lo=co.min(0).round(3).tolist(), hi=co.max(0).round(3).tolist(),
                        tris=len(me.loop_triangles), materials=[m.name for m in me.materials if m], anchor=anchor)
    print("PREFAB", o.name, PREF[o.name]["lo"], PREF[o.name]["hi"], PREF[o.name]["tris"], flush=True)
    return o


def scale_to(obs, P):
    if "scale" in P:
        s = P["scale"]
    else:
        co = np.vstack([verts(o) for o in obs])
        h = co[:, 2].max() - co[:, 2].min() if not P.get("stand_up") else co[:, 1].max() - co[:, 1].min()
        s = P["height"] / h
    for o in obs:
        o.data.transform(Matrix.Scale(s, 4))
    return s


for key, P in PACKS.items():
    obs = import_pack(key)
    s = scale_to(obs, P)
    front = tuple(P.get("front", (0.0, -1.0, 0.0)))
    if P["mode"] == "objects":
        for i, o in enumerate(sorted(obs, key=lambda o: o.name)):
            label = re.sub(r"[^A-Za-z0-9]+", "", re.sub(P["label"], "", o.name))
            finish(o, f"{key}_{label}", key, front)
        continue
    o = join(obs, key)
    if P.get("drop_boxes"):
        drop_boxes(o, P["drop_boxes"])
    if P.get("stand_up"):                                        # lying along y, front up: head end = the wider end (arms)
        co = verts(o); ymid = (co[:, 1].min() + co[:, 1].max()) / 2
        span = lambda m: np.ptp(co[m, 0]) if m.any() else 0
        head_pos = span(co[:, 1] > ymid) > span(co[:, 1] < ymid)
        R = Matrix.Rotation(math.radians(90 if head_pos else -90), 4, "X")
        o.data.transform(R); fr = R.to_3x3() @ Vector((0, 0, 1)); front = (fr.x, fr.y, fr.z)
    if P["mode"] == "whole":
        finish(o, key, key, front, P.get("anchor", "floor"))
        continue
    # clusters: one prefab per piece, named and turned by props_defs.FURN (matched on the piece's box in the showcase)
    for k, c in enumerate(clusters(o)):
        hit = [f for f in FURN if np.allclose(f["lo"], c["lo"], atol=0.06)]
        if not hit:
            print("unnamed piece", k, c["lo"].round(3).tolist(), (c["hi"] - c["lo"]).round(3).tolist())
        f = hit[0] if hit else dict(name=f"Piece{k:02d}", yaw=0.0)
        if f.get("skip"):
            continue
        p = keep_faces(o, c["faces"], f["name"])
        finish(p, f"{key}_{f['name']}", key, (1.0, 0.0, 0.0), f.get("anchor", "floor"), f.get("yaw", 0.0))
    bpy.data.objects.remove(o)

os.makedirs(OUT, exist_ok=True)
for o in list(sc.objects):
    if not o.name.startswith("PF_PR_"):
        bpy.data.objects.remove(o)
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "props.blend"))
json.dump(PREF, open(os.path.join(OUT, "props.json"), "w"), indent=1)
print("PROPS_DONE", len(PREF))

if SHEET:
    # contact sheet tiles: each prefab seen three-quarter from its front (+X), true handedness (mirrored back);
    # SHEET/views.json lists them for sheet.py
    os.makedirs(SHEET, exist_ok=True)
    sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "TEXTURE"
    sh.show_cavity = True; sh.show_backface_culling = False
    sc.render.resolution_x = sc.render.resolution_y = 360
    wo = bpy.data.worlds.new("w"); wo.color = (0.55, 0.58, 0.62); sc.world = wo
    cd = bpy.data.cameras.new("c"); cam = bpy.data.objects.new("c", cd); sc.collection.objects.link(cam); sc.camera = cam
    obs = sorted([o for o in sc.objects if o.name.startswith("PF_PR_")], key=lambda o: o.name)
    for o in obs:
        o.hide_render = True
    views = []
    for o in obs:
        o.hide_render = False; o.scale = (1, -1, 1)
        co = verts(o) * [1, -1, 1]; lo, hi = co.min(0), co.max(0)
        c = Vector(((lo + hi) / 2).tolist()); R = float(np.linalg.norm(hi - lo)) * 1.25 + 0.05
        az, el = math.radians(-25), math.radians(22)              # front (+X) seen a little from the right and above
        d = Vector((math.cos(az) * math.cos(el), -math.sin(az) * math.cos(el), math.sin(el)))
        cam.location = c + d * R; cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
        cd.lens = 40; cd.clip_start = R * 0.01; cd.clip_end = R * 10
        f = os.path.join(SHEET, o.name + ".png"); sc.render.filepath = f; bpy.ops.render.render(write_still=True)
        views.append([o.name[6:] + "  %.2f x %.2f x %.2f" % tuple(hi - lo), f])
        o.hide_render = True; o.scale = (1, 1, 1)
    json.dump(views, open(os.path.join(SHEET, "views.json"), "w"))
    print("SHEET", SHEET, len(views))
