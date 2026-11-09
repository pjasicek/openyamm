#!/usr/bin/env python3
"""See-through per zone and clip, before vs candidates (review/st_<tag>/see_through.json of the patched gate): the zone maxima
in both classifications (sep: head material = name contains 'Head', so hair/ears count as head; dm2: the 2026-11-02 sweep's,
where those faces count as collar), the worst view, and the lining poke counts. Usage: st_table.py <tag> [<tag> ...]"""
import json, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / 'review'
tags = sys.argv[1:]; D = {t: json.load(open(R / f'st_{t}' / 'see_through.json')) for t in tags}
for scheme in ('zones', 'zones_dm2'):
    print(f'### {scheme} (hole px at {D[tags[0]]["px_mm"]:.0f} mm, step {D[tags[0]]["step"]})')
    zones = sorted({z for d in D.values() for c in d['clips'].values() for z in c.get(scheme, {})})
    clips = list(D[tags[0]]['clips'])
    print('clip'.ljust(12) + ''.join(z.ljust(22) for z in zones))
    mx = {t: {} for t in tags}
    for c in clips:
        row = c.ljust(12)
        for z in zones:
            vals = []
            for t in tags:
                r = D[t]['clips'].get(c, {}).get(scheme, {}).get(z)
                v = r['hole_max'] if r else 0; vals.append(str(v))
                if v > mx[t].get(z, (0,))[0]:
                    mx[t][z] = (v, c, r['worst'])
            row += '/'.join(vals).ljust(22)
        print(row)
    for t in tags:
        print(f'max {t}: ' + ', '.join(f'{z} {v[0]} ({v[1]} {v[2][0]} {v[2][1]})' for z, v in sorted(mx[t].items())))
for t in tags:
    if 'poke' in D[t]:
        print(f'poke {t}: ' + ', '.join(f'{c} {v["max_px"]} px, own {v.get("own_max_px", 0)} ({len(v["frames"])} frames, visible lining max {v["visible_max"]})'
                                        for c, v in D[t]['poke'].items()))
