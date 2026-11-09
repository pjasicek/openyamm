"""Per-face groups of the welded source: 0 back skin and the rest of the main head, 1 face (grey face-region faces of
the main head except the horns), 2 horns (the two large face-region clusters at the sides), 9 separate pieces
(eyeball, brow ring, lips, gum, teeth). -> work/groups_bh.npy, work/keep_pieces.npy, work/keep_pieces_horns.npy"""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); v, f = d['verts'], d['faces']
comp = np.load('work/components.npy'); reg = np.load('work/mask_region.npy')
sel = np.where((comp == 1) & (reg == 1))[0]
edges = {}
for k, fi in enumerate(sel):
    a, b, c = f[fi]
    for e in ((a, b), (b, c), (c, a)):
        edges.setdefault((min(e), max(e)), []).append(k)
pairs = np.array([(l[0], l[1]) for l in edges.values() if len(l) == 2])
_, lab = connected_components(coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(len(sel),) * 2),
                              directed=False)
ctr = v[f[sel]].mean(1); g = np.zeros(len(f), int); g[sel] = 1
for k in np.unique(lab):
    s = lab == k
    if s.sum() > 200 and abs(ctr[s, 0].mean()) > .25:
        g[sel[s]] = 2
g[comp != 1] = 9
np.save('work/groups_bh.npy', g); np.save('work/keep_pieces.npy', g == 9); np.save('work/keep_pieces_horns.npy', (g == 9) | (g == 2))
print({k: int((g == k).sum()) for k in (0, 1, 2, 9)})
