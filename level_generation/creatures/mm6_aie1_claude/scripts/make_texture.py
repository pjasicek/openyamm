#!/usr/bin/env python3
"""Wind atlas and cone profile for the 3D air elemental, from the restored x2 standing frames (mm6_aie1/redo_2x).

Four 512-row bands, rows running from the top rim (band start) to the tip (band end):
1. Body (v 0..1/4). Each restored standing frame is unwrapped as a cylinder (row by row, about the row's own centre
   and silhouette radius); four frames each cover a quarter of the circumference with cos^2 crossfades, so the band
   tiles in u.
2. Outer wind: the body's pale streaks alone, smeared along the wind.
3. Dust: sparse wisps in the restored dust colours, for the thin rings outside the funnel.
4. Lightning: the bright discharge of the restored attack frames b, c and d, unwrapped about the standing silhouette at
   1.35 x its radius, so the branches that leave the body in the sprite sit on the bolt shells round it.

Alpha: the restored interior is opaque; the shell keeps the pale streaks dense and lets the dark smoky gaps show some
of the far side, so the body reads as moving air rather than a solid cone.

Tiers: textures/aie1_region_mask.png (R cool wind and lightning, G warm dust, by the restored materials.py hue rule)
and textures/aie1_ramps.json, ramps fitted to the restored package's own tier recolour (materials.recolor with its
native-palette curves, recolor_vectors.json) applied to this atlas: palettes 198 (aie1_a), 199 (aie1_b), 724 (aie1_c).

Writes textures/aie1_wind.png and textures/aie1_profile.json (silhouette per band row, in native logical pixels).
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent.parent
SOURCE = HERE.parent / 'mm6_aie1' / 'redo_2x' / 'aligned_2x'
MASKS = HERE.parent / 'mm6_aie1' / 'redo_2x' / 'masks_2x'
RESTORED = HERE.parent / 'mm6_aie1' / 'redo_2x'
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants  # noqa: E402
WIDTH, BAND = 1024, 512
PAD = 6
BODY_FRAMES = ['aie1fla', 'aie1flc', 'aie1fle', 'aie1flb']
# Unwrapped surface angle per circumference angle: each frame's third/quarter samples its face-on middle, away from
# the dusty silhouette where a cylinder unwrap smears.
SURFACE_ANGLE = 0.8
FRINGE_FRAMES = ['aie1fla', 'aie1flb', 'aie1flc', 'aie1fld', 'aie1fle', 'aie1flf']
LIGHTNING_FRAMES = ['aie1atc', 'aie1atb', 'aie1atc', 'aie1atd']
LIGHTNING_RADIUS = 1.35
VARIANTS = {'aie1_a': 198, 'aie1_b': 199, 'aie1_c': 724}
LUMA = np.array([0.2126, 0.7152, 0.0722])


def load(name):
    return np.asarray(Image.open(SOURCE / f'{name}.png').convert('RGBA'), dtype=np.float64) / 255.0


def smooth(values, radius):
    kernel = np.ones(2 * radius + 1) / (2 * radius + 1)
    padded = np.pad(values, radius, mode='edge')
    return np.convolve(padded, kernel, mode='valid')


def silhouette(image):
    """Per-row centre and radius of the dense body (alpha > 0.5), smoothed over the ragged wisps."""
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
    """Bilinear RGBA at float pixel coordinates."""
    h, w = image.shape[:2]
    x = np.clip(x, 0, w - 1.001)
    y = np.clip(y, 0, h - 1.001)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    a = image[y0, x0] * (1 - fx) + image[y0, x0 + 1] * fx
    b = image[y0 + 1, x0] * (1 - fx) + image[y0 + 1, x0 + 1] * fx
    return a * (1 - fy) + b * fy


def band_rows(top, bottom):
    """Source row for every band row; PAD transparent rows at each end keep the bands apart under filtering."""
    v = (np.arange(BAND) - PAD + 0.5) / (BAND - 2 * PAD)
    return top + np.clip(v, 0, 1) * (bottom - top), (v >= 0) & (v <= 1)


def unwrap(frames, radius_scale=1.0, shape_frame=None):
    """Cylinder unwrap of `frames` round the circumference (a quarter each, cos^2 crossfades). The silhouette comes
    from each frame itself, or from `shape_frame` (same canvas) when the frames' own outline is not the body's.
    Returns colour (weighted by alpha) and alpha."""
    accum = np.zeros((BAND, WIDTH, 4))
    weights = np.zeros((BAND, WIDTH, 1))
    theta = (np.arange(WIDTH) + 0.5) / WIDTH * 2 * np.pi
    shape = silhouette(load(shape_frame)) if shape_frame is not None else None
    for index, name in enumerate(frames):
        image = load(name)
        top, bottom, centre, radius = shape if shape is not None else silhouette(image)
        source_y, inside = band_rows(top, bottom)
        row = np.clip(np.round(source_y - top).astype(int), 0, len(centre) - 1)
        local = (theta - (index + 0.5) * 2 * np.pi / len(frames) + np.pi) % (2 * np.pi) - np.pi
        weight = np.where(np.abs(local) < np.pi / 2, np.cos(local) ** 2, 0.0)
        surface = SURFACE_ANGLE * np.clip(local, -np.pi / 2, np.pi / 2)
        x = centre[row][:, None] + radius_scale * radius[row][:, None] * np.sin(surface)[None, :]
        y = np.broadcast_to(source_y[:, None], x.shape)
        rgba = sample(image, x, y)
        rgba[~inside] = 0
        w = weight[None, :, None] * rgba[..., 3:4]
        accum[..., :3] += w * rgba[..., :3]
        accum[..., 3:] += weight[None, :, None] * rgba[..., 3:4]
        weights += w
    rgb = accum[..., :3] / np.maximum(weights, 1e-6)
    total = np.zeros(WIDTH)
    for index in range(len(frames)):
        local = (theta - (index + 0.5) * 2 * np.pi / len(frames) + np.pi) % (2 * np.pi) - np.pi
        total += np.where(np.abs(local) < np.pi / 2, np.cos(local) ** 2, 0.0)
    return rgb, np.clip(accum[..., 3] / total[None, :], 0, 1)


def body_band():
    rgb, alpha = unwrap(BODY_FRAMES)
    # Pale streaks stay dense; the darkest smoke lets about a quarter of the far side through (four layers overlap):
    # the sprite's body is dark smoke, and thinner smoke turned milky against a bright sky.
    luminance = rgb @ LUMA
    density = np.clip(0.75 + (luminance - 0.1) * 1.2, 0.75, 0.95)
    return np.concatenate([rgb, (alpha * density)[..., None]], axis=-1)


def streaks(body, turn, smear, threshold=0.22):
    """The body band's pale streaks alone (alpha by luminance), `turn` of a revolution round, smeared along u by a
    wrapping box of `smear` texels so they trail as the layer spins. Premultiplied RGBA."""
    rgba = np.roll(body, int(WIDTH * turn), axis=1)
    luminance = rgba[..., :3] @ LUMA
    alpha = rgba[..., 3] * np.clip((luminance - threshold) / 0.25, 0, 1)
    premultiplied = np.concatenate([rgba[..., :3] * alpha[..., None], alpha[..., None]], axis=-1)
    smeared = np.zeros_like(premultiplied)
    for shift in range(-(smear // 2), smear // 2 + 1):
        smeared += np.roll(premultiplied, shift, axis=1)
    return smeared / (2 * (smear // 2) + 1)


def unpremultiply(premultiplied, gain):
    covered = premultiplied[..., 3:4] > 1e-4
    rgb = np.where(covered, premultiplied[..., :3] / np.maximum(premultiplied[..., 3:4], 1e-4), 0)
    return np.concatenate([rgb, np.clip(premultiplied[..., 3:4] * gain, 0, 1)], axis=-1)


def fringe_band(body):
    """Outer wind: the pale streaks half a turn round, lightly smeared."""
    return unpremultiply(streaks(body, 0.5, 9, threshold=0.35), 1.2)


def dust_colours():
    """Dark and light dust colour of the restored frames: the warm-dust mask region (masks_2x green), 25th and 85th
    luminance percentiles."""
    pixels = []
    for name in FRINGE_FRAMES:
        image = load(name)
        mask = np.asarray(Image.open(MASKS / f'{name}.png').convert('RGBA'), dtype=np.float64) / 255.0
        pixels.append(image[(mask[..., 1] > 0.5) & (image[..., 3] > 0.5)][:, :3])
    pixels = np.concatenate(pixels)
    order = np.argsort(pixels @ LUMA)
    return pixels[order[int(len(order) * 0.25)]], pixels[order[int(len(order) * 0.85)]]


def dust_band(body):
    """Dust wisps for the thin outer rings: sparse streaks a third of a turn round, recoloured with the restored
    dust colours by their own brightness and smeared further."""
    premultiplied = streaks(body, 1.0 / 3.0, 13, threshold=0.28)
    rgba = unpremultiply(premultiplied, 1.6)
    dark, light = dust_colours()
    t = np.clip((rgba[..., :3] @ LUMA - 0.2) / 0.5, 0, 1)[..., None]
    rgba[..., :3] = dark * (1 - t) + light * 1.35 * t
    return rgba


def lightning_band():
    """The attack discharge: restored texels brighter than any standing streak (standing frames peak near 0.81)."""
    rgb, alpha = unwrap(LIGHTNING_FRAMES, LIGHTNING_RADIUS, shape_frame='aie1fla')
    bolt = np.clip((rgb @ LUMA - 0.8) / 0.12, 0, 1)
    return np.concatenate([rgb, (alpha * bolt)[..., None]], axis=-1)


def load_restored_materials():
    spec = importlib.util.spec_from_file_location('aie1_materials', RESTORED / 'materials.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tiers(atlas, out):
    """Region mask and per-tier ramps. The restored hue rule splits cool from warm on the bled colour, so the mask is
    padded into transparent texels like the colour; ramps are fitted over visible texels only."""
    materials = load_restored_materials()
    vectors = {int(k): v for k, v in json.loads((RESTORED / 'recolor_vectors.json').read_text()).items()}
    image = Image.fromarray(np.round(np.clip(atlas, 0, 1) * 255).astype(np.uint8), 'RGBA')
    opaque = np.asarray(image).copy()
    opaque[..., 3] = 255
    mask = materials.coverage(Image.fromarray(opaque, 'RGBA'))
    weights = np.asarray(mask, dtype=np.float64)[..., :2] / 255.0
    base = np.asarray(image, dtype=np.float64)[..., :3] / 255.0
    targets = {}
    for variant, palette in VARIANTS.items():
        recoloured = materials.recolor(Image.fromarray(opaque, 'RGBA'), mask, palette, None, vectors)
        targets[variant] = np.asarray(recoloured, dtype=np.float64)[..., :3] / 255.0
    visible = atlas[..., 3] > 0.1
    ramps = {variant: [] for variant in VARIANTS}
    report = {}
    for channel, name in enumerate(('cool', 'warm')):
        fitted, error = region_variants.fit_ramps(base, targets, weights[..., channel] * visible)
        for variant in VARIANTS:
            ramps[variant].append(fitted[variant])
        report[name] = error
    region_variants.write_mask([weights[..., 0], weights[..., 1]], out / 'aie1_region_mask.png',
                               size=(WIDTH // 2, atlas.shape[0] // 2))
    config = {'variants': list(VARIANTS),
              'palettes': VARIANTS,
              'fit_report': report,
              'materials': [{'base': 'AirElemental_Wind', 'prefix': 'AirElemental', 'mask': 'aie1_region_mask.png',
                             'ramps': ramps}]}
    (out / 'aie1_ramps.json').write_text(json.dumps(config, indent=1))
    return report


def bleed(rgba, passes=24):
    """Spread colour into transparent texels so filtering does not darken edges (alpha unchanged)."""
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


def profile():
    """Mean silhouette of the six standing frames, in native logical pixels above the canvas bottom."""
    rows = []
    for name in FRINGE_FRAMES:
        image = load(name)
        top, bottom, centre, radius = silhouette(image)
        source_y, _ = band_rows(top, bottom)
        v = np.linspace(0, 1, 25)
        y = top + v * (bottom - top)
        index = np.clip(np.round(y - top).astype(int), 0, len(radius) - 1)
        rows.append(np.stack([(image.shape[0] - y) / 2, radius[index] / 2, (centre[index] - image.shape[1] / 2) / 2]))
    mean = np.mean(rows, axis=0)
    return {'v': np.linspace(0, 1, 25).tolist(), 'height_px': mean[0].tolist(), 'radius_px': mean[1].tolist(),
            'offset_px': mean[2].tolist(), 'native_frame_scale': 0.599991}


def main():
    body = body_band()
    atlas = np.concatenate([bleed(body), bleed(fringe_band(body)), bleed(dust_band(body)), bleed(lightning_band())],
                           axis=0)
    out = HERE / 'textures'
    out.mkdir(exist_ok=True)
    Image.fromarray(np.round(np.clip(atlas, 0, 1) * 255).astype(np.uint8), 'RGBA').save(out / 'aie1_wind.png')
    (out / 'aie1_profile.json').write_text(json.dumps(profile(), indent=1))
    print('wrote', out / 'aie1_wind.png')
    print('tier fit (8-bit error):', json.dumps(tiers(np.round(np.clip(atlas, 0, 1) * 255) / 255.0, out)))


if __name__ == '__main__':
    main()
