#!/usr/bin/env python3
"""Greater Demon LOD0 composition: per primitive connected components (welded by position), their sizes, dominant bones.
Writes work/analyse.npz: per GLB face (concatenated in primitive order) prim, comp, comp_size, dominant joint name."""
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as glbio
doc, binary = glbio.read(HERE / 'before' / 'mm9_greaterdemon.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'GreaterDemon' and 'mesh' in n)
joints = [doc['nodes'][j]['name'] for j in doc['skins'][node['skin']]['joints']]
prims = glbio.prims(doc, binary, node['mesh'])
out = dict(prim=[], comp=[], csize=[], dom=[], cen=[])
cbase = 0
for pi, pr in enumerate(prims):
    P = pr['POSITION'].astype(float); T = pr['T']; J = pr['JOINTS_0']; W = pr['WEIGHTS_0'].astype(float)
    _, tp = np.unique(np.round(P, 5), axis=0, return_inverse=True); tp = tp.reshape(-1)
    TF = tp[T]; n = tp.max() + 1
    r = np.concatenate([TF[:, 0], TF[:, 1], TF[:, 2]]); c = np.concatenate([TF[:, 1], TF[:, 2], TF[:, 0]])
    nc, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)
    fl = lab[TF[:, 0]]
    sizes = np.bincount(fl, minlength=nc)
    domv = J[np.arange(len(J)), W.argmax(1)]
    # face dominant joint = majority of its vertices' dominant joints
    fd = domv[T]
    fdom = np.array([np.bincount(x).argmax() for x in fd])
    print(f"{pr['material']}: {len(T)} faces, {len(P)} verts, {nc} components")
    hist = {}
    for s in sizes:
        b = '1-20' if s <= 20 else '21-60' if s <= 60 else '61-200' if s <= 200 else '>200'
        hist[b] = hist.get(b, (0, 0)); hist[b] = (hist[b][0] + 1, hist[b][1] + s)
    print('   size bins (count, faces):', hist)
    for k in np.argsort(-sizes)[:8]:
        sel = fl == k; bones = np.bincount(fdom[sel]); top = np.argsort(-bones)[:4]
        print(f'   comp {k}: {sizes[k]} faces, bones', [(joints[b], int(bones[b])) for b in top if bones[b]])
    out['prim'].append(np.full(len(T), pi)); out['comp'].append(fl + cbase); out['csize'].append(sizes[fl])
    out['dom'].append(fdom); out['cen'].append(P[T].mean(1)); cbase += nc
    bones = np.bincount(fdom, minlength=len(joints))
    print('   faces by dominant bone:', [(joints[b], int(bones[b])) for b in np.argsort(-bones)[:30] if bones[b]])
np.savez(HERE / 'work' / 'analyse.npz', **{k: np.concatenate(v) for k, v in out.items()}, joints=np.array(joints))
