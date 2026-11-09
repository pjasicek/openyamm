"""Plane sections of a triangle mesh (numpy): loops, centroids, perimeters."""
import numpy as np


def section(co, tri, pt, n):
    """All closed loops of the plane (pt, n): list of dict(c=centroid, per=perimeter, pts=midpoints)."""
    d = (co - pt) @ n
    s = np.sign(d); s[s == 0] = 1
    t = tri[(s[tri].min(1) < 0) & (s[tri].max(1) > 0)]
    seg = {}
    nodes = {}
    for f in t:
        hits = []
        for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])):
            if s[a] != s[b]:
                k = (min(a, b), max(a, b))
                u = d[a] / (d[a] - d[b])
                nodes[k] = co[a] + (co[b] - co[a]) * u
                hits.append(k)
        if len(hits) == 2:
            seg.setdefault(hits[0], []).append(hits[1]); seg.setdefault(hits[1], []).append(hits[0])
    loops = []; seen = set()
    for k in seg:
        if k in seen: continue
        st = [k]; seen.add(k); ids = []
        while st:
            x = st.pop(); ids.append(x)
            for y in seg[x]:
                if y not in seen: seen.add(y); st.append(y)
        pts = np.array([nodes[i] for i in ids])
        per = 0.0; w = np.zeros(len(ids)); idx = {i: j for j, i in enumerate(ids)}
        for i in ids:
            for y in seg[i]:
                if idx[y] > idx[i]:
                    l = np.linalg.norm(nodes[i] - nodes[y]); per += l; w[idx[i]] += l / 2; w[idx[y]] += l / 2
        c = (pts * w[:, None]).sum(0) / max(w.sum(), 1e-9)
        loops.append(dict(c=c, per=per, pts=pts, n=len(ids)))
    return loops


def nearest_loop(loops, p):
    return min(loops, key=lambda l: np.linalg.norm(l['c'] - p)) if loops else None
