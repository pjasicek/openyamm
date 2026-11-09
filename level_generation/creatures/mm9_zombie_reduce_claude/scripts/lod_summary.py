#!/usr/bin/env python3
"""Side-by-side summary of lod_check.py reports. Usage: lod_summary.py <label> [<label> ...]"""
import json, sys
R = {l: json.load(open(f'work/lod_check_{l}.json')) for l in sys.argv[1:]}
for lev in ('0', '1', '2', '3'):
    print(f'LOD{lev}', ' | '.join(f"{l}: tris {r[lev]['tris']} h {r[lev]['rest_max'][2] - r[lev]['rest_min'][2]:.4f}" for l, r in R.items()))
    clips = R[sys.argv[1]][lev]['clips']
    for c in clips:
        print(f'   {c:14s}', ' | '.join(f"{r[lev]['clips'][c]['min_z'] * 100:6.2f} cm st {r[lev]['clips'][c]['stretched_faces']}" for r in R.values()))
