#!/usr/bin/env python3
"""See-through hole maxima per clip and zone, installed vs candidates (review/gates_<tag>/st_main.json + st_conv5.json).
Usage: st_compare.py before <tag> [tag ...]"""
import json, os, sys
tags = sys.argv[1:]
tot = {t: [0, 0] for t in tags}
for name in ('st_main', 'st_conv5'):
    if not all(os.path.exists(f'review/gates_{t}/{name}.json') for t in tags):
        continue
    D = {t: json.load(open(f'review/gates_{t}/{name}.json')) for t in tags}
    for c in D[tags[0]]['clips']:
        zs = sorted(set().union(*[D[t]['clips'][c]['zones'] for t in tags])); row = []
        for z in zs:
            v = [D[t]['clips'][c]['zones'].get(z, {}).get('hole_max', 0) for t in tags]
            for t, x in zip(tags, v):
                tot[t][0] += x
            if any(v):
                mark = ' UP' if any(x > v[0] for x in v[1:]) else ''
                row.append(f"{z} {'/'.join(map(str, v))}{mark}")
        print(f'{c:12s}', '; '.join(row))
print('sum of zone maxima', {t: v[0] for t, v in tot.items()})
