"""Crease under the chin (run 2): at the back of the jaw's underside the head mesh folds onto itself (dihedral 140-175 deg at y .64, z .145-.16),
a bright V line under the chin in the viewer. Laplacian-smooth the head vertices within R of the folded edges (ring and teeth fixed) until no
edge in the zone folds over FOLD deg. Positions only; topology and UVs unchanged. smooth(co, tri, part, fixed) -> new co, report."""
import numpy as np
from collections import defaultdict
ZONE = dict(x=.09, y=(.60, .69), z=(.12, .22)); R = .02; FOLD = 100.
def _dihedral(co, T):
    n = np.cross(co[T[:, 1]] - co[T[:, 0]], co[T[:, 2]] - co[T[:, 0]]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    E = defaultdict(list)
    for f, t in enumerate(T):
        for a, b in ((0, 1), (1, 2), (2, 0)): E[(min(t[a], t[b]), max(t[a], t[b]))].append(f)
    out = []
    for e, fs in E.items():
        if len(fs) == 2: out.append((e, np.degrees(np.arccos(np.clip(n[fs[0]] @ n[fs[1]], -1, 1)))))
    return out
def inzone(p): return (np.abs(p[..., 0]) < ZONE['x']) & (p[..., 1] > ZONE['y'][0]) & (p[..., 1] < ZONE['y'][1]) & (p[..., 2] > ZONE['z'][0]) & (p[..., 2] < ZONE['z'][1])
def smooth(co, tri, part, fixed):
    co = co.copy(); T = tri[(part[tri] == 1).all(1)]
    def folds():
        return [(e, a) for e, a in _dihedral(co, T) if a > FOLD and inzone((co[e[0]] + co[e[1]]) / 2)]
    f0 = folds(); before = max([a for _, a in f0], default=0)
    if not f0: return co, (0, 0, 0)
    seeds = np.unique(np.array([e for e, _ in f0]).ravel())
    vs = np.unique(T.ravel()); d = np.min(np.linalg.norm(co[vs][:, None] - co[seeds][None], axis=2), 1)
    mov = vs[(d < R) & ~np.isin(vs, fixed)]
    nb = defaultdict(set)
    for t in T:
        for a, b in ((0, 1), (1, 2), (2, 0)): nb[t[a]].add(t[b]); nb[t[b]].add(t[a])
    it = 0
    for it in range(1, 41):
        new = co.copy()
        for v in mov: new[v] = .5 * co[v] + .5 * co[list(nb[v])].mean(0)
        co = new
        if not folds(): break
    after = max([a for _, a in folds()], default=0)
    return co, (len(mov), round(before), round(after), it)
