"""Pose helpers on a GLB's node hierarchy in glTF model space (Y up, the Minotaur faces +Z): per-node local TRS from
the rest nodes and an animation clip sampled at its key times, world matrices by FK. Quaternions are glTF xyzw."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402


def qmul(a, b):
    ax, ay, az, aw = np.moveaxis(a, -1, 0); bx, by, bz, bw = np.moveaxis(b, -1, 0)
    return np.stack([aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
                     aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz], -1)


def qinv(q):
    return q * np.array([-1, -1, -1, 1.0])


def qrot(q, v):
    p = np.concatenate([v, np.zeros(v.shape[:-1] + (1,))], -1)
    return qmul(qmul(q, p), qinv(q))[..., :3]


def qaxis(axis, ang):
    axis = np.asarray(axis, float); axis = axis / np.linalg.norm(axis)
    return np.concatenate([axis * np.sin(ang / 2), [np.cos(ang / 2)]])


def qbetween(u, v):
    """shortest rotation taking direction u to v"""
    u = u / np.linalg.norm(u); v = v / np.linalg.norm(v); c = np.dot(u, v)
    if c < -0.999999:
        a = np.cross(u, [1, 0, 0]);
        if np.linalg.norm(a) < 1e-6:
            a = np.cross(u, [0, 1, 0])
        return qaxis(a, np.pi)
    a = np.cross(u, v); q = np.array([a[0], a[1], a[2], 1 + c])
    return q / np.linalg.norm(q)


def qslerp(a, b, f):
    if np.dot(a, b) < 0:
        b = -b
    d = np.clip(np.dot(a, b), -1, 1); th = np.arccos(d)
    if th < 1e-6:
        q = a * (1 - f) + b * f
    else:
        q = (np.sin((1 - f) * th) * a + np.sin(f * th) * b) / np.sin(th)
    return q / np.linalg.norm(q)


class Pose:
    def __init__(self, glb):
        self.doc, self.bin = read_glb(Path(glb))
        self.names = [n.get('name') for n in self.doc['nodes']]
        self.parent = {}
        for i, n in enumerate(self.doc['nodes']):
            for c in n.get('children', []):
                self.parent[c] = i
        self.idx = {n: i for i, n in enumerate(self.names)}

    def clip(self, name):
        """{node: {path: (times, values)}} of a clip"""
        an = next(a for a in self.doc['animations'] if a['name'] == name); out = {}
        for ch in an['channels']:
            s = an['samplers'][ch['sampler']]
            t = np.frombuffer(accessor_bytes(self.doc, self.bin, s['input']), np.float32)
            v = np.frombuffer(accessor_bytes(self.doc, self.bin, s['output']), np.float32).reshape(len(t), -1)
            out.setdefault(ch['target']['node'], {})[ch['target']['path']] = (t, v)
        return out

    def local(self, clip, t):
        """local (T, R, S) of every node at time t (linear / slerp between keys)"""
        L = []
        for i, n in enumerate(self.doc['nodes']):
            T = np.array(n.get('translation', [0, 0, 0]), float); R = np.array(n.get('rotation', [0, 0, 0, 1]), float)
            S = np.array(n.get('scale', [1, 1, 1]), float)
            for path, (tt, vv) in clip.get(i, {}).items():
                k = int(np.clip(np.searchsorted(tt, t, side='right') - 1, 0, len(tt) - 1)); k2 = min(k + 1, len(tt) - 1)
                f = 0 if k2 == k else float(np.clip((t - tt[k]) / (tt[k2] - tt[k]), 0, 1))
                if path == 'rotation':
                    val = qslerp(vv[k].astype(float), vv[k2].astype(float), f)
                else:
                    val = vv[k] * (1 - f) + vv[k2] * f
                if path == 'translation':
                    T = val
                elif path == 'rotation':
                    R = val
                else:
                    S = val
            L.append([T, R, S])
        return L

    def world(self, L):
        """world (position, rotation) per node (scale assumed 1)"""
        P = [None] * len(L); Q = [None] * len(L)

        def go(i):
            if P[i] is not None:
                return
            T, R, _ = L[i]
            if i in self.parent:
                p = self.parent[i]; go(p)
                P[i] = P[p] + qrot(Q[p], T); Q[i] = qmul(Q[p], R)
            else:
                P[i] = np.asarray(T, float); Q[i] = np.asarray(R, float)
        for i in range(len(L)):
            go(i)
        return np.array(P), np.array(Q)
