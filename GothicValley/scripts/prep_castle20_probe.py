import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asset_lib import tex, pbr, import_fbx, normalise, quick_views, bounds
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT, SC, TEXK = os.path.abspath(a[0]), os.path.abspath(a[1]), float(a[2]), a[3]
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
obs = import_fbx(os.path.join(SRC, [f for f in os.listdir(SRC) if f.endswith(".fbx")][0]))
T = lambda k: tex(SRC, k)
mats = {"wall": pbr("C2_Wall", T("WallStoneMix101_CLR"), T("WallStoneMix101_NRM"), None, ao=T("WallStoneMix101_OCC"), normal_gl=False),
        "roof": pbr("C2_Roof", T("RoofsDetails01_CLRA"), T("RoofsDetails01_NRM"), T("RoofsDetails01_RGH"), normal_gl=False),
        "floor": pbr("C2_Floor", T("FloorStone101Mix2_CLR"), T("FloorStone101Mix2_NRM"), T("FloorStone101Mix2_RGH"), normal_gl=False)}
for o in obs:
    m = mats["floor"] if o.name == "mesh14" else mats[TEXK]
    o.data.materials.clear(); o.data.materials.append(m)
lo, hi = normalise(obs, SC)
print("SIZE_M", [round(v, 1) for v in hi - lo])
quick_views(obs, OUT, f"c_{TEXK}", views=((35, 35),), res=(1400, 900))
quick_views(obs, OUT, f"cc_{TEXK}", views=((250, 12),), res=(1400, 900), target=Vector((lo.x + 0.3 * (hi.x - lo.x), lo.y + 0.15 * (hi.y - lo.y), 8)), radius=60)
if TEXK == "roof":
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "castle20_probe.blend"))
