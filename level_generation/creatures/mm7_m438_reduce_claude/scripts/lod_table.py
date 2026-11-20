#!/usr/bin/env python3
"""Compact table of work/lod_check_<label>.json files: per LOD triangles, rest bounds height, lowest point per clip (cm)
and stretched faces. Usage: lod_table.py <label> [label ...]"""
import json, sys
for lab in sys.argv[1:]:
    r = json.load(open(f'work/lod_check_{lab}.json'))
    for lv, it in r.items():
        cl = it['clips']
        print(f"{lab:12s} LOD{lv} {it['tris']:5d} tris  height {it['rest_max'][2]-it['rest_min'][2]:.4f}  "
              + '  '.join(f"{k} {v['min_z']*100:+.1f}" for k, v in sorted(cl.items()))
              + f"  stretched {max(v['stretched_faces'] for v in cl.values())}")
