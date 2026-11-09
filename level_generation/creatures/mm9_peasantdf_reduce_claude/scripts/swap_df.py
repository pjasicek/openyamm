#!/usr/bin/env python3
"""One cut, four designs: DF1's reduced LOD0 triangles (work/mp_<..>.npz from mpqem_df.py, indices into DF1's LOD0
vertices) -> a LOD0-only GLB of design <n> built on that design's installed GLB.
- body primitive: every DF1 vertex has a byte-identical vertex in the design (design_map.py) except the three corners of
  the one-texel face 6310, which is in the keep set and is taken from the design's own row 6310;
- head primitive: the design's own installed rows for everything but the hands (face skin, ears, hair/hood shell and twin,
  DF3's braids: exact), plus DF1's reduced hand triangles mapped onto the design's hand vertices.
Each primitive keeps only the vertices it still uses, every attribute copied byte for byte; LOD and shadow meshes are
dropped (build_lods.py rebuilds them); materials, variants, images, clips, skin and nodes are unchanged.
Usage: swap_df.py <n> <mp npz> <out.glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glbpack as G  # noqa: E402
import glbio  # noqa: E402
n, mp, out = sys.argv[1:4]
HERE = Path(__file__).resolve().parents[1]
sets = np.load(HERE / 'work' / 'glb_sets_a.npz')
dm = np.load(HERE / 'work' / 'design_map.npz'); d = np.load(mp)
_, _, _, D1 = glbio.load(HERE / 'before' / 'mm9_peasantdf1.glb', 'PeasantDF')
names1 = list(D1); nb = len(D1[names1[0]]['T'])
hand1 = sets['part'][nb:] == 13
doc, binary = G.read(str(HERE / 'before' / f'mm9_peasantdf{n}.glb'))
node = next(x for x in doc['nodes'] if x.get('name') == 'PeasantDF' and 'mesh' in x)
mesh = doc['meshes'][node['mesh']]; counts = {}
for pi, p in enumerate(mesh['primitives']):
    T0 = G.acc(doc, bytes(binary), p['indices']).reshape(-1, 3).astype(np.int64)
    R = d[names1[pi]].astype(np.int64)                       # DF1 indices
    if n == '1':
        T = R
    else:
        m = dm[f'map_{n}_{pi}']
        if pi == 0:
            odd = (m[R] < 0).any(1)
            T1 = D1[names1[0]]['T']
            assert odd.sum() == 1 and (np.sort(R[odd][0]) == np.sort(T1[6310])).all(), odd.sum()
            T = m[R]; T[odd] = T0[6310]                     # the design's own one-texel face
        else:
            # DF1 hand faces -> design faces: same in every design (make_sets_df.py asserts)
            hv1 = np.unique(D1[names1[1]]['T'][hand1]); hvn = set(m[hv1].tolist())
            own_hand = np.array([set(t) <= hvn for t in T0.tolist()])
            assert own_hand.sum() == hand1.sum(), (own_hand.sum(), hand1.sum())
            rh = R[np.isin(R, hv1).all(1)]
            assert (m[rh] >= 0).all()
            T = np.concatenate([T0[~own_hand], m[rh]])
            assert len(R) - len(rh) == len(T0) - own_hand.sum() if n != '3' else True
    counts[doc['materials'][p['material']]['name']] = len(T)
    if T.shape == T0.shape and (T == T0).all():
        continue
    used = np.unique(T); remap = -np.ones(doc['accessors'][p['attributes']['POSITION']]['count'], np.int64)
    remap[used] = np.arange(len(used))
    for sem, i in list(p['attributes'].items()):
        rows = G.raw_rows(doc, binary, i)[used]
        p['attributes'][sem] = G.append(doc, binary, doc['accessors'][i], rows)
        G.set_minmax(doc, binary, p['attributes'][sem])
    ct = doc['accessors'][p['indices']]['componentType']; assert len(used) < 65536 or ct == 5125
    p['indices'] = G.append(doc, binary, {'componentType': ct, 'type': 'SCALAR'},
                            remap[T].reshape(-1).astype(np.uint16 if ct == 5123 else np.uint32).reshape(-1, 1))
mesh.pop('extras', None)
keep = sorted({x['mesh'] for x in doc['nodes'] if 'mesh' in x}); mmap = {o: k for k, o in enumerate(keep)}
doc['meshes'] = [doc['meshes'][i] for i in keep]
for x in doc['nodes']:
    if 'mesh' in x:
        x['mesh'] = mmap[x['mesh']]
doc, binary = G.compact(doc, binary)
G.write(out, doc, binary)
print('SWAPPED', n, counts, 'total', sum(counts.values()))
