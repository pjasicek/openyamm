#!/usr/bin/env python3
"""Open rims of a GLB's LOD0 primitives (vertices welded by position): each boundary loop's edge count, centre (glTF, y up),
dominant bones and span. Usage: rims.py <glb> [mesh index 0]"""
import sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb  # noqa: E402

g = Glb(sys.argv[1]); mi = int(sys.argv[2]) if len(sys.argv) > 2 else 0
J = g.json; joints = J['skins'][0]['joints']; bname = [J['nodes'][j]['name'] for j in joints]


def weld(P):
    key = np.round(P, 5); _, inv = np.unique(key, axis=0, return_inverse=True); return inv.ravel()


for pi, p in enumerate(J['meshes'][mi]['primitives']):
    a = p['attributes']; P = g.accessor(a['POSITION']).astype(float); T = g.accessor(p['indices']).astype(int).reshape(-1, 3)
    Jt = g.accessor(a['JOINTS_0']).astype(int); W = g.accessor(a['WEIGHTS_0'])
    w = weld(P); TW = w[T]
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    n = w.max() + 1; r = np.r_[TW[:, 0], TW[:, 1]]; c = np.r_[TW[:, 1], TW[:, 2]]
    ncomp, comp = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)
    fc = comp[TW[:, 0]]; print('pieces', ncomp, {int(k): int(v) for k, v in zip(*np.unique(fc, return_counts=True))})
    ec = Counter()
    for t in TW:
        for i in range(3):
            e = tuple(sorted((t[i], t[(i + 1) % 3])))
            ec[e] += 1
    bnd = [e for e, c in ec.items() if c == 1]
    nonman = sum(1 for c in ec.values() if c > 2)
    rep = {}
    for k in range(len(P)):
        rep.setdefault(w[k], k)
    adj = defaultdict(list)
    for e in bnd:
        adj[e[0]].append(e); adj[e[1]].append(e)
    seen = set(); loops = []
    for e in bnd:
        if e in seen:
            continue
        st = [e]; seen.add(e); lp = []
        while st:
            x = st.pop(); lp.append(x)
            for v in x:
                for y in adj[v]:
                    if y not in seen:
                        seen.add(y); st.append(y)
        loops.append(lp)
    print(f'prim {pi} mat {p["material"]}: tris {len(T)} verts {len(P)} welded {w.max() + 1} boundary edges {len(bnd)} '
          f'loops {len(loops)} nonmanifold edges {nonman}')
    for lp in sorted(loops, key=len, reverse=True):
        vs = sorted({v for e in lp for v in e}); ks = [rep[v] for v in vs]
        dom = Counter(bname[Jt[k][np.argmax(W[k])]] for k in ks)
        c = P[ks].mean(0); span = P[ks].max(0) - P[ks].min(0)
        if len(lp) >= 4:
            print(f'  piece {comp[vs[0]]:2d} {len(lp):4d} edges c=({c[0]:+.3f},{c[1]:.3f},{c[2]:+.3f}) span=({span[0]:.3f},{span[1]:.3f},{span[2]:.3f}) '
                  + ', '.join(f'{n}:{m}' for n, m in dom.most_common(3)))
    print('  small loops (<4 edges):', sum(1 for lp in loops if len(lp) < 4))
