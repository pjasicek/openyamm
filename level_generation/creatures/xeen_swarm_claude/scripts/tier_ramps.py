#!/usr/bin/env python3
"""Swarm skins (one shared Stinger skin; region R = the orange-brown hairy body; legs, eyes, stinger and wings keep their
paint). Xeen draws the Insect Swarm and the Stingers with one sprite and palette, so swarm_c is a design choice:
  swarm_b  Insect Swarm  native rusty orange-brown
  swarm_c  Stingers      dark crimson red (hue 356, value x0.72)
Writes textures/wasp_ramps.json (region_variants.py format)."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
sys.path.insert(0, str(ROOT.parent / 'xeen_toad_claude' / 'scripts'))
import region_variants as RV
base = RV.load_srgb(ROOT / 'textures/wasp_basecolor_graded.png', 1024)
weight = np.asarray(Image.open(ROOT / 'textures/wasp_region_mask.png').getchannel('R'), np.float64) / 255.0


def recolour(rgb, hue_deg, sat_k, val_k):
    rgb = np.clip(rgb, 0, 1)
    v = rgb.max(-1); c = v - rgb.min(-1)
    s = np.clip(np.where(v > 1e-6, c / np.maximum(v, 1e-6), 0) * sat_k, 0, 1); v = np.clip(v * val_k, 0, 1)
    h6 = (hue_deg / 60.0) % 6; i = int(h6); f = h6 - i
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    return np.stack([(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)][i], -1)


tiers = {'swarm_b': base, 'swarm_c': recolour(base, 356, 1.0, 0.72)}
ramps, report = RV.fit_ramps(base, tiers, weight)
json.dump({'variants': list(tiers), 'materials': [{'base': 'Swarm_A', 'prefix': 'Swarm', 'mask': 'wasp_region_mask.png',
           'ramps': {v: [ramps[v]] for v in tiers}}], 'fit_report': report},
          open(ROOT / 'textures/wasp_ramps.json', 'w'), indent=1)
print('RAMPS', json.dumps(report))
