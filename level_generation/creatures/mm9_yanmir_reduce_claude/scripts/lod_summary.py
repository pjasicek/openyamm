#!/usr/bin/env python3
"""work/lod_check_<a>.json vs <b>.json: per LOD triangles, rest height (z extent), stretched faces (max over clips), and the
clips whose lowest point differs by more than 3 mm. Usage: lod_summary.py <a> <b>"""
import json, sys
A, B = (json.load(open(f'work/lod_check_{t}.json')) for t in sys.argv[1:3])
for lv in A:
    a, b = A[lv], B[lv]
    h = lambda x: round(x['rest_max'][2] - x['rest_min'][2], 4)
    st = lambda x: max(c['stretched_faces'] for c in x['clips'].values())
    print(f"LOD{lv}: tris {a['tris']} -> {b['tris']}, height {h(a)} -> {h(b)} m, rest min z {a['rest_min'][2]} -> {b['rest_min'][2]}, stretched {st(a)} -> {st(b)}")
    for c in a['clips']:
        za, zb = a['clips'][c]['min_z'], b['clips'][c]['min_z']
        if abs(za - zb) > 0.003:
            print(f"   {c}: lowest {za} -> {zb}")
