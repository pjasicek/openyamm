"""Minimal glTF node animation sampler (numpy): rest and animated global matrices of named nodes, in the file's own
(Y-up) space, LINEAR/STEP samplers. Used to read the Raven Man's spear handling and to check the Salamander export."""
import json
import struct
import numpy as np

TYPES = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
WIDTH = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


class Gltf:
    def __init__(self, path):
        d = open(path, 'rb').read(); n = struct.unpack('<I', d[12:16])[0]
        self.doc = json.loads(d[20:20 + n]); self.bin = d[20 + n + 8:]
        self.names = {nd.get('name'): i for i, nd in enumerate(self.doc['nodes'])}
        self.parent = {}
        for i, nd in enumerate(self.doc['nodes']):
            for c in nd.get('children', []):
                self.parent[c] = i

    def acc(self, i):
        a = self.doc['accessors'][i]; v = self.doc['bufferViews'][a['bufferView']]
        dt = np.dtype(TYPES[a['componentType']]); w = WIDTH[a['type']]
        start = v.get('byteOffset', 0) + a.get('byteOffset', 0); stride = v.get('byteStride', dt.itemsize * w)
        raw = np.frombuffer(self.bin, np.uint8, a['count'] * stride, start).reshape(a['count'], stride)
        out = raw[:, :dt.itemsize * w].copy().view(dt).reshape(a['count'], w).astype(np.float64)
        if a.get('normalized'):
            out /= np.iinfo(dt).max
        return out

    def rest_trs(self, i):
        nd = self.doc['nodes'][i]
        return (np.array(nd.get('translation', [0, 0, 0]), float), np.array(nd.get('rotation', [0, 0, 0, 1]), float),
                np.array(nd.get('scale', [1, 1, 1]), float))

    def animation(self, name):
        a = next(x for x in self.doc['animations'] if x['name'] == name); ch = {}
        for c in a['channels']:
            s = a['samplers'][c['sampler']]
            ch[(c['target']['node'], c['target']['path'])] = (self.acc(s['input'])[:, 0], self.acc(s['output']),
                                                             s.get('interpolation', 'LINEAR'))
        return ch

    def duration(self, name):
        return max(v[0][-1] for v in self.animation(name).values())

    def globals(self, anim, t):
        """Global 4x4 of every node at time t (anim None = rest)."""
        n = len(self.doc['nodes']); local = []
        for i in range(n):
            T, R, S = self.rest_trs(i)
            if anim is not None:
                for path in ('translation', 'rotation', 'scale'):
                    if (i, path) in anim:
                        ts, vs, mode = anim[(i, path)]
                        v = sample(ts, vs, t, mode, path == 'rotation')
                        if path == 'translation':
                            T = v
                        elif path == 'rotation':
                            R = v
                        else:
                            S = v
            local.append(trs(T, R, S))
        G = [None] * n

        def g(i):
            if G[i] is None:
                G[i] = local[i] if i not in self.parent else g(self.parent[i]) @ local[i]
            return G[i]
        return [g(i) for i in range(n)]


def sample(ts, vs, t, mode, quat):
    if t <= ts[0]:
        return vs[0]
    if t >= ts[-1]:
        return vs[-1]
    k = int(np.searchsorted(ts, t) - 1); f = (t - ts[k]) / max(ts[k + 1] - ts[k], 1e-12)
    if mode == 'STEP':
        return vs[k]
    a, b = vs[k], vs[k + 1]
    if quat:
        if np.dot(a, b) < 0:
            b = -b
        q = a * (1 - f) + b * f
        return q / np.linalg.norm(q)
    return a * (1 - f) + b * f


def quat_matrix(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def trs(T, R, S):
    m = np.eye(4); m[:3, :3] = quat_matrix(R) * S; m[:3, 3] = T
    return m


# glTF Y-up -> Blender Z-up
YUP = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float)
