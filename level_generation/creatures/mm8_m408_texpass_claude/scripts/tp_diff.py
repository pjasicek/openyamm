"""What a texture-pass GLB changed against the installed one (generalised mm8_m480_texpass_claude glb_diff.py).
Must be unchanged: node names and transforms, skins and inverse binds, every animation channel's data, materials apart
from their texture indices, variants, mesh names and extras, primitive material mappings, and per triangle corner every
attribute but TEXCOORD_0 in every mesh. Reported: UVs, vertex counts, images, texture references per material.

Usage: tp_diff.py <before glb> <after glb>; exit 1 on any unexpected difference."""
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


check(A['nodes'] == B['nodes'], 'nodes')
check([s['joints'] for s in A['skins']] == [s['joints'] for s in B['skins']], 'skin joints')
for sa, sb in zip(A['skins'], B['skins']):
    check(np.array_equal(a.accessor(sa['inverseBindMatrices']), b.accessor(sb['inverseBindMatrices'])), 'inverse binds')
check([x.get('name') for x in A.get('animations', [])] == [x.get('name') for x in B.get('animations', [])], 'clips')
for ca, cb in zip(A.get('animations', []), B.get('animations', [])):
    check(ca['channels'] == cb['channels'], f"{ca['name']} channels")
    for sa, sb in zip(ca['samplers'], cb['samplers']):
        for k in ('input', 'output'):
            check(np.array_equal(a.accessor(sa[k]), b.accessor(sb[k])), f"{ca['name']} sampler {k}")
        check(sa.get('interpolation') == sb.get('interpolation'), f"{ca['name']} interpolation")


def strip(m):
    m = json.loads(json.dumps(m))

    def walk(x):
        if isinstance(x, dict):
            if 'index' in x and set(x) <= {'index', 'texCoord', 'scale', 'strength', 'extensions'}:
                x.pop('index')
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(m)
    return m


def refs(doc, m):
    out = {}

    def walk(x, path):
        if isinstance(x, dict):
            if 'index' in x and isinstance(x['index'], int) and path:
                img = doc['images'][doc['textures'][x['index']]['source']]
                out[path] = img.get('name')
            for k, v in x.items():
                walk(v, k)
    walk(m, '')
    return out


check([strip(m) for m in A['materials']] == [strip(m) for m in B['materials']], 'materials (other than textures)')
for ma, mb in zip(A['materials'], B['materials']):
    ra, rb = refs(A, ma), refs(B, mb)
    if ra != rb:
        print('material', ma.get('name'), 'textures', {k: (ra.get(k), rb.get(k)) for k in set(ra) | set(rb)
                                                        if ra.get(k) != rb.get(k)})
check(A.get('extensions') == B.get('extensions'), 'variants')
check([m.get('name') for m in A['meshes']] == [m.get('name') for m in B['meshes']], 'mesh names')
for ma, mb in zip(A['meshes'], B['meshes']):
    check(ma.get('extras') == mb.get('extras'), f"{ma['name']} extras")
    for k, (pa, pb) in enumerate(zip(ma['primitives'], mb['primitives'])):
        check(pa.get('material') == pb.get('material') and pa.get('extensions') == pb.get('extensions'),
              f"{ma['name']} material mapping")
        check(sorted(pa['attributes']) == sorted(pb['attributes']), f"{ma['name']} attribute set")
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
                    print(f"{ma['name']} p{k}: UVs changed, vertices {len(va)} -> {len(vb)}")
                continue
            check(same, f"{ma['name']} p{k} {name} per corner")
ia = sorted((i.get('name'), a.image(k).size) for k, i in enumerate(A['images']))
ib = sorted((i.get('name'), b.image(k).size) for k, i in enumerate(B['images']))
print('images removed', [x for x in ia if x not in ib])
print('images added', [x for x in ib if x not in ia])
print('UNEXPECTED: ' + ', '.join(bad) if bad else 'OK: only UVs, vertex splits, images and texture references differ')
sys.exit(1 if bad else 0)
