#!/usr/bin/env python3
"""Textures of the MM8 props in props/textures/: <name>_basecolor.png (sRGB), <name>_normal.png (glTF / OpenGL +Y)
and <name>_mr.png (G roughness, B metal; R 1). Lit surfaces keep the source's luminance detail recoloured so the
texture's linear mean is the native sprite's measured colour (linear mean of the opaque sprite pixels, or of a
masked part). Sources: the CC0 Poly Haven sets in props/source/ (fetch_pbr.py) and, for bone, the project's own
MM6 skeleton atlas (assets_source/worlds/mm6/models/mm6_ske.glb, Meshy output owned by the project).
Usage: python3 -I make_textures.py [name ...]   (no names: all)"""
import json
import math
import os
import struct
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
OUT = os.path.join(HERE, 'textures')
SOURCE = os.path.join(HERE, 'source')
os.makedirs(OUT, exist_ok=True)
MEANS = os.path.join(OUT, 'means.json')
RNG = np.random.default_rng(8)


def linear(s):
    s = np.asarray(s, np.float64)
    return np.where(s <= 0.04045, s / 12.92, ((s + 0.055) / 1.055) ** 2.4)


def srgb(lin):
    lin = np.clip(lin, 0, 1)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)


def luminance(lin):
    return lin @ np.array([0.2126, 0.7152, 0.0722])


def load(asset, kind, size):
    path = os.path.join(SOURCE, asset, f'{asset}_{kind}_2k.png')
    im = Image.open(path)
    shape = (size, size * im.height // im.width)
    if im.mode.startswith('I'):
        a = np.asarray(im, np.float64) / 65535.0
        return np.asarray(Image.fromarray(a.astype(np.float32), 'F').resize(shape, Image.LANCZOS), np.float64).clip(0, 1)
    im = im.convert('RGB').resize(shape, Image.LANCZOS)
    a = np.asarray(im, np.float64) / 255.0
    return a if kind in ('diff', 'nor_gl') else a[..., 0]


def grade(diff_srgb, target_srgb, contrast=1.0, keep_hue=0.15, mask=None):
    """Scan albedo -> the native colour: relative luminance (^contrast) times the target's linear colour, a little of
    the scan's own hue kept, rescaled so the (masked) linear mean is the target."""
    lin = linear(diff_srgb)
    lum = luminance(lin)
    sel = (lambda a: a[mask]) if mask is not None else (lambda a: a.reshape(-1, *a.shape[2:]))
    rel = (lum / sel(lum).mean()) ** contrast
    target = linear(np.array(target_srgb) / 255.0)
    hue = lin / np.maximum(lum[..., None], 1e-5)
    hue = hue / sel(hue).mean(0)
    colour = target * rel[..., None] * (1 - keep_hue + keep_hue * hue)
    colour *= target / sel(colour).mean(0)
    return colour


def normal_map(asset, size, strength=1.0):
    n = load(asset, 'nor_gl', size) * 2 - 1
    n[..., :2] *= strength
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def shrink(a, size):
    """Area-average a float image (h, w[, c]) down to size x size."""
    f = a.shape[0] // size
    return a.reshape(size, f, size, f, *a.shape[2:]).mean((1, 3))


def save(name, colour_linear, normal=None, roughness=None, metal=0.0, alpha=None, mr_size=None, out_size=None):
    if out_size:
        colour_linear = shrink(colour_linear, out_size)
        if normal is not None:
            normal = shrink(normal, out_size); normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
        if np.ndim(roughness) == 2:
            roughness = shrink(roughness, out_size)
        if alpha is not None:
            alpha = shrink(alpha, out_size)
    rgb = (srgb(colour_linear) * 255 + 0.5).astype(np.uint8)
    if alpha is not None:
        rgba = np.dstack([rgb, (np.clip(alpha, 0, 1) * 255 + 0.5).astype(np.uint8)])
        Image.fromarray(rgba, 'RGBA').save(os.path.join(OUT, f'{name}_basecolor.png'), optimize=True)
    else:
        Image.fromarray(rgb, 'RGB').save(os.path.join(OUT, f'{name}_basecolor.png'), optimize=True)
    if normal is not None:
        nrm = ((normal * 0.5 + 0.5) * 255 + 0.5).clip(0, 255).astype(np.uint8)
        Image.fromarray(nrm, 'RGB').save(os.path.join(OUT, f'{name}_normal.png'), optimize=True)
    if roughness is not None:
        shape = colour_linear.shape[:2]
        mr = np.zeros(shape + (3,))
        mr[..., 0] = 1.0
        mr[..., 1] = np.broadcast_to(roughness, shape)
        mr[..., 2] = np.broadcast_to(metal, shape)
        im = Image.fromarray((mr * 255 + 0.5).astype(np.uint8), 'RGB')
        if mr_size:
            im = im.resize(mr_size, Image.LANCZOS)
        im.save(os.path.join(OUT, f'{name}_mr.png'), optimize=True)
    means = json.load(open(MEANS)) if os.path.exists(MEANS) else {}
    flat = colour_linear.reshape(-1, 3) if alpha is None else colour_linear[alpha > 0.5]
    means[name] = [round(float(v)) for v in srgb(flat.mean(0)) * 255]
    json.dump(means, open(MEANS, 'w'), indent=1)
    print('TEXTURE', name, means[name])


def sprite_mean(texture, mask_fn=None):
    """sRGB of the linear mean of a native x2 sprite's opaque pixels (optionally a colour-selected part)."""
    path = os.path.join(REPO, 'assets_legacy', 'decorations_x2_mm8_20261016', f'{texture}_p8.png')
    a = np.asarray(Image.open(path).convert('RGBA'), np.float64)
    m = a[..., 3] > 200
    if mask_fn is not None:
        m &= mask_fn(a[..., :3])
    return srgb(linear(a[..., :3][m] / 255).mean(0)) * 255


def glb_images(path):
    raw = open(path, 'rb').read()
    size = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20 + size]); start = 28 + size
    out = {}
    for image in doc['images']:
        view = doc['bufferViews'][image['bufferView']]
        offset = start + view.get('byteOffset', 0)
        import io
        out[image['name']] = Image.open(io.BytesIO(raw[offset:offset + view['byteLength']]))
    return out


