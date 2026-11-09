#!/usr/bin/env python3
"""lod_check json(s) -> per clip min_z (cm) for every LOD, side by side, plus stretched-face totals. Usage: lod_table.py <label> ..."""
import json, sys
D = {l: json.load(open(f'work/lod_check_{l}.json')) for l in sys.argv[1:]}
clips = list(next(iter(D.values()))['0']['clips'])
for l, d in D.items():
    print(l, 'tris', [d[k]['tris'] for k in d], 'top', [d[k]['rest_max'][2] for k in d], 'stretched', [sum(c['stretched_faces'] for c in d[k]['clips'].values()) for k in d])
for c in clips:
    print(f'{c:13s}', ' | '.join(' '.join(f"{D[l][k]['clips'][c]['min_z'] * 100:5.1f}" for k in D[l]) for l in D))
