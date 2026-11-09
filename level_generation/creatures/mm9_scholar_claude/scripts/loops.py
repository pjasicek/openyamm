#!/usr/bin/env python3
"""Boundary loops per component. Args: npz comp..."""
import sys, numpy as np
D = np.load(sys.argv[1]); co, tri, comp = D['co'], D['tri'], D['comp']
for c in map(int, sys.argv[2:]):
    t = tri[comp[tri[:, 0]] == c]
    e = np.sort(np.vstack([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), 1)
    u, n = np.unique(e, axis=0, return_counts=True); bd = u[n == 1]
    adj = {}
    for a, b in bd: adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    seen = set(); loops = []
    for k in adj:
        if k in seen: continue
        st = [k]; ids = []; seen.add(k)
        while st:
            x = st.pop(); ids.append(x)
            for y in adj[x]:
                if y not in seen: seen.add(y); st.append(y)
        loops.append(ids)
    print('comp', c, 'tris', len(t), 'loops', len(loops), 'bad', sum(1 for v in adj.values() if len(v) != 2), 'bounds', co[comp == c].min(0).round(3), co[comp == c].max(0).round(3))
    for l in sorted(loops, key=len, reverse=True)[:14]:
        q = co[l]; print('  ', len(l), q.mean(0).round(3), 'ext', np.ptp(q, 0).round(3))