# ---------------------------------------------------------------- bone (MM6 skeleton atlas)
def bone(name='skeleton', target=None, size=(2048, 1024), ao_weight=1.0):
    """skeleton_*: the MM6 skeleton's atlas (2080 x 1024: body set, skull set) resampled to 2048 x 1024, bone texels
    graded to dec05's measured bone colour; its baked AO (metal-rough R) deepened into the colour for the sprite's
    dark crevices. Eye swatches stay as they are (the eyes are dropped from the meshes)."""
    images = glb_images(os.path.join(REPO, 'assets_source', 'worlds', 'mm6', 'models', 'mm6_ske.glb'))
    base = np.asarray(images['ske_basecolor_1k_head_atlas'].convert('RGB').resize(size, Image.LANCZOS),
                      np.float64) / 255
    mr = np.asarray(images['ske_metal_rough_1k_head_atlas'].convert('RGB').resize(size, Image.LANCZOS),
                    np.float64) / 255
    region = np.asarray(images['ske_region_mask_head_atlas'].convert('RGBA').resize(size, Image.NEAREST),
                        np.float64)[..., 0] > 127
    # AO (R) into the colour; ao_weight < 1 for loose bones, whose ends were occluded joints in the creature
    ao = 1 - ao_weight * (1 - mr[..., 0:1])
    lin = linear(base) * (0.35 + 0.65 * ao) ** 1.2
    # aged grime (rev 2): brown-black dirt in the occluded crevices and in noise patches over the surface
    patches = np.clip(noise(max(size), 60, 41)[:size[1], :size[0]] * 0.5 + 0.2, 0, 1)[..., None]
    grime = np.clip((0.75 - ao) / 0.5, 0, 1) * 0.8 + patches * 0.35
    lin = lin * (1 - grime) + linear(np.array([52, 38, 20]) / 255) * grime * lin.mean() / 0.2
    # dec05's bone pixels are a saturated yellow-brown (median 114, 97, 61; linear mean 151, 136, 99): the target
    # keeps the mean's brightness with the median's saturation, as lit renders otherwise read pale grey-ivory.
    target = target or (146, 124, 78)
    graded = grade(srgb(lin), target, contrast=1.45, keep_hue=0.35, mask=region)
    colour = np.where(region[..., None], graded, linear(base))
    half = (size[0] // 2, size[1] // 2)
    normal = np.asarray(images['ske_normal_1k_head_atlas'].convert('RGB').resize(half, Image.LANCZOS),
                        np.float64) / 255 * 2 - 1
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    rough = np.clip(mr[..., 1] * 1.0 + 0.05, 0.45, 1.0)
    save(name, colour, normal, rough, 0.0, mr_size=half)


# ---------------------------------------------------------------- tileable noise
def noise(size, scale, seed, anisotropy=(1.0, 1.0)):
    """Tileable band-limited noise (FFT filtered white noise), zero mean, unit deviation. scale: feature size in
    texels; anisotropy stretches the features along x / y."""
    rng = np.random.default_rng(seed)
    white = rng.normal(size=(size, size))
    fy = np.fft.fftfreq(size)[:, None] * anisotropy[1]
    fx = np.fft.fftfreq(size)[None, :] * anisotropy[0]
    f = np.sqrt(fx * fx + fy * fy) * scale
    spectrum = np.fft.fft2(white) * np.exp(-f * f * 4)
    n = np.real(np.fft.ifft2(spectrum))
    return (n - n.mean()) / n.std()


def height_normal(height, strength):
    gy, gx = np.gradient(height)
    n = np.dstack([-gx * strength, gy * strength, np.ones_like(height)])
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


# ---------------------------------------------------------------- meat and hide (carcass, carrion)
def meat():
    """meat_*: raw, drying muscle for the carcass (dec21) and carrion (dec22). Procedural, tileable (rev 2 after the
    coordinator's review: striated, matte, darker): parallel muscle fibres (fine noise stretched 40 x along x) grouped
    in bundles whose dark seams run with the fibres, thin pale sinew streaks along them, a few dark clots, the CC0
    leather_white scan's pores for fine relief. The fibres are the strongest relief in the normal map. Roughness
    0.6-0.75 with small wet spots (about 4 % of the texels at 0.3). Colour from the sprites' red pixels (dec21 125, 59,
    26; dec22 129, 47, 14): dark brown-red to orange highlights, linear mean about 115, 45, 18."""
    size = 1024
    fibres = noise(size, 2.5, 11, (1.0, 0.025)) * 0.7 + noise(size, 6, 12, (1.0, 0.06)) * 0.6
    bundles = noise(size, 70, 13, (1.0, 0.18))
    seam = np.exp(-(noise(size, 55, 14, (1.0, 0.2)) / 0.12) ** 2)          # thin dark seams along the fibres
    sinew = np.clip((noise(size, 5, 16, (1.0, 0.02)) - 1.7) / 0.5, 0, 1) * (bundles > -0.3)
    clot = np.clip((noise(size, 40, 17) - 2.0) / 0.5, 0, 1)
    pores = load('leather_white', 'diff', size).mean(-1)
    pores = (pores - pores.mean()) / pores.std()
    t = np.clip(0.5 + 0.17 * fibres + 0.16 * bundles + 0.04 * pores - 0.35 * seam, 0, 1)
    dark, mid, light = (linear(np.array(c) / 255) for c in ((44, 12, 2), (138, 50, 10), (204, 106, 34)))
    colour = np.where(t[..., None] < 0.5, dark + (mid - dark) * (t[..., None] / 0.5),
                      mid + (light - mid) * ((t[..., None] - 0.5) / 0.5))
    sinew_colour = linear(np.array([196, 160, 120]) / 255)
    colour = colour * (1 - sinew[..., None] * 0.8) + sinew_colour * sinew[..., None] * 0.8
    colour *= (1 - 0.6 * clot[..., None])
    height = 1.0 * fibres + 0.5 * bundles - 1.2 * seam + 0.15 * pores + 0.6 * sinew - 0.5 * clot
    normal = height_normal(height, 0.9)
    wet = np.clip((noise(size, 6, 18) - 1.75) / 0.3, 0, 1)
    rough = np.clip(0.68 + 0.05 * noise(size, 25, 15) - 0.38 * wet + 0.05 * sinew, 0.28, 0.8)
    save('meat', colour, normal, rough, 0.0, mr_size=(256, 256), out_size=512)


def hide():
    """hide_*: grey dead skin and hair scraps (the sprites' grey patches, about 105, 103, 98): the CC0 leather_white
    scan graded grey, its normal and roughness."""
    size = 512
    diff = load('leather_white', 'diff', size)
    colour = grade(diff, (100, 98, 92), contrast=1.6, keep_hue=0.0)
    colour *= (1 + 0.12 * noise(size, 40, 21))[..., None]
    rough = np.clip(load('leather_white', 'rough', size) * 0.6 + 0.35, 0.3, 1.0)
    save('hide', colour, normal_map('leather_white', size, 1.2), rough, 0.0)


# ---------------------------------------------------------------- barrel atlas
def smear_u(a, sigma):
    """Blur along x (rows) with wrap: brushed / spun metal from a scan."""
    from numpy.fft import fft, ifft
    n = a.shape[1]
    f = np.fft.fftfreq(n)
    kernel = np.exp(-0.5 * (2 * np.pi * sigma * f) ** 2)
    axis_shape = (1, n) + (1,) * (a.ndim - 2)
    return np.real(ifft(fft(a, axis=1) * kernel.reshape(axis_shape), axis=1))


def brushed(asset, width, height, target, sigma=30, crop=(0.05, 0.12)):
    """A strip of a metal scan smeared along u (seamless around), graded to the target colour."""
    diff = load(asset, 'diff', 2048)
    rough = load(asset, 'rough', 2048)
    y0 = int(crop[0] * 2048); y1 = int(crop[1] * 2048)
    strip = smear_u(diff[y0:y1], sigma)
    r = smear_u(rough[y0:y1], sigma)
    img = lambda a, mode: np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), mode).resize(
        (width, height), Image.LANCZOS), np.float64) / 255
    return grade(img(strip, 'RGB'), target, contrast=1.3, keep_hue=0.1), img(r, 'L')


