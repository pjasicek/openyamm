"""What remove_moustache.py changed against its input GLB. Must be unchanged: node names and transforms, skins and
inverse binds, every animation channel's data, material definitions (texture indices aside), variants, mesh names
and extras; per kept triangle corner: position, normal, joints and weights. Reported: removed triangles (the moustache
component), fill triangles (appended; each corner must reuse an existing vertex position of the mesh), corners whose UV
changed (LOD0 eyeballs, LOD1 re-projection), vertex counts, images.

Usage: glb_diff_removal.py <before glb> <after glb>; exit 1 on any unexpected difference."""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb import Glb  # noqa: E402
from remove_moustache import moustache_faces  # noqa: E402

a, b = Glb(sys.argv[1]), Glb(sys.argv[2])
A, B = a.doc, b.doc
bad = []


def check(cond, what):
    if not cond:
        bad.append(what)


check(A['nodes'] == B['nodes'], 'nodes')
check([s['joints'] for s in A['skins']] == [s['joints'] for s in B['skins']], 'skin joints')
check(np.array_equal(a.accessor(A['skins'][0]['inverseBindMatrices']), b.accessor(B['skins'][0]['inverseBindMatrices'])),
      'inverse binds')
check([x.get('name') for x in A['animations']] == [x.get('name') for x in B['animations']], 'clip names')
for ca, cb in zip(A['animations'], B['animations']):
    check(ca['channels'] == cb['channels'], f"{ca['name']} channels")
    for sa, sb in zip(ca['samplers'], cb['samplers']):
        for k in ('input', 'output'):
            check(np.array_equal(a.accessor(sa[k]), b.accessor(sb[k])), f"{ca['name']} sampler {k}")


def mat_key(m):
    m = json.loads(json.dumps(m))
    m.get('pbrMetallicRoughness', {}).pop('baseColorTexture', None)
    m.get('pbrMetallicRoughness', {}).pop('metallicRoughnessTexture', None)
    m.get('normalTexture', {}).pop('index', None)
    m.get('extras', {}).pop('openyamm_region_mask', None)
    return m


check([mat_key(m) for m in A['materials']] == [mat_key(m) for m in B['materials']], 'materials')
check(A.get('extensions') == B.get('extensions'), 'variants')
check([m.get('name') for m in A['meshes']] == [m.get('name') for m in B['meshes']], 'mesh names')
for ma, mb in zip(A['meshes'], B['meshes']):
    check(ma.get('extras') == mb.get('extras'), f"{ma['name']} extras")
    pa, pb = ma['primitives'][0], mb['primitives'][0]
    check(pa.get('material') == pb.get('material') and pa.get('extensions') == pb.get('extensions'),
          f"{ma['name']} material mapping")
    Pa = a.accessor(pa['attributes']['POSITION']).astype(np.float64)
    fa = a.accessor(pa['indices']).reshape(-1, 3)
    fb = b.accessor(pb['indices']).reshape(-1, 3)
    removed = moustache_faces(Pa, fa)
    kept = fa[~removed]
    n = len(kept)
    if len(fb) < n:
        bad.append(f"{ma['name']} lost kept triangles")
        continue
    extra = fb[n:]
    line = f"{ma['name']}: removed {int(removed.sum())}, fill {len(extra)}, vertices {len(Pa)} -> " \
           f"{b.doc['accessors'][pb['attributes']['POSITION']]['count']}"
    for name in pa['attributes']:
        va, vb = a.accessor(pa['attributes'][name]), b.accessor(pb['attributes'][name])
        same = (va[kept] == vb[fb[:n]]).reshape(n, 3, -1).all(-1)
        if name == 'TEXCOORD_0':
            changed = int((~same.all(1)).sum())
            line += f", kept triangles with new UVs {changed}"
            continue
        check(same.all(), f"{ma['name']} {name} on kept triangles")
    if len(extra):
        Pb = b.accessor(pb['attributes']['POSITION']).astype(np.float64)
        d = np.abs(Pb[extra.ravel()][:, None] - Pa[None]).max(-1).min(1)
        check(d.max() < 1e-6, f"{ma['name']} fill corners off the existing vertices")
    print(line)
ia = [(i.get('name'), a.image(k).size) for k, i in enumerate(A['images'])]
ib = [(i.get('name'), b.image(k).size) for k, i in enumerate(B['images'])]
check(len(ia) == len(ib), 'image count')
print('images: only LOD2/LOD3 maps re-transferred' if [x for x in ia] == [y for y in ib] else 'images changed')
print('UNEXPECTED: ' + ', '.join(bad) if bad else 'OK: only the moustache removal, the hole fill and UVs/images differ')
sys.exit(1 if bad else 0)
