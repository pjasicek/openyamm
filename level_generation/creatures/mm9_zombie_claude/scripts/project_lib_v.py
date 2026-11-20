"""Fields on the mesh surface, free of UV seams: per-vertex values (welded by position) smoothed along edges, read back per texel through the raster's barycentrics."""
import numpy as np


def weld(co):
    key = np.round(co.reshape(-1, 3), 4)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    return inv.reshape(co.shape[0], 3)


def smooth(val, tri, nv, it):
    v = val.copy()
    e = np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]]); e = np.concatenate([e, e[:, ::-1]])
    cnt = np.bincount(e[:, 0], minlength=nv).astype(np.float64)
    for _ in range(it):
        s = np.zeros_like(v); np.add.at(s, e[:, 0], v[e[:, 1]])
        v = 0.5 * v + 0.5 * s / np.maximum(cnt, 1)[(...,) + (None,) * (v.ndim - 1)]
    return v


def per_vertex(corner, tri, nv):
    """corner: (F,3,...) values -> vertex means"""
    s = np.zeros((nv,) + corner.shape[2:]); c = np.zeros(nv)
    np.add.at(s, tri.ravel(), corner.reshape((-1,) + corner.shape[2:])); np.add.at(c, tri.ravel(), 1)
    return s / np.maximum(c, 1)[(...,) + (None,) * (corner.ndim - 2)]


def texel(v, tri, bar, fid):
    return (bar[..., None] * v[tri[fid]]).sum(2) if v.ndim == 2 else (bar * v[tri[fid]]).sum(2)
