#!/usr/bin/env python3
"""Region ramps of the Guardian (CLAUDE_CREATURE_TEXTURES.md): one shared graded skin, three regions
(R skull: cranium, jaw, teeth and bezel in chrome silver; G gem; B eye cores). Xeen image 83 has one palette, so one
skin: guardian_a reproduces the native look (the graded paint itself). The mask lets later tiers or worlds recolour
the chrome, the gem and the eyes by numbers only. Writes textures/guardian_ramps.json with the fit report."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import region_variants as RV

base = RV.load_srgb(ROOT / 'textures/guardian_basecolor_graded.png', 1024)
mask = Image.open(ROOT / 'textures/guardian_region_mask.png')
ramps, report = {'guardian_a': []}, {}
for channel, name in (('R', 'skull'), ('G', 'gem'), ('B', 'eyes')):
    weight = np.asarray(mask.getchannel(channel), np.float64) / 255.0
    r, rep = RV.fit_ramps(base, {'guardian_a': base}, weight)
    ramps['guardian_a'].append(r['guardian_a']); report[name] = rep
out = {'variants': ['guardian_a'],
       'materials': [{'base': 'Guardian_A', 'prefix': 'Guardian', 'mask': 'guardian_region_mask.png',
                      'ramps': ramps}],
       'regions': ['R skull (chrome cranium, jaw, teeth, bezel)', 'G gem', 'B eye cores'],
       'fit_report': report}
json.dump(out, open(ROOT / 'textures/guardian_ramps.json', 'w'), indent=1)
print('RAMPS', json.dumps(report))
