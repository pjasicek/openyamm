"""Shared helpers (Blender): loose parts of the Body mesh at rest, by vertex index."""
import numpy as np


def loose_parts(me):
    n = len(me.vertices)
    parent = np.arange(n)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    ev = np.zeros(len(me.edges) * 2, np.int64)
    me.edges.foreach_get('vertices', ev)
    for a, b in ev.reshape(-1, 2):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    roots = np.array([find(i) for i in range(n)])
    labels = {}
    for r in roots:
        labels.setdefault(r, len(labels))
    lab = np.array([labels[r] for r in roots])
    return lab


def rest_coords(body):
    me = body.data
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    mw = np.array(body.matrix_world)
    return co @ mw[:3, :3].T + mw[:3, 3]


def find_part(lab, co, zmin, zmax, tol=0.01):
    best = None
    for p in np.unique(lab):
        s = lab == p
        if abs(co[s, 2].min() - zmin) < tol and abs(co[s, 2].max() - zmax) < tol:
            if best is None or s.sum() > (lab == best).sum():
                best = p
    return best
