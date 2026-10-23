# Classic Library: colour maps the pack does not ship (its stone and metal used flat colours, the stained glass a
# procedural shader). Built from the pack's own roughness / AO maps, and a leaded-glass pattern for the windows.
# usage: python3 -I lib_fix_colors.py PACK_DIR OUT_DIR
import sys, os, glob, re
import numpy as np
from PIL import Image

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)


def find(key):
    for f in sorted(glob.glob(os.path.join(SRC, "*"))):
        if re.search(key, re.sub(r"^[0-9a-f]{32}_", "", os.path.basename(f)), re.I):
            return f


def load(f, mode="L"):
    return np.asarray(Image.open(f).convert(mode)).astype(np.float32) / 255.0


def tint(t, dark, light):
    return np.array(dark)[None, None] * (1 - t[..., None]) + np.array(light)[None, None] * t[..., None]


def save(a, name):
    Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8)).save(os.path.join(OUT, name)); print(name, a.mean((0, 1)).round(3))


r = load(find(r"Concrete012_2K_Roughness")); n = load(find(r"Concrete012_2K_NormalGL"), "RGB")
t = np.clip(0.5 + 0.25 * (r - r.mean()) / r.std(), 0, 1)
c = tint(t, (0.33, 0.30, 0.26), (0.55, 0.51, 0.45)) * (1 - 0.35 * (1 - np.clip(n[..., 2] * 2 - 1, 0, 1))[..., None])
save(c, "T_LB_Stone_D.png")
ao = load(find(r"WornMetal_1K_ao")); rm = load(find(r"WornMetal_1K_roughness"))
t = np.clip(0.5 + 0.3 * (rm - rm.mean()) / rm.std(), 0, 1)
save(tint(t, (0.035, 0.032, 0.03), (0.13, 0.11, 0.09)) * (0.55 + 0.45 * ao[..., None]), "T_LB_Metal_D.png")

# leaded glass: jittered cells (Voronoi), jewel colours, dark lead cames, slight streaks in each pane
rng = np.random.default_rng(7)
S = 1024
yy, xx = np.mgrid[0:S, 0:S].astype(np.float32) / S
cells = 9
pts = []
for i in range(cells):
    for j in range(cells * 2):
        pts.append(((i + 0.5 + rng.uniform(-0.35, 0.35)) / cells, (j + 0.5 + rng.uniform(-0.35, 0.35)) / (cells * 2)))
pts = np.array(pts, np.float32)
best = np.full((S, S), 9.0, np.float32); second = np.full((S, S), 9.0, np.float32); idx = np.zeros((S, S), np.int32)
for k, (px, py) in enumerate(pts):
    for ox in (-1, 0, 1):                                  # tileable
        for oy in (-1, 0, 1):
            d = np.hypot(xx - (px + ox), (yy - (py + oy)) * 2.0)
            closer = d < best
            second = np.where(closer, best, np.minimum(second, d)); idx = np.where(closer, k, idx); best = np.where(closer, d, best)
pal = np.array([(0.55, 0.05, 0.06), (0.06, 0.12, 0.45), (0.70, 0.50, 0.08), (0.08, 0.32, 0.12), (0.35, 0.08, 0.40), (0.62, 0.30, 0.06),
                (0.10, 0.25, 0.45), (0.55, 0.55, 0.40)], np.float32)
col = pal[rng.integers(0, len(pal), len(pts))][idx]
col *= (0.75 + 0.5 * rng.uniform(0, 1, len(pts))[idx])[..., None]
streak = 0.85 + 0.15 * np.sin(yy * 180 + np.sin(xx * 40) * 2)[..., None]
lead = np.clip((second - best) / 0.012, 0, 1)[..., None]           # 0 on the cell borders
save(col * streak * (0.04 + 0.96 * lead), "T_LB_StainedGlass_D.png")
