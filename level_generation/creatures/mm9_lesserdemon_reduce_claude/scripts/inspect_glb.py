#!/usr/bin/env python3
"""Print meshes/primitives/materials/triangle counts of a GLB (json chunk only)."""
import sys, json, struct
f = open(sys.argv[1], 'rb'); f.read(12); ln, _ = struct.unpack('<II', f.read(8)); j = json.loads(f.read(ln))
mats = j.get('materials', [])
for ni, n in enumerate(j['nodes']):
    if 'mesh' in n:
        m = j['meshes'][n['mesh']]
        print('NODE', ni, n.get('name'), 'mesh', n['mesh'], m.get('name'), 'skin', n.get('skin'), 'extras', m.get('extras', {}) and list(m['extras'].keys()))
        for p in m['primitives']:
            c = j['accessors'][p['indices']]['count'] // 3; v = j['accessors'][p['attributes']['POSITION']]['count']
            print('   prim mat', p.get('material'), mats[p['material']].get('name') if 'material' in p else '', 'tris', c, 'verts', v, 'attrs', sorted(p['attributes']), 'ext', list(p.get('extensions', {}).keys()))
print('materials', [m.get('name') for m in mats]); print('images', len(j.get('images', []))); print('anims', len(j.get('animations', [])), [a.get('name') for a in j.get('animations', [])])
print('extensionsUsed', j.get('extensionsUsed')); print('scene extras', j.get('scenes', [{}])[0].get('extras'))
print('asset extras', j['asset'].get('extras'))
