#!/usr/bin/env python3
"""Region ramps of the Carnage Hand (CLAUDE_CREATURE_TEXTURES.md): one shared graded skin, three regions (R skin:
hand and fingers; G maw: lips, gum rim, gullet, tongue; B fangs). Xeen image 49 has one palette, so one skin: hand_a
reproduces the native look (the graded paint itself). The mask lets later tiers or worlds recolour the skin, the maw
and the fangs by numbers only. Writes textures/hand_ramps.json with the fit report."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import region_variants as RV

base = RV.load_srgb(ROOT / 'textures/hand_basecolor_graded.png', 1024)
mask = Image.open(ROOT / 'textures/hand_region_mask.png')
ramps, report = {'hand_a': []}, {}
for channel, name in (('R', 'skin'), ('G', 'maw'), ('B', 'fangs')):
    weight = np.asarray(mask.getchannel(channel), np.float64) / 255.0
    r, rep = RV.fit_ramps(base, {'hand_a': base}, weight)
    ramps['hand_a'].append(r['hand_a']); report[name] = rep
out = {'variants': ['hand_a'],
       'materials': [{'base': 'Hand_A', 'prefix': 'Hand', 'mask': 'hand_region_mask.png', 'ramps': ramps}],
       'regions': ['R skin (hand, fingers)', 'G maw (lips, gum rim, gullet, tongue)', 'B fangs'],
       'fit_report': report}
json.dump(out, open(ROOT / 'textures/hand_ramps.json', 'w'), indent=1)
print('RAMPS', json.dumps(report))
