# Blender: Castle 2.0 ground plate (mesh14) heights and the castle's lowest points on a 2 m grid, at a given scale, in the
# centred frame of prep_castle20 (castle footprint centred, base of the castle at z = 0). -> assets/castle20/ground.npz
import bpy, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asset_lib import import_fbx, bounds
a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT, SC = a[0], a[1], float(a[2])
bpy.ops.wm.read_factory_settings(use_empty=True)
obs = import_fbx(SRC)
bpy.ops.object.select_all(action="DESELECT")
for o in obs:
    o.select_set(True)
bpy.context.view_layer.objects.active = obs[0]
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM"); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for o in obs:
    o.data.transform(__import__("mathutils").Matrix.Scale(SC, 4)); o.data.update()
plate = [o for o in obs if o.name == "mesh14"][0]
castle = [o for o in obs if o.name not in ("mesh14", "mesh0")]
lo, hi = bounds(castle)
off = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))       # same normalisation as prep_castle20
def tree(objs):
    import bmesh
    bm = bmesh.new()
    for o in objs:
        t = bmesh.new(); t.from_mesh(o.data); t.transform(o.matrix_world); m = bpy.data.meshes.new("t"); t.to_mesh(m); bm.from_mesh(m); t.free()
    return BVHTree.FromBMesh(bm)
TP, TC = tree([plate]), tree(castle)
xs = np.arange(lo.x - 10, hi.x + 10, 2.0); ys = np.arange(lo.y - 10, hi.y + 10, 2.0)
G = np.full((len(xs), len(ys)), np.nan); TOP = np.full_like(G, np.nan); BOT = np.full_like(G, np.nan)
for i, x in enumerate(xs):
    for j, y in enumerate(ys):
        h = TP.ray_cast(Vector((x, y, hi.z + 50)), Vector((0, 0, -1)), 1000)
        if h[0] is not None:
            G[i, j] = h[0].z - off.z
        h = TC.ray_cast(Vector((x, y, hi.z + 50)), Vector((0, 0, -1)), 1000)
        if h[0] is not None:
            TOP[i, j] = h[0].z - off.z
        h = TC.ray_cast(Vector((x, y, lo.z - 50)), Vector((0, 0, 1)), 1000)
        if h[0] is not None:
            BOT[i, j] = h[0].z - off.z
np.savez_compressed(OUT, xs=xs - off.x, ys=ys - off.y, plate=G, top=TOP, bottom=BOT)
print("GROUND plate z", np.nanmin(G).round(2), np.nanmax(G).round(2), "castle bottom", np.nanmin(BOT).round(2), np.nanmax(BOT).round(2))
