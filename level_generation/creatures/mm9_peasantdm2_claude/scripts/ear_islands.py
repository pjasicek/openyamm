#!/usr/bin/env python3
"""Ear UV islands of the head set (library + probe). Islands of the head primitive lying wholly inside the ear box
(export GLB rest pose: y up, +z forward): |x| > EAR_X, EAR_Y[0] < y < EAR_Y[1], |z| < EAR_Z.
Library: ear_islands(glb, n) -> (mask n x n glTF v down, per island: (faces, centre)).
Probe: ear_islands.py <export glb> <head basecolor png> <out png>: the islands in magenta on the image."""
import sys
import numpy as np
from pygltflib import GLTF2
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

EAR_X, EAR_Y, EAR_Z = 0.06, (0.98, 1.10), 0.06
MAT = 'PeasantDM2Head'


def _load(glb):
    g = GLTF2().load(glb)
    blob = g.binary_blob()

    def acc(i):
        a = g.accessors[i]
        bv = g.bufferViews[a.bufferView]
        k = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[a.type]
        dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32}[a.componentType]
        return np.frombuffer(blob, dt, a.count * k, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, k)
    prim = next(p for m in g.meshes for p in m.primitives if g.materials[p.material].name == MAT)
    P = acc(prim.attributes.POSITION).astype(float)
    UV = acc(prim.attributes.TEXCOORD_0).astype(float)
    tri = acc(prim.indices).reshape(-1, 3).astype(int)
    return P, UV, tri


def _components(keys, tri):
    _, inv = np.unique(np.round(keys, 5), axis=0, return_inverse=True)
    f = inv.ravel()[tri]
    nv = f.max() + 1
    r, c = np.r_[f[:, 0], f[:, 1], f[:, 2]], np.r_[f[:, 1], f[:, 2], f[:, 0]]
    _, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(nv, nv)), directed=False)
    return lab[f[:, 0]]


def _raster(UV, tri, labels, n, fill=-1):
    out = np.full((n, n), fill, int)
    for t, lb in zip(tri, labels):
        uv = UV[t] * n
        x0, y0 = np.maximum(np.floor(uv.min(0)).astype(int), 0)
        x1, y1 = np.minimum(np.ceil(uv.max(0)).astype(int), n - 1)
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, cc = uv
        den = (b[1] - cc[1]) * (a[0] - cc[0]) + (cc[0] - b[0]) * (a[1] - cc[1])
        if abs(den) < 1e-12:
            continue
        l0 = ((b[1] - cc[1]) * (xs - cc[0]) + (cc[0] - b[0]) * (ys - cc[1])) / den
        l1 = ((cc[1] - a[1]) * (xs - cc[0]) + (a[0] - cc[0]) * (ys - cc[1])) / den
        ins = (np.stack([l0, l1, 1 - l0 - l1], -1) >= -1e-3).all(-1)
        out[(ys[ins] - 0.5).astype(int), (xs[ins] - 0.5).astype(int)] = lb
    return out


def texel_parts(glb, n):
    """per texel: the loose part (shared positions) of its triangle, -1 outside; part sizes (triangles)"""
    P, UV, tri = _load(glb)
    part = _components(P, tri)
    return _raster(UV, tri, part, n), np.bincount(part)


def ear_islands(glb, n):
    P, UV, tri = _load(glb)
    _, inv = np.unique(np.round(np.c_[P, UV], 5), axis=0, return_inverse=True)
    f = inv.ravel()[tri]
    nv = f.max() + 1
    r, c = np.r_[f[:, 0], f[:, 1], f[:, 2]], np.r_[f[:, 1], f[:, 2], f[:, 0]]
    _, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(nv, nv)), directed=False)
    isl = lab[f[:, 0]]
    cen = P[tri].mean(1)
    inside = (np.abs(cen[:, 0]) > EAR_X) & (np.abs(cen[:, 2]) < EAR_Z) & (cen[:, 1] > EAR_Y[0]) & (cen[:, 1] < EAR_Y[1])
    ears = [k for k in np.unique(isl) if inside[isl == k].all()]
    mask = np.zeros((n, n), bool)
    for t in tri[np.isin(isl, ears)]:
        uv = UV[t] * n
        x0, y0 = np.maximum(np.floor(uv.min(0)).astype(int), 0)
        x1, y1 = np.minimum(np.ceil(uv.max(0)).astype(int), n - 1)
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, cc = uv
        den = (b[1] - cc[1]) * (a[0] - cc[0]) + (cc[0] - b[0]) * (a[1] - cc[1])
        if abs(den) < 1e-12:
            continue
        l0 = ((b[1] - cc[1]) * (xs - cc[0]) + (cc[0] - b[0]) * (ys - cc[1])) / den
        l1 = ((cc[1] - a[1]) * (xs - cc[0]) + (a[0] - cc[0]) * (ys - cc[1])) / den
        ins = (np.stack([l0, l1, 1 - l0 - l1], -1) >= -1e-3).all(-1)
        mask[(ys[ins] - 0.5).astype(int), (xs[ins] - 0.5).astype(int)] = True
    info = [(int((isl == k).sum()), cen[isl == k].mean(0).round(3).tolist()) for k in ears]
    return mask, info


if __name__ == '__main__':
    from PIL import Image
    img = np.asarray(Image.open(sys.argv[2]).convert('RGB')).copy()
    m, info = ear_islands(sys.argv[1], img.shape[0])
    img[m] = (255, 0, 255)
    Image.fromarray(img).save(sys.argv[3])
    print('EAR_ISLANDS', len(info), info, 'texels', int(m.sum()))
