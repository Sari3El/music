# Procedural, tileable surface textures for the greybox materials and the landscape (no third-party asset).
# Each material gets an albedo (sRGB), a normal map (OpenGL convention: green = up) and a roughness map, 1024 px, one
# tile = 2 m on buildings (UVs are world metres / 2, see gb_build.py) and 4 m on the ground. Also writes the landscape
# splat map (R rock, G road/track, B mud/banks, A snow; 2048 px over the 3024 m map, row = Y, column = X).
# usage: make_textures.py ROOT  ->  ROOT/textures/
import sys, os, json, math
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tlib import spectral

ROOT = sys.argv[1]
OUT = f"{ROOT}/textures"
os.makedirs(OUT, exist_ok=True)
N = 1024
rng = np.random.default_rng(7)
yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)


def noise(beta, seed, n=N):
    return spectral(n, beta, seed)                          # periodic (FFT), mean 0, std 1


def streaks(seed, stretch=24, beta=2.2):
    """Noise stretched along the image columns (wood grain, rain streaks), still tileable."""
    small = spectral(N, beta, seed)[::stretch, :]
    return ndimage.zoom(small, (stretch, 1), order=1, mode="grid-wrap")[:N]


def stamp(cx, cy, rr):
    """Index window (wrapping) around a disc and the radial falloff 1 - d / r inside it."""
    xs = np.arange(int(cx - rr) - 1, int(cx + rr) + 2); ys = np.arange(int(cy - rr) - 1, int(cy + rr) + 2)
    d = np.hypot(xs[None, :] - cx, ys[:, None] - cy)
    return np.ix_(ys % N, xs % N), np.clip(1 - d / rr, 0, 1)


