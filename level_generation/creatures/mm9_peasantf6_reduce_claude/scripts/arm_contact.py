#!/usr/bin/env python3
"""Body faces (dress, skirt) the arms touch: for every clip at HZ, the installed LOD0 posed; a dress/skirt face is an arm-contact
face when any of its corners comes within R m of an arm or hand vertex (parts 4, 5, 6) in any sampled pose.
Writes work/arm_contact.npy (bool per glb_parts face). Usage: arm_contact.py [R] [HZ]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
R = float(sys.argv[1]) if len(sys.argv) > 1 else 0.015; HZ = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
m = Model(Glb(str(HERE / 'before' / 'mm9_peasantf6.glb')))
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']
pr = m.primitives[:2]; off = np.cumsum([0] + [len(p['positions']) for p in pr])
T = np.concatenate([p['triangles'] + off[i] for i, p in enumerate(pr)]); assert len(T) == len(part)
arm = np.unique(T[np.isin(part, (4, 5, 6))].ravel()); body = np.isin(part, (1, 2))
bv = np.unique(T[body].ravel()); hitv = np.zeros(off[-1], bool); per = {}
for clip in m.clips:
    t1 = m.clip_times(clip)[-1]; n0 = hitv.sum()
    for t in np.append(np.arange(0, t1, 1 / HZ), t1):
        sp = m.skinned_positions(m.world(m.sample(clip, t))); X = np.concatenate([sp[0][0], sp[1][0]])
        d, _ = cKDTree(X[arm]).query(X[bv], distance_upper_bound=R); hitv[bv[np.isfinite(d)]] = True
    per[clip] = int(hitv.sum() - n0)
face = body & hitv[T].any(1)
print('arm-contact vertices per clip (new)', per); print('arm-contact faces', int(face.sum()), 'dress', int((face & (part == 1)).sum()), 'skirt', int((face & (part == 2)).sum()))
np.save(HERE / 'work' / 'arm_contact.npy', face)
