"""PartUV study: one markdown table row per layout from texture_quality.py JSON (+ partuv_layout_stats.py JSON line and
optional pack/runtime JSON).

  partuv_table.py <label>=<quality.json>[,<stats.json>[,<pack.json>|<seconds>]] [...] [material=<substring>]
"""
import json
import sys

rows = []
args = [a for a in sys.argv[1:] if not a.startswith('material=')]
mat = next((a.split('=', 1)[1] for a in sys.argv[1:] if a.startswith('material=')), None)
print('| Layout | Atlas % | Equiv. px | Density p50 | Spread | Islands | Fragments % | Stretch p90 | Zero-area '
      '| Seam length | Runtime |')
print('|---|---|---|---|---|---|---|---|---|---|---|')
for a in args:
    label, files = a.split('=', 1)
    files = files.split(',')
    q = json.load(open(files[0]))[0]['materials']
    m = next((x for x in q if mat is None or mat in x['material']), q[0])
    s = json.loads(open(files[1]).read()) if len(files) > 1 and files[1] else {}
    rt = ''
    if len(files) > 2:
        try:
            rt = f"{float(files[2]):.0f} s"
        except ValueError:
            rt = f"{json.load(open(files[2])).get('pack_seconds', 0):.0f} s pack"
    print(f"| {label} | {m['atlas_pct']} | {m['equivalent_px']} | {m['density_p50']} | {m['spread']} | {m['islands']} "
          f"| {m['fragment_surface_pct']} | {m['stretch_p90']} | {s.get('zero_area', '')} | {s.get('seam_length', '')} "
          f"| {rt} |")
