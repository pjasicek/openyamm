#!/usr/bin/env python3
"""The user's dressing rule (devdocs/xeen/formats/DRESSING.md, 2026-11-20) on a built outdoor map: no prop before a
door (a box `DEPTH` deep along the door's normal and `HALF` either side of its middle), barrels in pairs, clumps only
at storehouses. Usage: dress_check.py <build folder> <map stem>. Lists the decorations before each door and the
barrel/crate groups (props within 200 of each other)."""
import json
import math
import os
import sys
import yaml

B, STEM = sys.argv[1], sys.argv[2]
DEPTH, HALF = 448, 288
build = json.load(open(os.path.join(B, 'build.json')))
scene = yaml.safe_load(open(os.path.join(B, STEM + '.scene.yml')))
ents = [e for e in scene['entities'] if e['name'] != 'party start']
HINT = {}
for _line in open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               '../../../../assets_dev/engine/data_tables/decoration_data.txt'), encoding='latin1'):
    _f = _line.rstrip('\n').split('\t')
    if len(_f) > 2:
        HINT.setdefault(_f[1].lower(), _f[2].lower())
PROP = ('barrel', 'cask', 'crate', 'sack', 'keg', 'box', 'bag', 'wood', 'hay')

def is_prop(n):
    h = HINT.get(n.lower(), n.lower())
    return any(k in h for k in PROP)

bad = 0
for b in build['buildings']:
    if not (b.get('house') or b.get('event')):
        continue
    dx, dy, dz = b['door']
    nx, ny = b['normal']
    hits = []
    for e in ents:
        p = e['position']
        rx, ry = p['x'] - dx, p['y'] - dy
        along = rx * nx + ry * ny
        side = -rx * ny + ry * nx
        if 0 <= along <= DEPTH and abs(side) <= HALF and abs(p['z'] - dz) < 400:
            hits.append('%s(%s)@%d,%d' % (e['name'], HINT.get(e['name'].lower(), '?'), along, side))
    if hits:
        bad += 1
        print('DOOR %s (%s, house %s): %s' % (b['id'], b['title'], b['house'], ', '.join(hits)))
# groups of barrels and crates
props = [e for e in ents if is_prop(e['name'])]
seen, groups = set(), []
for i, e in enumerate(props):
    if i in seen:
        continue
    g, stack = [], [i]
    seen.add(i)
    while stack:
        j = stack.pop()
        g.append(j)
        pj = props[j]['position']
        for k, f in enumerate(props):
            if k not in seen and math.hypot(f['position']['x'] - pj['x'], f['position']['y'] - pj['y']) < 200:
                seen.add(k)
                stack.append(k)
    groups.append(g)
sizes = {}
for g in groups:
    sizes[len(g)] = sizes.get(len(g), 0) + 1
print('doors with something before them:', bad)
print('barrel/crate groups by size:', dict(sorted(sizes.items())), 'props', len(props))
for g in groups:
    if len(g) >= 3:
        p = props[g[0]]['position']
        print('  clump of %d at %d,%d (cell %.1f,%.1f): %s' % (len(g), p['x'], p['y'], p['x'] / 512 + 64,
              64 - p['y'] / 512, ', '.join(sorted(set(props[j]['name'] for j in g)))))
if '--singles' in sys.argv:
    for g in groups:
        if len(g) <= 2:
            p = props[g[0]]['position']
            print('  %d: %s at cell %.1f,%.1f' % (len(g), ', '.join(props[j]['name'] + '(' + HINT.get(props[j]['name'].lower(), '?') + ')' for j in g),
                  p['x'] / 512 + 64, 64 - p['y'] / 512))
