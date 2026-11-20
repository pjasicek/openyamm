#!/usr/bin/env python3
"""Grade the downloaded Poly Haven sets (fetch_pbr.py; CC0) into the fire props' textures in props/textures_pbr/:
<name>_basecolor.png (sRGB), <name>_normal.png (glTF / OpenGL +Y) and <name>_mr.png (G roughness, B metal).
Lit surfaces keep the scan's luminance detail recoloured to the native sprite's measured colour (linear mean of the
texture = linear native sRGB). The glow textures (unlit in the engine, which has only constant per-material emission)
are ramps over the scan's height and occlusion: alligatored char with red-orange plates (fire_glow) and deep red
lava pooled in the basalt's hollows (lava_glow, alpha-tested). Writes textures_pbr/means.json and a preview sheet.
Usage: make_pbr_textures.py   (run with python3 -I: the sources are downloaded data)"""
import json, os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'textures_pbr')
SOURCE = os.path.join(OUT, 'source')


def load(asset, kind, size):
    im = Image.open(os.path.join(SOURCE, asset, f'{asset}_{kind}_2k.png'))
    shape = (size, size * im.height // im.width)          # keep the scan's aspect (the cedar bark is 1 x 2)
    if im.mode.startswith('I'):
        a = np.asarray(im, np.float64) / 65535.0
        im = Image.fromarray(a.astype(np.float32), 'F')
        return np.asarray(im.resize(shape, Image.LANCZOS), np.float64).clip(0, 1)
    im = im.convert('RGB').resize(shape, Image.LANCZOS)
    a = np.asarray(im, np.float64) / 255.0
    return a if kind in ('diff', 'nor_gl') else a[..., 0]


def linear(s):
    s = np.asarray(s, np.float64)
    return np.where(s <= 0.04045, s / 12.92, ((s + 0.055) / 1.055) ** 2.4)


def srgb(l):
    l = np.clip(l, 0, 1)
    return np.where(l <= 0.0031308, l * 12.92, 1.055 * l ** (1 / 2.4) - 0.055)


def luminance(lin):
    return lin @ np.array([0.2126, 0.7152, 0.0722])


def grade(diff_srgb, target_srgb, contrast=1.0, keep_hue=0.15):
    """Scan albedo -> the native colour: its relative luminance (raised to `contrast`) times the target's linear
    colour, a little of the scan's own hue kept, rescaled so the texture's linear mean is the target."""
    lin = linear(diff_srgb)
    lum = luminance(lin)
    rel = (lum / lum.mean()) ** contrast
    target = linear(np.array(target_srgb) / 255.0)
    hue = lin / np.maximum(lum[..., None], 1e-5)
    hue = hue / hue.reshape(-1, 3).mean(0)
    colour = target * rel[..., None] * (1 - keep_hue + keep_hue * hue)
    colour *= target / colour.reshape(-1, 3).mean(0)
    return colour


def normal(asset, size, strength=1.0):
    n = load(asset, 'nor_gl', size) * 2 - 1
    n[..., :2] *= strength
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n


def save(name, colour_linear, normal_map, roughness, metal=0.0, alpha=None):
    rgb = (srgb(colour_linear) * 255 + 0.5).astype(np.uint8)
    if alpha is not None:
        rgba = np.dstack([rgb, (np.clip(alpha, 0, 1) * 255 + 0.5).astype(np.uint8)])
        Image.fromarray(rgba, 'RGBA').save(os.path.join(OUT, f'{name}_basecolor.png'), optimize=True)
    else:
        Image.fromarray(rgb, 'RGB').save(os.path.join(OUT, f'{name}_basecolor.png'), optimize=True)
    if normal_map is not None:
        nrm = ((normal_map * 0.5 + 0.5) * 255 + 0.5).clip(0, 255).astype(np.uint8)
        Image.fromarray(nrm, 'RGB').save(os.path.join(OUT, f'{name}_normal.png'), optimize=True)
    if roughness is not None:
        shape = colour_linear.shape[:2]
        mr = np.zeros(shape + (3,), np.float64)
        mr[..., 0] = 1.0
        mr[..., 1] = np.broadcast_to(roughness, shape)
        mr[..., 2] = np.broadcast_to(metal, shape)
        Image.fromarray((mr.clip(0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').save(
            os.path.join(OUT, f'{name}_mr.png'), optimize=True)
    mean = (srgb(colour_linear.reshape(-1, 3).mean(0)) * 255).round().tolist()
    means[name] = mean
    print('TEXTURE', name, colour_linear.shape[:2], 'linear-mean sRGB', mean)


def remap(x, lo, hi):
    return np.clip((x - lo) / max(hi - lo, 1e-6), 0, 1)


def smooth(x, lo, hi):
    t = remap(x, lo, hi)
    return t * t * (3 - 2 * t)


def blur(a, radius):
    """Wrap-around box blur (three passes ~ gaussian) keeping the texture tileable."""
    out = a.copy()
    for _ in range(3):
        for axis in (0, 1):
            acc = np.zeros_like(out)
            for k in range(-radius, radius + 1):
                acc += np.roll(out, k, axis=axis)
            out = acc / (2 * radius + 1)
    return out


means = {}
S = 512

# Tripod poles: Japanese cedar bark fibres, dark red-brown like the sprite's poles (64, 30, 19; fire-lit).
d = load('japanese_cedar_bark', 'diff', 256)              # thin poles: 256 x 512
save('fire_wood', grade(d, (70, 37, 25), contrast=1.25), normal('japanese_cedar_bark', 256, 1.2),
     0.55 + 0.4 * load('japanese_cedar_bark', 'rough', 256))

# Kettle: coarse rust greyed to the sprite's dark mauve iron (85, 63, 62 with fire highlights), partly metallic with
# a mid roughness so it takes a sheen.
d = load('rust_coarse_01', 'diff', S)
r = load('rust_coarse_01', 'rough', S)
save('fire_iron', grade(d, (76, 63, 67), contrast=1.6, keep_hue=0.05), normal('rust_coarse_01', S, 1.4),
     0.32 + 0.35 * remap(r, r.min(), r.max()), 0.45)

# Fire-ring stones: dry boulder scan, purple-grey like the sprite's stones (114-129, 81-92, 89-102).
d = load('rock_boulder_dry', 'diff', S)
ao = load('rock_boulder_dry', 'ao', S)
save('fire_stone', grade(d * (0.55 + 0.45 * ao[..., None]), (110, 88, 100), contrast=1.8, keep_hue=0.1),
     normal('rock_boulder_dry', S, 1.6), 0.6 + 0.35 * load('rock_boulder_dry', 'rough', S))

# Charred bark of the logs: willow bark burnt near black, deep grooves.
d = load('bark_willow', 'diff', S)
ao = load('bark_willow', 'ao', S)
save('fire_char', grade(d * (0.4 + 0.6 * ao[..., None]), (40, 22, 16), contrast=1.5, keep_hue=0.1),
     normal('bark_willow', S, 1.3), 0.8 + 0.2 * load('bark_willow', 'rough', S))

# Glowing log faces and ember bed (unlit): pine bark's plates as alligatored char, the plates glowing red-orange
# (the sprite's logs: 115, 26, 7) with black cracks between them and hot orange where the plates are highest.
h = load('pine_bark', 'disp', S)
ao = load('pine_bark', 'ao', S)
lift = remap(h * (0.5 + 0.5 * ao), np.percentile(h * (0.5 + 0.5 * ao), 4), np.percentile(h * (0.5 + 0.5 * ao), 99))
stops = [(0.00, (0.010, 0.0012, 0.0005)), (0.18, (0.05, 0.004, 0.0012)), (0.32, (0.17, 0.011, 0.002)),
         (0.65, (0.27, 0.021, 0.003)), (0.88, (0.50, 0.07, 0.007)), (1.00, (0.80, 0.20, 0.025))]
xs = [s[0] for s in stops]
glow = np.dstack([np.interp(lift, xs, [s[1][c] for s in stops]) for c in range(3)])
save('fire_glow', glow, None, None)

# Burning rock: dark basalt-like rock, charcoal with the sprite's purple-brown cast (64, 46, 46 lit / 37, 24, 23
# shadowed), rough and porous.
d = load('dark_rock', 'diff', 1024)
ao = load('dark_rock', 'ao', 1024)
rock_r = load('dark_rock', 'rough', 1024)
save('lava_rock', grade(d * (0.5 + 0.5 * ao[..., None]), (36, 25, 24), contrast=1.5, keep_hue=0.1),
     normal('dark_rock', 1024, 1.5), 0.7 + 0.3 * rock_r)

# Lava pools (unlit, alpha-tested shell over the upper rock): the rock's hollows at two scales (fine pores and broad
# basins), deep red like the sprite's glowing top (82, 21, 10), hotter where deepest.
h = load('dark_rock', 'disp', 1024)
basin = blur(h, 24)
depth = remap(-(h - 0.65 * basin - 0.35 * h.mean()), -0.02, 0.10)          # local hollows
broad = smooth(-(basin - basin.mean()) / basin.std(), -0.8, 0.9)           # broad low areas
heat = np.clip(0.85 * depth + 0.4 * broad + 0.02, 0, 1)
alpha = smooth(heat, 0.30, 0.42)
stops = [(0.0, (0.012, 0.0015, 0.001)), (0.36, (0.025, 0.0025, 0.0012)), (0.50, (0.06, 0.005, 0.002)),
         (0.70, (0.11, 0.009, 0.0025)), (0.88, (0.18, 0.016, 0.0035)), (1.00, (0.34, 0.04, 0.008))]
xs = [s[0] for s in stops]
lava = np.dstack([np.interp(heat, xs, [s[1][c] for s in stops]) for c in range(3)])
print('LAVA coverage', round(float((alpha > 0.5).mean()), 3))
save('lava_glow', lava, None, None, alpha=alpha)

# ---- log-pile fire `dec04` (appended; the sets above are unchanged)
# Less burnt logs and planks: rough weathered wood graded to the sprite's mid brown (89, 66, 41).
d = load('rough_wood', 'diff', S)
ao = load('rough_wood', 'ao', S)
save('logfire_wood', grade(d * (0.5 + 0.5 * ao[..., None]), (92, 68, 43), contrast=1.5, keep_hue=0.15),
     normal('rough_wood', S, 1.3), 0.7 + 0.3 * load('rough_wood', 'rough', S))

# Charred wood with ember glints (unlit): near-black char plates of the pine-bark scan, orange (the sprite's glints:
# 192, 96, 25) only deep in its cracks, so about a tenth of the surface glows.
h = load('pine_bark', 'disp', S)
ao = load('pine_bark', 'ao', S)
crack = h * (0.5 + 0.5 * ao)
lo, hi = np.percentile(crack, 1), np.percentile(crack, 14)
glint = 1 - smooth(crack, lo, hi)
d = load('pine_bark', 'diff', S)
char = grade(d, (20, 14, 10), contrast=1.3, keep_hue=0.1)
stops = [(0.0, (0.0, 0.0, 0.0)), (0.35, (0.10, 0.012, 0.002)), (0.7, (0.42, 0.10, 0.012)), (1.0, (0.62, 0.22, 0.03))]
xs = [s_[0] for s_ in stops]
hot = np.dstack([np.interp(glint, xs, [s_[1][c] for s_ in stops]) for c in range(3)])
print('EMBER glint coverage', round(float((glint > 0.5).mean()), 3))
save('logfire_embers', np.maximum(char, hot), None, None)

# Smoke flipbook (procedural; 8 x 4 frames of 160 x 128, a seamless 32-frame loop): a dense grey plume of puffs
# rising from the bottom centre, widening to most of the frame, drifting and fading in and out over their life. Each
# puff is a noise-textured gaussian; puff i in frame f has age (f / 32 + i / N) mod 1, so the loop closes. Grey like
# the sprite's lit smoke (about 120-140 sRGB), the plume core about 0.75 opaque.
FW, FH, COLS, ROWS = 160, 128, 8, 4
FRAMES = COLS * ROWS
rng = np.random.default_rng(1604)
field = blur(rng.random((256, 256)), 6) * 0.6 + blur(rng.random((256, 256)), 2) * 0.4
field = (field - field.min()) / (field.max() - field.min())
yy, xx = np.mgrid[0:FH, 0:FW].astype(np.float64)
N = 12
seeds = rng.random((N, 4))
alphas, shades = [], []
for f in range(FRAMES):
    alpha = np.zeros((FH, FW)); shade = np.zeros((FH, FW))
    for i in range(N):
        age = (f / FRAMES + i / N) % 1.0
        cx = FW * (0.5 + 0.16 * (seeds[i, 0] - 0.5) + 0.08 * age * np.sin(6.283 * (seeds[i, 1] + 0.6 * age)))
        cy = FH * (0.95 - 0.78 * age)
        r = FW * (0.12 + 0.20 * age)
        g = np.exp(-(((xx - cx) / r) ** 2 + ((yy - cy) / (r * 0.8)) ** 2))
        # noise texture moving with the puff (sampled with wrap-around)
        nx = ((xx - cx) / (r * 2.2) * 64 + seeds[i, 2] * 256).astype(int) % 256
        ny = ((yy - cy) / (r * 2.2) * 64 + seeds[i, 3] * 256 + age * 40).astype(int) % 256
        tex = field[ny, nx]
        life = smooth(age, 0.0, 0.12) * (1 - age) ** 0.9
        a = np.clip(g * (0.3 + 1.4 * tex) - 0.2, 0, 1) * life * (0.8 + 0.4 * seeds[i, 1])
        a = np.minimum(a, 0.9)
        shade = shade * (1 - a) + (0.8 + 0.4 * tex) * a
        alpha = alpha + a * (1 - alpha)
    # fade out at the frame edges so no puff is cut
    alpha *= smooth(xx, 0, FW * 0.1) * smooth(FW - xx, 0, FW * 0.1) * smooth(yy, 0, FH * 0.15)
    alphas.append(alpha); shades.append(shade)
scale = 0.75 / np.percentile(np.array(alphas), 99.5)
smoke_rgba = np.zeros((FH * ROWS, FW * COLS, 4))
grey = linear(np.array([130, 128, 127]) / 255.0)
for f, (alpha, shade) in enumerate(zip(alphas, shades)):
    colour = grey * np.clip(shade / np.maximum(alpha, 1e-4), 0.75, 1.2)[..., None]
    r0, c0 = (f // COLS) * FH, (f % COLS) * FW
    smoke_rgba[r0:r0 + FH, c0:c0 + FW, :3] = colour
    smoke_rgba[r0:r0 + FH, c0:c0 + FW, 3] = np.minimum(alpha * scale, 0.8)
print('SMOKE', smoke_rgba.shape, 'core alpha (p99.5)', round(float(np.percentile(smoke_rgba[..., 3], 99.5)), 2),
      'covered', round(float((smoke_rgba[..., 3] > 0.2).mean()), 2))
save('logfire_smoke', smoke_rgba[..., :3], None, None, alpha=smoke_rgba[..., 3])

with open(os.path.join(OUT, 'means.json'), 'w') as f:
    json.dump(means, f, indent=1)

# preview sheet
names = list(means)
tiles = []
for name in names:
    im = Image.open(os.path.join(OUT, f'{name}_basecolor.png')).convert('RGBA').resize((256, 256))
    bg = Image.new('RGBA', im.size, (90, 90, 90, 255)); bg.alpha_composite(im); tiles.append(bg)
sheet = Image.new('RGB', (256 * len(tiles), 256))
for i, t in enumerate(tiles):
    sheet.paste(t.convert('RGB'), (256 * i, 0))
os.makedirs(os.path.join(HERE, 'review', 'fire_rev2'), exist_ok=True)
sheet.save(os.path.join(HERE, 'review', 'fire_rev2', 'textures_pbr.png'))
