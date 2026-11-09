"""Minimal GLB access for the texture pass: read accessors and images, replace them, write a compacted GLB.

Everything not replaced (animations, skins, nodes, materials, extras) is carried over unchanged; buffer views are
re-packed in their original order with 4-byte alignment.
"""
import io
import json
import struct

import numpy as np
from PIL import Image

COMPONENTS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
TYPES = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8, 5122: np.int16, 5120: np.int8}
CODES = {np.dtype(v): k for k, v in TYPES.items()}


class Glb:
    def __init__(self, path):
        raw = open(path, 'rb').read()
        n = struct.unpack_from('<I', raw, 12)[0]
        self.doc = json.loads(raw[20:20 + n])
        self.bin = raw[28 + n:28 + n + struct.unpack_from('<I', raw, 20 + n)[0]]
        self.views = {}          # bufferView index -> replacement bytes

    def view_bytes(self, index):
        if index in self.views:
            return self.views[index]
        v = self.doc['bufferViews'][index]
        start = v.get('byteOffset', 0)
        return self.bin[start:start + v['byteLength']]

    def accessor(self, index):
        a = self.doc['accessors'][index]
        v = self.doc['bufferViews'][a['bufferView']]
        dtype = np.dtype(TYPES[a['componentType']])
        width = COMPONENTS[a['type']]
        data = self.view_bytes(a['bufferView'])
        stride = v.get('byteStride', 0) or dtype.itemsize * width
        off = a.get('byteOffset', 0)
        rows = [np.frombuffer(data, dtype, count=width, offset=off + i * stride) for i in range(a['count'])] \
            if stride != dtype.itemsize * width else None
        if rows is None:
            out = np.frombuffer(data, dtype, count=a['count'] * width, offset=off).reshape(a['count'], width)
        else:
            out = np.stack(rows)
        return out.copy() if width > 1 else out[:, 0].copy()

    def image(self, index):
        view = self.doc['images'][index]['bufferView']
        return Image.open(io.BytesIO(self.view_bytes(view)))

    def set_accessor(self, index, array):
        """Gives accessor `index` its own buffer view holding `array` (same component type and width)."""
        a = self.doc['accessors'][index]
        dtype = np.dtype(TYPES[a['componentType']])
        array = np.ascontiguousarray(np.asarray(array).astype(dtype))
        width = COMPONENTS[a['type']]
        if width > 1:
            assert array.ndim == 2 and array.shape[1] == width, (array.shape, a['type'])
        view = {'buffer': 0, 'byteLength': array.nbytes}
        if 'target' in self.doc['bufferViews'][a['bufferView']]:
            view['target'] = self.doc['bufferViews'][a['bufferView']]['target']
        self.doc['bufferViews'].append(view)
        vi = len(self.doc['bufferViews']) - 1
        self.views[vi] = array.tobytes()
        a['bufferView'] = vi
        a.pop('byteOffset', None)
        a['count'] = int(array.shape[0])
        if a['type'] in ('VEC2', 'VEC3', 'VEC4', 'SCALAR') and a['componentType'] == 5126 and 'min' in a:
            flat = array.reshape(len(array), -1)
            a['min'] = flat.min(0).tolist()
            a['max'] = flat.max(0).tolist()
        elif 'min' in a:
            flat = array.reshape(len(array), -1)
            a['min'] = [int(x) for x in flat.min(0)]
            a['max'] = [int(x) for x in flat.max(0)]

    def set_image(self, index, png_bytes, name=None):
        view = {'buffer': 0, 'byteLength': len(png_bytes)}
        self.doc['bufferViews'].append(view)
        vi = len(self.doc['bufferViews']) - 1
        self.views[vi] = png_bytes
        self.doc['images'][index]['bufferView'] = vi
        self.doc['images'][index]['mimeType'] = 'image/png'
        if name:
            self.doc['images'][index]['name'] = name

    def save(self, path):
        used = sorted({a['bufferView'] for a in self.doc['accessors'] if 'bufferView' in a}
                      | {i['bufferView'] for i in self.doc.get('images', []) if 'bufferView' in i})
        remap, chunks, offset = {}, [], 0
        views = []
        for old in used:
            data = self.view_bytes(old)
            view = {k: v for k, v in self.doc['bufferViews'][old].items() if k != 'byteOffset'}
            view['byteOffset'] = offset
            view['byteLength'] = len(data)
            remap[old] = len(views)
            views.append(view)
            pad = (-len(data)) % 4
            chunks.append(data + b'\0' * pad)
            offset += len(data) + pad
        for a in self.doc['accessors']:
            if 'bufferView' in a:
                a['bufferView'] = remap[a['bufferView']]
        for i in self.doc.get('images', []):
            if 'bufferView' in i:
                i['bufferView'] = remap[i['bufferView']]
        self.doc['bufferViews'] = views
        binary = b''.join(chunks)
        self.doc['buffers'] = [{'byteLength': len(binary)}]
        js = json.dumps(self.doc, separators=(',', ':')).encode()
        js += b' ' * ((-len(js)) % 4)
        total = 12 + 8 + len(js) + 8 + len(binary)
        with open(path, 'wb') as f:
            f.write(struct.pack('<III', 0x46546C67, 2, total))
            f.write(struct.pack('<II', len(js), 0x4E4F534A) + js)
            f.write(struct.pack('<II', len(binary), 0x004E4942) + binary)
        self.views = {}
        raw = open(path, 'rb').read()
        n = struct.unpack_from('<I', raw, 12)[0]
        self.doc = json.loads(raw[20:20 + n])
        self.bin = raw[28 + n:]


def png(array_or_image):
    img = array_or_image if isinstance(array_or_image, Image.Image) else Image.fromarray(array_or_image)
    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=False, compress_level=6)
    return buf.getvalue()
