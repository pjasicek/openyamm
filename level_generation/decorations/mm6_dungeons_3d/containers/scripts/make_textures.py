#!/usr/bin/env python3
"""Procedural, tileable textures for the dungeon containers batch (containers/textures/): burlap (sacks), suede (the
tied pouch), rope, straw litter (trash heap mound), rust, rag, crockery, mushroom caps (brown speckled, orange with
white warts, red with white dots), gills, stem and crystal. Every map is built from periodic (FFT-filtered) noise or
wrap-around drawing, so it repeats seamlessly. Per material: <name>_basecolor.png (sRGB), <name>_normal.png (OpenGL
tangent space from a height field), <name>_mr.png (G roughness, B metal). Colours are neutral-ish mid tones; the
build scripts tint them to the native sprites through COLOR_0. Usage: make_textures.py"""
import os

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'textures')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7321)
N = 512


def noise(shape=(N, N), beta=2.0, scale=(1.0, 1.0)):
    """Periodic fractal noise in [0, 1]: white noise filtered by 1 / f^beta (per-axis frequency scale stretches it)."""
    field = rng.normal(size=shape)
    fy = np.fft.fftfreq(shape[0])[:, None] * scale[0]
    fx = np.fft.fftfreq(shape[1])[None, :] * scale[1]
    radius = np.sqrt(fx * fx + fy * fy)
    radius[0, 0] = 1.0
    spectrum = np.fft.fft2(field) / radius ** beta
    spectrum[0, 0] = 0.0
    values = np.real(np.fft.ifft2(spectrum))
    return (values - values.min()) / (values.max() - values.min())


def linear(srgb_value):
    c = np.asarray(srgb_value, np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(lin):
    lin = np.clip(lin, 0, 1)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)


def mix(t, a, b):
    """Linear-space blend between two sRGB colours by t (H x W) -> H x W x 3 linear."""
    t = np.clip(t, 0, 1)[..., None]
    return linear(a) * (1 - t) + linear(b) * t


