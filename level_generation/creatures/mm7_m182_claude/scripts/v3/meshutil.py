"""Small numpy mesh helpers for the v3 graft (boundary loops, components)."""
import numpy as np
from collections import defaultdict


def boundary_loops(tri):
    """Ordered boundary loops of a triangle list (each loop a list of vertex ids following the face winding)."""
    cnt = defaultdict(int); nxt = {}
    for t in tri:
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            cnt[(min(a, b), max(a, b))] += 1
    for t in tri:
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            if cnt[(min(a, b), max(a, b))] == 1:
                nxt.setdefault(b, []).append(a)   # reversed: loop runs opposite the face edge
    loops = []; seen = set()
    for s in list(nxt):
        if s in seen: continue
        loop = [s]; seen.add(s); c = s
        while True:
            n = [v for v in nxt.get(c, []) if v not in seen or v == s]
            if not n: break
            c = n[0]
            if c == s: break
            loop.append(c); seen.add(c)
        loops.append(loop)
    return loops


def components(tri, nv):
    parent = np.arange(nv)
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for t in tri:
        ra = find(t[0])
        for v in t[1:]:
            rb = find(v)
            if ra != rb: parent[rb] = ra
    return np.array([find(i) for i in range(nv)])
