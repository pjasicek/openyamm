"""Minimal GLB access: JSON, accessor read and in-place accessor write (same count and type). Plain numpy, so it
runs in system Python and inside Blender."""
import json, struct
import numpy as np

COMP = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8, 5122: np.int16, 5120: np.int8}
NCOMP = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


class Glb:
    def __init__(self, path):
        data = open(path, 'rb').read()
        assert data[:4] == b'glTF'
        jlen = struct.unpack('<I', data[12:16])[0]
        self.json = json.loads(data[20:20 + jlen])
        off = 20 + jlen
        blen = struct.unpack('<I', data[off:off + 4])[0]
        assert data[off + 4:off + 8] == b'BIN\x00'
        self.bin = bytearray(data[off + 8:off + 8 + blen])

    def _view(self, index):
        acc = self.json['accessors'][index]
        bv = self.json['bufferViews'][acc['bufferView']]
        dtype = COMP[acc['componentType']]; n = NCOMP[acc['type']]
        stride = bv.get('byteStride', 0)
        assert stride in (0, n * np.dtype(dtype).itemsize), 'interleaved accessor'
        start = bv.get('byteOffset', 0) + acc.get('byteOffset', 0)
        return start, dtype, n, acc['count']

    def read(self, index):
        start, dtype, n, count = self._view(index)
        return np.frombuffer(bytes(self.bin[start:start + count * n * np.dtype(dtype).itemsize]),
                             dtype=dtype).reshape(count, n).copy()

    def write(self, index, values):
        start, dtype, n, count = self._view(index)
        values = np.asarray(values, dtype=dtype).reshape(count, n)
        raw = values.tobytes()
        self.bin[start:start + len(raw)] = raw
        acc = self.json['accessors'][index]
        if 'min' in acc:
            acc['min'] = values.min(0).tolist()
        if 'max' in acc:
            acc['max'] = values.max(0).tolist()

    def save(self, path):
        js = json.dumps(self.json, separators=(',', ':')).encode()
        js += b' ' * ((4 - len(js) % 4) % 4)
        bn = bytes(self.bin) + b'\x00' * ((4 - len(self.bin) % 4) % 4)
        total = 12 + 8 + len(js) + 8 + len(bn)
        with open(path, 'wb') as f:
            f.write(struct.pack('<III', 0x46546C67, 2, total))
            f.write(struct.pack('<I', len(js)) + b'JSON' + js)
            f.write(struct.pack('<I', len(bn)) + b'BIN\x00' + bn)

    def animation(self, name):
        return next(a for a in self.json['animations'] if a['name'] == name)

    def channels(self, name):
        """{(node name, path): (sampler dict, output accessor index)} of an animation."""
        anim = self.animation(name); nodes = self.json['nodes']; out = {}
        for c in anim['channels']:
            s = anim['samplers'][c['sampler']]
            out[(nodes[c['target']['node']]['name'], c['target']['path'])] = (s, s['output'])
        return out
