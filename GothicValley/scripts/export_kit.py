# Blender: asset-pack meshes -> FBX for Unreal + kit.blend for renders. The kit pieces (assets/library/prefabs.blend), the
# props (assets/props/props.blend) and
# the lodge shell (assets/fantasy/fantasy.blend) are authored in world axes (+X north, +Y east); like gb_build, the mesh
# is mirrored to Blender's y = -Y so that the FBX exporter + Unreal importer give back +Y east. The shell loses the door
# leaf (the door is open in game) and the fake-interior panels behind the windows of the visited hall wing.
# usage: blender -b --factory-startup --python export_kit.py -- ROOT OUT_CONTENT
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from c2cuts import planes, corners

a = sys.argv[sys.argv.index("--") + 1:]
ROOT, OUT = a[0], a[1]
common = dict(object_types={'MESH'}, use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE',
              mesh_smooth_type='FACE', use_mesh_modifiers=False, add_leaf_bones=False, bake_anim=False,
              path_mode='STRIP', embed_textures=False, axis_forward='-Z', axis_up='Y')
MIRROR = Matrix.Scale(-1, 4, (0, 1, 0))
HALL = (np.array([6.3, -7.0, -1.0]), np.array([22.6, 4.2, 7.4]))      # visited hall wing of the shell (shell frame)


def take(path):
    with bpy.data.libraries.load(path) as (src, dst):
        dst.objects = list(src.objects)
    return [o for o in dst.objects if o is not None and o.type == "MESH"]


def mirror(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.transform(bm, matrix=MIRROR, verts=bm.verts)
    bmesh.ops.reverse_faces(bm, faces=bm.faces, flip_multires=False)
    bm.to_mesh(ob.data); bm.free(); ob.data.update()


def export(ob, folder):
    os.makedirs(f"{OUT}/{folder}", exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(filepath=f"{OUT}/{folder}/{ob.name}.fbx", **common)
    REP.append(dict(name=ob.name, folder=folder, tris=sum(len(p.vertices) - 2 for p in ob.data.polygons),
                    materials=[m.name for m in ob.data.materials if m]))
    print("FBX", ob.name, REP[-1]["tris"], REP[-1]["materials"], flush=True)


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
REP = []
for o in take(f"{ROOT}/assets/library/prefabs.blend"):
    sc.collection.objects.link(o)
    o.name = o.name.replace("PF_", "SM_"); o.data.name = o.name
    o.matrix_world = Matrix.Identity(4)
    mirror(o)
    export(o, "Props/LibraryKit")
# the commissioner's prop packs (assets/props/props.blend, prep_props.py): one FBX per prefab, in its pack's folder
if os.path.exists(f"{ROOT}/assets/props/props.blend"):
    PJ = json.load(open(f"{ROOT}/assets/props/props.json"))
    for o in take(f"{ROOT}/assets/props/props.blend"):
        sc.collection.objects.link(o)
        folder = PJ[o.name]["folder"]
        o.name = o.name.replace("PF_", "SM_"); o.data.name = o.name
        o.matrix_world = Matrix.Identity(4)
        mirror(o)
        export(o, folder)
# lodge shell: one mesh, minus the door leaf and the hall-wing fake-interior panels
parts = take(f"{ROOT}/assets/fantasy/fantasy.blend")
for o in parts:
    sc.collection.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    kill = []
    if o.name.endswith("Wood_0"):
        kill = list(bm.faces)
    elif o.name.endswith("Back_0"):
        kill = [f for f in bm.faces if np.all(np.array(f.calc_center_median()) > HALL[0]) and np.all(np.array(f.calc_center_median()) < HALL[1])]
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(o.data); bm.free(); o.matrix_world = Matrix.Identity(4)
    print("shell part", o.name, "removed", len(kill))
bpy.ops.object.select_all(action="DESELECT")
for o in parts:
    o.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
shell = bpy.context.view_layer.objects.active
shell.name = shell.data.name = "SM_FC_Lodge"
mirror(shell)
export(shell, "Environment/Lodge")
# vampires' castle (Castle 2.0): one mesh at scale 160 (centred frame), minus the gate leaves (Movable ones replace them)
c2 = f"{ROOT}/assets/castle20/castle20_island.blend"
if os.path.exists(c2):
    CUTS = json.load(open(f"{ROOT}/greybox/castle_meta.json"))["model"]["cuts"]      # gate leaves, cut doorways, room clutter
    parts = [o for o in take(c2) if not o.get("not_exported")]
    BOX = [(planes(k), corners(k).min(0), corners(k).max(0), k["z"]) for k in CUTS]
    ncut = 0
    for o in parts:
        sc.collection.objects.link(o)
        bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
        # candidate faces (bounding box against any cut box), then each box: bisect them by its 6 planes, delete inside
        co = np.array([v.co[:] for v in bm.verts]); bm.faces.ensure_lookup_table()
        fmin = np.array([co[[v.index for v in f.verts]].min(0) for f in bm.faces]); fmax = np.array([co[[v.index for v in f.verts]].max(0) for f in bm.faces])
        hit = np.zeros(len(fmin), bool)
        for P, lo2, hi2, zz in BOX:
            hit |= ((fmax[:, 0] > lo2[0]) & (fmin[:, 0] < hi2[0]) & (fmax[:, 1] > lo2[1]) & (fmin[:, 1] < hi2[1]) & (fmax[:, 2] > zz[0]) & (fmin[:, 2] < zz[1]))
        pool = set(bm.faces[i] for i in np.nonzero(hit)[0])
        for P, lo2, hi2, zz in BOX:
            def near(f):
                c = np.array([v.co[:] for v in f.verts]); mn, mx = c.min(0), c.max(0)
                return mx[0] > lo2[0] and mn[0] < hi2[0] and mx[1] > lo2[1] and mn[1] < hi2[1] and mx[2] > zz[0] and mn[2] < zz[1]
            fs = [f for f in pool if f.is_valid and near(f)]
            for p0, n in P:
                if not fs:
                    break
                geom = list(set(fs) | {e for f in fs for e in f.edges} | {v for f in fs for v in f.verts})
                r = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=Vector(p0), plane_no=Vector(n), dist=1e-5)
                new = {g for g in r["geom"] if isinstance(g, bmesh.types.BMFace)}
                pool |= new
                fs = [f for f in set(fs) | new if f.is_valid and near(f)]
            kill = [f for f in fs if f.is_valid and all(np.dot(np.array(f.calc_center_median()[:]) - p0, n) < 0 for p0, n in P)]
            ncut += len(kill)
            bmesh.ops.delete(bm, geom=kill, context="FACES")
            pool = {f for f in pool if f.is_valid}
        bm.to_mesh(o.data); bm.free(); o.matrix_world = Matrix.Identity(4)
    print("CASTLE_CUT_FACES", ncut)
    bpy.ops.object.select_all(action="DESELECT")
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    castle = bpy.context.view_layer.objects.active
    castle.name = castle.data.name = "SM_C2_Castle"
    mirror(castle)
    export(castle, "Environment/Castle")
json.dump(REP, open(f"{ROOT}/export/kit_report.json", "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=f"{ROOT}/export/kit.blend")
print("KIT_DONE", len(REP))
