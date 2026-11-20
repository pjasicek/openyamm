"""MM7 Water Elemental tier ramps on the shared MM8 Water Elemental skin (same render, palettes 501/502/503).

MM7 draws tier C with palette 503 where MM8 reuses 501 for its tier C, so tier C needs its own ramps. Tiers A and B
use the same palette files and the same render (index-equal 0.98) as MM8 A and B, so they keep the installed MM8
ramps; a refit from the MM7 frames is reported for comparison. Tier C is fitted from the MM7 standing frames
m210sa0-4 with the m500 method (mm8_m500_claude/scripts/compose_textures.py):
palette indices classified by their palette-501 hue into scales / ventral / fins, the region's median native colour
times a gain (1.65 / 1.14 / 1.12) is the target, and the ramp scales that target linearly with luminance over the
region range: colour_i = target * (1 + k * ((lo + i / 15 * (hi - lo)) / mid - 1)), k = 1 before the 2026-10-31
texture pass, which pins each region's contrast with k < 1 (mm8_m500_claude README, "Texture quality pass").
The ranges are the installed MM8 ones; mid (the region's median texel luminance) and k are recovered from the MM8
tier A ramp (colour / target is linear in the stop luminance: intercept 1 - k, slope k / mid), and the method is
checked first by rebuilding MM8 tiers A and B from the MM8 frames m500sa0-4.
Writes textures/m210_ramps.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

P = Path(__file__).resolve().parents[1]
REPO = P.parents[2]
sys.path.insert(0, str(P.parent / 'claude_shared'))
import region_variants as RV  # noqa: E402

SOURCE = REPO / 'assets_source/worlds/mm8/models/mm8_m500.glb'
MM8_SPRITES = REPO / 'assets_legacy/sprites_mm8_monsters_20261019/assets_dev/engine/sprites'
MM7_SPRITES = REPO / 'assets_legacy/sprites_mm7_monsters_20261021/assets_dev/worlds/mm7/sprites'
GAINS = (1.65, 1.14, 1.12)
VARIANTS = {'m210_a': 501, 'm210_b': 502, 'm210_c': 503}
palettes = {pid: np.frombuffer((REPO / f'assets_dev/worlds/mm8/textures/pal{pid}.act').read_bytes()[:768],
                               np.uint8).reshape(256, 3) / 255 for pid in (501, 502, 503)}


def hsv(rgb):
    value = np.asarray(Image.fromarray(np.uint8(np.clip(rgb, 0, 1) * 255)[:, None]).convert('HSV'), float)[:, 0] / 255
    return value[:, 0] * 360, value[:, 1], value[:, 2]


def targets(directory, stem):
    ids = np.concatenate([np.asarray(Image.open(directory / f'{stem}{view}.bmp')).ravel() for view in range(5)])
    ids = ids[ids != 0]
    h, s, v = hsv(palettes[501][ids])
    select = [(h > 155) & (h < 285) & (s > .2), (s < .25) & (v > .25), ((h > 285) | (h < 20)) & (s > .15) & (v > .2)]
    result = {}
    for pid in palettes:
        result[pid] = []
        for region in range(3):
            colours = palettes[pid][ids[select[region]]]
            assert len(colours) > 100
            result[pid].append(np.clip(np.median(colours, axis=0) * GAINS[region], 0, 1))
    return result, [int(s.sum()) for s in select]


def ramp(target, lo, hi, mid, k):
    return [np.clip(RV.srgb_to_linear(target) * (1 + k * ((lo + i / 15 * (hi - lo)) / mid - 1)), 0, 1).tolist()
            for i in range(16)]


doc, _ = RV.read_glb(SOURCE)
installed = {m['name'].split('_')[-1].lower(): m['extras']['openyamm_region_ramps'] for m in doc['materials']}
mm8, _ = targets(MM8_SPRITES, 'm500sa')
mids, check = [], []
for region in range(3):
    lo, hi = installed['a'][region]['range']
    colours = np.asarray(installed['a'][region]['colors'])
    stops = lo + np.arange(16) / 15 * (hi - lo)
    target = RV.srgb_to_linear(mm8[501][region])
    unclipped = ((colours > 1e-6) & (colours < 1 - 1e-6)).all(1)
    slope, intercept = np.polyfit(np.repeat(stops[unclipped], 3), (colours / target[None, :])[unclipped].ravel(), 1)
    k = float(1 - intercept)
    mid = float(k / slope)
    mids.append((mid, k))
    for tier, pid in (('a', 501), ('b', 502)):
        rebuilt = np.asarray(ramp(mm8[pid][region], lo, hi, mid, k))
        check.append({'tier': tier, 'region': region,
                      'max_abs_linear': round(float(np.abs(rebuilt - np.asarray(installed[tier][region]['colors'])).max()), 6)})
mm7, samples = targets(MM7_SPRITES, 'm210sa')
ramps = {name: [] for name in VARIANTS}
deviation = []
for region in range(3):
    lo, hi = installed['a'][region]['range']
    ramps['m210_a'].append(installed['a'][region])
    ramps['m210_b'].append(installed['b'][region])
    ramps['m210_c'].append({'range': [lo, hi], 'colors': ramp(mm7[503][region], lo, hi, *mids[region])})
    for name, tier, pid in (('m210_a', 'a', 501), ('m210_b', 'b', 502)):
        refit = np.asarray(ramp(mm7[pid][region], lo, hi, *mids[region]))
        error = np.abs(refit - np.asarray(installed[tier][region]['colors']))
        deviation.append({'variant': name, 'region': region, 'mm7_refit_max_abs_linear_vs_mm8': round(float(error.max()), 6)})
report = {'method_check_mm8_rebuild': check, 'recovered_mid_k': [[round(m, 6), round(k, 6)] for m, k in mids],
          'mm7_samples_per_region': samples, 'mm7_vs_mm8_same_palette': deviation,
          'targets_srgb': {str(pid): [np.round(t, 4).tolist() for t in mm7[pid]] for pid in palettes}}
config = dict(variants=list(VARIANTS), palettes=VARIANTS, regions=['scales', 'ventral', 'fins'],
              materials=[dict(base='WaterElemental_A', prefix='WaterElemental', mask='(installed m500 atlas mask)',
                              ramps=ramps)], gains=GAINS, report=report)
(P / 'textures/m210_ramps.json').write_text(json.dumps(config, indent=2) + '\n')
print(json.dumps(report, indent=1))
