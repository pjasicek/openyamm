#!/usr/bin/env python3
"""lod_check.py results side by side: per LOD triangles, rest height and lowest rest point, per clip lowest posed point (cm)
and faces stretched over 20x. Usage: lod_compare.py <labelA> <labelB>"""
import json, sys
a, b = (json.load(open(f'work/lod_check_{t}.json')) for t in sys.argv[1:3])
for l in a:
    x, y = a[l], b[l]
    print(f"LOD{l}: tris {x['tris']} -> {y['tris']}, height {x['rest_max'][2]:.4f} -> {y['rest_max'][2]:.4f}, rest min z "
          f"{x['rest_min'][2]*100:.2f} -> {y['rest_min'][2]*100:.2f} cm, stretched {sum(c['stretched_faces'] for c in x['clips'].values())}"
          f" -> {sum(c['stretched_faces'] for c in y['clips'].values())}")
    rows = [f"{c} {x['clips'][c]['min_z']*100:.1f}/{y['clips'][c]['min_z']*100:.1f}" for c in x['clips']
            if abs(x['clips'][c]['min_z'] - y['clips'][c]['min_z']) > 0.002]
    print('   lowest point differs > 2 mm (installed/candidate cm):', ', '.join(rows) or 'none')