def barrel():
    """barrel_*: one 1024 atlas for the barrel dec03. v 0.25..1: the CC0 weathered_planks scan (planks vertical),
    tiled twice across (18 staves around), 1600 scan rows down the stave length, graded to the sprite's wood
    (100, 72, 42). v 0..0.22: a strip of the CC0 metal_plate_02 scan smeared along u (spun steel without the plate
    seams), graded to the hoops' grey (111, 108, 108), metallic 0.6 (engine deviation: dungeon light is too dark for
    pure metal, GAME_ASSET_MODELLING_GUIDELINES.md section 5)."""
    size = 1024
    diff = load('weathered_planks', 'diff', 2048)
    nrm = load('weathered_planks', 'nor_gl', 2048) * 2 - 1
    rough = load('weathered_planks', 'rough', 2048)
    rows = slice(200, 1800)

    def region(a, mode=None):
        a = np.concatenate([a[rows], a[rows]], axis=1)
        if a.ndim == 2:
            im = Image.fromarray(a.astype(np.float32), 'F').resize((size, 768), Image.LANCZOS)
            return np.asarray(im, np.float64)
        chans = [np.asarray(Image.fromarray(a[..., c].astype(np.float32), 'F').resize((size, 768), Image.LANCZOS),
                            np.float64) for c in range(3)]
        return np.dstack(chans)
    wood = grade(np.clip(region(diff), 0, 1), (90, 60, 30), contrast=1.55, keep_hue=0.2)
    wood_n = region(nrm); wood_n /= np.linalg.norm(wood_n, axis=-1, keepdims=True)
    wood_r = np.clip(region(rough), 0.4, 1.0)
    hoop, hoop_r = brushed('metal_plate_02', size, 225, (111, 108, 108))
    colour = np.zeros((size, size, 3)); normal = np.zeros((size, size, 3)); normal[..., 2] = 1
    rough_all = np.full((size, size), 0.8); metal = np.zeros((size, size))
    colour[:768] = wood; normal[:768] = wood_n; rough_all[:768] = wood_r          # image rows run top-down:
    colour[size - 225:] = hoop; rough_all[size - 225:] = np.clip(hoop_r * 0.7, 0.25, 0.7)   # v 0..0.22 at the bottom
    metal[size - 225:] = 0.6
    colour[768:size - 225] = linear(np.array([60, 44, 28]) / 255)
    save('barrel', colour, normal, rough_all, metal, mr_size=(512, 512))


