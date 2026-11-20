#!/usr/bin/env python3
"""Open boundary loops of the installed LOD0 (welded by position): per primitive, connected pieces (welded) and their open
loops (edges used by one face) with size, centre (GLB rest, Y up), radius and the dominant joints of their vertices.
Read-only. Usage: open_loops.py [glb] [mesh name, default Sven]"""
import sys
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402

glb = sys.argv[1] if len(sys.argv) > 1 else str(HERE / 'before' / 'mm9_sven.glb')
node = sys.argv[2] if len(sys.argv) > 2 else 'Sven'
doc, binary, nd, D = glbio.load(glb, node)
jn = [doc['nodes'][j]['name'] for j in doc['skins'][nd['skin']]['joints']]


def weld(P):
    _, inv = np.unique(P.round(6), axis=0, return_inverse=True)
    return inv.ravel()


def loops_of(TT):
    ec = Counter()
    for t in TT:
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            ec[(min(a, b), max(a, b))] += 1
    bnd = [e for e, c in ec.items() if c == 1]
    adj = defaultdict(list)
    for a, b in bnd:
        adj[a].append(b); adj[b].append(a)
    seen, out = set(), []
    for v in adj:
        if v in seen:
            continue
        st, comp = [v], []
        seen.add(v)
        while st:
            x = st.pop(); comp.append(x)
            for y in adj[x]:
                if y not in seen:
                    seen.add(y); st.append(y)
        out.append(comp)
    return out, bnd


for name, d in D.items():
    P, T, J, W = d['P'], d['T'], d['J'], d['W']
    inv = weld(P); TT = inv[T]; n = inv.max() + 1
    Pw = np.zeros((n, 3)); Pw[inv] = P
    Jw = np.zeros((n, 4), int); Jw[inv] = J; Ww = np.zeros((n, 4)); Ww[inv] = W
    e = np.concatenate([TT[:, [0, 1]], TT[:, [1, 2]], TT[:, [2, 0]]])
    _, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
    fl = lab[TT[:, 0]]
    print(f'== {name}: {len(T)} faces, {n} welded verts, pieces {len(np.unique(fl))}')
    for c in np.unique(fl):
        m = fl == c
        lps, _ = loops_of(TT[m])
        vs = np.unique(TT[m])
        lo, hi = Pw[vs].min(0), Pw[vs].max(0)
        print(f' piece {c:3d} faces {m.sum():5d} lo {lo.round(3)} hi {hi.round(3)} open loops {len(lps)}')
        for lp in sorted(lps, key=len, reverse=True):
            if len(lp) < 4:
                continue
            q = Pw[lp]; cen = q.mean(0); r = np.linalg.norm(q - cen, axis=1).mean()
            dom = Counter(jn[Jw[v][np.argmax(Ww[v])]] for v in lp).most_common(3)
            print(f'    loop {len(lp):4d} verts cen {cen.round(3)} r {r:.3f} {dom}')