def normal_map(h, strength):
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength
    dy = (np.roll(h, 1, 0) - np.roll(h, -1, 0)) * 0.5 * strength          # image up = +v
    n = np.stack([-dx, -dy, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return (n * 0.5 + 0.5)


def save(name, albedo, height, rough, strength=6.0):
    a = np.clip(albedo, 0, 1) ** (1 / 2.2)                                   # linear -> sRGB
    Image.fromarray((a * 255 + 0.5).astype(np.uint8)).save(f"{OUT}/T_{name}_D.jpg", quality=92)
    Image.fromarray((normal_map(height, strength) * 255 + 0.5).astype(np.uint8)).save(f"{OUT}/T_{name}_N.png")
    Image.fromarray((np.clip(rough, 0, 1) * 255 + 0.5).astype(np.uint8)).save(f"{OUT}/T_{name}_R.jpg", quality=92)
    print("texture", name, flush=True)


def blocks(rows, lmin, lmax, seed, jitter=0.18, stagger=True):
    """Coursed blocks: per pixel block id, distance to the block edge (px) and the block's row (all wrap around)."""
    r = np.random.default_rng(seed)
    h = r.uniform(1 - jitter, 1 + jitter, rows); h = np.round(h / h.sum() * N).astype(int); h[-1] = N - h[:-1].sum()
    y0s = np.concatenate([[0], np.cumsum(h)[:-1]])
    bid = np.zeros((N, N), np.int32); dist = np.zeros((N, N), np.float32); row = np.zeros((N, N), np.int32)
    k = 0
    for i, (y0, hh) in enumerate(zip(y0s, h)):
        L = []
        while sum(L) < N:
            L.append(int(r.uniform(lmin, lmax) * N))
        L[-1] -= sum(L) - N
        if L[-1] < lmin * N * 0.5 and len(L) > 1:
            L[-2] += L[-1]; L = L[:-1]
        off = int(r.uniform(0, N)) if stagger else 0
        xs = (np.concatenate([[0], np.cumsum(L)]) + off)
        xr = (xx[y0:y0 + hh] - off) % N
        idx = np.searchsorted(np.cumsum(L), xr, side="right")
        starts = np.concatenate([[0], np.cumsum(L)[:-1]])[idx]; ends = np.cumsum(L)[idx]
        dx = np.minimum(xr - starts, ends - xr)
        dy = np.minimum(yy[y0:y0 + hh] - y0, y0 + hh - yy[y0:y0 + hh])
        bid[y0:y0 + hh] = idx + k; dist[y0:y0 + hh] = np.minimum(dx, dy); row[y0:y0 + hh] = i
        k += len(L)
    return bid, dist, row, k


def per_block(bid, k, seed, scale=1.0):
    return np.random.default_rng(seed).normal(0, scale, k + 1)[bid]


def lerp(a, b, t):
    t = np.asarray(t)[..., None] if np.ndim(t) == 2 else t
    return a + (b - a) * t


def ashlar(name, rows, lmin, lmax, base, mortar_col, seed, mortar=5.0, bevel=14.0, var=0.16, dirt=0.3):
    bid, dist, row, k = blocks(rows, lmin, lmax, seed, jitter=0.28)
    n1, n2, n3, n4 = noise(2.0, seed + 1), noise(3.2, seed + 2), noise(1.4, seed + 3), noise(2.6, seed + 7)
    dist = dist + 4.0 * n4                                                     # irregular, chipped arrises
    face = np.clip((dist - mortar) / bevel, 0, 1) ** 0.6
    tone = 1 + per_block(bid, k, seed + 4, var) + 0.08 * n1 + 0.06 * n2
    warm = per_block(bid, k, seed + 8, 0.007)                                  # some blocks browner, some bluer
    col = np.array(base)[None, None] * tone[..., None] + np.stack([warm, warm * 0.4, -warm * 0.6], -1)
    col = col * (0.72 + 0.28 * face)[..., None]                                # darker toward the joints
    col = col * (1 - dirt * np.clip(0.5 + 0.5 * n3, 0, 1)[..., None] * 0.6)   # weathering, soot
    stain = np.clip(streaks(seed + 5) * 0.4 + 0.1, 0, 1) * 0.12
    col = col * (1 - stain[..., None])
    lichen = np.clip(noise(2.2, seed + 9) - 1.3, 0, 1) * 0.7
    col = lerp(col, np.array([0.12, 0.13, 0.08]), lichen)
    m = (dist < mortar)
    col = np.where(m[..., None], np.array(mortar_col)[None, None] * (1 + 0.08 * n1[..., None]), col)
    hgt = face * 1.0 + 0.18 * n2 + 0.08 * per_block(bid, k, seed + 6) - 0.3 * m
    rough = np.where(m, 0.95, 0.80 + 0.08 * n1 + 0.1 * lichen)
    save(name, col, hgt, rough, 6.0)


def planks(name, count, base, seed, gap=3.0, dark=0.55, ends=True, knots=True):
    r = np.random.default_rng(seed)
    w = r.uniform(0.7, 1.3, count); w = np.round(w / w.sum() * N).astype(int); w[-1] = N - w[:-1].sum()
    x0s = np.concatenate([[0], np.cumsum(w)[:-1]])
    board = np.searchsorted(np.cumsum(w), xx, side="right")
    dx = np.minimum(xx - x0s[board], x0s[board] + w[board] - xx)
    grain = streaks(seed + 1, 32, 2.6) * 0.6 + streaks(seed + 2, 12, 1.8) * 0.4
    tone = 1 + per_block(board, count, seed + 3, 0.12)
    col = np.array(base)[None, None] * (tone + 0.10 * grain)[..., None]
    hgt = 0.08 * grain + np.clip(dx / 6.0, 0, 1) ** 0.5
    if ends:                                                                  # butt joints at a random height per board
        cut = r.uniform(0, N, count + 1).astype(int)[board]
        dyc = np.minimum((yy - cut) % N, (cut - yy) % N)
        hgt = hgt - 0.6 * (dyc < 2); dx = np.where(dyc < 2, 0, dx)
    if knots:
        for _ in range(10):
            ix, kn = stamp(r.uniform(0, N), r.uniform(0, N), r.uniform(6, 16))
            col[ix] = col[ix] * (1 - 0.45 * kn[..., None]); hgt[ix] = hgt[ix] - 0.2 * kn
    gapm = dx < gap
    col = np.where(gapm[..., None], np.array(base)[None, None] * dark * 0.4, col)
    rough = np.where(gapm, 0.95, 0.78 + 0.08 * grain)
    save(name, col, hgt - 0.5 * gapm, rough, 4.0)


def plaster(name, base, seed, stains=0.18, grain=0.05, cracks=True):
    n1, n2, n3 = noise(3.4, seed), noise(1.6, seed + 1), noise(2.4, seed + 2)
    col = np.array(base)[None, None] * (1 + grain * n1 + 0.06 * n3)[..., None]
    st = np.clip(streaks(seed + 3, 40, 1.6) * 0.3 + 0.25 * n2, 0, 1) * stains
    col = col * (1 - st[..., None])
    hgt = 0.25 * n1 + 0.4 * n3
    if cracks:
        cr = np.abs(noise(2.0, seed + 4)) < 0.025
        col = np.where(cr[..., None], col * 0.6, col); hgt = hgt - 0.6 * cr
    save(name, col, hgt, 0.9 + 0.04 * n1, 2.5)


def tiles(name, rows, per_row, base, seed, slate=False):
    r = np.random.default_rng(seed)
    row = np.floor(yy * rows / N).astype(int); ty = yy * rows / N - row     # 0 at the top of a course, 1 at its lower lip
    off = (row % 2) * (N / per_row / 2)
    tw = N / per_row
    col_i = np.minimum((((xx + off) % N) // tw).astype(int), per_row - 1)
    tx = ((xx + off) % N % tw) / tw
    tid = row * per_row + col_i
    tone = 1 + r.normal(0, 0.10 if not slate else 0.07, rows * per_row + 1)[tid]
    n1, n2 = noise(2.6, seed + 1), noise(1.5, seed + 2)
    if slate:
        prof = 0.2 * np.clip(np.minimum(tx, 1 - tx) * 12, 0, 1)
    else:
        prof = np.cos((tx - 0.5) * np.pi) * 0.9                                 # barrel (Roman-style) tiles
    lip = ty ** 1.5                                                            # each course rises to its lower lip
    edge = np.minimum(tx, 1 - tx) < (0.03 if slate else 0.06)
    hgt = prof + 0.8 * lip + 0.08 * n1
    shade = 1 - 0.5 * np.clip((ty - 0.88) / 0.12, 0, 1) - 0.25 * (1 - lip) ** 4   # shadow under the next course
    col = np.array(base)[None, None] * (tone * shade + 0.06 * n1)[..., None]
    moss = np.clip(n2 - 0.9, 0, 1) * 0.8
    col = lerp(col, np.array([0.10, 0.13, 0.06]) * (1 + 0.2 * n1[..., None]), moss)
    col = np.where(edge[..., None], col * 0.45, col)
    rough = 0.75 + 0.1 * n1 + 0.1 * moss - (0.1 if slate else 0.0)
    save(name, col, hgt - 0.4 * edge, rough, 6.0)


def iron(name, seed):
    n1, n2, n3 = noise(3.0, seed), noise(1.8, seed + 1), noise(2.4, seed + 2)
    rust = np.clip((n2 + 0.3 * n1) - 0.4, 0, 1)
    col = lerp(np.array([0.05, 0.05, 0.055]) * (1 + 0.15 * n1[..., None]), np.array([0.22, 0.09, 0.035]) * (1 + 0.2 * n3[..., None]), rust)
    hgt = 0.3 * n1 + 0.5 * rust + 0.2 * n3
    save(name, col, hgt, 0.55 + 0.35 * rust, 3.0)


def cloth(name, base, seed):
    n1, n2 = noise(2.6, seed), noise(1.5, seed + 1)
    weave = (np.sin(xx / N * 2 * np.pi * 160) * np.sin(yy / N * 2 * np.pi * 160))
    col = np.array(base)[None, None] * (1 + 0.08 * weave + 0.10 * n1 - 0.2 * np.clip(n2, 0, 1))[..., None]
    save(name, col, 0.3 * weave + 0.3 * n1, 0.93 + 0.03 * n1, 2.0)


def leaded(name, glass, seed, came=0.012):
    n1 = noise(2.2, seed)
    k = 10                                                                     # diamond panes across the tile
    u, v = xx / N * k, yy / N * k * 1.4
    d = np.minimum(np.abs(((u + v) % 1) - 0.5), np.abs(((u - v) % 1) - 0.5))
    lead = d > 0.5 - came * k
    col = np.where(lead[..., None], np.array([0.05, 0.05, 0.05]), np.array(glass)[None, None] * (1 + 0.25 * n1[..., None]))
    save(name, col, 0.8 * lead + 0.05 * n1, np.where(lead, 0.6, 0.12), 5.0)


def foliage(name, seed):
    r = np.random.default_rng(seed)
    hgt = np.zeros((N, N), np.float32)
    for _ in range(700):
        ix, f = stamp(r.uniform(0, N), r.uniform(0, N), r.uniform(10, 34))
        hgt[ix] = np.maximum(hgt[ix], np.sqrt(np.clip(1 - (1 - f) ** 2, 0, 1)) * r.uniform(0.6, 1.0))
    n1 = noise(3.0, seed + 1)
    t = np.clip(hgt * 0.8 + 0.1 * n1, 0, 1)
    col = lerp(np.array([0.010, 0.025, 0.010]), np.array([0.07, 0.11, 0.035]), t)
    save(name, col, hgt + 0.1 * n1, 0.85 + 0.05 * n1, 5.0)


def ground(name, base, seed, pebbles=500, wet=0.0, ruts=False):
    r = np.random.default_rng(seed)
    n1, n2, n3 = noise(2.8, seed), noise(1.6, seed + 1), noise(2.2, seed + 2)
    col = np.array(base)[None, None] * (1 + 0.12 * n1 + 0.10 * n2)[..., None]
    hgt = 0.3 * n1 + 0.3 * n3
    for _ in range(pebbles):
        ix, pb = stamp(r.uniform(0, N), r.uniform(0, N), r.uniform(3, 11))
        pc = np.array([0.30, 0.28, 0.25]) * np.array(base) / 0.12 * r.uniform(0.5, 1.1)
        col[ix] = lerp(col[ix], pc, (pb > 0) * 0.85); hgt[ix] = hgt[ix] + pb ** 0.5 * 0.8
    if ruts:
        for xc in (0.3, 0.7):
            rt = np.exp(-(((xx / N - xc + 0.5) % 1 - 0.5) / 0.06) ** 2)
            hgt = hgt - 0.8 * rt; col = col * (1 - 0.25 * rt[..., None])
    save(name, col, hgt, np.clip(0.88 - wet + 0.05 * n1, 0.2, 1), 4.0)


def setts(name, rows, base, seed):
    """Cobbled paving: small domed setts in courses, dark earth in the joints."""
    bid, dist, row, k = blocks(rows, 0.035, 0.06, seed, jitter=0.25)
    n1, n2 = noise(2.6, seed + 1), noise(1.5, seed + 2)
    dome = np.clip(dist / 9.0, 0, 1) ** 0.5
    col = np.array(base)[None, None] * (1 + per_block(bid, k, seed + 3, 0.18) + 0.08 * n1)[..., None]
    col = col * (0.65 + 0.35 * dome)[..., None]
    joint = dist < 2.5
    col = np.where(joint[..., None], np.array([0.05, 0.04, 0.03]) * (1 + 0.2 * n1[..., None]), col)
    dirt = np.clip(n2 - 0.6, 0, 1) * 0.6
    col = lerp(col, np.array([0.07, 0.055, 0.04]), dirt)
    save(name, col, dome + 0.1 * n1 - 0.4 * joint, np.where(joint, 0.95, 0.7 + 0.1 * n1), 6.0)


def grass(name, seed):
    r = np.random.default_rng(seed)
    n1, n2, n3 = noise(3.6, seed), noise(1.4, seed + 1), noise(2.4, seed + 2)
    blades = streaks(seed + 3, 10, 3.6)
    t = np.clip(0.5 + 0.35 * n2 + 0.2 * n3, 0, 1)
    col = lerp(np.array([0.040, 0.052, 0.020]), np.array([0.095, 0.090, 0.035]), t)          # dull, late-autumn grass
    col = col * (1 + 0.07 * blades + 0.15 * n1)[..., None]
    dry = np.clip(n3 - 0.8, 0, 1)
    col = lerp(col, np.array([0.13, 0.10, 0.05]), dry)
    save(name, col, 0.2 * blades + 0.5 * n1 + 0.3 * n3, 0.9 + 0.05 * n1, 3.0)


def rock(name, seed):
    n1, n2, n3, n4 = noise(2.2, seed), noise(3.0, seed + 1), noise(1.6, seed + 2), noise(2.0, seed + 3)
    crack = np.clip(1 - np.abs(n4) / 0.12, 0, 1) ** 2                              # thin fissures along the noise zero-lines
    strata = np.sin((yy / N * 7 + 0.8 * n3) * 2 * np.pi) * 0.5 + 0.5
    hgt = 0.5 * n3 + 0.3 * n2 + 0.25 * strata - 0.8 * crack
    col = np.array([0.13, 0.125, 0.118])[None, None] * (1 + 0.22 * n1 + 0.12 * strata + 0.1 * n2)[..., None]
    col = col * (1 - 0.6 * crack[..., None])
    lichen = np.clip(n3 - 1.0, 0, 1) * 0.8
    col = lerp(col, np.array([0.14, 0.15, 0.09]), lichen)
    save(name, col, hgt, 0.82 + 0.08 * n2, 7.0)


def snow(name, seed):
    n1, n2 = noise(2.4, seed), noise(1.4, seed + 1)
    col = np.array([0.80, 0.83, 0.88])[None, None] * (1 + 0.04 * n1 + 0.05 * n2)[..., None]
    save(name, col, 0.5 * n2 + 0.2 * n1, 0.55 + 0.1 * n1, 2.0)


# ---------------------------------------------------------------- building surfaces (1 tile = 2 m)
ashlar("GB_Stone", 6, 0.22, 0.45, (0.15, 0.145, 0.14), (0.10, 0.095, 0.09), 11, mortar=3.5)             # dark grey castle ashlar
ashlar("GB_Church", 5, 0.25, 0.55, (0.33, 0.31, 0.275), (0.24, 0.23, 0.21), 12, mortar=3.5, var=0.10, dirt=0.25)    # pale limestone
ashlar("GB_Floor", 3, 0.25, 0.6, (0.17, 0.16, 0.145), (0.08, 0.075, 0.07), 13, mortar=4.0, bevel=6.0, var=0.14, dirt=0.15)  # flagstones
plaster("GB_Interior", (0.45, 0.42, 0.37), 14, stains=0.10)
plaster("GB_Plaster", (0.50, 0.44, 0.33), 15, stains=0.12)                                  # lime plaster, ochre
planks("GB_Wood", 9, (0.20, 0.13, 0.075), 16)
planks("GB_Timber", 5, (0.10, 0.07, 0.045), 17, gap=4.0)
tiles("GB_Tile", 14, 9, (0.30, 0.12, 0.07), 18)                                             # clay tiles, darkened
tiles("GB_Roof", 18, 7, (0.075, 0.08, 0.09), 19, slate=True)                                 # slate
iron("GB_Metal", 20)
cloth("GB_Detail", (0.22, 0.035, 0.03), 21)
ground("GB_Ground", (0.11, 0.08, 0.055), 22, pebbles=250)
foliage("GB_Hedge", 23)
leaded("GB_WinDark", (0.020, 0.028, 0.035), 24)
leaded("GB_WinLit", (0.90, 0.55, 0.20), 25)
# ---------------------------------------------------------------- landscape layers (1 tile = 4 m)
grass("L_Grass", 31)
rock("L_Rock", 32)
rock("GB_Rock", 36)                                                                          # boulders, talus, backdrop (2 m)
ground("L_Road", (0.13, 0.10, 0.07), 33, pebbles=700, ruts=True)
ground("L_Mud", (0.06, 0.045, 0.03), 34, pebbles=120, wet=0.45)
snow("L_Snow", 35)
setts("L_Paving", 24, (0.15, 0.14, 0.13), 37)

# ---------------------------------------------------------------- splat map from the final terrain
H = np.load(f"{ROOT}/terrain/H_4033.npy").astype(np.float32)
RM = np.load(f"{ROOT}/terrain/road_mask.npy")
DEP = np.load(f"{ROOT}/terrain/river_depth.npy").astype(np.float32)
S2 = 2048
zoom = S2 / H.shape[0]
Hs = ndimage.zoom(H, zoom, order=1)
gy, gx = np.gradient(Hs, 3024.0 / S2)
slope = np.degrees(np.arctan(np.hypot(gx, gy)))
rockw = np.clip((slope - 33.0) / 9.0, 0, 1)
road = ndimage.zoom(((RM > 0) & (RM < 5)).astype(np.float32), zoom, order=1)
wet = ndimage.zoom((DEP > 0.05).astype(np.float32), zoom, order=0)
bank = np.clip(ndimage.gaussian_filter(ndimage.binary_dilation(wet > 0, iterations=4).astype(np.float32), 1.5) * 1.4, 0, 1)
fen = np.clip(1 - (np.hypot(*np.meshgrid(np.linspace(-1512, 1512, S2) + 1230, np.linspace(-1512, 1512, S2) + 1230)) - 230) / 60, 0, 1)
mud = np.maximum(bank, fen * np.clip((8.0 - Hs) / 4.0, 0, 1))
snoww = np.clip((Hs - 385.0) / 15.0, 0, 1) * (1 - 0.6 * rockw)
road = np.clip(ndimage.gaussian_filter(road, 0.8) * 1.2, 0, 1)
splat = np.stack([rockw, road, mud, snoww], -1)
Image.fromarray((splat * 255 + 0.5).astype(np.uint8), "RGBA").save(f"{OUT}/T_GV_Splat.png")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from castle_shape import rim_sd
M = json.load(open(f"{ROOT}/data/layout_manifest.json"))
(ecx, ecy), (era, erb) = M["city"]["wall_ellipse"]["centre"], M["city"]["wall_ellipse"]["radii_ns_ew"]
ax2 = np.linspace(-1512, 1512, S2)
X2, Y2 = np.meshgrid(ax2, ax2)                                              # row = Y, column = X
town = np.hypot((X2 - ecx) / era, (Y2 - ecy) / erb) < 0.985
crag = np.asarray(rim_sd(X2, Y2)) < -1.5
pave = ndimage.gaussian_filter((town | crag).astype(np.float32), 1.2) * (1 - rockw)
splat2 = np.stack([pave, np.zeros_like(pave), np.zeros_like(pave), np.ones_like(pave)], -1)
Image.fromarray((np.clip(splat2, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(f"{OUT}/T_GV_Splat2.png")
json.dump(dict(tile_m_buildings=2.0, tile_m_landscape=4.0, splat="R rock, G road, B mud, A snow; row = Y, column = X, -1512..1512 m", splat2="R paving (town, castle crag)",
               normal="OpenGL (green up): flip the green channel in Unreal"), open(f"{OUT}/textures.json", "w"), indent=1)
print("splat written")
