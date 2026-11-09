#!/usr/bin/env python3
"""Textures and measurements for the 3D fire elemental, from the restored x2 frames (mm6_fie1/redo_2x).

textures/fie1_flame.png (1024 x 512, tiles in u and v): the flame cage. Six front and back walk frames are unwrapped
as cylinders round the circumference (row by row about each row's own centre and silhouette radius; narrow
crossfades so each slot keeps a crisp lattice), over the cylindrical middle of the cage (12-88 % of its height).
The band is 1.25 tiles long and its first quarter is crossfaded with the rows one tile further on, so it repeats
seamlessly in v and the cage can scroll upward. The restored package's core mask (materials.coverage: the dark red
figure seen through the cage) becomes transparent: the 3D figure shows through those gaps. A cage shell shows two
layers (its far inside and its near outside) where the sprite shows one composite of a front and a back lattice:
the tile keeps the lattice only under a smooth random mask that tiles and covers MASK_COVERAGE of it, so the near and
far sides (different parts of the tile) each carry part of the lattice, and the sprite's gaps stay open where both
are open. Without it the sides filled each other's gaps and hid the figure (sprite interiors are about 28 %
see-through: 11 % gaps, 17 % figure).

textures/fie1_fringe.png (1024 x 512, tiles in v like the cage): eight 128-texel strips, each the outer flames and
licks of one side of a cage frame, sampled along each row from FRINGE_INNER to FRINGE_OUTER times the row's
silhouette radius (fading in over the inner part; strips starting inside the silhouette carried its dense flame band, which near
edge-on fins in front of the body drew as vertical streaks). build_model.py hangs them on radial fins,
which face the camera exactly where they form the silhouette, so the outline shows the sprite's own flame tongues.

textures/fie1_fx.png (1024 x 1024, four 512 quadrants): hand burst (attack frame c, left hand, alpha by a radial
falloff), star flash (death frame d), sparks (death frame e) and embers (death frame f), each centred on the frame's
brightest point.

textures/fie1_body_colors.json: the core figure's colour stops (luminance percentiles of the restored core pixels),
which build_model.py bakes into the figure's texture.

textures/fie1_profile.json: the cage silhouette (mean of the same front/back frames plus the standing frame) in
native logical pixels above the canvas bottom, and the band mapping (the tile's share of the cage height).
"""
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent.parent
RESTORED = HERE.parent / 'mm6_fie1' / 'redo_2x'
SOURCE = RESTORED / 'aligned_2x'
WIDTH, TILE = 1024, 512
BAND_START, BAND_END = 0.12, 0.88
OVERLAP = 0.25
SURFACE_ANGLE = 0.8
# Crossfade sharpness: weights cos^(2 x SHARPNESS) keep each slot's own lattice over most of its width.
SHARPNESS = 4
MASK_COVERAGE = 0.92
# Semi-transparent flame edges washed out over bright ground in game (2026-10-13 check): their alpha is raised.
LATTICE_ALPHA_GAIN = 1.3
FRINGE_INNER, FRINGE_FADE, FRINGE_OUTER = 1.0, 1.08, 1.6
FRINGE_STRIP = 128
FRINGE_SOURCES = [('fie1fla0', -1), ('fie1fla0', 1), ('fie1flc0', -1), ('fie1flc0', 1), ('fie1fle0', -1),
                  ('fie1fle0', 1), ('fie1flb4', -1), ('fie1fld4', 1)]
MASK_FEATURE = 40.0     # texels: about the size of a lattice cell
MASK_SOFTNESS = 0.08
CAGE_FRAMES = ['fie1fla0', 'fie1flb4', 'fie1flc0', 'fie1fld4', 'fie1fle0', 'fie1flf4']
PROFILE_FRAMES = ['fie1fla0', 'fie1flb0', 'fie1flc0', 'fie1fld0', 'fie1fle0', 'fie1flf0',
                  'fie1fla4', 'fie1flb4', 'fie1flc4', 'fie1fld4', 'fie1fle4', 'fie1flf4', 'fie1ata0']
LUMA = np.array([0.2126, 0.7152, 0.0722])
NATIVE_FRAME_SCALE = 0.699997


