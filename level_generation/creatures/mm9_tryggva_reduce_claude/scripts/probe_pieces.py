"""List connected pieces (welded by position) per primitive with dominant joint, face count and bounds.
usage: probe_pieces.py <glb> <node>"""
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(sys.argv[1], sys.argv[2])
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
for name, d in D.items():
    P, T, J, W = d['P'], d['T'], d['J'], d['W']
    _, inv = np.unique(P.round(6), axis=0, return_inverse=True); inv = inv.ravel(); TT = inv[T]; n = inv.max() + 1
    e = np.concatenate([TT[:, [0, 1]], TT[:, [1, 2]], TT[:, [2, 0]]])
    _, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
    fl = lab[TT[:, 0]]
    acc = np.zeros((len(T), len(jn)))
    for c in range(3):
        for i in range(4):
            np.add.at(acc, (np.arange(len(T)), J[T[:, c], i]), W[T[:, c], i])
    dj = acc.argmax(1)
    print(name, len(T), 'floor', P[:, 1].min().round(4), 'top', P[:, 1].max().round(4))
    for c in sorted(np.unique(fl), key=lambda c: -(fl == c).sum()):
        m = fl == c; vs = P[np.unique(T[m])]
        u, cnt = np.unique(dj[m], return_counts=True); o = np.argsort(-cnt)[:3]
        print(f'  piece {c:3d} tris {m.sum():5d} lo {vs.min(0).round(3)} hi {vs.max(0).round(3)}',
              ', '.join(f'{jn[u[i]].replace("Bip01 ", "")}:{cnt[i]}' for i in o))
