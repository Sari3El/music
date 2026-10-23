# Fantasy Castle (Hawtor Studio, CC BY): materials rebuilt by part name, real scale, saved as assets/fantasy.blend
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asset_lib import tex, pbr, import_fbx, normalise, quick_views, bounds
a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT, SCALE = os.path.abspath(a[0]), os.path.abspath(a[1]), float(a[2])
FIX = os.path.join(OUT, "tex")                                   # rebuilt colour maps (fc_fix_colors.py)
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
fbx = [f for f in os.listdir(SRC) if f.lower().endswith(".fbx")][0]
obs = import_fbx(os.path.join(SRC, fbx))
T = lambda k: tex(SRC, k)
M = {"Concrete": pbr("FC_Concrete", os.path.join(FIX, "T_FC_Concrete_D.png"), T("ConcreteNormal"), T("ConcreteRoughness")),
     "StoneBricks": pbr("FC_StoneBrickWall", T("StoneBrickWallColor"), T("StoneBrickWallNormal"), T("StoneBrickWallRoughness")),
     "BrickWall": pbr("FC_StoneBrickWall", T("StoneBrickWallColor"), T("StoneBrickWallNormal"), T("StoneBrickWallRoughness")),
     "Roof": pbr("FC_Roof", os.path.join(FIX, "T_FC_Roof_D.png"), T("RoofNormal"), T("RoofRoughness")),
     "Wood": pbr("FC_WoodPlanks", os.path.join(FIX, "T_FC_WoodPlanks_D.png"), T("WoodPlanksNormal"), T("WoodPlanksRoughness")),
     "Glass": pbr("FC_Glass", T("GlassColor"), T("GlassNormal"), T("GlassRoughness"), rough_value=0.1),
     "Back": pbr("FC_Back", tint=(0.03, 0.03, 0.03), rough_value=0.9),
     "Ground": pbr("FC_StoneTilesGround", T("StoneTilesGroundColors"), T("StoneTilesGroundNormal"), T("StoneTilesGroundRoughness"))}
for o in obs:
    key = next((k for k in M if f"_{k}_" in o.name), "Concrete")
    o.data.materials.clear(); o.data.materials.append(M[key])
lo, hi = normalise(obs, SCALE)
print("SIZE_M", [round(v, 2) for v in hi - lo])
quick_views(obs, OUT, "fc")
quick_views(obs, OUT, "fc_low", views=((200, 5), (20, 5)), lens=24, radius=(hi - lo).length * 0.6, target=(lo + hi) / 2 * 0.0 + __import__("mathutils").Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, 2.0)))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "fantasy.blend"))
print("DONE")
