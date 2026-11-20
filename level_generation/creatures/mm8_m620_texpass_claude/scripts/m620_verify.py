"""Checks the m620 export against the installed GLB beyond what tp_diff.py expects (the body | head split adds a
primitive and a material): nodes, skin, inverse binds and every clip identical; LOD0 and LOD1 corners (position,
normal, joints, weights) identical as a multiset over both primitives; shadow LOD0/LOD1 positions, joints and weights
identical; the tier materials equal apart from texture references; Bedraggled_Head = Bedraggled_A without region
mask and ramps; variants unchanged. Far LODs are verify_far_only.py's job.
Usage: m620_verify.py <installed glb> <export glb>"""
import copy
import json
import sys

import numpy as np

from glb import Glb

a, b = Glb(sys.argv[1]), Glb(sys.argv[2])
problems = []


def same(label, x, y):
    if x != y:
        problems.append(label)


def acc(g, i):
    return g.accessor(i)


same('nodes', a.doc['nodes'], b.doc['nodes'])
same('skins', a.doc['skins'], b.doc['skins'])
same('variants', a.doc['extensions'], b.doc['extensions'])
if not np.array_equal(acc(a, a.doc['skins'][0]['inverseBindMatrices']), acc(b, b.doc['skins'][0]['inverseBindMatrices'])):
    problems.append('inverse binds')
same('clip count', len(a.doc['animations']), len(b.doc['animations']))
for ca, cb in zip(a.doc['animations'], b.doc['animations']):
    same(f"clip {ca['name']} channels", ca['channels'], cb['channels'])
    for sa, sb in zip(ca['samplers'], cb['samplers']):
        for k in ('input', 'output'):
            if not np.array_equal(acc(a, sa[k]), acc(b, sb[k])):
                problems.append(f"clip {ca['name']} {k}")


def corners(g, mesh_name, attrs):
    mesh = next(m for m in g.doc['meshes'] if m['name'] == mesh_name)
    rows = []
    for pr in mesh['primitives']:
        f = acc(g, pr['indices']).reshape(-1)
        cols = []
        for name in attrs:
            v = acc(g, pr['attributes'][name]).astype(np.float64)
            cols.append(v.reshape(len(v), -1)[f])
        rows.append(np.concatenate(cols, 1))
    r = np.concatenate(rows).round(6)
    return r[np.lexsort(r.T[::-1])]


for name, attrs in (('Bedraggled', ('POSITION', 'NORMAL', 'JOINTS_0', 'JOINTS_1', 'WEIGHTS_0', 'WEIGHTS_1')),
                    ('Bedraggled_LOD1', ('POSITION', 'NORMAL', 'JOINTS_0', 'JOINTS_1', 'WEIGHTS_0', 'WEIGHTS_1')),
                    ('Bedraggled_Shadow', ('POSITION', 'JOINTS_0', 'JOINTS_1', 'WEIGHTS_0', 'WEIGHTS_1')),
                    ('Bedraggled_LOD1_Shadow', ('POSITION', 'JOINTS_0', 'JOINTS_1', 'WEIGHTS_0', 'WEIGHTS_1'))):
    x, y = corners(a, name, attrs), corners(b, name, attrs)
    if x.shape != y.shape or not np.array_equal(x, y):
        problems.append(f'{name} corners')
    print(name, 'corners', x.shape[0], 'identical' if x.shape == y.shape and np.array_equal(x, y) else 'DIFFER')


def strip_textures(m):
    m = copy.deepcopy(m)
    pbr = m.get('pbrMetallicRoughness', {})
    for k in ('baseColorTexture', 'metallicRoughnessTexture'):
        pbr.pop(k, None)
    m.pop('normalTexture', None)
    m.get('extras', {}).pop('openyamm_region_mask', None)
    return m


mats_b = {m['name']: m for m in b.doc['materials']}
for m in a.doc['materials'][:3]:
    same(f"material {m['name']}", strip_textures(m), strip_textures(mats_b[m['name']]))
head = strip_textures(a.doc['materials'][0])
head['name'] = 'Bedraggled_Head'
head.get('extras', {}).pop('openyamm_region_ramps', None)
if not head.get('extras'):
    head.pop('extras', None)
same('Bedraggled_Head material', head, strip_textures(mats_b['Bedraggled_Head']))
lod0 = next(m for m in b.doc['meshes'] if m['name'] == 'Bedraggled')
print('LOD0 primitives', [(b.doc['materials'][p['material']]['name'], acc(b, p['indices']).size // 3)
                          for p in lod0['primitives']])
print('PROBLEMS' if problems else 'OK', json.dumps(problems))
