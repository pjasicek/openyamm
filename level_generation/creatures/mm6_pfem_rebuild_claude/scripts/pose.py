#!/usr/bin/env python3
"""Numpy skinning of a runtime GLB at a clip time (follow-up 4 diagnostics): returns the soft_render primitives posed.
pose_prims(glb, clip, t, mesh=0) -> [(co, nr, uv, tri, tex), ...] in the model's world frame (feet at y=0 like the viewer)."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from glbio import Glb
import soft_render as sr


def qmat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def sample(g, sampler, t):
    T = g.acc(sampler['input']).ravel(); V = g.acc(sampler['output']); V = V.reshape(len(T), -1)
    if t <= T[0]: return V[0]
    if t >= T[-1]: return V[-1]
    i = np.searchsorted(T, t) - 1; a = (t - T[i]) / (T[i + 1] - T[i])
    if sampler.get('interpolation', 'LINEAR') == 'STEP': return V[i]
    v = V[i] * (1 - a) + V[i + 1] * a
    if V.shape[1] == 4:
        if np.dot(V[i], V[i + 1]) < 0: v = V[i] * (1 - a) - V[i + 1] * a
        v = v / np.linalg.norm(v)
    return v


def pose_prims(g, clip, t, mesh=0):
    J = g.j; nodes = J['nodes']
    trs = [[np.array(n.get('translation', [0, 0, 0]), float), np.array(n.get('rotation', [0, 0, 0, 1]), float),
            np.array(n.get('scale', [1, 1, 1]), float)] for n in nodes]
    an = next(a for a in J['animations'] if a['name'] == clip)
    for ch in an['channels']:
        tgt = ch['target']; k = {'translation': 0, 'rotation': 1, 'scale': 2}.get(tgt['path'])
        if k is None: continue
        trs[tgt['node']][k] = sample(g, an['samplers'][ch['sampler']], t)
    parent = {}
    for i, n in enumerate(nodes):
        for c in n.get('children', []): parent[c] = i
    world = {}

    def W(i):
        if i in world: return world[i]
        tr, q, s = trs[i]; M = np.eye(4); M[:3, :3] = qmat(q) * s; M[:3, 3] = tr
        world[i] = (W(parent[i]) @ M) if i in parent else M
        return world[i]
    node = next(n for n in nodes if n.get('mesh') == mesh and 'skin' in n)
    skin = J['skins'][node['skin']]; ibm = g.acc(skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
    mats = np.array([W(j) @ ibm[k] for k, j in enumerate(skin['joints'])])
    out = []
    base = sr.load(g, mesh)
    for p, (co, nr, uv, tri, tex) in enumerate(base):
        d = g.prim(mesh, p); jj = d['JOINTS_0'].astype(int); ww = d['WEIGHTS_0']
        M = (mats[jj] * ww[:, :, None, None]).sum(1)
        pc = np.einsum('nij,nj->ni', M[:, :3, :3], co) + M[:, :3, 3]
        pn = np.einsum('nij,nj->ni', M[:, :3, :3], nr); pn /= np.maximum(np.linalg.norm(pn, axis=1, keepdims=True), 1e-12)
        out.append((pc, pn, uv, tri, tex))
    return out
