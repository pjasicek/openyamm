"""Minimal static GLB writer for built meshes: one node per mesh, POSITION/NORMAL/TEXCOORD_0/indices, one material per
mesh with an embedded PNG base colour (and optional metallic-roughness PNG). Optional LOD chain via extras."""
import io
import json
import struct
from pathlib import Path

import numpy as np


def smooth_normals(v, f):
    n = np.zeros_like(v)
    fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    for k in range(3):
        np.add.at(n, f[:, k], fn)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    return n / np.maximum(ln, 1e-12)


class Writer:
    def __init__(self):
        self.doc = {'asset': {'version': '2.0', 'generator': 'OpenYAMM xeen_pharaoh_claude'}, 'buffers': [{}],
                    'bufferViews': [], 'accessors': [], 'meshes': [], 'nodes': [], 'materials': [], 'images': [],
                    'textures': [], 'samplers': [{'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497,
                                                  'wrapT': 10497}], 'scenes': [{'nodes': []}], 'scene': 0}
        self.bin = bytearray()

    def _view(self, data, target=None):
        self.bin += b'\0' * (-len(self.bin) % 4)
        v = {'buffer': 0, 'byteOffset': len(self.bin), 'byteLength': len(data)}
        if target:
            v['target'] = target
        self.doc['bufferViews'].append(v)
        self.bin += data
        return len(self.doc['bufferViews']) - 1

    def _acc(self, arr, kind, comp=5126, target=34962):
        arr = np.ascontiguousarray(arr)
        view = self._view(arr.tobytes(), target)
        a = {'bufferView': view, 'componentType': comp, 'count': len(arr), 'type': kind}
        if kind != 'SCALAR' or comp == 5126:
            a['min'] = np.atleast_1d(arr.min(0)).tolist() if kind != 'SCALAR' else [float(arr.min())]
            a['max'] = np.atleast_1d(arr.max(0)).tolist() if kind != 'SCALAR' else [float(arr.max())]
        self.doc['accessors'].append(a)
        return len(self.doc['accessors']) - 1

    def image(self, png_path_or_image, name):
        if isinstance(png_path_or_image, (str, Path)):
            data = Path(png_path_or_image).read_bytes()
        else:
            buf = io.BytesIO(); png_path_or_image.save(buf, 'PNG'); data = buf.getvalue()
        view = self._view(data)
        self.doc['images'].append({'bufferView': view, 'mimeType': 'image/png', 'name': name})
        self.doc['textures'].append({'sampler': 0, 'source': len(self.doc['images']) - 1})
        return len(self.doc['textures']) - 1

    def material(self, name, base_tex, mr_tex=None, roughness=0.8, metallic=0.0, double=True, normal_tex=None):
        pbr = {'baseColorTexture': {'index': base_tex}, 'metallicFactor': metallic, 'roughnessFactor': roughness}
        if mr_tex is not None:
            pbr['metallicRoughnessTexture'] = {'index': mr_tex}
            pbr['roughnessFactor'] = 1.0
            pbr['metallicFactor'] = 1.0 if metallic > 0 else 0.0
        m = {'name': name, 'pbrMetallicRoughness': pbr, 'doubleSided': double}
        if normal_tex is not None:
            m['normalTexture'] = {'index': normal_tex}
        self.doc['materials'].append(m)
        return len(self.doc['materials']) - 1

    def mesh(self, name, prims):
        """prims: list of (v (n,3), n (n,3), uv (n,2), f (m,3), material)."""
        out = []
        for v, n, uv, f, mat in prims:
            att = {'POSITION': self._acc(v.astype(np.float32), 'VEC3'),
                   'NORMAL': self._acc(n.astype(np.float32), 'VEC3'),
                   'TEXCOORD_0': self._acc(uv.astype(np.float32), 'VEC2')}
            idx = self._acc(f.astype(np.uint32).reshape(-1), 'SCALAR', 5125, 34963)
            out.append({'attributes': att, 'indices': idx, 'material': mat})
        self.doc['meshes'].append({'name': name, 'primitives': out})
        return len(self.doc['meshes']) - 1

    def node(self, name, mesh, root=True):
        self.doc['nodes'].append({'name': name, 'mesh': mesh})
        i = len(self.doc['nodes']) - 1
        if root:
            self.doc['scenes'][0]['nodes'].append(i)
        return i

    def write(self, path):
        self.doc['buffers'][0]['byteLength'] = len(self.bin)
        for k in ('images', 'textures', 'materials'):
            if not self.doc[k]:
                del self.doc[k]
        text = json.dumps(self.doc, separators=(',', ':')).encode()
        text += b' ' * (-len(text) % 4)
        binary = bytes(self.bin) + b'\0' * (-len(self.bin) % 4)
        total = 12 + 8 + len(text) + 8 + len(binary)
        Path(path).write_bytes(struct.pack('<III', 0x46546C67, 2, total) + struct.pack('<II', len(text), 0x4E4F534A)
                               + text + struct.pack('<II', len(binary), 0x004E4942) + binary)
