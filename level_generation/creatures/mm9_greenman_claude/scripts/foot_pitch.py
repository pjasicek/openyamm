#!/usr/bin/env python3
"""Pitch the feet toe-up where they dip under the floor (mm9_greenman): our Meshy feet are longer than MM9's and their
joints sit further forward, so MM9's walk drove the toes 7-10 cm through the floor at every push-off, and grounding that
with the root bobbed the whole body (jitter gate) or left it hovering. Instead, at every key of the listed clips each
Foot joint is pitched about the body's lateral axis (through the ankle) by the smallest angle that brings that foot's
lowest vertex (dominant joint the Foot or Toe0 of that side) up to the floor (+MARGIN), the angles are smoothed over
the keys (Gaussian SIGMA keys) and written as Foot rotation keys. The body path is untouched, so the arms and shoulders
keep MM9's motion exactly. Usage: foot_pitch.py in.glb out.glb CLIP[,CLIP] [SIGMA 1.0] [MARGIN 0.003]"""
import sys
from pathlib import Path
import numpy as np
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, matrix_quaternion, quaternion_matrix
IN, OUT, CLIPS = sys.argv[1:4]
SIGMA = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0; MARGIN = float(sys.argv[5]) if len(sys.argv) > 5 else 0.003
g = Glb(Path(IN)); m = Model(g); d = g.json; names = [n.get('name') for n in d['nodes']]
def rotm(ax, a):
    ax = ax / np.linalg.norm(ax); K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K
# vertices per side: dominant joint the side's Foot or Toe0
dom = []
for pr in m.primitives:
    if pr['skinned']:
        dom.append([names[m.joints[j]] for j in pr['joints'][np.arange(len(pr['positions'])), np.argmax(pr['weights'], 1)]])
    else:
        dom.append([None] * len(pr['positions']))
rep = {}
for clip in CLIPS.split(','):
    an = d['animations'][m.clips[clip]]
    for side in 'LR':
        fi = names.index(f'Bip01 {side} Foot')
        ch = next(c for c in an['channels'] if c['target']['node'] == fi and c['target']['path'] == 'rotation')
        sm = an['samplers'][ch['sampler']]
        T = np.asarray(g.accessor(sm['input'])).ravel(); Q = np.array(g.accessor(sm['output']), float)
        ang = np.zeros(len(T)); axes = []
        for k, t in enumerate(T):
            loc = m.sample(clip, float(t)); W = m.world(loc)
            pelvis = W[names.index('Bip01 Pelvis')][:3, :3]
            fwd = np.array([0, 0, 1.0]); lat = np.cross([0, 1.0, 0], fwd)     # glTF: y up, +z forward (the body's frame)
            axes.append(lat)
            ank = W[fi][:3, 3]
            def lowest(a):
                Rw = rotm(lat, a)
                lo = 9.0
                posed = m.skinned_positions(W)
                for (p, _), dl in zip(posed, dom):
                    sel = np.array([x is not None and (x == f'Bip01 {side} Foot' or x == f'Bip01 {side} Toe0') for x in dl])
                    if sel.any():
                        q = (p[sel] - ank) @ Rw.T + ank
                        lo = min(lo, q[:, 1].min())
                return lo
            l0 = lowest(0.0)
            if l0 >= MARGIN:
                continue
            # toe-up = the rotation that raises points ahead (+z) of the ankle: search the sign and size
            best = 0.0
            for a in np.radians(np.arange(1, 41, 1)):
                for s in (1, -1):
                    if lowest(s * a) >= MARGIN:
                        best = s * a; break
                if best:
                    break
            ang[k] = best
        angs = ndimage.gaussian_filter1d(ang, SIGMA, mode='wrap' if clip in ('Walking', 'Running') else 'nearest')
        angs = np.where(np.abs(ang) > np.abs(angs), ang, angs)      # never less than needed
        angs = ndimage.gaussian_filter1d(angs, SIGMA * 0.6, mode='wrap' if clip in ('Walking', 'Running') else 'nearest')
        out = []
        for k, t in enumerate(T):
            if abs(angs[k]) < 1e-5:
                out.append(Q[k]); continue
            W = m.world(m.sample(clip, float(t)))
            Wf = W[fi][:3, :3] / np.linalg.norm(W[fi][:3, :3], axis=0)
            Wp = W[m.parent[fi]][:3, :3] / np.linalg.norm(W[m.parent[fi]][:3, :3], axis=0)
            Rn = Wp.T @ rotm(axes[k], angs[k]) @ Wf
            q2 = matrix_quaternion(Rn); out.append(q2 if q2 @ Q[k] >= 0 else -q2)
        sm['output'] = g.append_accessor(np.array(out, np.float32), 'VEC4')
        rep[f'{clip} {side}'] = round(float(np.degrees(np.abs(angs).max())), 1)
g.write(Path(OUT)); print('FOOTPITCH max deg', rep)