def normal_from_height(height, strength):
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 0.5 * strength
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 0.5 * strength
    n = np.stack([-dx, dy, np.ones_like(height)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5


def save(name, colour_linear, height, strength, roughness, metal=0.0):
    rgb = (srgb(colour_linear) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(rgb).save(os.path.join(OUT, f'{name}_basecolor.png'))
    Image.fromarray((normal_from_height(height, strength) * 255 + 0.5).astype(np.uint8)).save(
        os.path.join(OUT, f'{name}_normal.png'))
    shape = height.shape
    mr = np.dstack([np.zeros(shape), np.broadcast_to(roughness, shape), np.broadcast_to(metal, shape)])
    Image.fromarray((np.clip(mr, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(OUT, f'{name}_mr.png'))
    print('TEXTURE', name, shape, 'mean sRGB', (srgb(colour_linear).reshape(-1, 3).mean(0) * 255).round(1))


def wrap_blur(a, sigma):
    return ndimage.gaussian_filter(a, sigma, mode='wrap')


def wrap_strokes(count, length, width, angle_spread, base_angle, seed_values, size=N):
    """Height field of random wrap-around strokes (straw, fibres): returns height and per-stroke shade map."""
    image = Image.new('L', (size * 3, size * 3), 0)
    shade = Image.new('L', (size * 3, size * 3), 0)
    draw = ImageDraw.Draw(image); draw_shade = ImageDraw.Draw(shade)
    for k in range(count):
        x, y = rng.uniform(0, size, 2)
        a = base_angle + rng.uniform(-angle_spread, angle_spread)
        l = rng.uniform(*length)
        w = int(rng.integers(width[0], width[1] + 1))
        level = int(rng.uniform(*seed_values))
        tone = int(rng.uniform(60, 255))
        for ox in (0, size, 2 * size):
            for oy in (0, size, 2 * size):
                p0 = (x + ox, y + oy)
                p1 = (x + ox + np.cos(a) * l, y + oy + np.sin(a) * l)
                draw.line([p0, p1], fill=level, width=w)
                draw_shade.line([p0, p1], fill=tone, width=w)
    crop = (size, size, 2 * size, 2 * size)
    return (np.asarray(image.crop(crop), np.float64) / 255.0, np.asarray(shade.crop(crop), np.float64) / 255.0)


def blobs(count, radius, size=N, soft=1.5):
    """Wrap-around round spots of random radius: mask in [0, 1]."""
    image = Image.new('L', (size * 3, size * 3), 0)
    draw = ImageDraw.Draw(image)
    for _ in range(count):
        x, y = rng.uniform(0, size, 2)
        r = rng.uniform(*radius)
        rx, ry = r * rng.uniform(0.8, 1.25), r * rng.uniform(0.8, 1.25)
        for ox in (0, size, 2 * size):
            for oy in (0, size, 2 * size):
                draw.ellipse([x + ox - rx, y + oy - ry, x + ox + rx, y + oy + ry], fill=255)
    mask = np.asarray(image.crop((size, size, 2 * size, 2 * size)), np.float64) / 255.0
    return wrap_blur(mask, soft)


y, x = np.mgrid[0:N, 0:N] / N

# ------------------------------------------------------------ burlap: coarse plain weave, 32 threads per repeat
threads = 32
wobble = (noise(beta=2.4) - 0.5) * 0.18
wu = (x * threads + wobble * 3) % 1.0
wv = (y * threads + (noise(beta=2.4) - 0.5) * 0.5) % 1.0
warp = np.sin(np.pi * wu) ** 0.7                       # thread profile across a warp thread
weft = np.sin(np.pi * wv) ** 0.7
cell = (np.floor(x * threads + wobble * 3) + np.floor(y * threads)) % 2
height = np.where(cell > 0, warp * (0.6 + 0.4 * weft), weft * (0.6 + 0.4 * warp))
fibre = noise(beta=1.2, scale=(1.0, 6.0)) * 0.5 + noise(beta=1.2, scale=(6.0, 1.0)) * 0.5
height = height * 0.85 + fibre * 0.15
blotch = noise(beta=2.6)
colour = mix(height * 0.75 + fibre * 0.25, (82, 60, 36), (196, 160, 112)) * (0.75 + 0.5 * blotch[..., None])
save('burlap', colour, height, 3.0, 0.95)

# ------------------------------------------------------------ suede: soft fine nap, mottled (the tied pouch)
nap = noise(beta=0.9)
mottle = noise(beta=2.8)
streak = noise(beta=1.6, scale=(1.0, 5.0))
height = nap * 0.4 + streak * 0.4 + mottle * 0.2
colour = mix(mottle * 0.6 + nap * 0.25 + streak * 0.15, (120, 86, 46), (214, 170, 104))
save('suede', colour, height, 2.0, 0.9)

# ------------------------------------------------------------ rope: three twisted strands, diagonal lay (v along)
strands = 6                                           # strand crossings per repeat along v
phase = (y * strands + x * 3) % 1.0                    # u around the rope (3 strands)
height = np.sin(np.pi * phase) ** 0.6
fibre = noise(beta=1.0, scale=(4.0, 1.0))
height = height * 0.85 + fibre * 0.15
colour = mix(height * 0.8 + fibre * 0.2, (70, 74, 82), (206, 210, 216))
save('rope', colour, height, 5.0, 0.85)

# ------------------------------------------------------------ straw litter: straw, twigs, grit (trash heap mound)
straw_h, straw_tone = wrap_strokes(2600, (10, 46), (1, 3), np.pi, 0.0, (110, 255))
twig_h, twig_tone = wrap_strokes(240, (24, 90), (2, 5), np.pi, 0.0, (140, 255))
grit = noise(beta=0.6)
pebble = blobs(420, (1.5, 5.0), soft=1.0)
height = np.maximum(np.maximum(straw_h, twig_h * 0.9), pebble * 0.7) + grit * 0.1
dirt = mix(noise(beta=2.2), (26, 22, 16), (58, 48, 34))
straw_col = mix(straw_tone, (120, 104, 70), (214, 196, 150))
twig_col = mix(twig_tone, (52, 40, 28), (120, 98, 70))
pebble_col = mix(noise(beta=1.0), (60, 58, 56), (130, 124, 116))
colour = dirt
colour = colour * (1 - pebble[..., None] * 0.9) + pebble_col * pebble[..., None] * 0.9
colour = np.where((twig_h > 0.05)[..., None], twig_col, colour)
colour = np.where((straw_h > 0.05)[..., None], straw_col * (0.55 + 0.45 * straw_h[..., None]), colour)
colour *= (0.4 + 0.6 * wrap_blur(height, 2.0) ** 0.7)[..., None]      # gaps between stalks fall into shadow
save('straw', colour, height, 8.0, 0.95)

# ------------------------------------------------------------ rust: pitted rusty iron
pits = noise(beta=1.1)
scale_n = noise(beta=2.3)
height = scale_n * 0.6 + pits * 0.4
colour = mix(scale_n * 0.7 + pits * 0.3, (60, 30, 16), (168, 92, 46))
dark = (noise(beta=2.0) > 0.62)[..., None]
colour = np.where(dark, colour * 0.45, colour)
save('rust', colour, height, 4.0, 0.85, 0.25)

# ------------------------------------------------------------ rag: grimy loose-weave cloth
threads = 48
height = 0.5 + 0.25 * np.sin(2 * np.pi * x * threads) * np.sin(2 * np.pi * y * threads)
grime = noise(beta=2.4)
height = height * 0.7 + noise(beta=1.2) * 0.3
colour = mix(grime * 0.8 + height * 0.2, (70, 62, 50), (176, 162, 136))
save('rag', colour, height, 3.0, 0.95)

# ------------------------------------------------------------ crockery: glazed earthenware, broken edges darker
glaze = noise(beta=2.6)
height = noise(beta=1.4) * 0.3
colour = mix(glaze, (150, 96, 60), (200, 150, 104))
save('crockery', colour, height, 1.5, 0.45)

# ------------------------------------------------------------ mushroom caps (u around, v along the profile)
# Brown parasol: fine dark flecks on a pale buff ground, flecks densest toward the centre (v small).
fleck = blobs(1800, (0.8, 2.6), soft=0.8)
ground = noise(beta=2.2)
height = fleck * 0.6 + noise(beta=1.0) * 0.2
colour = mix(ground, (176, 150, 120), (214, 196, 170))
colour = colour * (1 - fleck[..., None] * 0.75) + mix(ground, (58, 44, 30), (94, 74, 52)) * fleck[..., None] * 0.75
save('capbrown', colour, height, 3.0, 0.8)

# Orange: saturated orange skin with large irregular pale warts.
warts = np.clip(blobs(70, (6, 18), soft=2.5) * 1.5 - (noise(beta=1.4) * 0.6), 0, 1)
skin = noise(beta=2.4)
height = warts * 0.8 + noise(beta=1.0) * 0.1
colour = mix(skin, (196, 92, 24), (236, 148, 52))
colour = colour * (1 - warts[..., None]) + mix(noise(beta=1.0), (196, 176, 150), (240, 230, 214)) * warts[..., None]
save('caporange', colour, height, 4.0, 0.6)

# Red fly agaric: glossy red with many small white dots.
dots = np.clip(blobs(520, (1.8, 4.2), soft=0.9) * 1.3, 0, 1)
skin = noise(beta=2.4)
height = dots * 0.8 + noise(beta=1.0) * 0.05
colour = mix(skin, (196, 58, 30), (242, 112, 66))
colour = colour * (1 - dots[..., None]) + mix(noise(beta=1.0), (210, 196, 186), (248, 242, 236)) * dots[..., None]
save('capred', colour, height, 4.0, 0.45)

# Gills: fine radial lamellae (lines along v, 128 per repeat in u).
lamella = np.abs(np.sin(np.pi * (x * 128 + (noise(beta=2.6) - 0.5) * 0.4)))
height = lamella ** 0.5
colour = mix(height * 0.8 + noise(beta=2.0) * 0.2, (70, 60, 52), (176, 162, 150))
save('gills', colour, height, 6.0, 0.85)

# Stem: off-white, fibrous along v with faint brown flecks and scales.
fibres = noise(beta=1.3, scale=(3.0, 0.15))
flecks = blobs(260, (0.8, 2.4), soft=0.8)
height = fibres * 0.7 + flecks * 0.3
colour = mix(fibres, (178, 166, 146), (238, 232, 218))
colour = colour * (1 - flecks[..., None] * 0.6) + linear((110, 86, 60)) * flecks[..., None] * 0.6
save('stem', colour, height, 3.0, 0.8)

# ------------------------------------------------------------ crystal: dark violet glass with angular facets
facets = np.zeros((N, N))
for _ in range(10):
    kx, ky = rng.integers(-3, 4, 2)                   # integer directions keep the lines periodic
    if kx == 0 and ky == 0:
        continue
    d = (x * kx + y * ky - rng.uniform(0, 1)) % 1.0
    facets += (d < 0.010) * rng.uniform(0.15, 0.4)
facets = np.clip(wrap_blur(facets, 0.8), 0, 1)
body = noise(beta=2.4)
height = body * 0.4 + facets * 0.6
colour = mix(body, (30, 24, 44), (96, 80, 124))
colour = colour * (1 - facets[..., None]) + linear((210, 200, 230)) * facets[..., None]
save('crystal', colour, height, 2.0, 0.35)

# ------------------------------------------------------------ staves: 8 vertical planks per repeat (u across), grain
# along v, dark gaps and a few knots; warm mid brown with some blue left in it (the bucket's tint needs room).
planks = 8
plank_index = np.floor(x * planks)
across = (x * planks) % 1.0
gap = np.clip(1.0 - np.minimum(across, 1.0 - across) / 0.035, 0, 1)
shade = (rng.uniform(0.75, 1.15, planks))[plank_index.astype(int) % planks]
grain = noise(beta=1.6, scale=(1.0, 0.04)) * 0.6 + noise(beta=1.0, scale=(1.0, 0.1)) * 0.4
grain = np.clip((grain - 0.5) * 1.8 + 0.5, 0, 1)
knots = blobs(10, (3, 7), soft=2.0)
height = (1.0 - gap) * 0.8 + grain * 0.2 - knots * 0.2
colour = mix(grain ** 1.4, (70, 40, 22), (214, 150, 92)) * shade[..., None]
colour = colour * (1 - knots[..., None] * 0.7)
colour = colour * (1 - gap[..., None] * 0.85)
save('staves', colour, height, 4.0, 0.75)

# ------------------------------------------------------------ end grain: pale sawn wood with rings (rims, plank ends)
rings_n = noise(beta=1.4, scale=(1.0, 0.1))
height = rings_n * 0.5 + noise(beta=1.0) * 0.5
colour = mix(rings_n * 0.7 + noise(beta=2.0) * 0.3, (150, 120, 90), (226, 204, 168))
save('endgrain', colour, height, 2.0, 0.8)
