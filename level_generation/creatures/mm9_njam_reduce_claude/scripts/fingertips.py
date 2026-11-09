#!/usr/bin/env python3
"""Fingertip faces (a50 close-up: the cut tips lost their painted nail ends and read angular): hand faces (part 0) whose three
vertices are all dominated by a distal finger bone (Index3, Middle3, Ring3, Pinky3, Thumb3). Writes work/fingertips.npy (per GLB
LOD0 face, glb_parts order). Usage: fingertips.py"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
m = Model(Glb(str(HERE / 'before' / 'mm9_njam.glb'))); g = np.load(HERE / 'work' / 'glb_parts.npz')
names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
out = []
for k, p in enumerate(m.primitives[:3]):
    T = np.asarray(p['triangles']).reshape(-1, 3)
    dom = [jn[p['joints'][v][np.argmax(p['weights'][v])]] for v in range(len(p['positions']))]
    tip = np.array([d.endswith('3') and any(f in d for f in ('Index', 'Middle', 'Ring', 'Pinky', 'Thumb')) for d in dom])
    out.append(tip[T].all(1))
out = np.concatenate(out) & (g['part'] == 0)
np.save(HERE / 'work' / 'fingertips.npy', out); print('FINGERTIP faces', int(out.sum()))