# ---------------------------------------------------------------- rune posts
RUNE_LINES = {   # Elder Futhark glyphs as strokes in a unit box (x right, y down)
    'uruz': [((0.25, 1), (0.25, 0)), ((0.25, 0), (0.78, 0.32)), ((0.78, 0.32), (0.78, 1))],
    'haglaz': [((0.25, 0), (0.25, 1)), ((0.75, 0), (0.75, 1)), ((0.25, 0.32), (0.75, 0.62))],
    'tiwaz': [((0.5, 0), (0.5, 1)), ((0.5, 0), (0.15, 0.36)), ((0.5, 0), (0.85, 0.36))],
    'ansuz': [((0.3, 0), (0.3, 1)), ((0.3, 0), (0.78, 0.3)), ((0.3, 0.36), (0.78, 0.66))],
    'fehu': [((0.3, 0), (0.3, 1)), ((0.3, 0.32), (0.78, 0.02)), ((0.3, 0.64), (0.78, 0.34))],
    'yr': [((0.5, 0), (0.5, 1)), ((0.5, 0.5), (0.13, 0.95)), ((0.5, 0.5), (0.87, 0.95))],
    'raidho': [((0.3, 0), (0.3, 1)), ((0.3, 0), (0.78, 0.25)), ((0.78, 0.25), (0.3, 0.52)), ((0.3, 0.52), (0.8, 1))],
    'thurisaz': [((0.3, 0), (0.3, 1)), ((0.3, 0.18), (0.8, 0.5)), ((0.8, 0.5), (0.3, 0.82))],
}
RUNE_COLUMNS = [   # (glyphs top to bottom); one column of the atlas each, 1024 tall
    ['uruz', 'haglaz', 'tiwaz', 'tiwaz', 'ansuz', 'fehu', 'fehu'],      # dec13, dec14
    ['yr', 'fehu', 'tiwaz'],                                             # dec15, dec16
    ['raidho', 'thurisaz'],                                              # dec17
]


