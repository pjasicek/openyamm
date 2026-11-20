#!/usr/bin/env python3
"""Head and foot orientation against MM9 per frame: the skinned rotation of each bone applied to its bind forward and up, ours (raw frame, after the floor pass, before the mirror) against the source clip, 30 fps. Args: <ours glb> <mm9 glb> <out json>"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
O, M, OUT = sys.argv[1:4]
a = Model(Glb(O)); b = Model(Glb(M))
na = [n.get('name') for n in a.glb.json['nodes']]; nb = [n.get('name') for n in b.glb.json['nodes']]
ja = [na[j] for j in a.joints]; jb = [nb[j] for j in b.joints]
ROLE = {'Standing': 'stand', 'Walking': 'walk', 'Running': 'Run', 'Backpedal': 'Backpedal', 'BackpedalRun': 'BackpedalRun', 'Fidget': 'fidget1', 'Fidget2': 'fidget2', 'Taunt': 'Taunt', 'AttackMelee': 'Hattack1', 'AttackRanged': 'RAttack1', 'ResurrectSpell': 'ResurrectSpell', 'Hit': 'wince1', 'Hit2': 'wince2', 'Death': 'die1', 'Death2': 'die2', 'Resurrect': 'resurrect'}
BONES = ('Bip01 Head', 'Bip01 L Foot', 'Bip01 R Foot')
def ang(u, v): return np.degrees(np.arccos(np.clip((u * v).sum(1), -1, 1)))
res = {}
for c, s in ROLE.items():
    dur = min(a.clip_times(c)[-1], b.clip_times(s)[-1]); ts = np.arange(0, dur + 1e-6, 1 / 30)
    out = {}
    for bn in BONES:
        Sa = []; Sb = []
        for t in ts:
            wa = a.world(a.sample(c, float(t))); wb = b.world(b.sample(s, float(t)))
            Sa.append((wa[a.joints[ja.index(bn)]] @ a.inverse_binds[ja.index(bn)])[:3, :3]); Sb.append((wb[b.joints[jb.index(bn)]] @ b.inverse_binds[jb.index(bn)])[:3, :3])
        Sa, Sb = np.array(Sa), np.array(Sb)
        f = ang(Sa @ [0, 0, 1], Sb @ [0, 0, 1]); u = ang(Sa @ [0, 1, 0], Sb @ [0, 1, 0])
        out[bn.replace('Bip01 ', '')] = {'forward_max': round(float(f.max()), 1), 'forward_mean': round(float(f.mean()), 1), 'up_max': round(float(u.max()), 1), 'up_mean': round(float(u.mean()), 1)}
    res[c] = out
    print(f'{c:15}', ' | '.join(f"{k} fwd {v['forward_mean']}/{v['forward_max']} up {v['up_mean']}/{v['up_max']}" for k, v in out.items()))
json.dump(res, open(OUT, 'w'), indent=1)
