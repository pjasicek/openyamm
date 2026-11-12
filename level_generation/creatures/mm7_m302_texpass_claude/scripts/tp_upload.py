"""Static Meshy upload GLB of a texture-pass layout without Blender (after tp_fix_collapsed.py changed the layout the
Blender script exported): welded LOD0 positions (glTF Y-up, as in the GLB), smooth area-weighted normals over welded
vertices, the layout's UVs, vertices split at UV seams, no material.
Usage: tp_upload.py <layout npz> <out glb> [head]   (head: only the head faces)"""
import json
import struct
import sys

import numpy as np

import tp_common as C

layout_path, out = sys.argv[1:3]
head_only = len(sys.argv) > 3 and sys.argv[3] == 'head'
L = np.load(layout_path)
d = np.load(C.lod0_path())
tri, weld = d['tri'], d['weld']
keep = np.nonzero(d['head_face'])[0] if head_only else np.arange(len(tri))
nweld = int(weld.max()) + 1
wpos = np.zeros((nweld, 3))
wpos[weld] = d['pos']
wtri = weld[tri]
fn = np.cross(wpos[wtri[:, 1]] - wpos[wtri[:, 0]], wpos[wtri[:, 2]] - wpos[wtri[:, 0]])
nrm = np.zeros((nweld, 3))
for k in range(3):
    np.add.at(nrm, wtri[:, k], fn)
nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
cw = wtri[keep]
cuv = L['uv'][keep]
key = np.concatenate([cw.reshape(-1, 1).astype(np.float64), np.round(cuv.reshape(-1, 2), 7)], 1)
_, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
src = cw.reshape(-1)[first]
P = wpos[src].astype(np.float32)
N = nrm[src].astype(np.float32)
U = cuv.reshape(-1, 2)[first].astype(np.float32)
I = inv.ravel().astype(np.uint32)
chunks, views, accs = [], [], []


def add(arr, kind, comp, target, minmax=False):
    off = sum(len(c) for c in chunks)
    data = arr.tobytes()
    data += b'\0' * (-len(data) % 4)
    chunks.append(data)
    views.append({'buffer': 0, 'byteOffset': off, 'byteLength': arr.nbytes, 'target': target})
    a = {'bufferView': len(views) - 1, 'componentType': comp, 'count': len(arr), 'type': kind}
    if minmax:
        a['min'] = arr.min(0).tolist()
        a['max'] = arr.max(0).tolist()
    accs.append(a)
    return len(accs) - 1


ip = add(P, 'VEC3', 5126, 34962, True)
inn = add(N, 'VEC3', 5126, 34962)
iu = add(U, 'VEC2', 5126, 34962)
ii = add(I, 'SCALAR', 5125, 34963)
binary = b''.join(chunks)
doc = {'asset': {'version': '2.0', 'generator': 'tp_upload.py'}, 'scene': 0, 'scenes': [{'nodes': [0]}],
       'nodes': [{'mesh': 0, 'name': 'Body'}],
       'meshes': [{'name': 'Body', 'primitives': [{'attributes': {'POSITION': ip, 'NORMAL': inn, 'TEXCOORD_0': iu},
                                                   'indices': ii, 'mode': 4}]}],
       'accessors': accs, 'bufferViews': views, 'buffers': [{'byteLength': len(binary)}]}
js = json.dumps(doc, separators=(',', ':')).encode()
js += b' ' * (-len(js) % 4)
with open(out, 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(binary)))
    f.write(struct.pack('<II', len(js), 0x4E4F534A) + js)
    f.write(struct.pack('<II', len(binary), 0x004E4942) + binary)
print('UPLOAD', out, len(keep), 'triangles', len(P), 'vertices')
