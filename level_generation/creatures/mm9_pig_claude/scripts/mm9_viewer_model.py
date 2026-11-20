#!/usr/bin/env python3
"""A reference model for the review viewer: the MM9 source GLB with its clips renamed to our roles (Dead = Death) and
lifted so its bind stands on the floor, so MM9 and ours can be compared in the same viewer at the same clip and time.
Usage: mm9_viewer_model.py <source glb> <out glb> <lift> role=mm9clip ..."""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb
src, out, lift = sys.argv[1], sys.argv[2], float(sys.argv[3])
roles = dict(a.split('=') for a in sys.argv[4:])
g = Glb(src)
doc = g.json
by = {a['name']: a for a in doc['animations']}
anims = []
for role, clip in roles.items():
    a = json.loads(json.dumps(by[clip]))
    a['name'] = role
    anims.append(a)
    if role == 'Death':
        d = json.loads(json.dumps(by[clip]))
        d['name'] = 'Dead'
        t = g.append_accessor(np.array([0.0, 1.0], np.float32), 'SCALAR')
        for sm in d['samplers']:
            last = g.accessor(sm['output'])[-1]
            sm['input'] = t
            sm['output'] = g.append_accessor(np.array([last, last], np.float32), 'VEC4' if len(last) == 4 else 'VEC3')
            sm['interpolation'] = 'LINEAR'
        anims.append(d)
doc['animations'] = anims
sc = doc['scenes'][doc.get('scene', 0)]
keep = [i for i in sc['nodes'] if not doc['nodes'][i].get('name', '').startswith('Icosphere')]
doc['nodes'].append({'name': 'mm9_lift', 'translation': [0, lift, 0], 'children': keep})
sc['nodes'] = [len(doc['nodes']) - 1]
g.write(out)
print('mm9 viewer model', out, [a['name'] for a in anims])
