#!/usr/bin/env python3
"""Derive Enhanced sky presets and colour cloud layers from the original MM6-MM8 sky textures.

For every sky texture the game data can select, this writes:
  assets_dev/engine/rendering/sky/legacy/<name>.png   RGBA colour layer: the original painting, with the open-sky
                                                      background keyed to transparent (fully painted skies stay opaque)
  a generated preset block in assets_dev/engine/rendering/sky/sky.yml (between the GENERATED LEGACY markers)
  legacy_skies.json                                   extracted colours and provenance

Daytime colours come from the texture itself; dawn, dusk and night blend into the shared base ramps. Skies that a
place shows all day (fixed: e.g. Dagger Wound's sunsetclouds) keep their own colours through the day and only dim.

  derive_legacy_skies.py [--preview DIR]
"""

import argparse
import glob
import hashlib
import json
import os
import re
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

ROOT = Path(__file__).resolve().parents[2]
SKY = ROOT / 'assets_dev/engine/rendering/sky'
SKY_YML = SKY / 'sky.yml'
BEGIN = '  # BEGIN GENERATED LEGACY PRESETS (tools/sky/derive_legacy_skies.py)\n'
END = '  # END GENERATED LEGACY PRESETS\n'
ALIAS_BEGIN = '  # BEGIN GENERATED LEGACY ALIASES (tools/sky/derive_legacy_skies.py)\n'
ALIAS_END = '  # END GENERATED LEGACY ALIASES\n'

# Every sky name the data can select (continent_settings.txt ladders, bolster_maps.txt custom skies, hardcoded
# fallbacks and event overrides), resolved per world by GameDataLoader::buildMergedSkyTextureCandidates.
WORLD_SEARCH = ['mm6', 'mm7', 'mm8', 'mmmerge', 'mm9']

# Skies painted edge to edge (no open background) and skies a place shows at every hour.
FULL_COVERAGE = {'6sky19', 'sky19', 'sunsetclouds', 'stormclds', 'sky6pm', 'sky01', 'sky04', 'skycity01'}
FIXED_LOOK = {'sunsetclouds'}
# Night-time textures from the original clock swap are covered by the shared night ramp.
SKIPPED = {'sky6pm'}
# Approved Codex HD repaints (see level_generation/lighting/sky_art/hd_masters/README.md) replace the originals.
HD_MASTERS = ROOT / 'level_generation/lighting/sky_art/hd_masters'
HD_LAYER_SIZE = 1024
# Edge band (fraction of the layer) over which an HD master's opposite edges are brought together.
HD_SEAM_BAND = 0.04
# Native layer PNGs are twice the source width; the sky-plane scale still follows the logical width.
LAYER_UPSCALE = 2
# Gaussian sigmas in upscaled texels: dither softening, alpha-key smoothing and edge colour bleed.
DITHER_SOFTEN = 1.1
KEY_SMOOTH = 1.6
EDGE_BLEED = 6.0
# Colour distance within which k-means clusters are shades of the same open sky.
SKY_SHADE_DISTANCE = 0.14

BASE_TIMES = ['02:00', '04:40', '05:20', '06:15', '12:00', '17:30', '19:50', '20:35', '21:10', '22:00']
# How much of the texture's own daytime colour shows at each base key (the rest is the shared ramp).
DAY_WEIGHT = [0.0, 0.08, 0.3, 0.7, 1.0, 1.0, 0.7, 0.3, 0.08, 0.0]
# Overcast paintings hide the sun, so dawn and dusk keep most of their own colour instead of a clear-sky glow.
COVERED_WEIGHT = [0.0, 0.25, 0.65, 0.9, 1.0, 1.0, 0.9, 0.65, 0.25, 0.0]


