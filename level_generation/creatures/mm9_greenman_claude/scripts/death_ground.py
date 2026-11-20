#!/usr/bin/env python3
"""Ground a death fall key by key, smoothly (mm9_greenman): the PeasantMale die1 retargeted onto the 2.6 m Green Man
(leg ratio 1.654) hovered up to 0.33 m mid-fall and sank 0.35 m at the impact; floor_fix.py's per-key raise failed the
jitter gate. Here, at every key of the clip's root translation channel (ROOT joint), the root's vertical offset is set to
minus the lowest visible point at that key, the offsets are smoothed (Gaussian, SIGMA keys) and then raised wherever the
smoothed curve would leave a point under the floor by more than TOL, so the body always touches the floor and moves
smoothly. Usage: death_ground.py in.glb out.glb CLIP [ROOT 'Scene Root': moves the staff bone too] [SIGMA 1.5] [TOL 0.01]"""
import sys
from pathlib import Path
import numpy as np
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
IN, OUT, CLIP = sys.argv[1:4]
ROOT = sys.argv[4] if len(sys.argv) > 4 else 'Scene Root'
SIGMA = float(sys.argv[5]) if len(sys.argv) > 5 else 1.5
TOL = float(sys.argv[6]) if len(sys.argv) > 6 else 0.01
g = Glb(Path(IN)); m = Model(g); d = g.json
ri = [n.get('name') for n in d['nodes']].index(ROOT)
an = next(a for a in d['animations'] if a['name'] == CLIP)
ch = next(c for c in an['channels'] if c['target']['node'] == ri and c['target']['path'] == 'translation')
sm = an['samplers'][ch['sampler']]
T = np.asarray(g.accessor(sm['input'])).ravel(); V = np.array(g.accessor(sm['output']), float)
# root translation is in its parent's frame: find how a unit +y in that frame moves the model (world y per unit)
low0 = np.array([m.lowest(CLIP, float(t)) for t in T])
V1 = V.copy(); V1[:, 1] += 0.1
sm['output'] = g.append_accessor(V1.astype(np.float32), 'VEC3'); m = Model(g)
k = (np.array([m.lowest(CLIP, float(t)) for t in T]) - low0) / 0.1      # world y per unit of the channel's y
off = -low0 / k
k = np.where(np.abs(k) < 0.5, 1.0, k)
off_s = ndimage.gaussian_filter1d(off, SIGMA, mode='nearest')
for _ in range(12):                                                   # raise where under the floor, re-smooth, repeat
    off_s = np.maximum(off_s, off - TOL / k)
    off_s = ndimage.gaussian_filter1d(off_s, SIGMA * 0.5, mode='nearest')
off_s = np.maximum(off_s, off - 2 * TOL / k)
V2 = V.copy(); V2[:, 1] += off_s
sm['output'] = g.append_accessor(V2.astype(np.float32), 'VEC3')
g.write(Path(OUT))
m = Model(Glb(Path(OUT)))
low = np.array([m.lowest(CLIP, float(t)) for t in T])
print('DEATHGROUND', CLIP, 'keys', len(T), 'before min %.3f max %.3f' % (low0.min(), low0.max()), 'after min %.3f max %.3f' % (low.min(), low.max()), 'k %.2f' % float(np.median(k)))
