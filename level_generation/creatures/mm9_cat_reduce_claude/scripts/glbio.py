"""Small GLB reader: per mesh-node primitive arrays by material name (P, UV, N, J, W, T)."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402,F401


def arr(doc, binary, idx):
    a = doc['accessors'][idx]; n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
    ct = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[a['componentType']]
    x = np.frombuffer(accessor_bytes(doc, binary, idx), ct)
    return x.reshape(-1, n) if n > 1 else x


def prims(doc, binary, mesh_index):
    out = {}
    for p in doc['meshes'][mesh_index]['primitives']:
        a = p['attributes']
        out[doc['materials'][p['material']]['name']] = dict(
            prim=p, P=arr(doc, binary, a['POSITION']).astype(float), UV=arr(doc, binary, a['TEXCOORD_0']).astype(float),
            N=arr(doc, binary, a['NORMAL']).astype(float), J=arr(doc, binary, a['JOINTS_0']).astype(int),
            W=arr(doc, binary, a['WEIGHTS_0']).astype(float), T=arr(doc, binary, p['indices']).astype(int).reshape(-1, 3))
    return out


def load(path, node='Monk'):
    doc, binary = read_glb(Path(path))
    nd = next(n for n in doc['nodes'] if n.get('name') == node and 'mesh' in n)
    return doc, binary, nd, prims(doc, binary, nd['mesh'])