def srgb_to_linear(c):
    c = np.asarray(c, dtype=float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def find_hd_master(name):
    path = HD_MASTERS / f'{name}.png'
    return path if path.exists() else None


def find_texture(name):
    for world in WORLD_SEARCH:
        for folder in ('textures_x2', 'textures'):
            for path in glob.glob(str(ROOT / f'assets_dev/worlds/{world}/{folder}/*')):
                if os.path.splitext(os.path.basename(path))[0].lower() == name:
                    return Path(path)
    return None


def selectable_names():
    names = set()
    for line in open(ROOT / 'assets_dev/engine/data_tables/continent_settings.txt', encoding='utf-8', errors='replace'):
        columns = line.rstrip('\n').split('\t')
        if not line.startswith('#') and len(columns) >= 22:
            names |= {sky.strip().lower() for sky in columns[21].split(',') if sky.strip()}
    for line in open(ROOT / 'assets_dev/engine/data_tables/bolster_maps.txt', encoding='utf-8', errors='replace'):
        columns = line.rstrip('\n').split('\t')
        if not line.startswith('#') and len(columns) > 9 and columns[9].strip():
            names.add(columns[9].strip().lower())
    names |= {'plansky1', 'plansky3', 'sky01', 'sky03', 'sky04', 'sky05', 'sky06', 'sunsetclouds', 'cloudsabove',
              'stormclds', 'skycity01'}
    return sorted(names - SKIPPED)


def kmeans(pixels, k, iterations=25, seed=3):
    rng = np.random.default_rng(seed)
    centres = pixels[rng.choice(len(pixels), k, replace=False)]
    for _ in range(iterations):
        labels = ((pixels[:, None, :] - centres[None]) ** 2).sum(-1).argmin(1)
        centres = np.array([pixels[labels == i].mean(0) if (labels == i).any() else centres[i] for i in range(k)])
    return centres, np.bincount(labels, minlength=k) / len(labels)


def analyse(name, image):
    rgb = np.asarray(image.convert('RGB'), dtype=float) / 255.0
    sample = rgb[::4, ::4].reshape(-1, 3)
    centres, shares = kmeans(sample, 5)
    luminance = centres @ np.array([0.2126, 0.7152, 0.0722])
    # Open sky: the bluest sizeable cluster. Paintings often split the open sky into several blue shades, so the
    # bluest one, not the biggest, marks it; a grey cloud-edge tone can outnumber any single shade.
    blueness = centres[:, 2] - centres[:, 0]
    background = None
    background_share = 0.0
    if name not in FULL_COVERAGE:
        candidates = [i for i in range(len(centres)) if blueness[i] > 0.08 and shares[i] >= 0.12]
        if candidates:
            background = max(candidates, key=lambda i: blueness[i])
            # Neighbouring shades of the same open sky count toward its share.
            near = np.sqrt(((centres - centres[background]) ** 2).sum(-1)) < SKY_SHADE_DISTANCE
            background_share = float(shares[near].sum())
    mean = sample.mean(0)
    order = np.argsort(luminance)
    return {
        'background_share': background_share,
        'background': centres[background].tolist() if background is not None else None,
        'mean': mean.tolist(),
        'dark': centres[order[0]].tolist(),
        'bright': centres[order[-1]].tolist(),
        'clusters': [{'rgb': centres[i].tolist(), 'share': float(shares[i])} for i in order],
    }


def make_tileable(rgb, band):
    """Meet the opposite edges of a nearly tiling image halfway, fading the correction out over `band` texels.

    Image generators repaint the tile without exact wrap continuity. Shifting colour, rather than cross-fading two
    pictures, keeps the painted detail sharp next to the seam.
    """
    rgb = rgb.copy()
    ramp = np.clip(1.0 - np.arange(band) / band, 0.0, 1.0)
    ramp = ramp * ramp * (3.0 - 2.0 * ramp)
    for axis in (1, 0):
        first = np.take(rgb, 0, axis=axis)
        last = np.take(rgb, -1, axis=axis)
        half = (last - first) * 0.5
        for offset in range(band):
            index = [slice(None)] * 3
            index[axis] = offset
            rgb[tuple(index)] += half * ramp[offset]
            index[axis] = -1 - offset
            rgb[tuple(index)] -= half * ramp[offset]
    return np.clip(rgb, 0.0, 1.0)


def seam_ratio(rgb):
    """Mean edge-to-opposite-edge difference over the mean neighbour difference (about 1 for a clean tile)."""
    seams = (np.abs(rgb[:, 0] - rgb[:, -1]).mean() + np.abs(rgb[0] - rgb[-1]).mean()) / 2.0
    neighbours = (np.abs(rgb[:, 1:] - rgb[:, :-1]).mean() + np.abs(rgb[1:] - rgb[:-1]).mean()) / 2.0
    return float(seams / max(neighbours, 1e-6))


def layer_rgb(image, hd_master):
    if hd_master:
        # Codex HD repaints: real detail at about 1254 px, resampled to the layer size and seam-matched.
        rgb = np.asarray(image.convert('RGB').resize((HD_LAYER_SIZE, HD_LAYER_SIZE), Image.LANCZOS),
                         dtype=float) / 255.0
        return make_tileable(rgb, round(HD_LAYER_SIZE * HD_SEAM_BAND))
    # Native originals are dithered 8-bit paintings stretched over the whole sky: upscale and soften the palette
    # speckle so the magnified layer shows painted forms. Filters wrap because the layer tiles.
    size = (image.width * LAYER_UPSCALE, image.height * LAYER_UPSCALE)
    rgb = np.asarray(image.convert('RGB').resize(size, Image.LANCZOS), dtype=float) / 255.0
    return np.clip(gaussian_filter(rgb, sigma=(DITHER_SOFTEN, DITHER_SOFTEN, 0), mode='wrap'), 0.0, 1.0)


def colour_layer(image, info, hd_master=False):
    rgb = layer_rgb(image, hd_master)
    if info['background'] is None:
        alpha = np.ones(rgb.shape[:2])
    else:
        # Key on a smoothed distance so cloud edges are soft shapes, not per-texel noise.
        distance = np.sqrt(((rgb - np.array(info['background'])) ** 2).sum(-1))
        distance = gaussian_filter(distance, sigma=KEY_SMOOTH, mode='wrap')
        # Adaptive key: the open-sky share of the painting stays transparent, then a soft edge into cloud.
        share = info['background_share']
        low = np.percentile(distance, 100.0 * share * 0.85)
        high = max(np.percentile(distance, 100.0 * min(share + 0.18, 0.97)), low + 0.04)
        t = np.clip((distance - low) / (high - low), 0.0, 1.0)
        alpha = t * t * (3.0 - 2.0 * t)
        # Edge texels still carry the painted sky blue; take their colour from nearby cloud instead, so the
        # filtered layer has no blue fringe.
        weight = alpha ** 2
        weighted = gaussian_filter(rgb * weight[..., None], sigma=(EDGE_BLEED, EDGE_BLEED, 0), mode='wrap')
        total = gaussian_filter(weight, sigma=EDGE_BLEED, mode='wrap')[..., None]
        cloud = np.where(total > 1e-4, weighted / np.maximum(total, 1e-4), rgb)
        rgb = cloud + (rgb - cloud) * alpha[..., None]
    out = np.dstack([rgb, alpha])
    return Image.fromarray(np.round(np.clip(out, 0.0, 1.0) * 255).astype(np.uint8), 'RGBA')


def fmt(values):
    return '[' + ', '.join(f'{max(v, 0.0):.3f}' for v in values) + ']'


def base_keys():
    import yaml
    data = yaml.safe_load(SKY_YML.read_text())
    keys = {key['time']: key for key in data['presets']['base']['keys']}
    return [keys[time] for time in BASE_TIMES]


def preset_yaml(name, info, texture_width):
    base = base_keys()
    noon = base[BASE_TIMES.index('12:00')]
    fixed = name in FIXED_LOOK
    if info['background'] is not None:
        sky = srgb_to_linear(info['background'])
        zenith = sky * 0.82
        horizon = srgb_to_linear(np.array(info['background']) * 0.55 + np.array(info['mean']) * 0.2 + 0.25)
    else:
        zenith = srgb_to_linear(info['dark']) * 0.9
        horizon = srgb_to_linear(np.array(info['mean']) * 0.8 + np.array(info['bright']) * 0.2)
    fog = horizon * 0.85
    noon_luminance = max(float(np.dot(noon['horizon'], [0.2126, 0.7152, 0.0722])), 1e-3)
    lines = [f'  legacy_{name}:', '    inherits: base', '    keys:']
    covered = info['background'] is None
    for index, key in enumerate(base):
        weight = 1.0 if fixed else (COVERED_WEIGHT if covered else DAY_WEIGHT)[index]
        dim = min(1.0, max(0.05, float(np.dot(key['horizon'], [0.2126, 0.7152, 0.0722])) / noon_luminance)) if fixed else 1.0
        values = {}
        for field, texture_value in (('zenith', zenith), ('horizon', horizon), ('fog', fog)):
            mixed = np.array(key[field]) * (1.0 - weight) + texture_value * dim * weight
            values[field] = mixed
        # Colour layers multiply their painting by cloud_lit: shared warm/dark ramp, or a plain dimmer when fixed.
        lit = np.array(key['cloud_lit']) / np.array(noon['cloud_lit'])
        if covered and not fixed:
            # Keep the brightness of the ramp but only a quarter of its sunset warmth.
            grey = float(np.dot(lit, [0.2126, 0.7152, 0.0722]))
            lit = grey + (lit - grey) * 0.25
        values['cloud_lit'] = np.full(3, dim) if fixed else lit
        extra = ''
        if fixed or info['background'] is None:
            extra = f', sun_disc_visibility: {0.0 if fixed else 0.25:.2f}'
        lines.append(f'      - {{time: "{key["time"]}", zenith: {fmt(values["zenith"])}, horizon: {fmt(values["horizon"])},')
        lines.append(f'         fog: {fmt(values["fog"])}, cloud_lit: {fmt(values["cloud_lit"])}{extra}}}')
    # The original sky plane: classic uv = 64 * direction / height per texture pixel, drifting one pixel per second.
    scale = 64.0 / texture_width
    speed = 1.4142 / texture_width
    ring = 0.0 if info['background'] is None else 0.35
    lines += [
        f'    horizon_ring: {{opacity: {ring:.2f}}}',
        '    clouds:',
        f'      - {{texture: legacy/{name}, mode: color, scale: {scale:.4f}, speed: {speed:.5f}, direction_deg: 45,',
        '         coverage: 1.0, softness: 0.001, opacity: 1.0, curvature: 0.12}',
    ]
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    out_dir = SKY / 'legacy'
    out_dir.mkdir(exist_ok=True)
    records = {}
    presets = []
    for name in selectable_names():
        original = find_texture(name)
        if original is None:
            print(f'missing source for {name}')
            continue
        # Logical (native x1) width sets the original sky-plane scale; x2 restorations are twice as wide.
        original_width = Image.open(original).width
        logical_width = original_width // 2 if 'textures_x2' in str(original) else original_width
        master = find_hd_master(name)
        source = master or original
        image = Image.open(source)
        info = analyse(name, image)
        layer = colour_layer(image, info, master is not None)
        path = out_dir / f'{name}.png'
        layer.save(path, optimize=True)
        path.chmod(0o644)
        presets.append(preset_yaml(name, info, logical_width))
        records[name] = {'source': str(source.relative_to(ROOT)), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                         'layer_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'logical_width': logical_width,
                         'hd_master': master is not None,
                         'seam_ratio': round(seam_ratio(np.asarray(layer, dtype=float)[..., :3] / 255.0), 2),
                         'full_coverage': info['background'] is None, 'fixed_look': name in FIXED_LOOK,
                         'background_srgb': info['background'], 'mean_srgb': info['mean']}
        print(f'{name}: {source.relative_to(ROOT)} background={"none" if info["background"] is None else [round(v, 2) for v in info["background"]]}')
    (SKY / 'legacy_skies.json').write_text(json.dumps({'generator': 'tools/sky/derive_legacy_skies.py', 'skies': records}, indent=1) + '\n')

    text = SKY_YML.read_text()
    block = BEGIN + '\n'.join(presets) + END
    if BEGIN in text:
        text = text[:text.index(BEGIN)] + block + text[text.index(END) + len(END):]
    else:
        text = text.rstrip('\n') + '\n\n' + block
    # Generated aliases replace hand-written ones for the same names (YAML maps must not repeat keys).
    if ALIAS_BEGIN in text:
        text = text[:text.index(ALIAS_BEGIN)] + text[text.index(ALIAS_END) + len(ALIAS_END):]
    lines = [line for line in text.split('\n')
             if not any(line.startswith(f'  {name}: ') for name in records)]
    text = '\n'.join(lines)
    aliases = ALIAS_BEGIN + ''.join(f'  {name}: legacy_{name}\n' for name in records) + ALIAS_END
    text = text.replace('\npresets:\n', '\n' + aliases + '\npresets:\n', 1)
    # Re-running must not accumulate blank lines above the generated alias block.
    text = re.sub(r'\n{3,}(' + re.escape(ALIAS_BEGIN) + ')', r'\n\n\1', text)
    SKY_YML.write_text(text)

    if args.preview:
        args.preview.mkdir(parents=True, exist_ok=True)
        from PIL import ImageDraw
        tile = 200
        names = list(records)
        sheet = Image.new('RGB', (tile * 2 * 4, (tile + 16) * ((len(names) + 3) // 4)), (30, 30, 30))
        draw = ImageDraw.Draw(sheet)
        for index, name in enumerate(names):
            x = (index % 4) * tile * 2
            y = (index // 4) * (tile + 16)
            original = Image.open(ROOT / records[name]['source']).convert('RGB').resize((tile, tile))
            layer = Image.open(out_dir / f'{name}.png').resize((tile, tile))
            checker = Image.new('RGB', (tile, tile), (60, 140, 220))
            checker.paste(layer, (0, 0), layer)
            sheet.paste(original, (x, y + 16))
            sheet.paste(checker, (x + tile, y + 16))
            draw.text((x + 2, y + 2), name, fill=(255, 255, 0))
        sheet.save(args.preview / 'legacy_layers.jpg', quality=88)


if __name__ == '__main__':
    main()
