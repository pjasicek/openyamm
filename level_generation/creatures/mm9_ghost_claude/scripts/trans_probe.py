"""Local translation of each MM9 joint in the clips against its bind translation (metres, max over keys). Args: glb"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1]))
doc = m.glb.json
rows = {}
for a in doc['animations']:
    for ch in a['channels']:
        if ch['target']['path'] != 'translation':
            continue
        n = ch['target']['node']
        v = m.glb.accessor(a['samplers'][ch['sampler']]['output'])
        d = np.linalg.norm(v - m.rest[n][0], axis=1).max()
        nm = doc['nodes'][n]['name']
        rows.setdefault(nm, []).append((round(float(d), 4), a['name']))
for k, v in sorted(rows.items(), key=lambda kv: -max(x[0] for x in kv[1])):
    print(f'{k:14s} max {max(x[0] for x in v):.4f}  stand {[x[0] for x in v if x[1] == "standair"]} ', max(v)[1])