def load(name):
    return np.asarray(Image.open(SOURCE / f'{name}.png').convert('RGBA'), dtype=np.float64) / 255.0


def load_restored_materials():
    spec = importlib.util.spec_from_file_location('fie1_materials', RESTORED / 'materials.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MATERIALS = load_restored_materials()


def core(name):
    image = Image.open(SOURCE / f'{name}.png').convert('RGBA')
    return np.asarray(MATERIALS.coverage(image), dtype=np.float64) / 255.0


def smooth(values, radius):
    kernel = np.ones(2 * radius + 1) / (2 * radius + 1)
    return np.convolve(np.pad(values, radius, mode='edge'), kernel, mode='valid')


def silhouette(image):
    """Per-row centre and radius of the cage (alpha > 0.5), smoothed over the ragged flame tips."""
    alpha = image[..., 3]
    rows = np.where((alpha > 0.5).sum(axis=1) > 6)[0]
    top, bottom = rows[0], rows[-1]
    centre, radius = [], []
    for y in range(top, bottom + 1):
        xs = np.where(alpha[y] > 0.5)[0]
        if len(xs) < 2:
            xs = np.array([alpha.shape[1] // 2 - 1, alpha.shape[1] // 2 + 1])
        left, right = np.percentile(xs, 3), np.percentile(xs, 97)
        centre.append((left + right) / 2)
        radius.append(max((right - left) / 2, 1.0))
    return top, bottom, smooth(np.array(centre), 12), smooth(np.array(radius), 12)


def sample(image, x, y):
    """Bilinear sample at float pixel coordinates (any channel count)."""
    h, w = image.shape[:2]
    x = np.clip(x, 0, w - 1.001)
    y = np.clip(y, 0, h - 1.001)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = x - x0, y - y0
    if image.ndim == 3:
        fx, fy = fx[..., None], fy[..., None]
    a = image[y0, x0] * (1 - fx) + image[y0, x0 + 1] * fx
    b = image[y0 + 1, x0] * (1 - fx) + image[y0 + 1, x0 + 1] * fx
    return a * (1 - fy) + b * fy


def cage_band():
    """Cylinder unwrap of the cage frames over 1.25 tiles of rows: premultiplied colour and lattice alpha."""
    rows = int(TILE * (1 + OVERLAP))
    theta = (np.arange(WIDTH) + 0.5) / WIDTH * 2 * np.pi
    slots = len(CAGE_FRAMES)
    accum = np.zeros((rows, WIDTH, 3))
    alpha_sum = np.zeros((rows, WIDTH))
    total = np.zeros(WIDTH)
    for index, name in enumerate(CAGE_FRAMES):
        image = load(name)
        top, bottom, centre, radius = silhouette(image)
        t = BAND_START + (np.arange(rows) + 0.5) / rows * (BAND_END - BAND_START)
        source_y = top + t * (bottom - top)
        row = np.clip(np.round(source_y - top).astype(int), 0, len(centre) - 1)
        local = (theta - (index + 0.5) * 2 * np.pi / slots + np.pi) % (2 * np.pi) - np.pi
        reach = np.pi / slots * 2
        weight = np.where(np.abs(local) < reach, np.cos(local / reach * np.pi / 2) ** (2 * SHARPNESS), 0.0)
        surface = SURFACE_ANGLE * np.clip(local / reach * np.pi / 2, -np.pi / 2, np.pi / 2)
        x = centre[row][:, None] + radius[row][:, None] * np.sin(surface)[None, :]
        y = np.broadcast_to(source_y[:, None], x.shape)
        rgba = sample(image, x, y)
        lattice = rgba[..., 3] * (1 - sample(core(name), x, y))
        accum += weight[None, :, None] * lattice[..., None] * rgba[..., :3]
        alpha_sum += weight[None, :] * lattice
        total += weight
    alpha = alpha_sum / total[None, :]
    premultiplied = accum / total[None, :, None]
    return premultiplied, alpha


def fringe():
    """Outer flame strips (premultiplied colour and alpha over 1.25 tiles of rows), one per source frame side; column
    0 is the inner end (FRINGE_INNER x radius), the last the outer (FRINGE_OUTER)."""
    rows = int(TILE * (1 + OVERLAP))
    premultiplied = np.zeros((rows, FRINGE_STRIP * len(FRINGE_SOURCES), 3))
    alpha = np.zeros((rows, FRINGE_STRIP * len(FRINGE_SOURCES)))
    reach = FRINGE_INNER + (FRINGE_OUTER - FRINGE_INNER) * (np.arange(FRINGE_STRIP) + 0.5) / FRINGE_STRIP
    fade = np.clip((reach - FRINGE_INNER) / (FRINGE_FADE - FRINGE_INNER), 0, 1)
    for index, (name, side) in enumerate(FRINGE_SOURCES):
        image = load(name)
        top, bottom, centre, radius = silhouette(image)
        t = BAND_START + (np.arange(rows) + 0.5) / rows * (BAND_END - BAND_START)
        source_y = top + t * (bottom - top)
        row = np.clip(np.round(source_y - top).astype(int), 0, len(centre) - 1)
        x = centre[row][:, None] + side * radius[row][:, None] * reach[None, :]
        y = np.broadcast_to(source_y[:, None], x.shape)
        rgba = sample(image, x, y)
        a = rgba[..., 3] * (1 - sample(core(name), x, y)) * fade[None, :]
        columns = slice(index * FRINGE_STRIP, (index + 1) * FRINGE_STRIP)
        premultiplied[:, columns] = rgba[..., :3] * a[..., None]
        alpha[:, columns] = a
    return premultiplied, alpha


def tile(premultiplied, alpha, mask=True):
    """Fold the 1.25-tile band into one tile that repeats in v (rows run from the cage top down)."""
    overlap = TILE * OVERLAP
    y = np.arange(TILE)
    w = np.clip(y / overlap, 0, 1)
    shifted = np.minimum(y + TILE, len(alpha) - 1)
    colour = premultiplied[y] * w[:, None, None] + premultiplied[shifted] * (1 - w[:, None, None])
    coverage = alpha[y] * w[:, None] + alpha[shifted] * (1 - w[:, None])
    rgb = np.where(coverage[..., None] > 1e-4, colour / np.maximum(coverage[..., None], 1e-4), 0)
    if mask:
        coverage = np.clip(coverage * LATTICE_ALPHA_GAIN, 0, 1) * layer_mask(coverage.shape)
    return np.concatenate([rgb, coverage[..., None]], axis=-1)


def layer_mask(shape):
    """Smooth periodic random field (Gaussian-filtered white noise in the frequency domain, so it tiles), thresholded
    to cover MASK_COVERAGE with soft edges."""
    rng = np.random.default_rng(6)
    noise = rng.standard_normal(shape)
    fy = np.fft.fftfreq(shape[0])[:, None]
    fx = np.fft.fftfreq(shape[1])[None, :]
    field = np.real(np.fft.ifft2(np.fft.fft2(noise) * np.exp(-2 * (np.pi * MASK_FEATURE) ** 2 * (fx ** 2 + fy ** 2))))
    field = (field - field.mean()) / field.std()
    threshold = np.quantile(field, 1 - MASK_COVERAGE)
    return np.clip((field - threshold) / MASK_SOFTNESS + 0.5, 0, 1)


def bleed(rgba, passes=24):
    """Spread colour into transparent texels so filtering does not darken edges (alpha unchanged; wraps)."""
    rgb, alpha = rgba[..., :3].copy(), rgba[..., 3]
    known = alpha > 0.02
    for _ in range(passes):
        if known.all():
            break
        total = np.zeros_like(rgb)
        count = np.zeros(alpha.shape)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            shifted_known = np.roll(np.roll(known, dy, 0), dx, 1)
            total += np.roll(np.roll(rgb, dy, 0), dx, 1) * shifted_known[..., None]
            count += shifted_known
        grow = ~known & (count > 0)
        rgb[grow] = total[grow] / count[grow][:, None]
        known = known | grow
    return np.concatenate([rgb, alpha[..., None]], axis=-1)


def crop(image, cx, cy, size, out, falloff=None):
    """Square crop centred at (cx, cy), resized to out x out; optional radial alpha falloff (start, end) as
    fractions of the half size."""
    half = size / 2
    grid = (np.arange(out) + 0.5) / out * size - half
    x = cx + grid[None, :] + np.zeros((out, 1))
    y = cy + grid[:, None] + np.zeros((1, out))
    inside = (x >= 0) & (x < image.shape[1]) & (y >= 0) & (y < image.shape[0])
    rgba = sample(image, x, y)
    rgba[~inside] = 0
    if falloff is not None:
        r = np.hypot(x - cx, y - cy) / half
        rgba[..., 3] *= np.clip((falloff[1] - r) / (falloff[1] - falloff[0]), 0, 1)
    return rgba


def brightest(image):
    luminance = image[..., :3] @ LUMA * image[..., 3]
    ys, xs = np.where(luminance > 0.9 * luminance.max())
    return xs.mean(), ys.mean()


def fx_atlas():
    quadrant = 512
    atlas = np.zeros((1024, 1024, 4))
    # Hand burst: the left-hand ball of attack frame c (2x pixels about (128, 226)); the cage flames round it fade
    # out with the radial falloff and the figure seen through it (core mask) is cut out.
    image = load('fie1atc0')
    image[..., 3] *= 1 - core('fie1atc0')
    atlas[:quadrant, :quadrant] = crop(image, 128, 226, 124, quadrant, falloff=(0.4, 0.95))
    for (row, col), name in (((0, 1), 'fie1ded0'), ((1, 0), 'fie1dee0'), ((1, 1), 'fie1def0')):
        image = load(name)
        cx, cy = brightest(image)
        atlas[row * quadrant:(row + 1) * quadrant, col * quadrant:(col + 1) * quadrant] = \
            crop(image, cx, cy, 500, quadrant, falloff=(0.85, 1.0))
    return atlas


def body_colors():
    """Colour stops of the restored figure: luminance percentiles of strongly core-masked pixels."""
    pixels = []
    for name in PROFILE_FRAMES + ['fie1atc0']:
        image = load(name)
        mask = core(name)
        pixels.append(image[(mask > 0.8) & (image[..., 3] > 0.9)][:, :3])
    pixels = np.concatenate(pixels)
    order = np.argsort(pixels @ LUMA)
    stops = [5, 30, 60, 90, 99]
    return {'percentiles': stops,
            'colors': [np.median(pixels[order[max(0, int(len(order) * p / 100) - 200):
                                              int(len(order) * p / 100) + 200]], axis=0).tolist() for p in stops]}


def profile():
    rows = []
    for name in PROFILE_FRAMES:
        image = load(name)
        top, bottom, centre, radius = silhouette(image)
        y = top + np.linspace(0, 1, 25) * (bottom - top)
        index = np.clip(np.round(y - top).astype(int), 0, len(radius) - 1)
        rows.append(np.stack([(image.shape[0] - y) / 2, radius[index] / 2, (centre[index] - image.shape[1] / 2) / 2]))
    mean = np.mean(rows, axis=0)
    return {'v': np.linspace(0, 1, 25).tolist(), 'height_px': mean[0].tolist(), 'radius_px': mean[1].tolist(),
            'offset_px': mean[2].tolist(), 'native_frame_scale': NATIVE_FRAME_SCALE,
            'fringe': {'inner': FRINGE_INNER, 'outer': FRINGE_OUTER, 'strips': len(FRINGE_SOURCES)},
            # One texture tile covers this share of the cage height (band 12-88 % over 1.25 tiles).
            'tile_share': (BAND_END - BAND_START) / (1 + OVERLAP)}


def save(rgba, path):
    Image.fromarray(np.round(np.clip(rgba, 0, 1) * 255).astype(np.uint8), 'RGBA').save(path)


def main():
    out = HERE / 'textures'
    out.mkdir(exist_ok=True)
    save(bleed(tile(*cage_band())), out / 'fie1_flame.png')
    save(bleed(fx_atlas()), out / 'fie1_fx.png')
    save(bleed(tile(*fringe(), mask=False)), out / 'fie1_fringe.png')
    (out / 'fie1_body_colors.json').write_text(json.dumps(body_colors(), indent=1))
    (out / 'fie1_profile.json').write_text(json.dumps(profile(), indent=1))
    print('wrote', sorted(p.name for p in out.iterdir()))


if __name__ == '__main__':
    main()
