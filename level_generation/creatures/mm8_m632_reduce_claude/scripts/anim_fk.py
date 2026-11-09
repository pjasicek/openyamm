#!/usr/bin/env python3
"""Forward kinematics of one clip straight from a GLB (glTF Y-up world, every key time of the clip's longest
channel): world matrices per node, used by the clip fix scripts and checks. Import: from anim_fk import Clip."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402


def qmat(q):
    x, y, z, w = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    return np.stack([np.stack([1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], -1),
                     np.stack([2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], -1),
                     np.stack([2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)], -1)], -2)


def slerp(a, b, t):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if np.dot(a, b) < 0:
        b = -b
    d = np.clip(np.dot(a, b), -1, 1); th = np.arccos(d)
    if th < 1e-8:
        return a
    return (np.sin((1 - t) * th) * a + np.sin(t * th) * b) / np.sin(th)


class Clip:
    def __init__(self, glb, name, doc=None, binary=None):
        if doc is None:
            doc, binary = read_glb(Path(glb))
        self.doc, self.binary = doc, binary
        self.nodes = doc['nodes']; self.idx = {n.get('name'): i for i, n in enumerate(self.nodes)}
        self.parent = {c: i for i, n in enumerate(self.nodes) for c in n.get('children', [])}
        self.anim = next(a for a in doc['animations'] if a['name'] == name)
        self.chan = {}
        for ch in self.anim['channels']:
            s = self.anim['samplers'][ch['sampler']]
            self.chan[ch['target']['node'], ch['target']['path']] = (self.F(s['input']).ravel(), self.F(s['output']), ch)
        self.times = max((t for t, _, _ in self.chan.values()), key=len)

    def F(self, a):
        return np.frombuffer(accessor_bytes(self.doc, self.binary, a), '<f4').reshape(
            self.doc['accessors'][a]['count'], -1).astype(np.float64)

    def value(self, i, path, default, over=None):
        if over and (i, path) in over:
            return over[i, path]
        T = len(self.times)
        if (i, path) not in self.chan:
            return np.broadcast_to(np.array(self.nodes[i].get(path, default), float), (T, len(default))).copy()
        t, v, _ = self.chan[i, path]
        if len(t) == T:
            return v.copy()
        return np.array([v[min(np.searchsorted(t, x, 'right') - 1, len(v) - 1)] if len(t) <= 2 else
                         [np.interp(x, t, v[:, c]) for c in range(v.shape[1])] for x in self.times])

    def world(self, name, over=None):
        i = self.idx[name]; chain = [i]
        while chain[-1] in self.parent:
            chain.append(self.parent[chain[-1]])
        M = np.tile(np.eye(4), (len(self.times), 1, 1))
        for j in reversed(chain):
            r = self.value(j, 'rotation', [0, 0, 0, 1], over); t = self.value(j, 'translation', [0, 0, 0], over)
            s = self.value(j, 'scale', [1, 1, 1], over)
            L = np.zeros((len(self.times), 4, 4)); L[:, :3, :3] = qmat(r) * s[:, None, :]; L[:, :3, 3] = t; L[:, 3, 3] = 1
            M = M @ L
        return M
