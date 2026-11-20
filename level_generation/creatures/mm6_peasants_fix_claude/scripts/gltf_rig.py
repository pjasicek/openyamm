"""Minimal glTF skeleton/animation access for editing installed actor GLBs in place (numpy, no Blender): node
hierarchy, rest TRS, sampled local TRS per clip, forward kinematics, and writing new rotation channels.
glTF frame of our actor exports: +Y up, +Z forward (the character faces +Z), +X the character's left."""
import json, struct
import numpy as np

COMP = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
CT = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}


def qmul(a, b):
    x1, y1, z1, w1 = np.moveaxis(a, -1, 0); x2, y2, z2, w2 = np.moveaxis(b, -1, 0)
    return np.stack([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2], -1)


def qinv(q):
    return q * np.array([-1, -1, -1, 1.0])


def qrot(q, v):
    p = np.concatenate([v, np.zeros(v.shape[:-1] + (1,))], -1)
    return qmul(qmul(q, p), qinv(q))[..., :3]


def qaxis(axis, ang):
    axis = np.asarray(axis, float); axis = axis / np.linalg.norm(axis)
    return np.concatenate([axis * np.sin(ang / 2), [np.cos(ang / 2)]])


def slerp(a, b, t):
    d = np.sum(a * b, -1, keepdims=True); b = np.where(d < 0, -b, b); d = np.abs(d)
    lin = d > 0.9995
    th = np.arccos(np.clip(d, -1, 1)); s = np.sin(th)
    wa = np.where(lin, 1 - t, np.sin((1 - t) * th) / np.where(lin, 1, s))
    wb = np.where(lin, t, np.sin(t * th) / np.where(lin, 1, s))
    q = wa * a + wb * b
    return q / np.linalg.norm(q, axis=-1, keepdims=True)


