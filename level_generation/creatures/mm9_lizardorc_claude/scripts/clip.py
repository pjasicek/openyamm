"""Clip a triangle mesh with a plane, keeping d >= 0. New vertices on the plane, shared per edge. Extra per-vertex arrays are interpolated. Faces to clip may be restricted by mask `only` (others kept or dropped by their centroid side)."""
import numpy as np
def clip(P, T, p0, n, extras=(), only=None):
    d = (P - p0) @ n; d = np.where(np.abs(d) < 1e-7, 1e-7, d)
    Pn = [P]; Ex = [[e] for e in extras]; nv = len(P); cache = {}
    def cut(a, b):
        nonlocal nv
        k = (min(a, b), max(a, b))
        if k in cache: return cache[k]
        t = d[a] / (d[a] - d[b]); Pn.append((P[a] + (P[b] - P[a]) * t)[None])
        for i, e in enumerate(extras): Ex[i].append((e[a] + (e[b] - e[a]) * t)[None])
        cache[k] = nv; nv += 1; return nv - 1
    out = []; rim = []
    for fi, f in enumerate(T):
        s = d[f] > 0
        if only is not None and not only[fi]:
            if only[fi] == 0 and (d[f].mean() > 0): out.append(f)
            continue
        c = s.sum()
        if c == 3: out.append(f)
        elif c == 0: continue
        else:
            i = int(np.where(s if c == 1 else ~s)[0][0]); a, b, e = f[i], f[(i + 1) % 3], f[(i + 2) % 3]
            q1, q2 = cut(a, b), cut(a, e); rim += [q1, q2]
            if c == 1: out.append([a, q1, q2])
            else: out.append([q1, b, e]); out.append([q1, e, q2])
    co = np.vstack(Pn); ex = [np.vstack(x) if x[0].ndim > 1 else np.concatenate(x) for x in Ex]
    return co, np.array(out), ex, np.array(sorted(set(rim)))
