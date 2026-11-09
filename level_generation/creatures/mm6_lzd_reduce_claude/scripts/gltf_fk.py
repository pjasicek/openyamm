"""Minimal glTF animation evaluation (numpy): sampled local TRS per node and world matrices, quaternions as x,y,z,w."""
import struct
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402,F401


def qmul(a, b):
    ax, ay, az, aw = np.moveaxis(a, -1, 0); bx, by, bz, bw = np.moveaxis(b, -1, 0)
    return np.stack([aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
                     aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz], -1)


def qaxis(axis, angle):
    axis = np.asarray(axis, float) / np.linalg.norm(axis); s = np.sin(angle / 2)
    return np.array([*(axis * s), np.cos(angle / 2)])


def qmat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def matq(m):
    """rotation matrix (3x3) -> quaternion x,y,z,w"""
    w = np.sqrt(max(0.0, 1 + m[0, 0] + m[1, 1] + m[2, 2])) / 2; x = np.sqrt(max(0.0, 1 + m[0, 0] - m[1, 1] - m[2, 2])) / 2
    y = np.sqrt(max(0.0, 1 - m[0, 0] + m[1, 1] - m[2, 2])) / 2; z = np.sqrt(max(0.0, 1 - m[0, 0] - m[1, 1] + m[2, 2])) / 2
    x = np.copysign(x, m[2, 1] - m[1, 2]); y = np.copysign(y, m[0, 2] - m[2, 0]); z = np.copysign(z, m[1, 0] - m[0, 1])
    q = np.array([x, y, z, w]); return q / np.linalg.norm(q)


def slerp(a, b, f):
    d = float(np.dot(a, b))
    if d < 0: b, d = -b, -d
    if d > .9995: q = a + (b - a) * f; return q / np.linalg.norm(q)
    th = np.arccos(d); return (np.sin((1 - f) * th) * a + np.sin(f * th) * b) / np.sin(th)


class Gltf:
    def __init__(self, path):
        self.doc, self.bin = read_glb(Path(path)); d = self.doc
        self.names = {n.get('name'): i for i, n in enumerate(d['nodes'])}
        self.parent = {c: i for i, n in enumerate(d['nodes']) for c in n.get('children', [])}
        self.anim = {a['name']: a for a in d['animations']}

    def floats(self, acc):
        a = self.doc['accessors'][acc]; k = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a['type']]
        return np.array(struct.unpack(f'<{a["count"] * k}f', accessor_bytes(self.doc, self.bin, acc))).reshape(a['count'], k).squeeze()

    def channel(self, clip, node, path):
        a = self.anim[clip]
        for c in a['channels']:
            if c['target']['node'] == node and c['target']['path'] == path:
                return c, a['samplers'][c['sampler']]
        return None, None

    def sample(self, clip, node, path, t, override=None):
        if override is not None and (node, path) in override:
            return override[(node, path)](t)
        c, s = self.channel(clip, node, path)
        n = self.doc['nodes'][node]
        if c is None:
            return np.array(n.get(path, {'translation': [0, 0, 0], 'rotation': [0, 0, 0, 1], 'scale': [1, 1, 1]}[path]), float)
        ts = np.atleast_1d(self.floats(s['input'])); vs = self.floats(s['output']).reshape(len(ts), -1)
        if t <= ts[0] or len(ts) == 1: return vs[0]
        if t >= ts[-1]: return vs[-1]
        i = int(np.searchsorted(ts, t) - 1); f = (t - ts[i]) / (ts[i + 1] - ts[i])
        if s.get('interpolation', 'LINEAR') == 'STEP': return vs[i]
        return slerp(vs[i], vs[i + 1], f) if path == 'rotation' else vs[i] * (1 - f) + vs[i + 1] * f

    def world(self, clip, node, t, override=None):
        m = np.eye(4); chain = []
        while node is not None:
            chain.append(node); node = self.parent.get(node)
        for nd in reversed(chain):
            l = np.eye(4); l[:3, :3] = qmat(self.sample(clip, nd, 'rotation', t, override)) * self.sample(clip, nd, 'scale', t, override)
            l[:3, 3] = self.sample(clip, nd, 'translation', t, override); m = m @ l
        return m

    def duration(self, clip):
        return max(float(np.atleast_1d(self.floats(s['input']))[-1]) for s in self.anim[clip]['samplers'])
