#!/usr/bin/env python3
"""Grip gate on a GLB with the halberd in it: right-hand finger skin against the shaft. Per clip key sample: finger and thumb vertices inside the shaft cylinder (depth, count); per finger how far it wraps round the shaft
(degrees of angle covered within 3.5 cm of the axis); gap of the thumb to the shaft. Args: <glb> [out txt]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
g = Glb(Path(sys.argv[1])); m = Model(g)
names = [n.get('name') for n in g.json['nodes']]; jn = [names[j] for j in m.joints]
Pr = m.primitives; body = Pr[0]; pk = next(i for i, p in enumerate(Pr) if jn[p['joints'][0][0]] == 'Xbase')

dom = np.array([jn[j] for j in body['joints'][np.arange(len(body['joints'])), body['weights'].argmax(1)]])
F = {f: np.where(np.char.startswith(dom.astype(str), f'Bip01 R {f}'))[0] for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')}
R = 0.0165
out = []
for clip in [a['name'] for a in g.json['animations']]:
    dur = m.clip_times(clip)[-1]
    rows = {}
    worst = 0.0; nin = 0
    for t in np.linspace(0, dur, 5):
        w = m.world(m.sample(clip, float(t))); sp = m.skinned_positions(w)
        X = sp[0][0]; Q = sp[pk][0]
        c = Q.mean(0); u = np.linalg.svd(Q - c)[2][0]
        for f, ids in F.items():
            v = X[ids] - c; a_ = v @ u; pr = v - np.outer(a_, u); r = np.linalg.norm(pr, axis=1)
            worst = max(worst, float((R - r).max())); nin += int((r < R - 0.001).sum())
            k = r < 0.035
            if k.sum() > 3:
                e1 = np.cross(u, [0.3, 0.9, 0.2]); e1 /= np.linalg.norm(e1); e2 = np.cross(u, e1)
                ang = np.degrees(np.arctan2(pr[k] @ e2, pr[k] @ e1))
                h = np.unique((ang // 15).astype(int)); rows.setdefault(f, []).append(len(h) * 15)
            else:
                rows.setdefault(f, []).append(0)
    out.append(f"{clip:13s} inside shaft: max {worst * 100:4.1f} cm, {nin:4d} vert-samples | wrap deg " + ' '.join(f'{f} {int(np.median(v))}' for f, v in rows.items()))
    print(out[-1], flush=True)
if len(sys.argv) > 2: open(sys.argv[2], 'w').write('\n'.join(out) + '\n')
