#!/usr/bin/env python3
"""Tier ramps of the toad (CLAUDE_CREATURE_TEXTURES.md): one shared graded skin, one region (R: the hide; the eyeballs
are out of the mask). Xeen has one toad palette, so only tier A is native; B and C are design choices made by
recolouring the graded base in HSV (texel luminance detail kept) and fitting the shader's ramp to it:
  toad_a  Giant Toad   the native tan to reddish brown (the Meshy paint from the masters)
  toad_b  Bog Toad     olive moss green-brown
  toad_c  Swamp Toad   dark slate green with a teal cast
Writes textures/toad_ramps.json (region_variants.py format) with the fit report."""
import json, sys, colorsys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import region_variants as RV

base = RV.load_srgb(ROOT / 'textures/toad_basecolor_graded.png', 1024)
weight = np.asarray(Image.open(ROOT / 'textures/toad_region_mask.png').getchannel('R'), np.float64) / 255.0


def recolour(rgb, hue_deg, sat_k, val_k):
    rgb = np.clip(rgb, 0, 1)
    v = rgb.max(-1); c = v - rgb.min(-1)
    s = np.where(v > 1e-6, c / np.maximum(v, 1e-6), 0) * sat_k
    v = v * val_k
    s = np.clip(s, 0, 1); v = np.clip(v, 0, 1)
    h6 = (hue_deg / 60.0) % 6; i = int(h6); f = h6 - i
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    return np.stack([(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)][i], -1)


tiers = {'toad_a': base, 'toad_b': recolour(base, 72, 0.85, 0.92), 'toad_c': recolour(base, 158, 0.6, 0.80)}
ramps, report = RV.fit_ramps(base, tiers, weight)
out = {'variants': list(tiers), 'materials': [{'base': 'Toad_A', 'prefix': 'Toad', 'mask': 'toad_region_mask.png',
                                              'ramps': {v: [ramps[v]] for v in tiers}}],
       'fit_report': report, 'design': {'toad_b': 'hue 72, sat x0.85, value x0.92',
                                        'toad_c': 'hue 158, sat x0.6, value x0.8'}}
json.dump(out, open(ROOT / 'textures/toad_ramps.json', 'w'), indent=1)
print('RAMPS', json.dumps(report))
