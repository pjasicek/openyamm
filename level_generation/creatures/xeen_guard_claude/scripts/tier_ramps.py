#!/usr/bin/env python3
"""Region ramps of the guard (CLAUDE_CREATURE_TEXTURES.md): one shared graded paint, four regions (R chrome plates and
dome, G red seam/stripes/band and the gem, B cyan hip tubes and waist ring, A black boots/briefs/waist band/knee
rings and the dark joints). Xeen image 62 has one palette and one row uses it, so one skin: guard_a reproduces the
native look (the graded paint itself). The mask lets later tiers recolour by numbers only.
Writes textures/guard_ramps.json with the fit report (mean / p95 error in 8-bit levels)."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import region_variants as RV

base = RV.load_srgb(ROOT / 'textures/guard_basecolor_graded.png', 1024)
mask = Image.open(ROOT / 'textures/guard_region_mask.png')
ramps, report = {'guard_a': []}, {}
for channel, name in (('R', 'chrome'), ('G', 'red'), ('B', 'cyan'), ('A', 'black')):
    weight = np.asarray(mask.getchannel(channel), np.float64) / 255.0
    r, rep = RV.fit_ramps(base, {'guard_a': base}, weight)
    ramps['guard_a'].append(r['guard_a']); report[name] = rep
out = {'variants': ['guard_a'],
       'materials': [{'base': 'Guard_A', 'prefix': 'Guard', 'mask': 'guard_region_mask.png', 'ramps': ramps}],
       'regions': ['R chrome plates and dome', 'G red seam, stripes and forearm band (the gem keeps its ruby paint)',
                   'B cyan hip tubes and waist ring', 'A black boots, briefs, waist band, knee rings, joints'],
       'fit_report': report}
json.dump(out, open(ROOT / 'textures/guard_ramps.json', 'w'), indent=1)
print('RAMPS', json.dumps(report))
