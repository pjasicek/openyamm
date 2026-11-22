#!/usr/bin/env python3
"""Sorceress skins: one shared body set (+ the head set, no region: skin, hair, eyes and circlet are kept in every
tier), region R = the white cloth (halter, shoulder caps, front and back panels; compose_sorc.py). Gloves, boots,
girdle, gems, skin and hair outside it.
Xeen draws Sorceress, Enchantress, Grand Sorceress and Morgana with one sprite (Clouds image 31: neutral white cloth,
palette greys (140..252)), so only A is native:
  sorc_a  Sorceress (also Apprentice D, Head Sorceress)  native white: the ramp fitted to the paint itself
          (region_variants.fit_ramps, the accepted look)
  sorc_b  Enchantress       pale violet (design): the cloth's mean shown colour #b8a0dc
  sorc_c  Grand Sorceress   deep emerald green (design): #106e40
  sorc_m  Morgana (D-32)    deep crimson with black trim (design): #8c0e1e, contrast 1.9 so the folds, hems and
          edges (the paint's darkest cloth texels) go near-black; the paint has no separately maskable hem
B, C and M keep the paint's shading: stop k = mid colour (linear) x (A's stop luminance / the region's mean shown
luminance) ^ contrast, clipped (the xeen_tiers_claude 'mid' rule). Writes textures/sorc_ramps.json."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import region_variants as RV

DESIGN = {'sorc_b': ((184, 160, 220), 1.0), 'sorc_c': ((16, 110, 64), 1.1), 'sorc_m': ((140, 14, 30), 1.9)}
base = RV.load_srgb(ROOT / 'textures/sorc_basecolor_graded.png', 1024)
weight = np.asarray(Image.open(ROOT / 'textures/sorc_region_mask.png').getchannel('R'), np.float64) / 255
ramps_a, rep = RV.fit_ramps(base, {'sorc_a': base}, weight)
ra = ramps_a['sorc_a']
lin_a = np.array(ra['colors']); lum_stops = lin_a @ RV.LUMA
core = weight >= 0.9
lum = RV.luminance(base)
t = np.clip((lum[core] - ra['range'][0]) / (ra['range'][1] - ra['range'][0]), 0, 1)
i0 = np.minimum((t * 15).astype(int), 14); f = t * 15 - i0
shown = lum_stops[i0] * (1 - f) + lum_stops[i0 + 1] * f
mean = float(shown.mean())
ramps = {'sorc_a': [ra]}
for v, (mid, k) in DESIGN.items():
    ml = RV.srgb_to_linear(np.array(mid) / 255.0)
    # scale so that the region's average shown colour is the mid colour after the contrast curve
    ratio = np.maximum(lum_stops / mean, 1e-4) ** k
    shown_ratio = (np.maximum(shown / mean, 1e-4) ** k).mean()
    cols = np.clip(ml[None, :] * (ratio / shown_ratio)[:, None], 0, 1)
    ramps[v] = [{'range': ra['range'], 'colors': np.round(cols, 6).tolist()}]
rep = {'tier_a_fit': rep['sorc_a'], 'core_texels_1k': int(core.sum()), 'mean_shown_luminance': round(mean, 4),
       'design_mid_srgb': {v: m for v, (m, _) in DESIGN.items()}, 'contrast': {v: k for v, (_, k) in DESIGN.items()}}
json.dump({'variants': list(ramps), 'materials': [{'base': 'Sorc_A', 'prefix': 'Sorc', 'mask': 'sorc_region_mask.png',
           'ramps': ramps}], 'fit_report': rep}, open(ROOT / 'textures/sorc_ramps.json', 'w'), indent=1)
print('RAMPS', json.dumps(rep))
