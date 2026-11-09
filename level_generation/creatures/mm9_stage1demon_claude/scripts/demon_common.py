"""Shared loaders (no Blender): GLB meshes and rest joints in Blender coordinates (x, -z, y of glTF), the global fit of the
Meshy body onto MM9 (uniform scale by height, feet on MM9's floor, torso centred)."""
import numpy as np
from pygltflib import GLTF2
from scipy.spatial.transform import Rotation as R

TO_B = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)   # glTF -> Blender


def _acc(g, i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; blob = g.binary_blob()
    k = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a.type]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a.componentType]
    off = (bv.byteOffset or 0) + (a.byteOffset or 0)
    st = bv.byteStride or k * np.dtype(dt).itemsize
    if st == k * np.dtype(dt).itemsize:
        return np.frombuffer(blob, dt, a.count * k, off).reshape(a.count, k).astype(float)
    raw = np.frombuffer(blob, np.uint8, st * (a.count - 1) + k * np.dtype(dt).itemsize, off)
    return np.lib.stride_tricks.as_strided(raw.view(dt), (a.count, k), (st, np.dtype(dt).itemsize)).astype(float)


def _local(n):
    if n.matrix: return np.array(n.matrix).reshape(4, 4).T
    m = np.eye(4); m[:3, :3] = R.from_quat(n.rotation or [0, 0, 0, 1]).as_matrix() * (n.scale or [1, 1, 1]); m[:3, 3] = n.translation or [0, 0, 0]
    return m


def world_mats(g):
    par = {c: i for i, n in enumerate(g.nodes) for c in (n.children or [])}
    W = {}
    def w(i):
        if i not in W: W[i] = (w(par[i]) @ _local(g.nodes[i])) if i in par else _local(g.nodes[i])
        return W[i]
    return {i: w(i) for i in range(len(g.nodes))}


def load_mesh(path, skinned_rest=True):
    """All primitives, rest pose (node transforms applied for unskinned meshes), Blender coords. Returns V, F, prim id per face."""
    g = GLTF2().load(path); W = world_mats(g); V, F, PI = [], [], []
    off = 0
    for ni, n in enumerate(g.nodes):
        if n.mesh is None: continue
        for pk, p in enumerate(g.meshes[n.mesh].primitives):
            v = _acc(g, p.attributes.POSITION)
            if n.skin is None or not skinned_rest:
                v = (W[ni][:3, :3] @ v.T).T + W[ni][:3, 3]
            f = _acc(g, p.indices).astype(int).reshape(-1, 3)
            V.append(v); F.append(f + off); PI += [len(PI)] * 0 + [ni * 100 + pk] * len(f); off += len(v)
    V = np.vstack(V) @ TO_B.T
    return V, np.vstack(F), np.array(PI)


def joints(path):
    g = GLTF2().load(path); W = world_mats(g)
    return {n.name: W[i][:3, 3] @ TO_B.T for i, n in enumerate(g.nodes) if n.name}


def global_fit(P, A):
    """Uniform scale from the height, feet on MM9's floor, x centred, torso band centred in y. Returns (s, t) with P' = P*s + t."""
    nt = P[:, 1] < np.percentile(P[:, 1], 5) + 0.62 * np.ptp(P[:, 1])        # Meshy's tail sticks out far behind: not in the height
    at = A[:, 1] < 0.45
    s = np.ptp(A[at, 2]) / np.ptp(P[nt, 2])
    Q = P * s; dz = A[at, 2].min() - Q[nt, 2].min()
    zl, zh = -0.2, 0.5
    m = (Q[:, 2] + dz > zl) & (Q[:, 2] + dz < zh) & (np.abs(Q[:, 0]) < 0.25)
    ma = (A[:, 2] > zl) & (A[:, 2] < zh) & (np.abs(A[:, 0]) < 0.25)
    dy = 0.5 * (A[ma, 1].min() + A[ma, 1].max()) - 0.5 * (Q[m, 1].min() + Q[m, 1].max())
    dx = 0.5 * (A[:, 0].min() + A[:, 0].max()) - 0.5 * (Q[:, 0].min() + Q[:, 0].max())
    return s, np.array([dx, dy, dz])
