#!/usr/bin/env python3
"""Reduction check of the opaque LOD0 surfaces (cactus bodies, pots, bark), adapted from
../../mm6_reduce_pilot/scripts/deco_ladder.py: the GLB is read directly (no Blender dump), the opaque primitives
of LOD0 are welded and collapsed texture-aware at 70/55/45/35/25 %, and the two-way Hausdorff distance is given in %
of the model height. Pass, as the pilot: max <= 1.5 % and mean <= 0.15 %. Alpha cards are not touched.
  ladder <glb> ...            the pilot's ladder per model (the lowest passing step is the possible cut)
  compare <old.glb> <new.glb> two-way distance between the opaque LOD0 surfaces of two builds (a procedural cut
                              passes with the same limits)
Runs in a venv with pymeshlab. Writes only to work/reduce/."""
import os, sys, struct, zlib
import numpy as np
import pymeshlab as ml

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
import json
from pathlib import Path


def read_glb(path):
    raw = path.read_bytes()
    size = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + size]), raw[28 + size:]

W = os.path.join(HERE, 'work', 'reduce')
TYPES = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
WIDTH = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def accessor_array(document, binary, index):
    accessor = document['accessors'][index]
    view = document['bufferViews'][accessor['bufferView']]
    dtype = np.dtype(TYPES[accessor['componentType']]); width = WIDTH[accessor['type']]
    start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    stride = view.get('byteStride', dtype.itemsize * width)
    raw = np.frombuffer(bytes(binary), np.uint8, accessor['count'] * stride, start).reshape(accessor['count'], stride)
    return raw[:, :dtype.itemsize * width].copy().view(dtype).reshape(accessor['count'], width)
OPAQUE = {'Body', 'Bark', 'Pot'}
RATIOS = [0.7, 0.55, 0.45, 0.35, 0.25]


def opaque_lod0(path):
    doc, binary = read_glb(Path(path))
    node = next(n for n in doc['nodes'] if 'mesh' in n)
    global MODEL_HEIGHT
    V, F, U, total, ys = [], [], [], 0, []
    for prim in doc['meshes'][node['mesh']]['primitives']:
        idx = accessor_array(doc, binary, prim['indices']).reshape(-1, 3)
        total += len(idx)
        acc = doc['accessors'][prim['attributes']['POSITION']]
        ys += [acc['min'][1], acc['max'][1]]
        MODEL_HEIGHT = max(ys) - min(ys)          # distances in % of the whole model's height, as the pilot
        if doc['materials'][prim['material']]['name'] not in OPAQUE:
            continue
        pos = accessor_array(doc, binary, prim['attributes']['POSITION'])
        uv = accessor_array(doc, binary, prim['attributes']['TEXCOORD_0'])
        base = sum(len(v) for v in V)
        V.append(pos); F.append(idx + base); U.append(uv[idx].reshape(-1, 2) + [100.0 * prim['material'], 0])
    if not V:
        return None, None, None, total
    V = np.concatenate(V).astype(float); F = np.concatenate(F); U = np.concatenate(U)
    # weld positions (seams duplicate vertices); the wedge UVs keep the seams for the texture-aware collapse
    key = np.round(V / 1e-5).astype(np.int64)
    _, first, inverse = np.unique(key, axis=0, return_index=True, return_inverse=True)
    return V[first], inverse.reshape(-1)[F], U, total


def write_obj(path, verts, faces, uv):
    folder = os.path.dirname(path)
    chunk = lambda t, b: struct.pack('>I', len(b)) + t + b + struct.pack('>I', zlib.crc32(t + b))
    open(os.path.join(folder, 'tex.png'), 'wb').write(
        b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
        + chunk(b'IDAT', zlib.compress(b'\x00\xff\xff\xff')) + chunk(b'IEND', b''))
    open(os.path.join(folder, 'in.mtl'), 'w').write('newmtl m\nmap_Kd tex.png\n')
    with open(path, 'w') as f:
        f.write('mtllib in.mtl\n')
        f.writelines(f'v {x} {y} {z}\n' for x, y, z in verts)
        f.writelines(f'vt {u} {v}\n' for u, v in uv)
        f.write('usemtl m\n')
        f.writelines(f'f {a+1}/{3*i+1} {b+1}/{3*i+2} {c+1}/{3*i+3}\n' for i, (a, b, c) in enumerate(faces))


def distance(ms, H):
    a = ms.get_hausdorff_distance(sampledmesh=1, targetmesh=0, samplevert=True, sampleface=True, samplenum=20000)
    b = ms.get_hausdorff_distance(sampledmesh=0, targetmesh=1, samplevert=True, sampleface=True, samplenum=20000)
    return max(a['max'], b['max']) / H * 100, max(a['mean'], b['mean']) / H * 100


def ladder(path):
    name = os.path.basename(path)
    V, F, U, total = opaque_lod0(path)
    if V is None:
        print(f'{name}: no opaque faces'); return
    H = MODEL_HEIGHT
    tmp = os.path.join(W, 'obj'); os.makedirs(tmp, exist_ok=True)
    write_obj(os.path.join(tmp, 'in.obj'), V, F, U)
    out = []
    for r in RATIOS:
        ms = ml.MeshSet(); ms.load_new_mesh(os.path.join(tmp, 'in.obj')); ms.load_new_mesh(os.path.join(tmp, 'in.obj'))
        ms.meshing_decimation_quadric_edge_collapse_with_texture(
            targetfacenum=max(int(len(F) * r), 12), qualitythr=.3, extratcoordw=1.0, preserveboundary=True,
            boundaryweight=10.0, optimalplacement=True, preservenormal=True)
        n = ms.current_mesh().face_number()
        mx, mean = distance(ms, H)
        out.append(f"r{int(r * 100)}:{n}:{mx:.2f}/{mean:.3f}{'*' if mx <= 1.5 and mean <= 0.15 else ''}")
    print(f'{name:24s} LOD0 {total:5d} opaque {len(F):5d}  ' + ' '.join(out))


def compare(old, new):
    tmp = os.path.join(W, 'cmp'); os.makedirs(tmp, exist_ok=True)
    ms = ml.MeshSet()
    for i, path in enumerate((old, new)):
        V, F, U, total = opaque_lod0(path)
        write_obj(os.path.join(tmp, f'{i}.obj'), V, F, U)
        ms.load_new_mesh(os.path.join(tmp, f'{i}.obj'))
        if i == 0:
            H = MODEL_HEIGHT
        print(os.path.basename(path), 'LOD0', total, 'opaque', len(F))
    mx, mean = distance(ms, H)
    print(f'distance max {mx:.2f} % mean {mean:.3f} % of the height:', 'PASS' if mx <= 1.5 and mean <= 0.15 else 'FAIL')


if __name__ == '__main__':
    if sys.argv[1] == 'ladder':
        for p in sys.argv[2:]:
            ladder(p)
    else:
        compare(sys.argv[2], sys.argv[3])