def runes():
    """runes_*: carved, faintly glowing runes on an alpha-tested strip (Rune material, emissive + pulse in the engine).
    Three 256-wide columns of 1024 (the posts' glyph sequences from the sprites: Elder Futhark letters), each stroke
    a pale pink rim (the sprite's lit chisel edge), red body (measured 140, 28, 20) and a dark carved core; the
    alpha is the rim. Normal map: a V-groove across each stroke."""
    from PIL import ImageDraw, ImageFilter
    W, H = 1024, 1024
    rim = Image.new('L', (W, H)); body = Image.new('L', (W, H)); core = Image.new('L', (W, H))
    for c, glyphs in enumerate(RUNE_COLUMNS):
        cell = H / len(glyphs)
        h = min(cell * 0.84, 176 * 1.6)
        w = min(176, h * 0.6)
        x0 = c * 256 + (256 - w) / 2
        stroke = max(w * 0.2, 19)
        for g, name in enumerate(glyphs):
            y0 = g * cell + (cell - h) / 2
            for (ax, ay), (bx, by) in RUNE_LINES[name]:
                p = [(x0 + ax * w, y0 + ay * h), (x0 + bx * w, y0 + by * h)]
                for img, width in ((rim, stroke * 1.35), (body, stroke), (core, stroke * 0.38)):
                    d = ImageDraw.Draw(img)
                    d.line(p, fill=255, width=int(width))
                    for q in p:
                        r = width / 2
                        d.ellipse((q[0] - r, q[1] - r, q[0] + r, q[1] + r), fill=255)
    f = lambda im, blur: np.asarray(im.filter(ImageFilter.GaussianBlur(blur)), np.float64) / 255
    a_rim, a_body, a_core = f(rim, 1.5), f(body, 2.5), f(core, 2.0)
    pink, red, dark = (linear(np.array(c) / 255) for c in ((205, 120, 108), (150, 26, 18), (40, 4, 3)))
    colour = pink * (1 - a_body[..., None]) + red * a_body[..., None]
    colour = colour * (1 - a_core[..., None]) + dark * a_core[..., None]
    height = -a_body * 0.5 - a_core * 0.8
    normal = height_normal(np.asarray(Image.fromarray((height * 255 + 255).astype(np.uint8) // 2).filter(
        ImageFilter.GaussianBlur(3)), np.float64) / 255, 6.0)
    rough = 0.55 - 0.15 * a_body
    save('runes', colour, normal, rough, 0.0, alpha=a_rim, mr_size=(256, 256))


def runerock():
    """runerock_*: the CC0 lichen_rock scan graded to the posts' weathered grey stone (rock pixels 86, 86, 81) with
    raised contrast (the sprites' bright faces and black cracks); its normal and roughness."""
    size = 1024
    colour = grade(load('lichen_rock', 'diff', size), (88, 87, 82), contrast=1.15, keep_hue=0.1)
    rough = np.clip(load('lichen_rock', 'rough', size), 0.55, 1.0)
    save('runerock', colour, normal_map('lichen_rock', size, 1.3), rough, 0.0, mr_size=(512, 512))


