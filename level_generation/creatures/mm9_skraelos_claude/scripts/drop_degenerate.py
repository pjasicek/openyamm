#!/usr/bin/env python3
"""Drop back-to-back duplicate triangles (the same welded vertex triple twice: decimation collapsed a tooth into a two-sided sliver, which the
winding check reads as an inverted closed part) and zero-area triangles from a mesh npz. Positions, UVs and the other faces are unchanged.
Args: <in npz> <out npz>"""
import sys
import numpy as np
from collections import Counter
D = dict(np.load(sys.argv[1])); t = D['tri']; co = D['co']; names = [str(x) for x in D['names']]
key = np.round(co, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
s = [tuple(x) for x in np.sort(inv[t], 1)]; cnt = Counter(s)
area = np.linalg.norm(np.cross(co[t[:, 1]] - co[t[:, 0]], co[t[:, 2]] - co[t[:, 0]]), axis=1)
bad = np.array([cnt[x] > 1 for x in s]) | (area < 1e-10) | (np.array([len(set(x)) for x in s]) < 3)
print('DROP', int(bad.sum()), 'faces', Counter(names[D['comp'][t[i, 0]]] for i in np.where(bad)[0]))
keep = ~bad
for k in ('tri', 'mat', 'inner'):
    if k in D and len(D[k]) == len(t): D[k] = D[k][keep]
np.savez(sys.argv[2], **D)
