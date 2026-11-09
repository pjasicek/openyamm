#!/usr/bin/env python3
"""Impostor tone: compares the front renders of LOD0 and the impostor (work/<id>/lod_stats.json, Eevee, no shadows)
and folds the linear per-channel ratio into impostor_tone.json (read by finish_impostor.py). Prints CHANGED when
the tone moved by more than 3 %, so build.sh re-finishes the impostor once. Usage: calibrate_impostor.py <id>"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desert_common as dc
SID = sys.argv[1]
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'impostor_tone.json')
tones = json.load(open(path)) if os.path.exists(path) else {}
st = json.load(open(os.path.join(dc.work(SID), 'lod_stats.json')))
lin = lambda c: np.where(np.asarray(c) / 255 <= 0.04045, np.asarray(c) / 255 / 12.92, ((np.asarray(c) / 255 + 0.055) / 1.055) ** 2.4)
ratio = lin(st['Plant']['mean_rgb']) / lin(st['Plant_LOD3']['mean_rgb'])
old = np.asarray(tones.get(SID, [1.0, 1.0, 1.0]))
new = np.clip(old * ratio, 0.5, 2.0)
print('IMPOSTOR TONE', SID, old.round(3).tolist(), '->', new.round(3).tolist())
if np.abs(ratio - 1).max() > 0.03:
    tones[SID] = new.round(3).tolist()
    json.dump(tones, open(path, 'w'), indent=1, sort_keys=True)
    print('CHANGED')