def roots():
    """roots_*: a card of dark tangled brambles and roots (dec13, dec15, dec17 bases): seeded random-walk branches
    tapering outward with thorns, alpha tested; colours from the sprites' base tangles (dark grey-brown)."""
    from PIL import ImageDraw, ImageFilter
    W, H = 512, 256
    rng = np.random.default_rng(31)
    alpha = Image.new('L', (W, H)); shade = Image.new('L', (W, H))
    da, ds = ImageDraw.Draw(alpha), ImageDraw.Draw(shade)

    def branch(x, y, angle, length, width, depth):
        steps = int(length / 6)
        for _ in range(steps):
            nx, ny = x + 6 * math.cos(angle), y - 6 * math.sin(angle)
            da.line((x, y, nx, ny), fill=255, width=max(1, int(width)))
            ds.line((x, y, nx, ny), fill=int(rng.uniform(60, 200)), width=max(1, int(width)))
            if rng.random() < 0.18:                                 # thorn
                ta = angle + rng.choice([-1, 1]) * rng.uniform(0.8, 1.4)
                da.line((nx, ny, nx + 5 * math.cos(ta), ny - 5 * math.sin(ta)), fill=255, width=1)
            x, y = nx, ny; angle += rng.normal(0, 0.25); width *= 0.97
            if depth < 3 and rng.random() < 0.08:
                branch(x, y, angle + rng.choice([-1, 1]) * rng.uniform(0.4, 0.9), length * 0.5, width * 0.7, depth + 1)
    for _ in range(60):
        x = rng.uniform(20, W - 20)
        branch(x, H - 2, rng.uniform(0.35, 2.8), rng.uniform(70, 220), rng.uniform(7, 14), 0)
    a = np.asarray(alpha.filter(ImageFilter.GaussianBlur(0.6)), np.float64) / 255
    s = np.asarray(shade.filter(ImageFilter.GaussianBlur(1.0)), np.float64) / 255
    base = linear(np.array([48, 41, 36]) / 255)
    colour = base * (0.45 + 0.9 * s[..., None])
    save('roots', colour, None, np.full((H, W), 0.85), 0.0, alpha=a, mr_size=(64, 32))


def rose():
    """rose_*: a small atlas for the white rose at dec13's foot: left half cream-white petal (shaded toward the base,
    pale veins), right half dark green leaf with a midrib. Procedural."""
    W, H = 256, 128
    y, x = np.mgrid[0:H, 0:W] / np.array([H, W / 2])[:, None, None]
    petal = linear(np.array([238, 234, 222]) / 255) * (0.75 + 0.25 * y[..., None])
    petal *= (1 - 0.05 * (np.sin(x * 40 + np.sin(y * 9) * 2) > 0.8))[..., None]
    leaf = linear(np.array([52, 78, 38]) / 255) * (0.8 + 0.3 * np.abs(np.sin(y * 3.1))[..., None])
    rib = np.abs(x - 1.5) < 0.03
    colour = np.where((x < 1)[..., None], petal, leaf)
    colour[rib & (x >= 1)] = linear(np.array([110, 130, 80]) / 255)
    save('rose', colour, None, np.where(x < 1, 0.6, 0.5), 0.0)


# ---------------------------------------------------------------- MM7-shared props (cauldron, trash heap, goblet, fruit)
def cauldron():
    """cauldron_iron (CC0 rust_coarse_01 greyed to the pot's dark iron 46, 41, 39, a hammered sheen),
    cauldron_coals (CC0 rock_boulder_dry graded to the glowing coal lumps' copper 170, 95, 70), cauldron_logs (CC0
    bark_willow charred near black), cauldron_brew (unlit: the glowing red surface inside the rim, 182, 80, 49 with
    bright swirls)."""
    size = 1024
    iron = grade(load('rust_coarse_01', 'diff', size), (50, 45, 43), contrast=1.4, keep_hue=0.05)
    save('cauldron_iron', iron, normal_map('rust_coarse_01', size, 0.8),
         np.clip(load('rust_coarse_01', 'rough', size) * 0.7 + 0.15, 0.3, 0.8), 0.5, mr_size=(512, 512))
    coals = grade(load('rock_boulder_dry', 'diff', 512), (128, 66, 46), contrast=2.2, keep_hue=0.0)
    save('cauldron_coals', coals, normal_map('rock_boulder_dry', 512, 1.2), 0.45, 0.0)
    logs = grade(load('bark_willow', 'diff', 512), (52, 30, 20), contrast=1.4, keep_hue=0.1)
    save('cauldron_logs', logs, normal_map('bark_willow', 512, 1.0), np.clip(load('bark_willow', 'rough', 512), 0.6, 1), 0.0)
    swirl = noise(256, 18, 51) * 0.6 + noise(256, 5, 52) * 0.4
    t = np.clip(0.5 + 0.35 * swirl, 0, 1)[..., None]
    brew = linear(np.array([110, 22, 10]) / 255) * (1 - t) + linear(np.array([235, 120, 60]) / 255) * t
    save('cauldron_brew', brew, None, 0.3, 0.0)


