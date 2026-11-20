#!/usr/bin/env python3
"""Grip gate: right-hand finger skin against the cutlass grip in Bone07's frame, every clip, 8 samples: vertices inside the grip cylinder (depth, count), per finger the angle wrapped round the axis. Args: <glb> [out]"""
import sys, json
from pathlib import Path
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
g = Glb(Path(sys.argv[1])); m = Model(g)
names = [n.get('name') for n in g.json['nodes']]; jn = [names[j] for j in m.joints]
P = [p for p in m.primitives if p['skinned'] and p['node'] == m.primitives[0]['node']]
dom = np.concatenate([np.array([jn[j] for j in p['joints'][np.arange(len(p['joints'])), p['weights'].argmax(1)]]) for p in P]).astype(str)
def allpos(w): return np.vstack([m.skinned_positions(w)[i][0] for i in range(len(P))])
H = json.load(open('work/hand_poses.json')); G0, AX0 = np.array(H['G']), np.array(H['AX']); R = .0235
ib = m.inverse_binds[jn.index('Bone07')]; bn = m.joints[jn.index('Bone07')]
F = {f: np.where(np.char.startswith(dom, f'Bip01 R {f}'))[0] for f in ('Finger0', 'Finger1', 'Finger2', 'Finger3')}
rows = []
for clip in [a['name'] for a in g.json['animations']]:
    dur = m.clip_times(clip)[-1]; worst = 0.; nin = 0; wrap = {f: [] for f in F}
    for t in np.linspace(0, dur, 8):
        w = m.world(m.sample(clip, float(t))); X = allpos(w); S = w[bn] @ ib
        Sinv = np.linalg.inv(S); Y = (Sinv[:3, :3] @ X.T).T + Sinv[:3, 3]          # into the bind frame of the weapon
        for f, ids in F.items():
            v = Y[ids] - G0; a_ = v @ AX0; pr = v - np.outer(a_, AX0); r = np.linalg.norm(pr, axis=1)
            on = (a_ > -.075) & (a_ < .075)
            if on.any(): worst = max(worst, float((R - r[on]).max())); nin += int((r[on] < R - .001).sum())
            k = (np.abs(a_) < .11) & (r < .06)
            if k.sum() > 2:
                e1 = np.cross(AX0, [0, 1., 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(AX0, e1); ang = np.degrees(np.arctan2(pr[k] @ e2, pr[k] @ e1))
                wrap[f].append(len(np.unique((ang // 15).astype(int))) * 15)
            else: wrap[f].append(0)
    rows.append(f"{clip:13s} inside grip max {max(worst, 0) * 100:4.1f} cm, {nin:4d} vert-samples | wrap deg " + ' '.join(f'{f} {int(np.median(v))}' for f, v in wrap.items())); print(rows[-1], flush=True)
if len(sys.argv) > 2: open(sys.argv[2], 'w').write('\n'.join(rows) + '\n')
