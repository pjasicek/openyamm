#!/usr/bin/env python3
"""List the open boundary loops (welded by position) of each LOD0 primitive of a PeasantM1d GLB: edges, centre (GLB space,
y up), mean radius, dominant joint, connected piece and its size. Usage: rims.py <glb> [min_edges 3]"""
import sys
from collections import defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glbio  # noqa: E402
glb = sys.argv[1]; MIN = int(sys.argv[2]) if len(sys.argv) > 2 else 3
doc, binary, nd, D = glbio.load(glb, 'PM1d')
jn = [doc['nodes'][j]['name'] for j in doc['skins'][nd['skin']]['joints']]
for name, d in D.items():
    P, T, J, W = d['P'], d['T'], d['J'], d['W']
    _, inv = np.unique(P.round(6), axis=0, return_inverse=True); inv = inv.ravel(); TT = inv[T]
    # pieces
    par = list(range(inv.max() + 1))
    def f(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for t in TT:
        a, b, c = f(t[0]), f(t[1]), f(t[2]); par[b] = a; par[f(c)] = a
    piece = np.array([f(x) for x in range(len(par))]); psize = defaultdict(int)
    for t in TT: psize[piece[t[0]]] += 1
    ec = defaultdict(int)
    for t in TT:
        for i in range(3):
            ec[tuple(sorted((t[i], t[(i + 1) % 3])))] += 1
    bnd = [e for e, n in ec.items() if n == 1]
    nonman = sum(1 for n in ec.values() if n > 2)
    adj = defaultdict(list)
    for a, b in bnd: adj[a].append(b); adj[b].append(a)
    seen = set(); loops = []
    for e in bnd:
        if e[0] in seen: continue
        st = [e[0]]; comp = []
        while st:
            x = st.pop()
            if x in seen: continue
            seen.add(x); comp.append(x); st += adj[x]
        loops.append(comp)
    wp = np.zeros((inv.max() + 1, 3)); wp[inv] = P
    dj = np.zeros(inv.max() + 1, int); dj[inv] = J[np.arange(len(J)), W.argmax(1)]
    print(f'== {name}: {len(T)} tris, {len(bnd)} boundary edges, {len(loops)} loops, non-manifold edges {nonman}')
    for comp in sorted(loops, key=len, reverse=True):
        if len(comp) < MIN: continue
        c = wp[comp].mean(0); r = np.linalg.norm(wp[comp] - c, axis=1).mean()
        u, cnt = np.unique(dj[comp], return_counts=True)
        doms = ', '.join(f'{jn[a]}:{b}' for a, b in sorted(zip(u, cnt), key=lambda x: -x[1])[:3])
        print(f'  {len(comp):3d} v  c {np.round(c, 3)}  r {r * 100:5.1f} cm  piece {piece[comp[0]]} ({psize[piece[comp[0]]]} tris)  {doms}')
