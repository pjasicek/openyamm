"""Structure of the installed PeasantM3 LOD0: one-texel faces, own-paint twins (faces whose UV triplet equals another face's),
components, dominant joints. Read-only."""
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantm3.glb', 'PeasantM3')
jn = [doc['nodes'][j]['name'] for j in doc['skins'][nd['skin']]['joints']]
for name, d in D.items():
    P, T, UV = d['P'], d['T'], d['UV']
    print(name, 'verts', len(P), 'tris', len(T), 'bbox', P.min(0).round(3), P.max(0).round(3))
    uvt = UV[T]; span = (uvt.max(1) - uvt.min(1)).max(1)
    one = span < 1.5 / 2048
    print('  one-texel faces', int(one.sum()))
    # components by shared vertex positions
    key = np.unique(np.round(P, 6), axis=0, return_inverse=True)[1].ravel()
    TT = key[T]; n = TT.max() + 1
    r = np.concatenate([TT[:, 0], TT[:, 1], TT[:, 2]]); c = np.concatenate([TT[:, 1], TT[:, 2], TT[:, 0]])
    ncomp, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)
    fl = lab[TT[:, 0]]; u, cnt = np.unique(fl, return_counts=True)
    order = np.argsort(-cnt)
    print('  components', ncomp, 'face counts', cnt[order][:30].tolist())
    # twins: identical UV triplet (sorted) on two faces
    kuv = np.sort(np.round(uvt * 8192).astype(np.int64).reshape(len(T), 3, 2).view([('a', np.int64), ('b', np.int64)]).ravel()
                  .reshape(len(T), 3), axis=1) if False else None
    q = np.round(uvt * 65536).astype(np.int64); q = q[:, :, 0] * 1000003 + q[:, :, 1]; q = np.sort(q, 1)
    _, inv, cnts = np.unique(q, axis=0, return_inverse=True, return_counts=True)
    dup = (cnts[inv.ravel()] >= 2) & ~one
    print('  faces sharing a UV triplet (not one-texel)', int(dup.sum()))
    acc = np.zeros((len(T), len(jn)))
    for k in range(3):
        for i in range(4):
            np.add.at(acc, (np.arange(len(T)), d['J'][T[:, k], i]), d['W'][T[:, k], i])
    dj = acc.argmax(1)
    for cid in u[order][:20]:
        m = fl == cid
        uj, cj = np.unique(dj[m], return_counts=True); top = np.argsort(-cj)[:4]
        print(f'   comp {cid}: {m.sum()} faces, one-texel {int((one & m).sum())}, uvdup {int((dup & m).sum())}, z {P[T[m]][:, :, 1].min():.3f}..{P[T[m]][:, :, 1].max():.3f}',
              {jn[uj[t]]: int(cj[t]) for t in top})
