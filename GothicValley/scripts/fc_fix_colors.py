# Fantasy Castle: three colour maps of the pack are blank (2-colour black palettes). Rebuild them from the same set's
# roughness + normal maps (identical UV layout, so mortar joints, tiles and planks line up), tinted stone / slate / oak.
# usage: python3 -I fc_fix_colors.py PACK_DIR OUT_DIR
import sys, os, glob, re
import numpy as np
from PIL import Image

SRC, OUT = sys.argv[1], sys.argv[2]


def find(key):
    for f in sorted(glob.glob(os.path.join(SRC, "*"))):
        if re.search(key, re.sub(r"^[0-9a-f]{32}_", "", os.path.basename(f)), re.I):
            return f


def load(f, mode):
    return np.asarray(Image.open(f).convert(mode)).astype(np.float32) / 255.0


def build(name, rough_key, normal_key, base, dark, light, cavity=0.55, gamma=1.0):
    r = load(find(rough_key), "L")
    n = load(find(normal_key), "RGB")
    if n.shape[:2] != r.shape:
        n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize(r.shape[::-1], Image.BILINEAR)).astype(np.float32) / 255
    flat = np.clip(n[..., 2] * 2 - 1, 0, 1)                          # 1 on flat faces, lower in joints / grooves
    t = (r - r.mean()) / (r.std() + 1e-6)
    t = np.clip(0.5 + 0.22 * t, 0, 1) ** gamma                       # rougher = paler / more weathered
    c = np.array(dark)[None, None] * (1 - t[..., None]) + np.array(light)[None, None] * t[..., None]
    c = c * (1 - cavity * (1 - flat[..., None]) ** 0.7)               # darken joints
    c = c * np.array(base)[None, None]
    Image.fromarray(np.clip(c * 255, 0, 255).astype(np.uint8)).save(os.path.join(OUT, f"T_FC_{name}_D.png"))
    print(name, c.mean((0, 1)).round(3))


os.makedirs(OUT, exist_ok=True)
build("Concrete", r"ConcreteRoughness", r"ConcreteNormal", (1, 1, 1), (0.36, 0.32, 0.27), (0.62, 0.57, 0.49))        # pale limestone trim
build("Roof", r"RoofRoughness", r"RoofNormal", (1, 1, 1), (0.10, 0.11, 0.13), (0.27, 0.28, 0.31), cavity=0.7)            # slate
build("WoodPlanks", r"WoodPlanksRoughness", r"WoodPlanksNormal", (1, 1, 1), (0.16, 0.10, 0.06), (0.38, 0.26, 0.16))     # aged oak
