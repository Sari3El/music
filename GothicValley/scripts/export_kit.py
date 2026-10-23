# Blender: asset-pack meshes -> FBX for Unreal + kit.blend for renders. The kit pieces (assets/library/prefabs.blend) and
# the lodge shell (assets/fantasy/fantasy.blend) are authored in world axes (+X north, +Y east); like gb_build, the mesh
# is mirrored to Blender's y = -Y so that the FBX exporter + Unreal importer give back +Y east. The shell loses the door
# leaf (the door is open in game) and the fake-interior panels behind the windows of the visited hall wing.
# usage: blender -b --factory-startup --python export_kit.py -- ROOT OUT_CONTENT
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Matrix

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
json.dump(REP, open(f"{ROOT}/export/kit_report.json", "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=f"{ROOT}/export/kit.blend")
print("KIT_DONE", len(REP))
