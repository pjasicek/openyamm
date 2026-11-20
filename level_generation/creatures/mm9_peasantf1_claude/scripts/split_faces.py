#!/usr/bin/env python3
"""Face-connected shells of component 0 (over edges used by exactly two faces); writes vertices split per shell. Args: in out"""
import sys, numpy as np
from collections import defaultdict
D = dict(np.load(sys.argv[1])); co, tri, comp = D['co'], D['tri'], D['comp']
f0 = np.where(comp[tri[:, 0]] == 0)[0]
ed = defaultdict(list)
for f in f0:
    a, b, c = tri[f]
    for e in ((a, b), (b, c), (c, a)): ed[tuple(sorted(e))].append(f)
adj = defaultdict(list)
nm = 0
for e, fs in ed.items():
    if len(fs) == 2: adj[fs[0]].append(fs[1]); adj[fs[1]].append(fs[0])
    elif len(fs) > 2: nm += 1
print('non-manifold edges', nm)
lab = {}; n = 0; sizes = []
for f in f0:
    if f in lab: continue
    st = [f]; lab[f] = n; c = 0
    while st:
        x = st.pop(); c += 1
        for y in adj[x]:
            if y not in lab: lab[y] = n; st.append(y)
    sizes.append(c); n += 1
for k in range(n):
    fs = [f for f in f0 if lab[f] == k]; v = np.unique(tri[fs]); print(k, sizes[k], co[v].min(0).round(3), co[v].max(0).round(3))
