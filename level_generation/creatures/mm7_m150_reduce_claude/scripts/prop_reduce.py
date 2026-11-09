"""Rigid attachment (helmet / shield GLB, unskinned; split off by tools/split_attachment.py) with a reduced LOD0:
the LOD0 primitive (POSITION, NORMAL, TEXCOORD_0) is welded by position+UV, decimated by MeshLab's texture-aware
quadric collapse to TARGET triangles (boundaries and normals preserved, as decimate_tex.py), and written back as new
accessors; normals are recomputed per vertex from the faces (smooth, as the source), LOD1-3, materials, images and
extras stay as they are. Run with the MeshLab venv (python -I). Usage: prop_reduce.py <in.glb> <out.glb> <target>"""
import struct, sys, os, tempfile
from pathlib import Path
import numpy as np
import pymeshlab as ml
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

src, out, target = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
doc, binary = read_glb(src); binary = bytearray(binary)
mesh = doc['meshes'][doc['nodes'][0]['mesh']]
prim = mesh['primitives'][0]; at = prim['attributes']


def arr(i, dt, c):
    return np.frombuffer(accessor_bytes(doc, binary, i), dt).reshape(-1, c)


P = arr(at['POSITION'], np.float32, 3).astype(np.float64); UV = arr(at['TEXCOORD_0'], np.float32, 2).astype(np.float64)
ia = doc['accessors'][prim['indices']]
I = arr(prim['indices'], {5125: np.uint32, 5123: np.uint16}[ia['componentType']], 1).reshape(-1, 3).astype(np.int64)
tmp = tempfile.mkdtemp(dir=str(Path(__file__).resolve().parents[1] / 'work'))
import zlib
chunk = lambda t, b: struct.pack('>I', len(b)) + t + b + struct.pack('>I', zlib.crc32(t + b))
open(f'{tmp}/tex.png', 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
                                    + chunk(b'IDAT', zlib.compress(b'\x00\xff\xff\xff')) + chunk(b'IEND', b''))
open(f'{tmp}/in.mtl', 'w').write('newmtl m\nmap_Kd tex.png\n')
with open(f'{tmp}/in.obj', 'w') as f:
    f.write('mtllib in.mtl\nusemtl m\n')
    f.writelines(f'v {x} {y} {z}\n' for x, y, z in P)
    f.writelines(f'vt {u} {v}\n' for u, v in UV)
    f.writelines(f'f {a+1}/{a+1} {b+1}/{b+1} {c+1}/{c+1}\n' for a, b, c in I)
ms = ml.MeshSet(); ms.load_new_mesh(f'{tmp}/in.obj')
ms.meshing_merge_close_vertices(threshold=ml.PercentageValue(0.0001))
before = ms.current_mesh().face_number()
ms.meshing_decimation_quadric_edge_collapse_with_texture(targetfacenum=target, qualitythr=.3, extratcoordw=1.0,
    preserveboundary=True, boundaryweight=10.0, optimalplacement=True, preservenormal=True)
m = ms.current_mesh()
V = m.vertex_matrix(); F = m.face_matrix(); W = m.wedge_tex_coord_matrix().reshape(-1, 3, 2)
# glTF needs one UV per vertex: split per (vertex, uv) wedge
keys = {}; nv, nuv, nf = [], [], []
for fi, face in enumerate(F):
    row = []
    for k in range(3):
        key = (int(face[k]), round(float(W[fi, k, 0]), 6), round(float(W[fi, k, 1]), 6))
        if key not in keys:
            keys[key] = len(nv); nv.append(V[face[k]]); nuv.append(W[fi, k])
        row.append(keys[key])
    nf.append(row)
nv, nuv, nf = np.array(nv), np.array(nuv), np.array(nf)
fn = np.cross(nv[nf[:, 1]] - nv[nf[:, 0]], nv[nf[:, 2]] - nv[nf[:, 0]])
vn = np.zeros_like(nv)
for k in range(3):
    np.add.at(vn, nf[:, k], fn)
# smooth across UV splits too: accumulate by position
pos_key = {}
for i, p in enumerate(nv):
    pos_key.setdefault(tuple(np.round(p, 6)), []).append(i)
for ids in pos_key.values():
    s = vn[ids].sum(0); vn[ids] = s
vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
pa = doc['accessors'][at['POSITION']]
new_pos = append_accessor(doc, binary, pa, nv.astype(np.float32).tobytes())
doc['accessors'][new_pos]['count'] = len(nv)
doc['accessors'][new_pos]['min'] = nv.min(0).astype(float).tolist(); doc['accessors'][new_pos]['max'] = nv.max(0).astype(float).tolist()
new_nrm = append_accessor(doc, binary, doc['accessors'][at['NORMAL']], vn.astype(np.float32).tobytes())
doc['accessors'][new_nrm]['count'] = len(nv)
for key in ('min', 'max'):
    doc['accessors'][new_nrm].pop(key, None)
new_uv = append_accessor(doc, binary, doc['accessors'][at['TEXCOORD_0']], nuv.astype(np.float32).tobytes())
doc['accessors'][new_uv]['count'] = len(nv)
for key in ('min', 'max'):
    doc['accessors'][new_uv].pop(key, None)
ida = dict(ia); ida['componentType'] = 5125
new_idx = append_accessor(doc, binary, ida, nf.astype(np.uint32).tobytes())
doc['accessors'][new_idx]['count'] = int(nf.size); doc['accessors'][new_idx]['componentType'] = 5125
for key in ('min', 'max'):
    doc['accessors'][new_idx].pop(key, None)
extra = {k: v for k, v in at.items() if k not in ('POSITION', 'NORMAL', 'TEXCOORD_0')}
if extra:
    raise SystemExit(f'unexpected attributes {list(extra)}')
prim['attributes'] = {'POSITION': new_pos, 'NORMAL': new_nrm, 'TEXCOORD_0': new_uv}; prim['indices'] = new_idx
write_glb(out, doc, bytes(binary))
print('PROPREDUCE', src.name, 'LOD0', len(I), '-> welded', before, '->', len(nf), 'tris, verts', len(nv), '->', out)
