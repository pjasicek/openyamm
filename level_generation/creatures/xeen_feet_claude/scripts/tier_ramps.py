#!/usr/bin/env python3
"""Flying Feet skin: feet_a (Flying Feet, Xeen Construct A) reproduces the graded paint, whose skin matches the native
palette (native mid 192,132,92 / light 228,184,160, hue 24-26 deg; paint median 210,141,94 before grading). Regions:
R = skin (foot, ankle bumps, toes, nails), G = the feathered wings. Later Xeen construct tiers that reuse this model
are new ramps only. Writes textures/feet_ramps.json (region_variants.py format)."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import region_variants as RV
base = RV.load_srgb(ROOT / 'textures/feet_basecolor_graded.png', 1024)
mask = np.asarray(Image.open(ROOT / 'textures/feet_region_mask.png').convert('RGBA'), np.float64) / 255.0
tiers = {'feet_a': base}
ramps, report = {v: [] for v in tiers}, {}
for c, region in enumerate(('skin', 'wings')):
    r, rep = RV.fit_ramps(base, tiers, mask[..., c])
    for v in tiers:
        ramps[v].append(r[v])
    report[region] = rep
json.dump({'variants': list(tiers), 'materials': [{'base': 'Feet_A', 'prefix': 'Feet', 'mask': 'feet_region_mask.png',
           'ramps': ramps}], 'fit_report': report}, open(ROOT / 'textures/feet_ramps.json', 'w'), indent=1)
print('RAMPS', json.dumps(report))
