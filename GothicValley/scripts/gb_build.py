# Blender: greybox JSON groups -> one mesh per group + UCX_ convex collisions -> FBX (Unreal) and a .blend for renders.
# World (design document) = +X north, +Y east, +Z up (Unreal, left-handed). Blender is right-handed, so Blender y = -Y
# (faces reversed); the FBX exporter + Unreal importer then give back Unreal Y = +east. An axis probe lets the Unreal
# script verify it.
import bpy, sys, os, json
import numpy as np

a = sys.argv[sys.argv.index('--') + 1:]
ROOT, OUTFBX, BLEND = a[0], a[1], a[2]
FILES = a[3:]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
COL = {"GB_Stone": (0.42, 0.42, 0.44), "GB_Roof": (0.17, 0.15, 0.17), "GB_Wood": (0.40, 0.28, 0.18), "GB_Interior": (0.62, 0.60, 0.57),
       "GB_Floor": (0.50, 0.48, 0.45), "GB_Detail": (0.62, 0.16, 0.12), "GB_Metal": (0.12, 0.12, 0.14), "GB_Plaster": (0.72, 0.67, 0.56),
       "GB_Tile": (0.48, 0.24, 0.17), "GB_Timber": (0.30, 0.20, 0.13), "GB_Water": (0.22, 0.34, 0.42), "GB_Church": (0.70, 0.68, 0.62),
       "GB_Ground": (0.35, 0.33, 0.28), "GB_Hedge": (0.18, 0.26, 0.14), "GB_Marker": (0.95, 0.75, 0.10),
       "GB_WinLit": (0.95, 0.62, 0.25), "GB_WinDark": (0.08, 0.09, 0.12)}
MAT = {}
for n, c in COL.items():
    m = bpy.data.materials.new(n); m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*c, 1)
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.85
    MAT[n] = m
common = dict(object_types={'MESH'}, use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE',
              mesh_smooth_type='FACE', use_mesh_modifiers=False, add_leaf_bones=False, bake_anim=False,
              path_mode='STRIP', embed_textures=False, axis_forward='-Z', axis_up='Y')


PIV = np.zeros(3)                                     # current group pivot (world metres)


def to_blender(v):
    v = np.asarray(v, float) - PIV
    return np.stack([v[:, 0], -v[:, 1], v[:, 2]], 1)


def build(name, prims):
    V, F, MI, mats = [], [], [], []
    off = 0
    for p in prims:
        if p["col"] == "only":
            continue
        v = to_blender(p["v"])
        if p["m"] not in mats:
            mats.append(p["m"])
        for f in p["f"]:
            F.append([off + i for i in f[::-1]]); MI.append(mats.index(p["m"]))
        V.append(v); off += len(v)
    if not V:
        return None
    me = bpy.data.meshes.new(name)
    me.from_pydata(np.concatenate(V).tolist(), [], F)
    for m in mats:
        me.materials.append(MAT.get(m, MAT["GB_Stone"]))
    me.polygons.foreach_set("material_index", MI)
    me.validate(); me.update()
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    return ob


def ucx(name, prims):
    obs = []
    k = 0
    for p in prims:
        if p["col"] is False:
            continue
        v = to_blender(p["v"])
        me = bpy.data.meshes.new(f"UCX_{name}_{k:03d}")
        me.from_pydata(v.tolist(), [], [list(f[::-1]) for f in p["f"]])
        ob = bpy.data.objects.new(f"UCX_{name}_{k:03d}", me); sc.collection.objects.link(ob)
        obs.append(ob); k += 1
    return obs


HINGES = {}
for fpath in FILES:
    mp = fpath.replace("_groups.json", "_meta.json")
    if os.path.exists(mp):
        for mv in json.load(open(mp)).get("movable", []):
            if "pivot" in mv:
                HINGES[mv["name"]] = mv["pivot"]
report = []
render_coll = bpy.data.collections.new("greybox"); sc.collection.children.link(render_coll)
for fpath in FILES:
    for g in json.load(open(fpath)):
        name, folder = g["name"], g["folder"]
        allv = np.concatenate([np.asarray(p["v"], float) for p in g["prims"]])
        if name in HINGES:                                 # doors, gates, portcullis: pivot on the hinge
            PIV[:] = HINGES[name]
        else:                                              # everything else: bottom centre of the bounds
            lo, hi = allv.min(0), allv.max(0)
            PIV[:] = [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]]
        PIV[:] = np.round(PIV, 2)
        vis = build(name, g["prims"])
        if vis is None:
            continue
        cols = ucx(name, g["prims"])
        os.makedirs(f"{OUTFBX}/{folder}", exist_ok=True)
        bpy.ops.object.select_all(action='DESELECT')
        vis.select_set(True)
        for o in cols:
            o.select_set(True)
        bpy.context.view_layer.objects.active = vis
        bpy.ops.export_scene.fbx(filepath=f"{OUTFBX}/{folder}/{name}.fbx", **common)
        for o in cols:
            bpy.data.objects.remove(o, do_unlink=True)
        sc.collection.objects.unlink(vis); render_coll.objects.link(vis)
        vis.location = (PIV[0], -PIV[1], PIV[2])           # the .blend keeps everything in place for renders
        report.append(dict(name=name, folder=folder, tris=sum(len(p.vertices) - 2 for p in vis.data.polygons), ucx=len(cols),
                           location_m=PIV.tolist(), movable=name in HINGES))
        print("FBX", name, report[-1]["tris"], "tris", len(cols), "UCX", flush=True)

# axis probe: a 2 m cube at world X = +1000 (north), Y = +500 (east), Z = 10 (pivot at the world origin)
PIV[:] = 0
probe = bpy.data.meshes.new("SM_GB_AxisProbe")
pv = to_blender([[999, 499, 9], [1001, 499, 9], [1001, 501, 9], [999, 501, 9], [999, 499, 11], [1001, 499, 11], [1001, 501, 11], [999, 501, 11]])
probe.from_pydata(pv.tolist(), [], [list(f[::-1]) for f in [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]])
probe.materials.append(MAT["GB_Marker"])
po = bpy.data.objects.new("SM_GB_AxisProbe", probe); sc.collection.objects.link(po)
bpy.ops.object.select_all(action='DESELECT'); po.select_set(True); bpy.context.view_layer.objects.active = po
os.makedirs(f"{OUTFBX}/Maps", exist_ok=True)
bpy.ops.export_scene.fbx(filepath=f"{OUTFBX}/Maps/SM_GB_AxisProbe.fbx", **common)
bpy.data.objects.remove(po, do_unlink=True)
json.dump(report, open(f"{ROOT}/greybox/build_report_{os.path.basename(BLEND).replace('.blend', '')}.json", "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("GB_BUILD_DONE", len(report))
