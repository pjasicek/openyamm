"""Boundary loops of each component of a raw npz: edges count, centre, extents. Args: <npz> [comp]"""
import sys, numpy as np
from collections import defaultdict
D = np.load(sys.argv[1]); co, tri, comp = D['co'], D['tri'], D['comp']
cs = [int(sys.argv[2])] if len(sys.argv) > 2 else sorted(set(comp.tolist()))
for c in cs:
    t = tri[comp[tri[:, 0]] == c]; ec = defaultdict(int)
    for a, b, d in t:
        for e in ((a, b), (b, d), (d, a)): ec[(min(e), max(e))] += 1
    be = [e for e, n in ec.items() if n == 1]; nm = sum(1 for n in ec.values() if n > 2)
    adj = defaultdict(list)
    for a, b in be: adj[a].append(b); adj[b].append(a)
    seen = set(); loops = []
    for v in adj:
        if v in seen: continue
        st = [v]; seen.add(v); L = []
        while st:
            x = st.pop(); L.append(x)
            for y in adj[x]:
                if y not in seen: seen.add(y); st.append(y)
        loops.append(L)
    if not loops and not nm: continue
    print('COMP', c, 'faces', len(t), 'boundary edges', len(be), 'nonmanifold', nm)
    for L in sorted(loops, key=len, reverse=True)[:12]:
        q = co[L]; print('   loop', len(L), 'centre', q.mean(0).round(3).tolist(), 'min', q.min(0).round(3).tolist(), 'max', q.max(0).round(3).tolist())