def trash():
    """trash_bark (CC0 pine_bark graded to the heap's red-brown bark flakes 100, 76, 62) and trash_core (CC0
    brown_mud_leaves_01 graded to the mossy green-grey core 49, 63, 37)."""
    size = 1024
    bark = grade(load('pine_bark', 'diff', size), (150, 100, 72), contrast=1.6, keep_hue=0.2)
    save('trash_bark', bark, normal_map('pine_bark', size, 1.2), np.clip(load('pine_bark', 'rough', size), 0.55, 1),
         0.0, mr_size=(512, 512))
    core = grade(load('brown_mud_leaves_01', 'diff', 512), (108, 106, 84), contrast=1.8, keep_hue=0.15)
    save('trash_core', core, normal_map('brown_mud_leaves_01', 512, 1.0), 0.85, 0.0)


def goblet():
    """goblet: red glass (the sprite's 138, 52, 39 mean; deep red 110, 15, 1 with pale facet highlights): a vertical
    gradient of streaks so the faceted cup and stem catch bright and dark bands. Glossy (roughness 0.08)."""
    w, h = 128, 128
    x = np.arange(w)[None, :] / w
    y = np.arange(h)[:, None] / h
    streak = np.sin(x * 2 * np.pi * 3) ** 12 * (0.6 + 0.4 * np.sin(y * 9) ** 2)
    colour = linear(np.array([105, 6, 2]) / 255) * (0.75 + 0.25 * np.cos(x * 2 * np.pi * 2))[..., None] \
        * np.ones((h, w, 1))
    colour = colour * (1 - 0.6 * streak[..., None]) + linear(np.array([250, 120, 85]) / 255) * 0.6 * streak[..., None]
    save('goblet', colour, None, 0.08, 0.0)


def fruit():
    """fruitbowl_wood (CC0 fine_grained_wood graded to the bowl's grey-tan 150, 135, 112), fruit_orange and
    fruit_grape (the CC0 food_lime_01 scan's luminance graded to orange 230, 140, 40 and pale grape green 150, 180,
    70; the lime's texture coordinates are reused on its own mesh)."""
    bowl = grade(load('fine_grained_wood', 'diff', 1024), (118, 98, 78), contrast=1.4, keep_hue=0.2)
    save('fruitbowl_wood', bowl, normal_map('fine_grained_wood', 1024, 1.0),
         np.clip(load('fine_grained_wood', 'rough', 1024), 0.5, 0.9), 0.0, mr_size=(512, 512))
    lime = np.asarray(Image.open(os.path.join(SOURCE, 'food_lime_01', 'textures', 'food_lime_01_diff_1k.jpg'))
                      .convert('RGB').resize((512, 512), Image.LANCZOS), np.float64) / 255
    save('fruit_orange', grade(lime, (214, 108, 26), contrast=1.0, keep_hue=0.0), None, 0.5, 0.0)
    grape = grade(lime, (150, 180, 70), contrast=0.8, keep_hue=0.0)
    skin = luminance(linear(lime)) > 0.3 * luminance(linear(lime)).mean()      # the scan atlas's dark gutter
    grape[~skin] = grape[skin].mean(0)                                          # the grape spheres span it all
    save('fruit_grape', grape, None, 0.3, 0.0)
    # the CC0 apple and banana scans' own maps, renamed to this batch's naming (512, the fruit is small on screen)
    def jpg(asset, kind, size=512):
        im = Image.open(os.path.join(SOURCE, asset, 'textures', f'{asset}_{kind}_1k.jpg')).convert('RGB')
        return np.asarray(im.resize((size, size), Image.LANCZOS), np.float64) / 255
    for asset, name, rough in (('food_apple_01', 'fruit_apple', jpg('food_apple_01', 'rough')[..., 0]),
                               ('bananas', 'fruit_banana', jpg('bananas', 'arm')[..., 1])):
        n = jpg(asset, 'nor_gl') * 2 - 1
        save(name, linear(jpg(asset, 'diff')), n / np.linalg.norm(n, axis=-1, keepdims=True), rough, 0.0)


