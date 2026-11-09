#!/usr/bin/env python3
"""LOD check summaries (work/lod_check_<tag>.json, lod_check.py): per LOD triangles, rest height, and per clip lowest point (cm)
and stretched faces. Usage: lod_compare.py <tag> [<tag> ...]"""
import json, sys
for tag in sys.argv[1:]:
    d = json.load(open(f'work/lod_check_{tag}.json'))
    print('==', tag)
    for lv, it in d.items():
        h = it['rest_max'][2] - it['rest_min'][2]
        cl = ' '.join(f"{c[:5]} {v['min_z'] * 100:+.2f}{'/S' + str(v['stretched_faces']) if v['stretched_faces'] else ''}" for c, v in it['clips'].items())
        print(f"LOD{lv} {it['tris']:6d} h {h:.4f} | {cl}")
