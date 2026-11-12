#!/usr/bin/env python3
"""Markdown rows for seam trials: <dir>/<name>_report.json (+ <name>_quality.json from texture_quality.py).

    tabulate.py <dir> <name>...
"""
import json
import sys
from pathlib import Path

d = Path(sys.argv[1])
print('| Trial | Atlas % | Islands | Fragments % | Stretch p90 | Spread | Seam length | Vis-weighted | Exposed '
      '| Hidden share % | Pack s |')
print('|---|---|---|---|---|---|---|---|---|---|---|')
for name in sys.argv[2:]:
    r = json.loads((d / f'{name}_report.json').read_text())
    qf = d / f'{name}_quality.json'
    q = json.loads(qf.read_text())[0]['materials'][0] if qf.exists() else {}
    s = r['seams']
    print(f"| {name} | {q.get('atlas_pct', r.get('uv_area_pct'))} | {q.get('islands', '-')} | "
          f"{q.get('fragment_surface_pct', '-')} | {q.get('stretch_p90', '-')} | {q.get('spread', '-')} | "
          f"{s['total_len']} | {s['vis_weighted_len']} | {s['exposed_len']} | {s['hidden_share_pct']} | "
          f"{r.get('seconds', '-')} |")
