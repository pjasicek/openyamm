#!/usr/bin/env python3
"""MM9's dagger at bind, in Blender axes (x, -z, y): handle axis (pommel -> tip), blade-plane normal, grip centre. Writes work/dagger_rest.npz."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb('source/skel/skel2_true.glb'))
P = np.asarray(m.skinned_positions(m.world({}))[1][0])
P = np.c_[P[:, 0], -P[:, 2], P[:, 1]]
c = P.mean(0); u, s, vt = np.linalg.svd(P - c, full_matrices=False)
ax, wd, nr = vt[0], vt[1], vt[2]
t = (P - c) @ ax
# the tip is the narrow far end
span = lambda m_: ((P[m_] - c) @ wd).max() - ((P[m_] - c) @ wd).min()
lo, hi = t < np.percentile(t, 15), t > np.percentile(t, 85)
print('axis', ax, 'width lo', span(lo), 'hi', span(hi), 't', t.min(), t.max())
d = P[t.argmax()] - P[t.argmin()]
print('bounds', P.min(0), P.max(0), 'extreme', P[t.argmax()], P[t.argmin()])
np.savez('work/dagger_rest.npz', axis=ax, width=wd, normal=nr, centre=c, verts=P)
