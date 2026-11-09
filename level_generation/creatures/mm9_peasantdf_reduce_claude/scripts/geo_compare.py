#!/usr/bin/env python3
"""Compare DF1 against DF2-4 per primitive: vertex match by position (KD tree), UV / joints / weights equality, and
triangle-set equality under the matching."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes

def arr(doc, b, i):
    a = doc['accessors'][i]; n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    ct = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[a['componentType']]
    x = np.frombuffer(accessor_bytes(doc, b, i), ct); return x.reshape(-1, n) if n > 1 else x

def lod0(path):
    doc, b = read_glb(Path(path)); out = []
    for p in doc['meshes'][0]['primitives']:
        a = p['attributes']
        out.append({k: arr(doc, b, a[v]).astype(float) for k, v in
                    dict(P='POSITION', UV='TEXCOORD_0', N='NORMAL', J='JOINTS_0', W='WEIGHTS_0').items()} |
                   {'T': arr(doc, b, p['indices']).astype(int).reshape(-1, 3)})
    return out

ref = lod0('before/mm9_peasantdf1.glb')
for n in '234':
    oth = lod0(f'before/mm9_peasantdf{n}.glb')
    for pi, (A, B) in enumerate(zip(ref, oth)):
        # match B vertices to A by position+uv
        ka = np.hstack([A['P'], A['UV'] * 0.01]); kb = np.hstack([B['P'], B['UV'] * 0.01])
        d, idx = cKDTree(ka).query(kb)
        dp = np.linalg.norm(A['P'][idx] - B['P'], axis=1); du = np.abs(A['UV'][idx] - B['UV']).max(1)
        moved = dp > 1e-5
        print(f'df{n} prim{pi}: verts {len(A["P"])}/{len(B["P"])} pos diff p50 {np.median(dp)*1000:.3f} mm max {dp.max()*1000:.2f} mm, moved>0.01mm {moved.sum()}, uv max {du.max():.2e}, uv>1e-4 {(du>1e-4).sum()}')
        # triangle sets
        if len(A['P']) == len(B['P']):
            ta = set(tuple(sorted(t)) for t in A['T']); tb = set(tuple(sorted(idx[t])) for t in B['T'])
            print(f'   tris {len(A["T"])}/{len(B["T"])} common (as vertex sets under match) {len(ta & tb)}')
            wd = np.abs(np.sort(A['W'][idx],1) - np.sort(B['W'],1)).max(1)
            print(f'   weight diff >1e-3: {(wd>1e-3).sum()}  (max {wd.max():.3f})')
            if moved.sum():
                mv = B['P'][moved]
                print(f'   moved bbox y {mv[:,1].min():.3f}..{mv[:,1].max():.3f} x {mv[:,0].min():.3f}..{mv[:,0].max():.3f} z {mv[:,2].min():.3f}..{mv[:,2].max():.3f}')
for pi, A in enumerate(ref):
    print('df1 prim', pi, 'bbox', A['P'].min(0).round(3), A['P'].max(0).round(3))
