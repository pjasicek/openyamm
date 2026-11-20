"""UV islands of a dumped mesh (dump_mesh.py npz): faces joined where they share a vertex AND the same UV there."""
import numpy as np, sys, collections
def islands(d, faces, key='huv'):
    L, ls, lt = d['L'], d['ls'], d['lt']; U = np.round(d[key] * 1e5).astype(np.int64)
    par = {f: f for f in faces}
    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    seen = {}
    for f in faces:
        for li in range(ls[f], ls[f] + lt[f]):
            k = (L[li], U[li, 0], U[li, 1])
            if k in seen:
                a, b = find(f), find(seen[k])
                if a != b: par[a] = b
            else:
                seen[k] = f
    g = collections.defaultdict(list)
    for f in faces: g[find(f)].append(f)
    return list(g.values())
if __name__ == '__main__':
    d = np.load(sys.argv[1], allow_pickle=True)
    P, L, ls, lt = d['P'], d['L'], d['ls'], d['lt']
    faces = list(np.where(d['head'])[0])
    cx = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    for isl in sorted(islands(d, faces), key=len):
        vs = np.unique(np.concatenate([L[ls[f]:ls[f] + lt[f]] for f in isl])); Q = P[vs]
        c = Q.mean(0)
        if abs(c[0] - cx) > 0.06 and 0.70 < c[2] < 0.86:
            print(len(isl), 'faces', len(vs), 'verts centre', np.round(c, 3), 'min', np.round(Q.min(0), 3), 'max', np.round(Q.max(0), 3))
