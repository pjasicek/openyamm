#!/usr/bin/env python3
"""Braid placement against the back (follow-up 3): per clip, the braid's end joints (Ponytail11, Ponytail12) relative to the
upper chest (Spine3) in the chest's own frame, cm: back = how far behind the chest joint (+ = behind), down = below it.
Usage: braid_place.py <glb> Clip ..."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); n = [x.get('name') for x in m.glb.json['nodes']]; ix = {k: i for i, k in enumerate(n)}
R0 = m.world({})
for clip in sys.argv[2:]:
    ts = m.clip_times(clip); rows = []
    for t in ts:
        W = m.world(m.sample(clip, t)); C = W[ix['FHP Spine3']]
        Rc = C[:3, :3] @ R0[ix['FHP Spine3']][:3, :3].T
        r = []
        for j in ('FHP Ponytail11', 'FHP Ponytail12'):
            v = Rc.T @ (W[ix[j]][:3, 3] - C[:3, 3]); r += [-v[2] * 100, -v[1] * 100]
        rows.append(r)
    a = np.array(rows)
    print(f'{clip:10s} P11 back {a[:,0].mean():5.1f} ({a[:,0].min():5.1f}..{a[:,0].max():5.1f}) down {a[:,1].mean():5.1f} | '
          f'P12 back {a[:,2].mean():5.1f} ({a[:,2].min():5.1f}..{a[:,2].max():5.1f}) down {a[:,3].mean():5.1f}')
