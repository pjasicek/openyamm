#!/usr/bin/env python3
"""Leaf tint: compares the LOD0 front render (work/<id>/lod_stats.json, Eevee, no shadows) with the native sprite's mean
colour and folds the linear per-channel ratio (damped) into leaf_tint.json (read by build_palm.py, multiplying the
species' leaf_tint). Prints CHANGED when the tint moved by more than 2 %. Usage: calibrate_tint.py <id>"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palm_common as pc
SID = sys.argv[1]
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'leaf_tint.json')
tints = json.load(open(path)) if os.path.exists(path) else {}
import contrast
sprite_stats, model_stats = contrast.compare(SID, os.environ.get('RENDER', 'rv_Plant_front.png'))
lin = lambda c: np.where(np.asarray(c) / 255 <= 0.04045, np.asarray(c) / 255 / 12.92, ((np.asarray(c) / 255 + 0.055) / 1.055) ** 2.4)
# target: the sprite's mean, measured on the front review render with sun shadows (rv_Plant_front.png)
target = sprite_stats['mean']
ratio = (lin(target) / lin(model_stats['mean'])) ** 0.9
old = np.asarray(tints.get(SID, [1.0, 1.0, 1.0]))
new = np.clip(old * ratio, 0.05, 2.5)
print('LEAF TINT', SID, old.round(3).tolist(), '->', new.round(3).tolist(), 'LOD0', model_stats['mean'].round(1).tolist(),
      'sprite', target.round(1).tolist())
if np.abs(ratio - 1).max() > 0.04:
    tints[SID] = new.round(3).tolist()
    json.dump(tints, open(path, 'w'), indent=1, sort_keys=True)
    print('CHANGED')
