"""Shared helpers: read a creature GLB's LOD0 primitives (bind-pose positions, UVs) and embedded images, and
rasterise a primitive's UV layout into per-texel 3D positions."""
import io, json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
TY = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
WID = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def arr(doc, binary, i):
    a = doc['accessors'][i]
    return np.frombuffer(accessor_bytes(doc, binary, i), TY[a['componentType']]).reshape(-1, WID[a['type']])


def lod0_primitives(doc, binary, node_name):
    node = next(n for n in doc['nodes'] if n.get('name') == node_name and 'mesh' in n)
    out = {}
    for p in doc['meshes'][node['mesh']]['primitives']:
        out[doc['materials'][p['material']]['name']] = dict(
            prim=p, pos=arr(doc, binary, p['attributes']['POSITION']).astype(np.float64),
            uv=arr(doc, binary, p['attributes']['TEXCOORD_0']).astype(np.float64),
            idx=arr(doc, binary, p['indices']).reshape(-1, 3))
    return out


def image(doc, binary, tex_index):
    v = doc['bufferViews'][doc['images'][doc['textures'][tex_index]['source']]['bufferView']]
    s = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(bytes(binary[s:s + v['byteLength']])))


def raster(pos, uv, idx, size):
    """Per-texel 3D position (glTF space) and coverage of a UV layout (v flipped to image rows)."""
    xyz = np.zeros((size, size, 3), np.float32); cov = np.zeros((size, size), bool)
    for tri in idx:
        p = uv[tri] * size; p[:, 1] = p[:, 1]  # glTF UV origin is top-left: rows = v * size
        x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, size - 1), min(y1, size - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        a, b, c = p; den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den; w2 = 1 - w0 - w1
        ins = (w0 >= 0) & (w1 >= 0) & (w2 >= 0); ys, xs = np.nonzero(ins)
        q = pos[tri]
        xyz[y0 + ys, x0 + xs] = w0[ins, None] * q[0] + w1[ins, None] * q[1] + w2[ins, None] * q[2]
        cov[y0 + ys, x0 + xs] = True
    return xyz, cov
