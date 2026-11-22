#!/usr/bin/env python3
"""Doom Bug skin: one tier (bug_a, the native teal chitin; region R = the teal chitin) whose ramp reproduces the paint,
so later tiers or Hornet-like recolours are ramp numbers only. Writes textures/bug_ramps.json."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import region_variants as RV
base = RV.load_srgb(ROOT / 'textures/bug_basecolor_graded.png', 1024)
weight = np.asarray(Image.open(ROOT / 'textures/bug_region_mask.png').getchannel('R'), np.float64) / 255.0
ramps, report = RV.fit_ramps(base, {'bug_a': base}, weight)
json.dump({'variants': ['bug_a'], 'materials': [{'base': 'Bug_A', 'prefix': 'Bug', 'mask': 'bug_region_mask.png',
           'ramps': {'bug_a': [ramps['bug_a']]}}], 'fit_report': report}, open(ROOT / 'textures/bug_ramps.json', 'w'), indent=1)
print('RAMPS', json.dumps(report))
