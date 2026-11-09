#!/usr/bin/env python3
"""Lowest point, pelvis, feet per clip. Args: <glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); names = [n.get('name') for n in m.glb.json['nodes']]
for a in m.glb.json['animations']:
    c = a['name']; T = m.clip_times(c)[-1]; ts = np.arange(0, T + 1e-6, 1 / 15); lo = []; pe = []; fl = []; fr = []
    for t in ts:
        w = m.world(m.sample(c, float(t)))
        P = m.skinned_positions(w)
        lo.append(min(p[0][:, 1].min() for p in P[:2])); pe.append(w[names.index('Bip01 Pelvis')][1, 3])
        fl.append(w[names.index('Bip01 L Foot')][1, 3]); fr.append(w[names.index('Bip01 R Foot')][1, 3])
    print(f'{c:14s} low {min(lo):+.3f}..{max(lo):+.3f} pelvis {min(pe):+.3f}..{max(pe):+.3f} footL {min(fl):+.3f}..{max(fl):+.3f} footR {min(fr):+.3f}..{max(fr):+.3f}')
