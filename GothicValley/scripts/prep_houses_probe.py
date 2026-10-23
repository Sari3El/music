# probe: apply the declared textures (TownHouse2 on mesh0-2, BlackSmith on mesh6, WindowBlue on mesh3-5) and render
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asset_lib import tex, pbr, import_fbx, normalise, quick_views
a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = os.path.abspath(a[0]), os.path.abspath(a[1]); os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
obs = import_fbx(os.path.join(SRC, [f for f in os.listdir(SRC) if f.endswith(".fbx")][0]))
T = lambda k: tex(SRC, k)
th2 = pbr("TH2", T("TownHouse2HighPoly")); bs = pbr("BS", T("BlackSmithHighPoly")); win = pbr("WIN", T("WindowBlue1"))
for o in obs:
    m = th2 if o.name in ("mesh0", "mesh1", "mesh2") else bs if o.name == "mesh6" else win
    o.data.materials.clear(); o.data.materials.append(m)
lo, hi = normalise(obs, 150.0)
print("SIZE_M", [round(v, 1) for v in hi - lo])
quick_views(obs, OUT, "h", views=((30, 30), (210, 30)), res=(1200, 800))
# close-up of a few houses
import mathutils
quick_views(obs, OUT, "hc", views=((45, 20),), res=(1200, 800), target=mathutils.Vector((lo.x + 0.25 * (hi.x - lo.x), lo.y + 0.3 * (hi.y - lo.y), 5)), radius=45)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "houses_probe.blend"))
