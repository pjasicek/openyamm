#!/usr/bin/env python3
"""Markdown table of the combined-layout trials of one subject (combo/<subject>/): texture_quality.py measures of the
packed layouts plus the seam measures of the trial (72 cameras; lengths in creature sizes) and the sparrow time.

    combo_table.py <subject> [<extra name>=<quality json>,<report json> ...]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
subject = sys.argv[1]
base = ROOT / 'combo' / subject
rows = []
for extra in sys.argv[2:]:
    name, files = extra.split('=', 1)
    q, r = files.split(',')
    rows.append((name, ROOT / q, ROOT / r, None))
for q in sorted((base / 'final').glob('*_quality.json')):
    v = q.name[:-len('_quality.json')]
    log = base / f'sparrow_{v}.log'
    rows.append((v, q, base / f'{v}_report.json', log if log.exists() else None))
print('| Layout | Atlas % | Equiv. px | Density p50 | Spread | Islands | Fragments % | Stretch p90 | Seam length | '
      'Visible seam | Exposed | Charts in | Pack s |')
print('|---|---|---|---|---|---|---|---|---|---|---|---|---|')
for name, q, r, log in rows:
    m = json.load(open(q))[0]['materials'][0]
    rep = json.load(open(r))
    s = rep['seams']
    t = ''
    if log:
        hit = re.search(r'total (\d+)s', log.read_text())
        t = hit.group(1) if hit else ''
    print(f"| {name} | {m['atlas_pct']} | {m['equivalent_px']} | {m['density_p50']} | {m['spread']} | {m['islands']} | "
          f"{m['fragment_surface_pct']} | {m['stretch_p90']} | {s['total_len']} | {s['vis_weighted_len']} | "
          f"{s['exposed_len']} | {rep.get('xatlas_charts', '')} | {t} |")
