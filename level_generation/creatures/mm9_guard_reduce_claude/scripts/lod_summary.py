#!/usr/bin/env python3
"""Summary of work/lod_check_<label>.json (lod_check.py): per LOD triangles, rest height, lowest point in Standing / Walking /
Death / Dead, the lowest over all living clips, faces stretched > 20x (max over clips). Usage: lod_summary.py <label> [...]"""
import json, sys
LIVING = ('Death', 'Death2', 'Dead')
for lab in sys.argv[1:]:
    d = json.load(open(f'work/lod_check_{lab}.json'))
    for lv, it in d.items():
        c = it['clips']; mz = lambda k: round(c[k]['min_z'] * 100, 2)
        live = min(v['min_z'] for k, v in c.items() if k not in LIVING) * 100
        print(f"{lab:10s} LOD{lv} tris {it['tris']:6d} height {it['rest_max'][2]:.4f} rest min {it['rest_min'][2] * 100:+.2f} cm | "
              f"Standing {mz('Standing'):+.2f} Walking {mz('Walking'):+.2f} living min {live:+.2f} Death {mz('Death'):+.2f} "
              f"Death2 {mz('Death2'):+.2f} Dead {mz('Dead'):+.2f} cm | stretched max {max(v['stretched_faces'] for v in c.values())}")