class Glb:
    def __init__(self, path):
        raw = open(path, 'rb').read(); n = struct.unpack_from('<I', raw, 12)[0]
        self.doc = json.loads(raw[20:20 + n]); self.bin = bytearray(raw[28 + n:])
        self.names = [nd.get('name', '') for nd in self.doc['nodes']]
        self.parent = {c: i for i, nd in enumerate(self.doc['nodes']) for c in nd.get('children', [])}

    def acc(self, i):
        a = self.doc['accessors'][i]; v = self.doc['bufferViews'][a['bufferView']]
        k = COMP[a['type']]; t = CT[a['componentType']]
        off = v.get('byteOffset', 0) + a.get('byteOffset', 0); stride = v.get('byteStride', 0)
        if stride and stride != k * np.dtype(t).itemsize:
            rows = [np.frombuffer(self.bin, t, k, off + r * stride) for r in range(a['count'])]
            arr = np.array(rows)
        else:
            arr = np.frombuffer(self.bin, t, a['count'] * k, off).reshape(a['count'], k).copy()
        if a.get('normalized'):
            arr = arr.astype(np.float64) / np.iinfo(t).max
        return arr

    def add_acc(self, arr, typ, minmax=False):
        arr = np.ascontiguousarray(arr, np.float32)
        while len(self.bin) % 4:
            self.bin.append(0)
        off = len(self.bin); self.bin += arr.tobytes()
        self.doc['bufferViews'].append({'buffer': 0, 'byteOffset': off, 'byteLength': arr.nbytes})
        a = {'bufferView': len(self.doc['bufferViews']) - 1, 'componentType': 5126, 'count': len(arr), 'type': typ}
        if minmax:
            a['min'] = arr.min(0).tolist(); a['max'] = arr.max(0).tolist()
        self.doc['accessors'].append(a)
        return len(self.doc['accessors']) - 1

    def write_acc(self, i, arr):
        """Overwrite an accessor's data in place (same count and type)."""
        a = self.doc['accessors'][i]; v = self.doc['bufferViews'][a['bufferView']]
        off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        data = np.ascontiguousarray(arr, CT[a['componentType']]).tobytes()
        assert not v.get('byteStride') or v['byteStride'] == len(data) // a['count']
        self.bin[off:off + len(data)] = data
        if 'min' in a:
            a['min'] = np.asarray(arr).min(0).tolist(); a['max'] = np.asarray(arr).max(0).tolist()

    def save(self, path):
        while len(self.bin) % 4:
            self.bin.append(0)
        self.doc['buffers'][0]['byteLength'] = len(self.bin)
        enc = json.dumps(self.doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
        open(path, 'wb').write(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(self.bin))
                               + struct.pack('<II', len(enc), 0x4e4f534a) + enc
                               + struct.pack('<II', len(self.bin), 0x004e4942) + bytes(self.bin))

    def node(self, name):
        return self.names.index(name)

    def rest(self):
        T = np.zeros((len(self.names), 3)); R = np.tile([0, 0, 0, 1.0], (len(self.names), 1)); S = np.ones((len(self.names), 3))
        for i, nd in enumerate(self.doc['nodes']):
            if 'translation' in nd: T[i] = nd['translation']
            if 'rotation' in nd: R[i] = nd['rotation']
            if 'scale' in nd: S[i] = nd['scale']
        return T, R, S

    def anim(self, name):
        return next(a for a in self.doc['animations'] if a['name'] == name)

    def clip_times(self, name):
        a = self.anim(name)
        return np.unique(np.concatenate([self.acc(s['input'])[:, 0] for s in a['samplers']]))

    def sample(self, name, times):
        """Local TRS of every node at the given times (rest where a channel is missing)."""
        T0, R0, S0 = self.rest(); n = len(times)
        T = np.repeat(T0[None], n, 0); R = np.repeat(R0[None], n, 0); S = np.repeat(S0[None], n, 0)
        a = self.anim(name)
        for ch in a['channels']:
            s = a['samplers'][ch['sampler']]; node = ch['target']['node']; path = ch['target']['path']
            ti = self.acc(s['input'])[:, 0]; vo = self.acc(s['output']).astype(np.float64)
            j = np.clip(np.searchsorted(ti, times, 'right') - 1, 0, len(ti) - 1); j1 = np.minimum(j + 1, len(ti) - 1)
            span = np.where(ti[j1] > ti[j], ti[j1] - ti[j], 1.0)
            f = np.clip((times - ti[j]) / span, 0, 1)[:, None]
            if s.get('interpolation', 'LINEAR') == 'STEP':
                f = f * 0
            if path == 'rotation':
                R[:, node] = slerp(vo[j], vo[j1], f)
            elif path == 'translation':
                T[:, node] = vo[j] * (1 - f) + vo[j1] * f
            elif path == 'scale':
                S[:, node] = vo[j] * (1 - f) + vo[j1] * f
        return T, R, S

    def fk(self, T, R):
        """World rotation and position per node, T/R shaped (frames, nodes, 3|4); scale ignored (unit rigs)."""
        n = T.shape[1]; WR = np.zeros_like(R); WT = np.zeros_like(T); done = np.zeros(n, bool)
        def go(i):
            if done[i]:
                return
            p = self.parent.get(i)
            if p is None:
                WR[:, i] = R[:, i]; WT[:, i] = T[:, i]
            else:
                go(p); WR[:, i] = qmul(WR[:, p], R[:, i]); WT[:, i] = WT[:, p] + qrot(WR[:, p], T[:, i])
            done[i] = True
        for i in range(n):
            go(i)
        return WT, WR

    def set_rotation_channel(self, clip, node, times, quats):
        """Replace (or add) the rotation channel of node in clip with LINEAR keys at times."""
        a = self.anim(clip)
        ti = self.add_acc(np.asarray(times, np.float32)[:, None], 'SCALAR', minmax=True)
        q = np.asarray(quats, np.float64)
        for k in range(1, len(q)):                       # sign-continuous
            if np.dot(q[k], q[k - 1]) < 0:
                q[k] = -q[k]
        qo = self.add_acc(q, 'VEC4')
        for ch in a['channels']:
            if ch['target']['node'] == node and ch['target']['path'] == 'rotation':
                a['samplers'][ch['sampler']] = {'input': ti, 'output': qo, 'interpolation': 'LINEAR'}
                return
        a['samplers'].append({'input': ti, 'output': qo, 'interpolation': 'LINEAR'})
        a['channels'].append({'sampler': len(a['samplers']) - 1, 'target': {'node': node, 'path': 'rotation'}})
