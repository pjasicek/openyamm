"""MM7 Wyvern tier ramps on the shared MM8 Wyvern skin (same render, MM7 palettes 114/115/116).

The MM7 frames carry the MM8 frames' palette indices (index-equal 0.975), drawn with other palettes: MM8 561/562/563,
MM7 114/115/116. So the body and texture are the MM8 model's and only the ramps are fitted again, with the m560
method (mm8_m560_reduce_claude/scripts/compose.py): standing and walking pixels are split into membrane / body by
their palette-561 hue, ranked by tier-A luminance, and each of the 16 stops takes the median native colour (x1.15)
around the rank where the region's texel luminance reaches that stop. Region membership is a property of the index,
so the MM7 pixels are classified with palette 561 as well; colours and rank come from the MM7 palettes (tier A 114).
The method is checked first by rebuilding the installed MM8 ramps from the MM8 frames.
Writes textures/m434_ramps.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

P = Path(__file__).resolve().parents[1]
REPO = P.parents[2]
sys.path[:0] = [str(P.parent / 'claude_shared'), str(P.parent / 'mm6_gob_claude/scripts')]
import compose_textures_v2 as C  # noqa: E402
import region_variants as RV  # noqa: E402

SOURCE = REPO / 'assets_source/worlds/mm8/models/mm8_m560.glb'
M560 = P.parent / 'mm8_m560_reduce_claude'
MM8_SPRITES = REPO / 'assets_legacy/sprites_mm8_monsters_20261019/assets_dev/engine/sprites'
MM7_SPRITES = REPO / 'assets_dev/worlds/mm7/sprites'
VARIANTS = {'m434_a': 114, 'm434_b': 115, 'm434_c': 116}
encode = lambda x: np.where(x <= .0031308, x * 12.92, 1.055 * np.maximum(x, 0) ** (1 / 2.4) - .055)


def palette(world, pid):
    return np.frombuffer((REPO / f'assets_dev/worlds/{world}/textures/pal{pid}.act').read_bytes()[:768],
                         np.uint8).reshape(256, 3).astype(np.float32) / 255


def native_pixels(directory, stem, pids, world):
    """Region labels and per-palette colours of every opaque membrane/body pixel of the s* and w* frames."""
    reference = palette('mm8', 561)
    colours = {pid: palette(world, pid) for pid in pids}
    regions, pixels = [], {pid: [] for pid in pids}
    names = sorted(entry for entry in (e.name for e in directory.iterdir())
                   if entry.lower().startswith((stem + 's', stem + 'w')) and entry.lower().endswith('.bmp'))
    for name in names:
        ids = np.asarray(Image.open(directory / name))
        hh, ss, _ = C.hsv(reference[ids])
        opaque = ids != 0
        wing = opaque & (hh > 20) & (hh < 65) & (ss > .35)
        skin = opaque & (hh >= 65) & (hh < 170) & (ss > .18)
        yy, xx = np.nonzero(wing | skin)
        regions.append(np.where(wing[yy, xx], 0, 1))
        for pid in pids:
            pixels[pid].append(colours[pid][ids[yy, xx]])
    return np.concatenate(regions), {pid: np.concatenate(v) for pid, v in pixels.items()}, len(names)


def ramps_for(regions, pixels, pids, rank_pid, quantiles):
    out = {pid: [] for pid in pids}
    for region, (lo, hi, quant) in enumerate(quantiles):
        sel = regions == region
        assert sel.sum() > 500
        order = np.argsort(RV.luminance(pixels[rank_pid][sel]))
        half = max(2, len(order) // 100)
        for pid in pids:
            native = pixels[pid][sel][order]
            colours = []
            for q in quant:
                centre = int(q * (len(order) - 1))
                rgb = np.median(native[max(0, centre - half):centre + half + 1], axis=0)
                colours.append(RV.srgb_to_linear(np.clip(rgb * 1.15, 0, 1)).tolist())
            out[pid].append({'range': [float(lo), float(hi)], 'colors': colours})
    return out


# The m560 texel quantiles: luminance of the shared base colour under each region's full-weight texels.
part, _ = C.rasterise(np.load(M560 / 'work/uv3d.npz'), tol=0)
valid = part >= 0
base = C.load(M560 / 'textures/wyvern_basecolor.png')
# The mask is stored at 1K; m560 thresholded its 2K weights, so the 1K mask is upsampled (bilinear) to the raster.
mask = np.stack([np.asarray(ch.resize(valid.shape[::-1], Image.BILINEAR), np.float32) / 255
                 for ch in Image.open(M560 / 'textures/wyvern_region_mask.png').split()], -1)
lum = RV.luminance(base)
quantiles = []
for region in range(2):
    values = np.sort(lum[(mask[..., region] > .9) & valid])
    lo, hi = np.percentile(values, [.5, 99.5])
    quantiles.append((lo, hi, np.searchsorted(values, np.linspace(lo, hi, 16)) / len(values)))

doc, _ = RV.read_glb(SOURCE)
installed = {m['name'].split('_')[-1].lower(): m['extras']['openyamm_region_ramps'] for m in doc['materials']}
regions8, pixels8, frames8 = native_pixels(MM8_SPRITES, 'm560', (561, 562, 563), 'mm8')
rebuilt = ramps_for(regions8, pixels8, (561, 562, 563), 561, quantiles)
check = []
for tier, pid in zip('abc', (561, 562, 563)):
    for region in range(2):
        a, b = rebuilt[pid][region], installed[tier][region]
        check.append({'tier': tier, 'region': region,
                      'range_abs': round(float(np.abs(np.subtract(a['range'], b['range'])).max()), 6),
                      'max_abs_linear': round(float(np.abs(np.subtract(a['colors'], b['colors'])).max()), 6),
                      'mean_abs_8bit_srgb': round(float(np.abs(encode(np.asarray(a['colors']))
                                                               - encode(np.asarray(b['colors']))).mean() * 255), 2)})
regions7, pixels7, frames7 = native_pixels(MM7_SPRITES, 'm434', tuple(VARIANTS.values()), 'mm7')
fitted = ramps_for(regions7, pixels7, tuple(VARIANTS.values()), 114, quantiles)
# The engine reads the installed ranges; keep them exactly so only the colours change.
ramps = {name: [dict(fitted[pid][region], range=installed['a'][region]['range']) for region in range(2)]
         for name, pid in VARIANTS.items()}
report = {'method_check_mm8_rebuild': check, 'mm8_frames': frames8, 'mm7_frames': frames7,
          'mm7_region_pixels': [int((regions7 == r).sum()) for r in range(2)],
          'mm8_region_pixels': [int((regions8 == r).sum()) for r in range(2)],
          'native_median_srgb': {str(pid): [np.round(np.median(pixels7[pid][regions7 == r], axis=0), 4).tolist()
                                            for r in range(2)] for pid in VARIANTS.values()}}
config = dict(variants=list(VARIANTS), palettes=VARIANTS, regions=['membrane', 'body'],
              materials=[dict(base='Wyvern_A', prefix='Wyvern', mask='(installed m560 mask)', ramps=ramps)],
              report=report)
(P / 'textures/m434_ramps.json').write_text(json.dumps(config, indent=2) + '\n')
print(json.dumps(report, indent=1))
