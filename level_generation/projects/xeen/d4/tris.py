#!/usr/bin/env python3
"""D1's model triangles from the build's export (A6, D-30): all, shown at load, hidden at load (structures with
`hidden: true` in the sketch), and Castle Kalindra's parts by stage. Usage: tris.py <build dir> <project L4>"""
import json
import os
import sys
import yaml

B, P = sys.argv[1], sys.argv[2]
e = json.load(open(os.path.join(B, 'export.json')))['map']
sk = yaml.safe_load(open(os.path.join(P, 'sketch.yml')))
hidden = {s['id'] for s in sk['structures'] if s.get('hidden')}

def tris(b):
    faces = b.get('faces') or []
    if faces:
        return sum(max(0, len(f.get('vertex_ids') or f.get('vertices') or []) - 2) for f in faces)
    return 0

tot = shown = hid = 0
kal = {}
for b in e['bmodels']:
    t = tris(b)
    tot += t
    if b['name'] in hidden:
        hid += t
    else:
        shown += t
    if 'kalindra' in b['name'] and 'rubble' not in b['name'] and 'ramp' not in b['name']:
        kal[b['name']] = t
print('model triangles: total %d, shown at load %d, hidden at load %d' % (tot, shown, hid))
for k in sorted(kal):
    print('  %-36s %5d%s' % (k, kal[k], '  (hidden)' if k in hidden else ''))
print('  Castle Kalindra shown at load %d, hidden %d' % (sum(v for k, v in kal.items() if k not in hidden),
                                                     sum(v for k, v in kal.items() if k in hidden)))
