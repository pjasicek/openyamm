#!/usr/bin/env python3
"""Hold the toe joints at a fixed rotation in the given clips (mm9_greenman): our Meshy feet are longer than MM9's and
sit 10 cm further forward, so MM9's toe bend in the walk pushed the toes 7-10 cm through the floor at every push-off,
and grounding that per key bobbed the body. Each listed clip's Toe0 rotation channels are replaced by the rest rotation
times FRAC of the clip's own bend (0 = rest). Usage: toe_rest.py in.glb out.glb CLIP[,CLIP] [FRAC 0]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb
IN, OUT, CLIPS = sys.argv[1:4]; FRAC = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
g = Glb(Path(IN)); d = g.json; names = [n.get('name') for n in d['nodes']]
toes = [i for i, n in enumerate(names) if n and n.endswith('Toe0')]
def slerp(a, b, t):
    if a @ b < 0: b = -b
    q = a * (1 - t) + b * t; return q / np.linalg.norm(q)
n = 0
for an in d['animations']:
    if an['name'] not in CLIPS.split(','): continue
    for ch in an['channels']:
        if ch['target']['node'] in toes and ch['target']['path'] == 'rotation':
            sm = an['samplers'][ch['sampler']]
            Q = np.array(g.accessor(sm['output']), float)
            r = np.array(d['nodes'][ch['target']['node']].get('rotation', [0, 0, 0, 1.0]))
            sm['output'] = g.append_accessor(np.array([slerp(r, q, FRAC) for q in Q], np.float32), 'VEC4'); n += 1
g.write(Path(OUT)); print('TOEREST channels', n, 'clips', CLIPS, 'frac', FRAC)
