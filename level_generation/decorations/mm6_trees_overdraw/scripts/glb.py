"""Minimal GLB reader/writer for the installed MM6 tree models (system Python and Blender's Python: json, struct, numpy).

read(path) -> Model: the glTF JSON, every accessor as a numpy array and every image's bytes. Model.write(path)
re-packs the whole binary chunk (one bufferView per accessor or image, 4-byte aligned), so removed primitives leave
no orphaned data. Untouched accessors are written back with their own bytes, component types and flags."""
import copy, json, struct
import numpy as np

COMP = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
DT = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}
TYPE_OF = {1: 'SCALAR', 2: 'VEC2', 3: 'VEC3', 4: 'VEC4'}


class Model:
    def __init__(self, doc, arrays, images):
        self.doc = doc            # glTF JSON (accessor/bufferView/image byte locations are rebuilt on write)
        self.arrays = arrays      # accessor index -> raw numpy array (stored component type, not normalised)
        self.images = images      # image index -> bytes

    # ---------------------------------------------------------------- reading helpers
    def get(self, i, as_float=True):
        """Accessor i as float32 (normalised integers mapped to 0..1) or raw."""
        a = self.doc['accessors'][i]; x = self.arrays[i]
        if as_float and a.get('normalized') and x.dtype != np.float32:
            return x.astype(np.float32) / np.iinfo(x.dtype).max
        return x

    def mesh_chain(self):
        """Mesh indices LOD0, LOD1, ... (node 'Tree' and its openyamm_lods)."""
        base = next(n for n in self.doc['nodes'] if n['name'] == 'Tree')
        return [base['mesh']] + self.doc['meshes'][base['mesh']]['extras']['openyamm_lods']

    def material_index(self, name):
        return next(i for i, m in enumerate(self.doc['materials']) if m['name'] == name)

    def primitive(self, mesh, material_name):
        for p in self.doc['meshes'][mesh]['primitives']:
            if self.doc['materials'][p['material']]['name'] == material_name:
                return p
        return None

    # ---------------------------------------------------------------- editing helpers
    def add_accessor(self, array, normalized=False, minmax=False):
        array = np.ascontiguousarray(array)
        n = 1 if array.ndim == 1 else array.shape[1]
        ct = {np.dtype(np.float32): 5126, np.dtype(np.uint32): 5125, np.dtype(np.uint16): 5123,
              np.dtype(np.uint8): 5121}[array.dtype]
        acc = {'componentType': ct, 'count': int(array.shape[0]), 'type': TYPE_OF[n]}
        if normalized:
            acc['normalized'] = True
        if minmax:
            acc['min'] = [float(v) for v in array.reshape(len(array), -1).min(0)]
            acc['max'] = [float(v) for v in array.reshape(len(array), -1).max(0)]
        self.doc['accessors'].append(acc)
        i = len(self.doc['accessors']) - 1
        self.arrays[i] = array.reshape(len(array), n) if n > 1 else array.reshape(-1)
        return i

    def add_primitive(self, mesh, material, positions, normals, uvs, colours, indices):
        """Appends a triangle primitive: float32 positions/normals/uvs, colours 0..1 RGBA (stored as normalised
        uint16 like the exporter), indices uint16/uint32."""
        col = np.clip(np.round(np.asarray(colours, np.float64) * 65535), 0, 65535).astype(np.uint16)
        attrs = {'POSITION': self.add_accessor(np.asarray(positions, np.float32), minmax=True),
                 'NORMAL': self.add_accessor(np.asarray(normals, np.float32)),
                 'TEXCOORD_0': self.add_accessor(np.asarray(uvs, np.float32)),
                 'COLOR_0': self.add_accessor(col, normalized=True)}
        idx = np.asarray(indices).reshape(-1)
        idx = idx.astype(np.uint16 if idx.max() < 65535 else np.uint32)
        prim = {'attributes': attrs, 'indices': self.add_accessor(idx), 'material': material}
        self.doc['meshes'][mesh]['primitives'].append(prim)
        return prim

    def add_image(self, name, data, mime='image/png'):
        self.doc['images'].append({'mimeType': mime, 'name': name})
        i = len(self.doc['images']) - 1
        self.images[i] = data
        return i

    def add_texture(self, image):
        self.doc['textures'].append({'sampler': 0, 'source': image})
        return len(self.doc['textures']) - 1

    # ---------------------------------------------------------------- writing
    def write(self, path):
        doc = copy.deepcopy(self.doc)
        used = set()
        for m in doc['meshes']:
            for p in m['primitives']:
                used.update(p['attributes'].values()); used.add(p['indices'])
        remap = {}; accessors = []
        for i, a in enumerate(doc['accessors']):
            if i in used:
                remap[i] = len(accessors); accessors.append((i, a))
        for m in doc['meshes']:
            for p in m['primitives']:
                p['attributes'] = {k: remap[v] for k, v in p['attributes'].items()}
                p['indices'] = remap[p['indices']]
        index_set = {p['indices'] for m in doc['meshes'] for p in m['primitives']}
        blob = bytearray(); views = []

        def put(data, target=None):
            while len(blob) % 4:
                blob.append(0)
            view = {'buffer': 0, 'byteLength': len(data), 'byteOffset': len(blob)}
            if target:
                view['target'] = target
            blob.extend(data); views.append(view)
            return len(views) - 1

        for k in range(len(doc['images'])):
            doc['images'][k]['bufferView'] = put(self.images[k])
        new_acc = []
        for new_i, (old_i, a) in enumerate(accessors):
            a = dict(a); a.pop('byteOffset', None)
            a['bufferView'] = put(np.ascontiguousarray(self.arrays[old_i]).tobytes(),
                                  34963 if new_i in index_set else 34962)
            new_acc.append(a)
        doc['accessors'] = new_acc; doc['bufferViews'] = views
        while len(blob) % 4:
            blob.append(0)
        doc['buffers'] = [{'byteLength': len(blob)}]
        js = json.dumps(doc, separators=(',', ':')).encode()
        js += b' ' * ((4 - len(js) % 4) % 4)
        total = 12 + 8 + len(js) + 8 + len(blob)
        with open(path, 'wb') as f:
            f.write(struct.pack('<III', 0x46546C67, 2, total))
            f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
            f.write(struct.pack('<II', len(blob), 0x004E4942)); f.write(bytes(blob))


def read(path):
    data = open(path, 'rb').read()
    jl = struct.unpack('<I', data[12:16])[0]
    doc = json.loads(data[20:20 + jl])
    binary = data[20 + jl + 8:]
    arrays = {}
    for i, a in enumerate(doc['accessors']):
        v = doc['bufferViews'][a['bufferView']]
        n = COMP[a['type']]; dt = np.dtype(DT[a['componentType']])
        assert 'byteStride' not in v or v['byteStride'] == n * dt.itemsize
        off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        x = np.frombuffer(binary[off:off + a['count'] * n * dt.itemsize], dt).copy()
        arrays[i] = x.reshape(a['count'], n) if n > 1 else x
    images = {}
    for k, im in enumerate(doc['images']):
        v = doc['bufferViews'][im['bufferView']]
        images[k] = binary[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']]
    return Model(doc, arrays, images)
