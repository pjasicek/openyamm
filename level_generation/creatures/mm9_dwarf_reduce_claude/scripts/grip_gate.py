#!/usr/bin/env python3
"""Grip gate (from mm9_guard_claude/scripts/grip_gate.py, both hands): finger skin against the hilt per clip sample: verts inside the grip's ellipse-ish cylinder (depth, count), per finger how far it wraps (degrees covered within 3.8 cm of the axis), thumb gap. Args: <glb> [out txt]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
g = Glb(Path(sys.argv[1])); m = Model(g)
names = [n.get('name') for n in g.json['nodes']]; jn = [names[j] for j in m.joints]
P = [p for p in m.primitives if p['skinned'] and p['node'] == m.primitives[0]['node']]
dom = np.concatenate([np.array([jn[j] for j in p['joints'][np.arange(len(p['joints'])), p['weights'].argmax(1)]]) for p in P]).astype(str)
def allpos(w): return np.vstack([m.skinned_positions(w)[i][0] for i in range(len(P))])
import json
W = {'R': ('RHand1', 0.0125, (-0.055, 0.055))}
GR = json.load(open('work/grips.json'))['R']; UR = np.array(GR['U']); UR = np.array([UR[0], UR[2], -UR[1]])     # glTF axes
out = []
rest = allpos(m.world({}))
for S, (bone, R, (t0, t1)) in W.items():
    wv = np.where(dom == bone)[0]
    F = {f: np.where(np.char.startswith(dom, f'Bip01 {S} {f}'))[0] for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')}
    tt = rest[wv] @ UR
    tip = wv[np.argmax(tt)]; pom = wv[np.argmin(tt)]
    for clip in [a['name'] for a in g.json['animations']]:
        dur = m.clip_times(clip)[-1]; rows = {}; worst = 0.0; nin = 0
        for t in np.linspace(0, dur, 5):
            X = allpos(m.world(m.sample(clip, float(t))))
            
            uu = X[tip] - X[pom]; uu = uu / np.linalg.norm(uu)
            org = X[tip] - uu * (0.341 - 0.035)                  # the fist's centre on the haft
            for f, ids in F.items():
                v = X[ids] - org; a_ = v @ uu; pr = v - np.outer(a_, uu); r = np.linalg.norm(pr, axis=1)
                on = (a_ > t0) & (a_ < t1)
                if on.any():
                    worst = max(worst, float((R - r[on]).max())); nin += int((r[on] < R - 0.001).sum())
                k = on & (r < 0.038)
                if k.sum() > 3:
                    e1 = np.cross(uu, [0.3, 0.9, 0.2]); e1 /= np.linalg.norm(e1); e2 = np.cross(uu, e1)
                    ang = np.degrees(np.arctan2(pr[k] @ e2, pr[k] @ e1))
                    rows.setdefault(f, []).append(len(np.unique((ang // 15).astype(int))) * 15)
                else: rows.setdefault(f, []).append(0)
        out.append(f"{S} {clip:13s} inside grip: max {worst * 100:4.1f} cm, {nin:4d} vert-samples | wrap deg " + ' '.join(f'{f} {int(np.median(v))}' for f, v in rows.items()))
        print(out[-1], flush=True)
if len(sys.argv) > 2: open(sys.argv[2], 'w').write('\n'.join(out) + '\n')
