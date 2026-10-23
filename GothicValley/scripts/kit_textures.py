# Texture sets of the asset packs used by the lodge and the library, renamed like the generated ones
# (T_<material>_D.jpg / _N.png / _R.jpg in textures/) so that gb_build (renders) and setup_map.py (Unreal) treat them the
# same way, plus data/materials_kit.json (fallback colour, physical surface, metallic, emissive, two-sided, tile size).
# usage: python3 -I kit_textures.py ROOT PACKS_DIR      (PACKS_DIR = the extracted Dropbox folder)
import sys, os, glob, re, json
import numpy as np
from PIL import Image

ROOT, PACKS = sys.argv[1], sys.argv[2]
OUT = os.path.join(ROOT, "textures")
LIB = glob.glob(os.path.join(PACKS, "denniswoo1993", "*"))[0]
FC = glob.glob(os.path.join(PACKS, "HawtorStudio", "*"))[0]
FIX_LB, FIX_FC = os.path.join(ROOT, "assets", "library", "tex"), os.path.join(ROOT, "assets", "fantasy", "tex")
MAXRES = 2048


def find(folder, key):
    for f in sorted(glob.glob(os.path.join(folder, "*"))):
        if re.search(key, re.sub(r"^[0-9a-f]{32}_", "", os.path.basename(f)), re.I):
            return f
    raise SystemExit(f"missing texture {key} in {folder}")


# material: D, N, R sources (None = no map), colour, physical surface, metallic, emissive, two-sided, tile (m per repeat)
MATS = {
    "LB_GlossyWood": ((LIB, r"Wood027_2K_Color"), (LIB, r"Wood027_2K_NormalGL"), (LIB, r"Wood027_2K_Roughness"), (0.35, 0.22, 0.13), "Wood", 0, 0, False, 1.5),
    "LB_WoodFloor": ((LIB, r"WoodFloor016_2K_Color"), (LIB, r"WoodFloor016_2K_NormalGL"), (LIB, r"WoodFloor016_2K_Roughness"), (0.4, 0.28, 0.18), "Wood", 0, 0, False, 2.5),
    "LB_Leather": ((LIB, r"Leather023_2K_Color"), (LIB, r"Leather023_2K_NormalGL"), (LIB, r"Leather023_2K_Roughness"), (0.3, 0.15, 0.1), "Wood", 0, 0, False, 1.0),
    "LB_Sandstone": ((LIB, r"sandstone_blocks_04_diff"), (LIB, r"sandstone_blocks_04_nor_gl"), (LIB, r"sandstone_blocks_04_rough"), (0.55, 0.45, 0.35), "Stone", 0, 0, False, 2.0),
    "LB_Stone": ((FIX_LB, r"T_LB_Stone_D"), (LIB, r"Concrete012_2K_NormalGL"), (LIB, r"Concrete012_2K_Roughness"), (0.45, 0.41, 0.36), "Stone", 0, 0, False, 2.0),
    "LB_Metal": ((FIX_LB, r"T_LB_Metal_D"), (LIB, r"WornMetal_1K_normal"), (LIB, r"WornMetal_1K_roughness"), (0.08, 0.07, 0.06), "Metal", 0.85, 0, False, 1.0),
    "LB_OldBook": ((LIB, r"SHC_Old_Book_Diffuse"), (LIB, r"SHC_Old_Book_Normal"), (LIB, r"SHC_Old_Book_Roughness"), (0.3, 0.2, 0.15), "Wood", 0, 0, False, 1.0),
    "LB_Paper": ((LIB, r"RGB_unnamed"), None, None, (0.75, 0.68, 0.52), "Wood", 0, 0, False, 1.0),
    "LB_StainedGlass": ((FIX_LB, r"T_LB_StainedGlass_D"), None, None, (0.5, 0.25, 0.6), "Wood", 0, 3.0, True, 1.0),
    "LB_CandleLight": (None, None, None, (1.0, 0.7, 0.35), "Wood", 0, 12.0, False, 1.0),
    "FC_Concrete": ((FIX_FC, r"T_FC_Concrete_D"), (FC, r"ConcreteNormal"), (FC, r"ConcreteRoughness"), (0.45, 0.41, 0.35), "Stone", 0, 0, True, 4.0),
    "FC_StoneBrickWall": ((FC, r"StoneBrickWallColor"), (FC, r"StoneBrickWallNormal"), (FC, r"StoneBrickWallRoughness"), (0.27, 0.26, 0.26), "Stone", 0, 0, True, 3.0),
    "FC_Roof": ((FIX_FC, r"T_FC_Roof_D"), (FC, r"RoofNormal"), (FC, r"RoofRoughness"), (0.13, 0.13, 0.15), "Stone", 0, 0, True, 2.0),
    "FC_WoodPlanks": ((FIX_FC, r"T_FC_WoodPlanks_D"), (FC, r"WoodPlanksNormal"), (FC, r"WoodPlanksRoughness"), (0.25, 0.16, 0.1), "Wood", 0, 0, True, 2.0),
    "FC_Glass": ((FC, r"GlassColor"), (FC, r"GlassNormal"), (FC, r"GlassRoughness"), (0.3, 0.35, 0.4), "Metal", 0, 0.4, True, 1.0),
    "FC_Back": (None, None, None, (0.02, 0.02, 0.025), "Stone", 0, 0, True, 1.0),
    "FC_StoneTiles": ((FC, r"StoneTilesGroundColors"), (FC, r"StoneTilesGroundNormal"), (FC, r"StoneTilesGroundRoughness"), (0.31, 0.3, 0.29), "Stone", 0, 0, True, 3.0),
}


def save(src, dst, mode):
    im = Image.open(src)
    im = im.convert("RGBA" if (mode == "RGB" and dst.endswith(".png") and "A" in im.getbands()) else mode)
    if max(im.size) > MAXRES:
        im = im.resize((MAXRES, MAXRES), Image.LANCZOS)
    if dst.endswith(".jpg"):
        im.convert("RGB" if mode == "RGB" else "L").save(dst, quality=90)
    else:
        im.save(dst, optimize=True)


meta = {}
for name, (d, n, r, col, phys, metal, emis, two, tile) in MATS.items():
    files = {}
    if d:
        alpha = name == "FC_Glass"
        dst = os.path.join(OUT, f"T_{name}_D" + (".png" if alpha else ".jpg"))
        save(find(*d), dst, "RGB"); files["D"] = os.path.basename(dst)
    if n:
        dst = os.path.join(OUT, f"T_{name}_N.png"); save(find(*n), dst, "RGB"); files["N"] = os.path.basename(dst)
    if r:
        dst = os.path.join(OUT, f"T_{name}_R.jpg"); save(find(*r), dst, "L"); files["R"] = os.path.basename(dst)
    meta[name] = dict(color=list(col), phys=phys, metallic=metal, emissive=emis, two_sided=two, tile_m=tile, files=files,
                      translucent=name == "FC_Glass")
    print(name, files)
json.dump(meta, open(os.path.join(ROOT, "data", "materials_kit.json"), "w"), indent=1)
