# Classic Library (denniswoo1993): materials rebuilt from the object name suffixes, saved as assets/library.blend,
# plus a plan view and interior views to design the underground library from its parts.
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asset_lib import tex, pbr, import_fbx, normalise, quick_views, bounds
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = os.path.abspath(a[0]), os.path.abspath(a[1])
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
obs = import_fbx(os.path.join(SRC, [f for f in os.listdir(SRC) if f.endswith(".fbx")][0]))
T = lambda k: tex(SRC, k)
FIX = os.path.join(OUT, "tex")                         # colour maps rebuilt by lib_fix_colors.py
M = {"Glossy wood": pbr("LB_GlossyWood", T("Wood027_2K_Color"), T("Wood027_2K_NormalGL"), T("Wood027_2K_Roughness"), rough_value=0.45),
     "Wood floor": pbr("LB_WoodFloor", T("WoodFloor016_2K_Color"), T("WoodFloor016_2K_NormalGL"), T("WoodFloor016_2K_Roughness")),
     "Leather": pbr("LB_Leather", T("Leather023_2K_Color"), T("Leather023_2K_NormalGL"), T("Leather023_2K_Roughness")),
     "Sandstone bricks": pbr("LB_Sandstone", T("sandstone_blocks_04_diff"), T("sandstone_blocks_04_nor_gl"), T("sandstone_blocks_04_rough")),
     "Stone": pbr("LB_Stone", os.path.join(FIX, "T_LB_Stone_D.png"), T("Concrete012_2K_NormalGL"), T("Concrete012_2K_Roughness"), tint=(1, 1, 1)),
     "Metal": pbr("LB_Metal", os.path.join(FIX, "T_LB_Metal_D.png"), T("WornMetal_1K_normal"), T("WornMetal_1K_roughness"), tint=(1, 1, 1), metallic=0.85, rough_value=0.5),
     "SHC Old Book Material": pbr("LB_OldBook", T("SHC_Old_Book_Diffuse"), T("SHC_Old_Book_Normal"), T("SHC_Old_Book_Roughness"), T("SHC_Old_Book_Metallic")),
     "Paper": pbr("LB_Paper", T("RGB_unnamed"), tint=(0.75, 0.68, 0.52), rough_value=0.9),
     "Procedural stained glass": pbr("LB_StainedGlass", os.path.join(FIX, "T_LB_StainedGlass_D.png"), rough_value=0.2, emission=3.0),
     "Light": pbr("LB_CandleLight", tint=(1.0, 0.7, 0.35), emission=12.0)}
for o in obs:
    key = next((k for k in sorted(M, key=len, reverse=True) if o.name.endswith("_" + k + "_0") or ("_" + k + "_") in o.name), None)
    if key is None:
        print("UNMAPPED", o.name); key = "Stone"
    o.data.materials.clear(); o.data.materials.append(M[key])
lo, hi = normalise(obs, 1.0, centre=False)
print("SIZE_M", [round(v, 2) for v in hi - lo], "LO", [round(v, 2) for v in lo])
# plan view (orthographic from above, roof parts hidden)
sc = bpy.context.scene
roofs = [o for o in obs if any(k in o.name for k in ("Vaulted roof", "Cross vault", "Ceiling", "Vaulted ceiling", "Ceiling top trim", "Small ceiling arch", "Ceiling arch", "Plane_Sandstone"))]
for o in roofs:
    o.hide_render = True
cam_d = bpy.data.cameras.new("plan"); cam_d.type = "ORTHO"; cam_d.ortho_scale = max(hi.x - lo.x, hi.y - lo.y) * 1.05
cam = bpy.data.objects.new("plan", cam_d); sc.collection.objects.link(cam); sc.camera = cam
cam.location = ((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z + 20); cam.rotation_euler = (0, 0, 0)
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading; sh.light = "STUDIO"; sh.color_type = "TEXTURE"; sh.show_cavity = True
sc.render.resolution_x = sc.render.resolution_y = 1000
sc.render.filepath = os.path.join(OUT, "plan.png"); bpy.ops.render.render(write_still=True)
for o in roofs:
    o.hide_render = False
# interior views at eye level from four points
c = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z + 1.7))
cam_d2 = bpy.data.cameras.new("eye"); cam_d2.lens = 16; cam_d2.clip_start = 0.05
cam2 = bpy.data.objects.new("eye", cam_d2); sc.collection.objects.link(cam2); sc.camera = cam2
sc.render.resolution_x, sc.render.resolution_y = 1000, 600
lamp = bpy.data.lights.new("fill", "POINT"); lamp.energy = 0
for k, (dx, dy, az) in enumerate(((-8, -8, 45), (8, 8, 225), (-8, 8, 315), (8, -8, 135))):
    cam2.location = c + Vector((dx, dy, 0)); cam2.rotation_euler = (math.radians(95), 0, math.radians(az - 90))
    sc.render.filepath = os.path.join(OUT, f"eye_{k}.png"); bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "library.blend"))
print("DONE")
