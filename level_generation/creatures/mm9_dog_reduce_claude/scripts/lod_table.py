#!/usr/bin/env python3
"""LOD check table, installed vs candidate (work/lod_check_<a>.json, work/lod_check_<b>.json from lod_check.py): per LOD the
triangles, rest top/width, stretched faces over every clip, and the lowest point per clip (cm). Usage: lod_table.py <a> <b>"""
import json, sys
A, B = (json.load(open(f'work/lod_check_{k}.json')) for k in sys.argv[1:3])
for lv in A:
    a, b = A[lv], B[lv]
    print(f"LOD{lv}: tris {a['tris']} -> {b['tris']}; top {a['rest_max'][2]:.3f} -> {b['rest_max'][2]:.3f} m; width "
          f"{a['rest_max'][0] - a['rest_min'][0]:.3f} -> {b['rest_max'][0] - b['rest_min'][0]:.3f} m; depth "
          f"{a['rest_max'][1] - a['rest_min'][1]:.3f} -> {b['rest_max'][1] - b['rest_min'][1]:.3f}; stretched "
          f"{sum(c['stretched_faces'] for c in a['clips'].values())} -> {sum(c['stretched_faces'] for c in b['clips'].values())}")
    print('   min z cm: ' + ', '.join(f"{c} {a['clips'][c]['min_z'] * 100:+.2f}/{b['clips'][c]['min_z'] * 100:+.2f}" for c in a['clips']))