def tableware():
    """table_wood (CC0 rosewood_veneer1 graded to the plates' orange-brown 150, 85, 45, glossy oiled wood),
    table_pewter (CC0 metal_plate_02 graded to the metal plates' worn silver 140, 136, 130) and table_tarnish (the
    same scan graded to the bowls' dark tarnished metal 96, 88, 76, with darker blotches). Metallic 0.6 (dungeon
    light is too dark for pure metal; GAME_ASSET_MODELLING_GUIDELINES.md section 5)."""
    wood = grade(load('rosewood_veneer1', 'diff', 1024), (150, 85, 45), contrast=1.3, keep_hue=0.3)
    save('table_wood', wood, normal_map('rosewood_veneer1', 1024, 0.6),
         np.clip(load('rosewood_veneer1', 'rough', 1024) * 0.6 + 0.2, 0.25, 0.6), 0.0, mr_size=(512, 512))
    diff = load('metal_plate_02', 'diff', 1024)
    rough = np.clip(load('metal_plate_02', 'rough', 1024) * 0.7 + 0.15, 0.25, 0.7)
    save('table_pewter', grade(diff, (140, 136, 130), contrast=1.4, keep_hue=0.0),
         normal_map('metal_plate_02', 1024, 0.5), rough, 0.6, mr_size=(512, 512))
    tarnish = grade(diff, (96, 88, 76), contrast=1.6, keep_hue=0.2) * (1 + 0.3 * noise(1024, 30, 61))[..., None]
    save('table_tarnish', tarnish, normal_map('metal_plate_02', 1024, 0.5), rough, 0.6, mr_size=(512, 512))


def elfstone():
    """elfstone_*: the MM6 fighter's atlas (assets_source/worlds/mm6/models/mm6_fgt.glb, the project's own model;
    2080 x 1024, body and head sets) turned to weathered stone: its luminance (armour plates, straps, boot lacing,
    face) with raised contrast, times the CC0 mossy_rock scan tiled over the atlas, graded to the statue's grey-green
    (sprite 89, 88, 80; moss in the crevices from the scan). The fighter's normal map is blended with the rock's, so
    the armour detail stays carved. Matte stone roughness. Also `elfsword_*`, the sword's own strip: the same rock,
    darker and greener (the sprite's mossy blade)."""
    images = glb_images(os.path.join(REPO, 'assets_source', 'worlds', 'mm6', 'models', 'mm6_fgt.glb'))
    size = (2048, 1024)
    base = np.asarray(images['fgt_basecolor_1k_head_atlas'].convert('RGB').resize(size, Image.LANCZOS),
                      np.float64) / 255
    lum = luminance(linear(base))
    rel = np.clip(lum / np.median(lum), 0.35, 2.0) ** 0.55
    rock = load('mossy_rock', 'diff', 1024)
    rock = np.concatenate([rock, rock], axis=1)                       # tile across the 2:1 atlas
    stone = grade(rock, (92, 94, 82), contrast=1.1, keep_hue=0.4)
    colour = stone * rel[..., None]
    colour *= np.array([92, 94, 82]) / 255 / srgb(colour.reshape(-1, 3).mean(0))   # rough mean back to target
    fn = np.asarray(images['fgt_normal_1k_head_atlas'].convert('RGB').resize((1024, 512), Image.LANCZOS),
                    np.float64) / 255 * 2 - 1
    rn = normal_map('mossy_rock', 512, 0.8)
    rn = np.concatenate([rn, rn], axis=1)
    n = fn.copy(); n[..., :2] += rn[..., :2]; n /= np.linalg.norm(n, axis=-1, keepdims=True)
    save('elfstone', colour, n, 0.85, 0.0, mr_size=(256, 128))
    sword = grade(load('mossy_rock', 'diff', 512), (78, 84, 66), contrast=1.4, keep_hue=0.7)
    save('elfsword', sword, normal_map('mossy_rock', 512, 1.0), 0.8, 0.0)


JOBS = {
    'elfstone': elfstone,
    'tableware': tableware,
    'cauldron': cauldron,
    'trash': trash,
    'goblet': goblet,
    'fruit': fruit,
    'runes': runes,
    'runerock': runerock,
    'roots': roots,
    'rose': rose,
    'barrel': barrel,
    'skeleton': bone,
    # dec29 skull and bones: greyer ivory (linear mean 127, 116, 94; median 95, 83, 66); a small, low prop: 1K atlas
    'bonepile': lambda: bone('bonepile', (112, 98, 72), (1024, 512), ao_weight=0.25),
    'meat': lambda: meat(),
    'hide': lambda: hide(),
}

if __name__ == '__main__':
    names = sys.argv[1:] or list(JOBS)
    for n in names:
        JOBS[n]()
