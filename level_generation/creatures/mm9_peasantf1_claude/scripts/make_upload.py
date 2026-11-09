"""Meshy upload: the whole figure in its true-handed orientation (x negated, the final GLB is mirrored), body UV layout, head faces on one free point. Args: <uv npz> <out glb>"""
import sys, json, struct
import numpy as np
IN, OUT = sys.argv[1:3]
D = np.load(IN); co, tri, uv, mat = D['co'], D['tri'], D['uv'].copy(), D['mat']
P = np.c_[-co[:, 0], co[:, 2], -co[:, 1]].astype('f4')       # Blender -> glTF, mirrored
hv = np.unique(tri[mat == 1]); uv[hv] = (0.002, 0.002)
UV = (uv * [1, -1] + [0, 1]).astype('f4')
T = tri[:, ::-1].astype('u4')
fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); N = np.zeros_like(P)
key = np.round(P, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel(); Ns = np.zeros((inv.max() + 1, 3))
for c in range(3): np.add.at(Ns, inv[T[:, c]], fn)
N = Ns[inv]; N = (N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)).astype('f4')
blob = bytearray(); views = []; accs = []
def add(a, ct, ty, tg, mm=False):
    while len(blob) % 4: blob.append(0)
    o = len(blob); b = a.tobytes(); blob.extend(b); views.append({'buffer': 0, 'byteOffset': o, 'byteLength': len(b), 'target': tg})
    x = {'bufferView': len(views) - 1, 'componentType': ct, 'count': len(a), 'type': ty}
    if mm: x['min'] = a.min(0).tolist(); x['max'] = a.max(0).tolist()
    accs.append(x); return len(accs) - 1
pa = add(P, 5126, 'VEC3', 34962, True); na = add(N, 5126, 'VEC3', 34962); ua = add(UV, 5126, 'VEC2', 34962); ia = add(T.ravel(), 5125, 'SCALAR', 34963)
doc = {'asset': {'version': '2.0'}, 'scene': 0, 'scenes': [{'nodes': [0]}], 'nodes': [{'mesh': 0, 'name': 'Monk'}], 'meshes': [{'name': 'Monk', 'primitives': [{'attributes': {'POSITION': pa, 'NORMAL': na, 'TEXCOORD_0': ua}, 'indices': ia, 'mode': 4}]}], 'accessors': accs, 'bufferViews': views, 'buffers': [{'byteLength': len(blob)}]}
j = json.dumps(doc, separators=(',', ':')).encode(); j += b' ' * (-len(j) % 4)
while len(blob) % 4: blob.append(0)
doc['buffers'][0]['byteLength'] = len(blob); j = json.dumps(doc, separators=(',', ':')).encode(); j += b' ' * (-len(j) % 4)
with open(OUT, 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, 28 + len(j) + len(blob))); f.write(struct.pack('<II', len(j), 0x4E4F534A)); f.write(j); f.write(struct.pack('<II', len(blob), 0x004E4942)); f.write(blob)
print('UPLOAD', OUT, len(P), len(T))
