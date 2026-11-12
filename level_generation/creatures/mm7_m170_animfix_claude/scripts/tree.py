#!/usr/bin/env python3
"""Print a GLB's node tree (names), skinned joint flags and clip list with lengths."""
import json, struct, sys
p = sys.argv[1]
d = open(p, 'rb').read()
n = struct.unpack_from('<I', d, 12)[0]
j = json.loads(d[20:20 + n])
nodes = j['nodes']
joints = set()
for s in j.get('skins', []):
    joints.update(s['joints'])
children = {i for nd in nodes for i in nd.get('children', [])}
def walk(i, depth):
    nd = nodes[i]
    tag = '' if i in joints else ' (non-joint)'
    if 'mesh' in nd:
        tag += ' [mesh]'
    print('  ' * depth + nd.get('name', str(i)) + tag)
    for c in nd.get('children', []):
        walk(c, depth + 1)
for r in j['scenes'][0]['nodes']:
    walk(r, 0)
acc = j['accessors']
for a in j['animations']:
    mx = max(acc[s['input']]['max'][0] for s in a['samplers'])
    print('clip', a['name'], round(mx, 3), len(a['channels']))
