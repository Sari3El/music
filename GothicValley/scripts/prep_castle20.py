# Castle 2.0 (EldersCrawler): materials rebuilt per face (assets/castle20/classes.npz from c20_classes.py, or by
# orientation with MODE=face), uniform scale, centred on its footprint with the ground plate removed, saved as
# assets/castle20/castle20.blend, with check views.
# usage: blender -b --factory-startup --python prep_castle20.py -- PACK_DIR ROOT SCALE [island|face] [views]
import bpy, sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asset_lib import tex, pbr, import_fbx, normalise, quick_views, bounds
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
SRC, ROOT, SC = os.path.abspath(a[0]), os.path.abspath(a[1]), float(a[2])
MODE = a[3] if len(a) > 3 else "island"
VIEWS = len(a) > 4 and a[4] == "views"
OUT = f"{ROOT}/assets/castle20"
bpy.ops.wm.read_factory_settings(use_empty=True)
obs = import_fbx(os.path.join(SRC, [f for f in os.listdir(SRC) if f.lower().endswith(".fbx")][0]))
T = lambda k: tex(SRC, k)
M = [pbr("C2_Wall", T("WallStoneMix101_CLR"), T("WallStoneMix101_NRM"), None, ao=T("WallStoneMix101_OCC"), rough_value=0.85, normal_gl=False),
     pbr("C2_Roof", T("RoofsDetails01_CLRA"), T("RoofsDetails01_NRM"), T("RoofsDetails01_RGH"), normal_gl=False),
     pbr("C2_Floor", T("FloorStone101Mix2_CLR"), T("FloorStone101Mix2_NRM"), T("FloorStone101Mix2_RGH"), normal_gl=False)]
C = np.load(f"{OUT}/classes.npz")["cls"]
k0 = 0
order = sorted(obs, key=lambda o: o.name)            # faces.npz was written in bpy.data.objects order (sorted by name)
for o in order:
    n = len(o.data.polygons)
    o.data.materials.clear()
    for m in M:
        o.data.materials.append(m)
    if MODE == "face":
        nr = np.empty(n * 3); o.data.polygons.foreach_get("normal", nr); nz = nr.reshape(-1, 3)[:, 2]
        cl = np.where(nz > 0.9, 2, np.where(nz > 0.25, 1, 0))
    else:
        cl = C[k0:k0 + n]
    o.data.polygons.foreach_set("material_index", cl.astype(np.int32))
    k0 += n
assert k0 == len(C), (k0, len(C))
plate = [o for o in obs if o.name == "mesh14"][0]   # the hill the castle was modelled on: kept aside (not exported) for
for o in list(obs):                                  # views; the terrain of the crag takes its relief
    if o.name in ("mesh14", "mesh0"):
        if o.name == "mesh0":
            bpy.data.objects.remove(o, do_unlink=True)
        obs.remove(o)
lo, hi = normalise(obs + [plate], SC)                 # scale all, then re-centre on the castle alone
from mathutils import Matrix
lo, hi = bounds(obs)
off = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
for o in obs + [plate]:
    o.data.transform(Matrix.Translation(-off)); o.data.update()
lo, hi = bounds(obs)
plate.name = "C2_GroundPlate"; plate["not_exported"] = True
print("SIZE_M", [round(v, 1) for v in hi - lo])
if VIEWS:
    quick_views(obs, OUT, f"v_{MODE}", views=((35, 30), (215, 30)), res=(1400, 900))
    quick_views(obs, OUT, f"vc_{MODE}", views=((250, 8), (70, 8)), res=(1400, 900), target=Vector((0, 0, 15)), radius=95, lens=28)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f"castle20_{MODE}.blend"))
print("DONE")
