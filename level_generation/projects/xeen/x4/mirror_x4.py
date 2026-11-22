#!/usr/bin/env python3
"""Which Burlock doors have a mirror partner (town_feel's rule: 512 about the best axis through the doors' centre)."""
import json, math, sys
import numpy as np
b = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'output/studio_cal/x4/build_w/build.json'))
doors = [(x['id'], x['door'][0], x['door'][1]) for x in b['buildings'] if x.get('door') and 'burlock' in x['id']
         and 'castle' not in x['id']]
pts = np.array([(d[1], d[2]) for d in doors], float)
c = pts.mean(axis=0)
best = (0, 0, [])
for deg in range(0, 180, 5):
    ax = np.array([math.cos(math.radians(deg)), math.sin(math.radians(deg))])
    rel = pts - c
    m = c + 2 * np.outer(rel @ ax, ax) - rel
    hit = []
    for i, q in enumerate(m):
        d = np.hypot(pts[:, 0] - q[0], pts[:, 1] - q[1]); d[i] = 1e9
        if d.min() <= 512:
            hit.append(doors[i][0])
    if len(hit) > best[0]:
        best = (len(hit), deg, hit)
print('%d of %d, axis %d deg' % (best[0], len(doors), best[1]))
for d in doors:
    print('  %-34s %7.0f %7.0f  cell [%.2f, %.2f] %s' % (d[0], d[1], d[2], d[1] / 512 + 64, 64 - d[2] / 512,
                                                         'MIRRORED' if d[0] in best[2] else ''))
