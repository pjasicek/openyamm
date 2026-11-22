#!/usr/bin/env python3
"""Print a GLB's animations (name, length), meshes (triangles), materials, variants, skeleton joint names."""
import json, struct, sys
def load(p):
    b = open(p, 'rb').read()
    n = struct.unpack_from('<I', b, 12)[0]
    return json.loads(b[20:20 + n])
d = load(sys.argv[1])
print('animations:', [a.get('name') for a in d.get('animations', [])])
for a in d.get('animations', []):
    mx = 0
    for s in a['samplers']:
        acc = d['accessors'][s['input']]
        mx = max(mx, acc.get('max', [0])[0])
    print('  ', a.get('name'), round(mx, 3))
for m in d.get('meshes', []):
    t = 0
    for p in m['primitives']:
        if 'indices' in p:
            t += d['accessors'][p['indices']]['count'] // 3
    print('mesh', m.get('name'), t)
print('materials', [m.get('name') for m in d.get('materials', [])])
print('variants', d.get('extensions', {}).get('KHR_materials_variants', {}).get('variants'))
print('nodes', [n.get('name') for n in d['nodes']][:200])
print('scene extras', d.get('scenes', [{}])[0].get('extras'))
print('asset extras', d.get('asset', {}).get('extras'))
