#!/usr/bin/env python3
"""Leaf contrast: compares the luminance spread (90th - 10th percentile) of the LOD0 front review render with the native
sprite's (contrast.py) and scales the palm's contrast exponent in leaf_contrast.json (read by build_palm.py; the spread
grows roughly with the exponent). Prints CHANGED when it moved by more than 5 %. Usage: calibrate_contrast.py <id>"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import contrast
import palm_common as pc
SID = sys.argv[1]
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'leaf_contrast.json')
values = json.load(open(path)) if os.path.exists(path) else {}
s, m = contrast.compare(SID, os.environ.get('RENDER', 'rv_Plant_front.png'))
old = values.get(SID, 1.8)
ratio = s['spread'] / max(m['spread'], 1.0)
new = float(np.clip(old * ratio ** 0.9, 1.0, pc.SPECIES[SID].get('contrast_max', 4.0)))
# a strong exponent leaves most of the crown dark and clips the lit part at COLOR_0 = 1, so the tint can no longer
# raise the mean: when the tint is saturated and the model is still too dark, back the exponent off instead
tints = json.load(open(os.path.join(os.path.dirname(path), 'leaf_tint.json'))).get(SID, [1, 1, 1])
luma = np.array([0.2126, 0.7152, 0.0722])
if max(tints) >= 2.4 and m['mean'] @ luma < s['mean'] @ luma - 3:
    new = float(max(old * 0.85, 1.0))
print('LEAF CONTRAST', SID, round(old, 3), '->', round(new, 3), 'spread model', round(m['spread']), 'sprite', round(s['spread']))
if abs(new / old - 1) > 0.05:
    values[SID] = round(new, 3)
    json.dump(values, open(path, 'w'), indent=1, sort_keys=True)
    print('CHANGED')
