"""Shared: per-face piece labels of work/mesh_in.npz (welded source): connected component, material, dominant bone,
size, open edges, category. Import and call pieces()."""
import re
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components


def pieces(work='work'):
    d = np.load(f'{work}/mesh_in.npz'); sw = np.load(f'{work}/src_weights.npz')
    V, F = d['verts'], d['faces']; W = sw['weights']; names = [str(n) for n in sw['names']]
    mat = (d['wuv'].reshape(-1, 3, 2)[:, 0, 0] // 2).astype(int)
    n = len(V)
    r = np.concatenate([F[:, 0], F[:, 1], F[:, 2]]); c = np.concatenate([F[:, 1], F[:, 2], F[:, 0]])
    _, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)
    comp = lab[F[:, 0]]
    e = np.sort(np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1)
    ek, inv, cnt = np.unique(e, axis=0, return_inverse=True, return_counts=True)
    open_face = (cnt[inv.ravel()] == 1).reshape(3, -1).T.any(1)
    info = {}
    for k in np.unique(comp):
        s = np.where(comp == k)[0]; vs = np.unique(F[s])
        bone = names[int(W[vs].sum(0).argmax())]
        size = float(np.ptp(V[vs], 0).max())
        m = int(np.bincount(mat[s]).argmax())
        b = bone
        if m == 1:
            cat = 'head'
        elif m == 2:
            cat = 'dagger'
        elif open_face[s].any() and len(s) > 30:
            cat = 'sheet'
        elif re.search('Hand|Thumb|Index|Middle|Ring|Pinky', b):
            cat = 'hand'
        elif 'Foot' in b or 'Toe' in b:
            cat = 'foot'
        elif re.search('UpperArm|Forearm|Clavicle|Thigh|Calf', b):
            cat = 'limb'
        else:
            cat = 'torso'
        info[int(k)] = dict(n=len(s), bone=bone, size=size, mat=m, cat=cat, open=int(open_face[s].sum()),
                            cen=V[vs].mean(0))
    return V, F, mat, comp, info
