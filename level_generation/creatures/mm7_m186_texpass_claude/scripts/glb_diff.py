"""What a texture-pass GLB changed against the installed one. Must be unchanged: node names and transforms, skins and
inverse binds, every animation channel's data, material names, variants, extras other than texture indices, LOD
lists; per LOD0/LOD1 triangle corner: position, normal, joints and weights. Changed (reported): UVs, vertex counts,
images.

Usage: glb_diff.py <before glb> <after glb>; exit 1 on any unexpected difference."""
import json
import sys

import numpy as np

from glb import Glb

a, b = Glb(sys.argv[1]), Glb(sys.argv[2])
A, B = a.doc, b.doc
bad = []


def check(cond, what):
    if not cond:
        bad.append(what)


strip = lambda n: {k: v for k, v in n.items()}
check([strip(n) for n in A['nodes']] == [strip(n) for n in B['nodes']], 'nodes')
check(A['skins'] == B['skins'] or [s['joints'] for s in A['skins']] == [s['joints'] for s in B['skins']], 'skin joints')
check(np.array_equal(a.accessor(A['skins'][0]['inverseBindMatrices']), b.accessor(B['skins'][0]['inverseBindMatrices'])),
      'inverse binds')
check([x.get('name') for x in A['animations']] == [x.get('name') for x in B['animations']], 'clip names')
for ca, cb in zip(A['animations'], B['animations']):
    check(ca['channels'] == cb['channels'], f"{ca['name']} channels")
    for sa, sb in zip(ca['samplers'], cb['samplers']):
        for k in ('input', 'output'):
            check(np.array_equal(a.accessor(sa[k]), b.accessor(sb[k])), f"{ca['name']} sampler {k}")
        check(sa.get('interpolation') == sb.get('interpolation'), f"{ca['name']} interpolation")


def mat_key(m):
    m = json.loads(json.dumps(m))
    m.get('pbrMetallicRoughness', {}).pop('baseColorTexture', None)
    m.get('pbrMetallicRoughness', {}).pop('metallicRoughnessTexture', None)
    m.pop('normalTexture', None) if 'normalTexture' in m and set(m['normalTexture']) <= {'index'} else \
        m.get('normalTexture', {}).pop('index', None)
    m.get('extras', {}).pop('openyamm_region_mask', None)
    return m


check([mat_key(m) for m in A['materials']] == [mat_key(m) for m in B['materials']], 'materials')
check(A.get('extensions') == B.get('extensions'), 'variants')
check([m.get('name') for m in A['meshes']] == [m.get('name') for m in B['meshes']], 'mesh names')
for ma, mb in zip(A['meshes'], B['meshes']):
    check(ma.get('extras') == mb.get('extras'), f"{ma['name']} extras")
    for pa, pb in zip(ma['primitives'], mb['primitives']):
        check(pa.get('material') == pb.get('material') and pa.get('extensions') == pb.get('extensions'),
              f"{ma['name']} material mapping")
        fa = a.accessor(pa['indices']).reshape(-1, 3)
        fb = b.accessor(pb['indices']).reshape(-1, 3)
        if len(fa) != len(fb):
            bad.append(f"{ma['name']} triangle count")
            continue
        for name in pa['attributes']:
            va, vb = a.accessor(pa['attributes'][name]), b.accessor(pb['attributes'][name])
            same = np.array_equal(va[fa], vb[fb])
            if name == 'TEXCOORD_0':
                if not same:
                    print(f"{ma['name']}: UVs changed, vertices {len(va)} -> {len(vb)}")
                continue
            check(same, f"{ma['name']} {name} per corner")
ia = [(i.get('name'), a.image(k).size) for k, i in enumerate(A['images'])]
ib = [(i.get('name'), b.image(k).size) for k, i in enumerate(B['images'])]
for x, y in zip(ia, ib):
    if x != y:
        print('image', x, '->', y)
check(len(ia) == len(ib), 'image count')
print('UNEXPECTED: ' + ', '.join(bad) if bad else 'OK: only UVs, vertex splits and images differ')
sys.exit(1 if bad else 0)
