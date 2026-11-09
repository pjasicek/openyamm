#!/usr/bin/env python3
"""MM9's Rattack1 hides the dagger (HidePiece at 0.125 s, ShowPiece at 0.9 s) while the hand goes to the hip, and throws at 0.5 s. Here the hand draws it: hidden 0.07-0.23 s while the fist is at the hip (the blade would run through the body), in the raised hand until the release,
gone until the clip's end: Ybasedagger's scale goes to 0.001 and back. Args: <in glb> <out glb> [release s]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb
IN, OUT = sys.argv[1:3]; REL = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
g = Glb(Path(IN)); d = g.json
ix = next(i for i, n in enumerate(d['nodes']) if n.get('name') == 'Ybasedagger')
for an in d['animations']:
    if an['name'] != 'AttackRanged': continue
    T = np.array([0.0, 0.069, 0.07, 0.23, 0.231, REL - 0.001, REL, 0.87, 0.871, 0.9], np.float32)
    S = np.array([1, 1, 0.001, 0.001, 1, 1, 0.001, 0.001, 1, 1], np.float32)[:, None].repeat(3, 1)
    ta = g.append_accessor(T, 'SCALAR'); d['accessors'][ta]['min'] = [float(T.min())]; d['accessors'][ta]['max'] = [float(T.max())]
    oa = g.append_accessor(S, 'VEC3')
    an['samplers'].append(dict(input=ta, output=oa, interpolation='LINEAR'))
    an['channels'] = [c for c in an['channels'] if not (c['target']['node'] == ix and c['target']['path'] == 'scale')]
    an['channels'].append(dict(sampler=len(an['samplers']) - 1, target=dict(node=ix, path='scale')))
g.write(Path(OUT)); print('DAGGER hide', REL)
