#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep masks.
MM7 Ooze (m298, faces -y). Pieces: the blob (3,294 faces, lump weights), the pseudopod (600 faces: lumpy lathe stalk on
PodRoot/Pod1-5 and the onion knob rigid on Knob) and 12 globules (64 faces each, rigid on Glob_NN). The pieces are
separate shells and must stay separate (no triangle may join two of them).
Labels: 0 blob, 1 stalk (Pod-dominated faces of the pod piece), 2 knob (Knob-dominated), 3 globules.
work/keep_base.npy keeps pod, knob and globules exactly (blob-only ladder); work/keep_none.npy keeps nothing."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc); blob = np.argmax(sizes)
dom = info['dom'].astype(str)
pod = np.array([s.startswith('Pod') or s == 'Knob' for s in dom])
podpiece = np.bincount(pc[pod]).argmax()
g = np.full(len(f), 3)
g[pc == blob] = 0
g[(pc == podpiece)] = 1
g[(pc == podpiece) & (dom == 'Knob')] = 2
np.save('work/groups.npy', g); np.save('work/keep_base.npy', g != 0); np.save('work/keep_none.npy', np.zeros(len(f), bool))
np.save('work/pieces.npy', pc)
print('GROUPS', {k: int((g == k).sum()) for k in range(4)}, 'pieces', len(sizes))
