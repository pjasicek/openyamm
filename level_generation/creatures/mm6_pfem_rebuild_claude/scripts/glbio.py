"""Minimal GLB read/write helpers (json + binary chunk as numpy views) for follow-up 4."""
import json, struct
import numpy as np

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


class Glb:
    def __init__(self, path):
        f = open(path, 'rb').read()
        jl = struct.unpack('<I', f[12:16])[0]
        self.j = json.loads(f[20:20 + jl])
        o = 20 + jl
        bl = struct.unpack('<I', f[o:o + 4])[0]
        self.bin = bytearray(f[o + 8:o + 8 + bl])

    def acc(self, i):
        a = self.j['accessors'][i]; bv = self.j['bufferViews'][a['bufferView']]
        n = NC[a['type']]; dt = np.dtype(CT[a['componentType']])
        off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        stride = bv.get('byteStride', 0)
        if stride and stride != n * dt.itemsize:
            raise RuntimeError('strided accessor %d' % i)
        arr = np.frombuffer(self.bin, dt, a['count'] * n, off).reshape(a['count'], n) if n > 1 else \
            np.frombuffer(self.bin, dt, a['count'], off)
        return arr.copy()

    def put(self, i, arr):
        a = self.j['accessors'][i]; bv = self.j['bufferViews'][a['bufferView']]
        dt = np.dtype(CT[a['componentType']]); arr = np.ascontiguousarray(arr, dt)
        assert arr.size == a['count'] * NC[a['type']], (i, arr.shape, a['count'])
        off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        self.bin[off:off + arr.nbytes] = arr.tobytes()
        if 'min' in a and dt == np.float32:
            r = arr.reshape(a['count'], -1); a['min'] = r.min(0).tolist(); a['max'] = r.max(0).tolist()

    def add(self, arr, ctype, typ, target=None):
        """append a new accessor (own buffer view), return its index"""
        dt = np.dtype(CT[ctype]); arr = np.ascontiguousarray(arr, dt)
        while len(self.bin) % 4: self.bin.append(0)
        off = len(self.bin); self.bin += arr.tobytes()
        bv = {'buffer': 0, 'byteOffset': off, 'byteLength': arr.nbytes}
        if target: bv['target'] = target
        self.j['bufferViews'].append(bv)
        n = NC[typ]; cnt = arr.size // n
        a = {'bufferView': len(self.j['bufferViews']) - 1, 'componentType': ctype, 'count': cnt, 'type': typ}
        if typ in ('VEC3',) and ctype == 5126:
            r = arr.reshape(cnt, n); a['min'] = r.min(0).tolist(); a['max'] = r.max(0).tolist()
        self.j['accessors'].append(a)
        return len(self.j['accessors']) - 1

    def prim(self, mesh, p):
        pr = self.j['meshes'][mesh]['primitives'][p]
        d = {k: self.acc(v) for k, v in pr['attributes'].items()}
        d['idx'] = self.acc(pr['indices']).reshape(-1, 3).astype(np.int64)
        return d

    def save(self, path):
        while len(self.bin) % 4: self.bin.append(0)
        self.j['buffers'][0]['byteLength'] = len(self.bin)
        js = json.dumps(self.j, separators=(',', ':')).encode()
        while len(js) % 4: js += b' '
        out = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(self.bin))
        out += struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(self.bin), 0x004E4942) + bytes(self.bin)
        open(path, 'wb').write(out)


def _compact(self):
    """drop accessors nothing references, then buffer views no accessor or image references; rebuild the binary chunk in order"""
    J = self.j; refs = []
    for m in J['meshes']:
        for p in m['primitives']:
            refs += list(p['attributes'].values()) + ([p['indices']] if 'indices' in p else [])
            for t in p.get('targets', []): refs += list(t.values())
    for sk in J.get('skins', []):
        if 'inverseBindMatrices' in sk: refs.append(sk['inverseBindMatrices'])
    for an in J.get('animations', []):
        for sm in an['samplers']: refs += [sm['input'], sm['output']]
    used_a = sorted(set(refs)); amap = {o: n for n, o in enumerate(used_a)}
    J['accessors'] = [J['accessors'][i] for i in used_a]
    for m in J['meshes']:
        for p in m['primitives']:
            p['attributes'] = {k: amap[v] for k, v in p['attributes'].items()}
            if 'indices' in p: p['indices'] = amap[p['indices']]
            if 'targets' in p: p['targets'] = [{k: amap[v] for k, v in t.items()} for t in p['targets']]
    for sk in J.get('skins', []):
        if 'inverseBindMatrices' in sk: sk['inverseBindMatrices'] = amap[sk['inverseBindMatrices']]
    for an in J.get('animations', []):
        for sm in an['samplers']: sm['input'] = amap[sm['input']]; sm['output'] = amap[sm['output']]
    used = set(a['bufferView'] for a in self.j['accessors'] if 'bufferView' in a) | set(im['bufferView'] for im in self.j.get('images', []) if 'bufferView' in im)
    remap = {}; out = bytearray(); views = []
    for i, bv in enumerate(self.j['bufferViews']):
        if i not in used: continue
        while len(out) % 4: out.append(0)
        o = bv.get('byteOffset', 0); data = self.bin[o:o + bv['byteLength']]
        nb = dict(bv); nb['byteOffset'] = len(out); out += data; remap[i] = len(views); views.append(nb)
    for a in self.j['accessors']:
        if 'bufferView' in a: a['bufferView'] = remap[a['bufferView']]
    for im in self.j.get('images', []):
        if 'bufferView' in im: im['bufferView'] = remap[im['bufferView']]
    self.j['bufferViews'] = views; self.bin = out


Glb.compact = _compact
