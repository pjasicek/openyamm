#!/usr/bin/env python3
"""Grip gate (from mm9_guard_claude/scripts/grip_gate.py, both hands): finger skin against the hilt per clip sample: verts inside the grip's ellipse-ish cylinder (depth, count), per finger how far it wraps (degrees covered within 3.8 cm of the axis), thumb gap. Args: <glb> [out txt]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared/floor'))
from glb_pose import Glb, Model
g = Glb(Path(sys.argv[1])); m = Model(g)
names = [n.get('name') for n in g.json['nodes']]; jn = [names[j] for j in m.joints]
P = [p for p in m.primitives if p['skinned'] and p['node'] == m.primitives[0]['node']]
dom = np.concatenate([np.array([jn[j] for j in p['joints'][np.arange(len(p['joints'])), p['weights'].argmax(1)]]) for p in P]).astype(str)
def allpos(w): return np.vstack([m.skinned_positions(w)[i][0] for i in range(len(P))])
# MM6 thief daggers (finish_thf.py): tip at t 0.16, guard at -0.035 (0.195 from the tip), grip -0.12..-0.04 from the guard, radius 1.36 cm
W = {'R': ('Ybasesword', 0.0136, (-0.085, -0.008)), 'L': ('Ybasedagger', 0.0136, (-0.085, -0.008))}
DAGGER_CLIPS = ('Attack', 'Attack2', 'AttackRanged')
out = []
rest = allpos(m.world({}))
for S, (bone, R, (t0, t1)) in W.items():
    wv = np.where(dom == bone)[0]
    F = {f: np.where(np.char.startswith(dom, f'Bip01 {S} {f}'))[0] for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')}
    q = rest[wv]; c = q.mean(0); u = np.linalg.svd(q - c)[2][0]
    tt = (q - c) @ u
    tip = wv[np.argmax(np.abs(tt))]
    for clip in [a['name'] for a in g.json['animations'] if a['name'] in DAGGER_CLIPS]:
        dur = m.clip_times(clip)[-1]; rows = {}; worst = 0.0; nin = 0
        for t in np.linspace(0.15, dur - 0.17, 5):              # the fist is closed between the eases
            X = allpos(m.world(m.sample(clip, float(t))))
            if clip == 'AttackRanged' and S == 'L' and (t > 0.41 or t < 0.2): continue
            Q = X[wv]; c_ = Q.mean(0); uu = np.linalg.svd(Q - c_)[2][0]
            if (X[tip] - c_) @ uu < 0: uu = -uu
            tv = (Q - X[tip]) @ uu                               # from the tip, negative toward the pommel
            hilt = np.sort(tv)[0], np.sort(tv)[-1]
            org = X[tip] - uu * 0.195                              # guard station t = 0
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
