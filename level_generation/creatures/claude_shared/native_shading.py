#!/usr/bin/env python3
"""Native shading transfer: carry a sprite's prerendered shading and palette colours onto a 3D creature texture.

Technique, decision rules and trade-offs: ../NATIVE_SHADING_TRANSFER.md. First used on the MM6 Patrol Unit
(mm6_rob1_claude/), where it fixed a flat, washed-out look that global gains could not.

Three parts, each usable on its own:

1. measure (CLI or `measure(config)`): from native frames in several palettes, sample pixels in the central band of
   each view (away from the silhouette rim), give each a body coordinate and a region, and write
   - <out>/profile.json: median sRGB luminance of the reference palette per coordinate bin, overall and per region;
   - <out>/pixels.npz: the same pixels in every palette (aligned), their coordinate and region label;
   - <out>/profile.png: the overall profile as a grey strip (top of the image = top of the body).
   Coordinates: "elevation" (degrees on a sphere around the body centre, corrected by the sprites' camera elevation;
   for round, upright bodies) or "height" (0 at the lowest opaque row, 1 at the highest; for any upright body).
   Regions: coordinate bands from the config, or the restored region masks (`region_masks`) when their channels
   follow the parts (they did not on the robot; they do on the flying eye).
2. `shade(base, coord, region, profile, ...)`: in a compose script, replace the base colour inside a region by the
   native brightness at each texel's coordinate (grey) times the base's own local detail (a high-pass ratio), blended
   with the original by `amount`.
3. `transfer_ramps(...)`: region ramps (claude_shared/region_variants.py format) whose colours come from the aligned
   native pixels: for each stop, the reference-palette pixels nearest in luminance, read in each tier's palette.

Config for measure (JSON):
{
  "sprites": "level_generation/creatures/mm6_rob1",      # folder with native_variants/<frame>_<palette>.png
  "frames": ["rob1fla2", "rob1fla3", "rob1fla4"],         # views without front-only features
  "palettes": [810, 811, 812], "reference": 810,
  "coordinate": "elevation",                              # or "height"
  "camera_elevation": 8.6,                                # degrees, elevation mode (number or {frame: degrees}),
  "camera_reference": {"elevation": 0, "channel": 0,      # ...or measured per view from a band at a known
                       "ratio": 2.0, "minimum": 0.3},     # elevation whose pixels have one dominant channel
  "central_band": 0.5,                                    # fraction of each row's half width kept
  "bin": 2,
  "regions": {"belt": [[-6.5, 6.5]], "rings": [[6.5, 30], [-30, -6.5]], "caps": [[30, 91], [-91, -30]]},
  # ...or regions from the restored masks when they follow the parts (check first; the robot's did not):
  # "region_masks": {"folder": "masks_2x", "channels": {"skin": 0, "face": 1}, "threshold": 0.6},
  "out": "level_generation/creatures/mm6_rob1_claude/work/native_shading"
}
Usage: native_shading.py measure <config.json>   (paths relative to the repository root)"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

LUMA = np.array([0.2126, 0.7152, 0.0722])
REPO = Path(__file__).resolve().parents[3]


def srgb_to_linear(value):
    value = np.asarray(value, dtype=np.float64)
    return np.where(value <= 0.04045, value / 12.92, ((value + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(value):
    value = np.maximum(np.asarray(value, dtype=np.float64), 0)
    return np.where(value <= 0.0031308, value * 12.92, 1.055 * value ** (1 / 2.4) - 0.055)


def srgb_luminance(rgb):
    """Luminance of sRGB colours, returned as an sRGB grey value (what a grey texel must hold to match)."""
    return linear_to_srgb(srgb_to_linear(rgb) @ LUMA)


# --------------------------------------------------------------------------------------------- measure

def _load(path):
    return np.asarray(Image.open(path).convert('RGBA'), np.float64) / 255


def _sphere(alpha):
    """Centre and radius of a round body: the widest row sets the radius (narrow parts above, such as antennae or
    sensor heads, do not), the lowest opaque row its bottom."""
    rows = np.nonzero(alpha.any(1))[0]
    widths = np.array([np.ptp(np.nonzero(r)[0]) if r.any() else 0 for r in alpha])
    radius = widths.max() / 2
    xs = np.nonzero(alpha[np.argmax(widths)])[0]
    return (xs.min() + xs.max()) / 2, rows.max() - radius, radius


def camera_elevation(frame, reference):
    """Sprite camera elevation in degrees from a band at a known elevation (elevation mode): its pixels are those
    whose `channel` exceeds `minimum` and `ratio` times each other channel, near the body's vertical axis. A point on
    the meridian facing the camera at elevation e appears at asin(h) = e - camera."""
    alpha = frame[..., 3] > 0.5
    cx, cy, radius = _sphere(alpha)
    rgb = frame[..., :3]
    c = reference['channel']
    others = [rgb[..., i] for i in range(3) if i != c]
    hit = alpha & (rgb[..., c] > reference.get('minimum', 0.3))
    for other in others:
        hit &= rgb[..., c] > reference.get('ratio', 2.0) * other
    hit &= np.abs(np.arange(frame.shape[1])[None, :] - cx) < 0.4 * radius
    ys = np.nonzero(hit)[0]
    if len(ys) < 10:
        raise ValueError('camera_reference band not found')
    apparent = np.degrees(np.arcsin(np.clip((cy - np.median(ys)) / radius, -1, 1)))
    return float(reference.get('elevation', 0.0) - apparent)


def _sample_view(frame, mode, camera, band):
    """Central-band pixels of one view: (rows, cols, coordinates)."""
    alpha = frame[..., 3] > 0.5
    rows = np.nonzero(alpha.any(1))[0]
    if mode == 'elevation':
        cx, cy, radius = _sphere(alpha)
        y, x = np.nonzero(alpha)
        h = (cy - y) / radius
        keep = np.abs(h) < 0.98
        y, x, h = y[keep], x[keep], h[keep]
        half = np.sqrt(1 - h * h) * radius
        keep = np.abs(x - cx) < band * half
        return y[keep], x[keep], np.degrees(np.arcsin(h[keep])) + camera
    if mode == 'height':
        top, bottom = rows.min(), rows.max()
        ys, xs, coords = [], [], []
        for r in rows:
            cols = np.nonzero(alpha[r])[0]
            centre, half = (cols.min() + cols.max()) / 2, (cols.max() - cols.min()) / 2
            keep = cols[np.abs(cols - centre) < band * max(half, 1)]
            ys.append(np.full(len(keep), r)); xs.append(keep)
            coords.append(np.full(len(keep), (bottom - r) / max(bottom - top, 1)))
        return np.concatenate(ys), np.concatenate(xs), np.concatenate(coords)
    raise ValueError(f'unknown coordinate mode: {mode}')


def _region_labels(coords, regions):
    labels = np.full(len(coords), -1)
    for index, bands in enumerate(regions.values()):
        for lo, hi in bands:
            labels[(coords >= lo) & (coords < hi) & (labels < 0)] = index
    return labels


def _binned(coords, values, bins, step):
    med = np.full(len(bins), np.nan)
    for i, b in enumerate(bins):
        s = values[np.abs(coords - b) <= step * 0.75]
        if len(s) >= 4:
            med[i] = np.median(s)
    known = ~np.isnan(med)
    if not known.any():
        return med, known
    return np.interp(bins, bins[known], med[known]), known


def measure(config):
    sprites = REPO / config['sprites']
    mode = config['coordinate']
    palettes, reference = config['palettes'], config['reference']
    camera_config = config.get('camera_elevation', 0.0)
    band = float(config.get('central_band', 0.5))
    step = float(config.get('bin', 2 if mode == 'elevation' else 0.02))
    masks = config.get('region_masks')
    regions = {name: None for name in masks['channels']} if masks else config['regions']
    coords, colours, cameras, mask_labels = [], {p: [] for p in palettes}, {}, []
    for name in config['frames']:
        frames = {p: _load(sprites / 'native_variants' / f'{name}_{p}.png') for p in palettes}
        if mode != 'elevation':
            camera = 0.0
        elif 'camera_reference' in config:
            camera = camera_elevation(frames[reference], config['camera_reference'])
        else:
            camera = float(camera_config[name] if isinstance(camera_config, dict) else camera_config)
        cameras[name] = round(camera, 2)
        y, x, c = _sample_view(frames[reference], mode, camera, band)
        if masks:
            mask = _load(sprites / masks['folder'] / f'{name}.png')
            fy, fx = mask.shape[0] // frames[reference].shape[0], mask.shape[1] // frames[reference].shape[1]
            mask = mask[:fy * frames[reference].shape[0], :fx * frames[reference].shape[1]]
            mask = mask.reshape(frames[reference].shape[0], fy, frames[reference].shape[1], fx, 4).mean((1, 3))
            channels = np.stack([mask[y, x, ch] for ch in masks['channels'].values()], 1)
            label = np.argmax(channels, 1)
            label[channels.max(1) < masks.get('threshold', 0.6)] = -1
            mask_labels.append(label)
        coords.append(c)
        for p in palettes:
            colours[p].append(frames[p][y, x, :3])
    coords = np.concatenate(coords)
    colours = {p: np.concatenate(v) for p, v in colours.items()}
    labels = np.concatenate(mask_labels) if masks else _region_labels(coords, regions)
    lum = srgb_luminance(colours[reference])
    lo, hi = (-90.0, 90.0) if mode == 'elevation' else (0.0, 1.0)
    bins = np.round(np.arange(lo, hi + step / 2, step), 6)
    overall, known = _binned(coords, lum, bins, step)
    profile = {'coordinate': mode, 'camera_elevation': cameras, 'bins': bins.tolist(),
               'luminance': np.round(overall, 4).tolist(),
               'measured_range': [float(bins[known].min()), float(bins[known].max())], 'regions': {}}
    for index, name in enumerate(regions):
        sel = labels == index
        values, _ = _binned(coords[sel], lum[sel], bins, step)
        profile['regions'][name] = {'pixels': int(sel.sum()), 'luminance': np.round(values, 4).tolist()}
    out = REPO / config['out']
    out.mkdir(parents=True, exist_ok=True)
    (out / 'profile.json').write_text(json.dumps(profile, indent=1) + '\n')
    np.savez_compressed(out / 'pixels.npz', coordinate=coords, region=labels, region_names=np.array(list(regions)),
                        **{f'p{p}': colours[p] for p in palettes})
    strip = np.repeat(np.repeat(np.nan_to_num(overall)[::-1, None], 60, 1), 4, 0)
    Image.fromarray((np.clip(strip, 0, 1) * 255).astype(np.uint8)).save(out / 'profile.png')
    print('MEASURED', len(coords), 'pixels;', {n: profile['regions'][n]['pixels'] for n in regions},
          'range', profile['measured_range'], 'camera', cameras)
    return profile


# ----------------------------------------------------------------------------------------------- shade

def texel_coordinate(xyz, mode, centre=None, z_range=None):
    """Body coordinate per texel from its rest-pose 3D position (H x W x 3), matching measure()."""
    if mode == 'elevation':
        d = xyz - np.asarray(centre, dtype=np.float64)
        dist = np.linalg.norm(d, axis=-1)
        return np.degrees(np.arcsin(np.clip(d[..., 2] / np.maximum(dist, 1e-9), -1, 1)))
    if mode == 'height':
        z0, z1 = z_range
        return (xyz[..., 2] - z0) / max(z1 - z0, 1e-9)
    raise ValueError(f'unknown coordinate mode: {mode}')


def detail_of(base, sigma=10.0):
    """Local detail of a texture: luminance over its blur, clipped to 0.55..1.6 (1 = no detail)."""
    lum = base @ LUMA
    return np.clip(lum / np.maximum(ndimage.gaussian_filter(lum, sigma), 1e-3), 0.55, 1.6)


def shade(base, coord, region, profile, scale=1.0, detail_strength=1.0, detail=None, amount=1.0, luminance=None):
    """Replace base (H x W x 3 sRGB, edited in place) inside the boolean `region` by the native brightness at each
    texel's coordinate, as grey, times the local detail (detail_of(base) unless given; compute it once before shading
    several regions) raised to detail_strength, mixed with the original by `amount`. `luminance` overrides
    profile['luminance'] (for example one region's own profile). Returns base."""
    curve = profile['luminance'] if luminance is None else luminance
    target = np.interp(coord[region], profile['bins'], curve) * scale
    if detail is None:
        detail = detail_of(base)
    grey = np.clip(target * detail[region] ** detail_strength, 0, 1)
    base[region] = base[region] * (1 - amount) + grey[:, None] * amount
    return base


# ------------------------------------------------------------------------------------------------ ramps

def transfer_ramps(base, weights, pixels, region_for, variants, reference, gain=None, chroma=1.0, nearest=0.03,
                   percentiles=(0.5, 99.5)):
    """Ramps for claude_shared/region_variants.py from aligned native pixels.

    base: shared base colour (sRGB, the graded texture the runtime uses); weights: {mask region: H x W weight};
    pixels: the loaded pixels.npz; region_for: {mask region: native region name}; variants: {variant: palette};
    reference: the palette the base brightness came from. For each stop (linear luminance lo..hi over the region's
    full-weight texels), the `nearest` share of reference pixels closest in luminance is read in each variant's palette
    (median), times gain[region], saturation scaled by chroma. Returns {variant: [ramp per region in weights order]}.
    """
    gain = gain or {}
    names = list(pixels['region_names'])
    lum_all = srgb_to_linear(base) @ LUMA
    ramps = {variant: [] for variant in variants}
    for region, weight in weights.items():
        lum = lum_all[weight > 0.9]
        lo, hi = np.percentile(lum, percentiles[0]), np.percentile(lum, percentiles[1])
        stops = lo + (hi - lo) * np.arange(16) / 15
        sel = pixels['region'] == names.index(region_for[region])
        ref_lum = srgb_to_linear(pixels[f'p{reference}'][sel]) @ LUMA
        k = max(int(len(ref_lum) * nearest), 20)
        picks = [np.argsort(np.abs(ref_lum - stop))[:k] for stop in stops]
        for variant, palette in variants.items():
            tier = pixels[f'p{palette}'][sel]
            colours = []
            for idx in picks:
                c = np.median(tier[idx], 0) * gain.get(region, 1.0)
                grey = c @ LUMA
                colours.append(srgb_to_linear(np.clip(grey + (c - grey) * chroma, 0, 1)))
            ramps[variant].append({'range': [round(float(lo), 6), round(float(hi), 6)],
                                   'colors': np.round(np.clip(colours, 0, 1), 6).tolist()})
    return ramps


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] != 'measure':
        raise SystemExit(__doc__)
    measure(json.loads(Path(sys.argv[2]).read_text()))
