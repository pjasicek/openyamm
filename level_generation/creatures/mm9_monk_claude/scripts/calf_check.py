#!/usr/bin/env python3
import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
g = Glb(sys.argv[1]); m = Model(g); names = [n.get('name') for n in g.json['nodes']]
ix = {n: i for i, n in enumerate(names)}
for c in ['stand', 'walk', 'run', 'pray', 'die1', 'cower', 'castspell3']:
    a = next(x for x in g.json['animations'] if x['name'] == c)
    dur = max(g.accessor(s['input']).max() for s in a['samplers'])
    r = {k: [] for k in ('Calf', 'Sp2', 'Xmain_rel', 'calf_rel', 'floor', 'spine')}
    for t in np.linspace(0, dur, 9):
        w = m.world(m.sample(c, t))
        S = w[ix['Bip01 Spine']]; 
        r['Calf'].append(np.linalg.norm(w[ix['Bip01 L Foot']][:3, 3] - w[ix['Bip01 L Calf']][:3, 3]))
        r['calf_rel'].append(np.linalg.norm(w[ix['Bip01 L Calf']][:3, 3] - S[:3, 3]))
        r['Xmain_rel'].append(np.linalg.norm(w[ix['Xmain']][:3, 3] - S[:3, 3]))
        r['spine'].append(S[1, 3])
        r['floor'].append(min(w[ix['Bip01 L Toe0']][1, 3], w[ix['Bip01 R Toe0']][1, 3]))
    print(c, round(dur, 2), {k: (round(min(v), 3), round(max(v), 3)) for k, v in r.items() if v})
