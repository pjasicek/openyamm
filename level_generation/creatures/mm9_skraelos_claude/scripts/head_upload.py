"""Head-only GLB with its own UVs for the AO bake. Args: <uv npz> <out glb>"""
import sys, json, struct
import numpy as np
D = np.load(sys.argv[1]); co, tri, uv, mat = D['co'], D['tri'], D['uv'], D['mat']
t = tri[mat == 1]; vs, inv = np.unique(t, return_inverse=True); T = inv.reshape(-1, 3).astype('u4')
P = np.c_[co[vs, 0], co[vs, 2], -co[vs, 1]].astype('f4'); U = (uv[vs] * [1, -1] + [0, 1]).astype('f4')
blob = bytearray(); views = []; accs = []
def add(a, ct, ty, tg, mm=False):
    while len(blob) % 4: blob.append(0)
    o = len(blob); b = a.tobytes(); blob.extend(b); views.append({'buffer': 0, 'byteOffset': o, 'byteLength': len(b), 'target': tg})
    x = {'bufferView': len(views) - 1, 'componentType': ct, 'count': len(a), 'type': ty}
    if mm: x['min'] = a.min(0).tolist(); x['max'] = a.max(0).tolist()
    accs.append(x); return len(accs) - 1
pa = add(P, 5126, 'VEC3', 34962, True); ua = add(U, 5126, 'VEC2', 34962); ia = add(T.ravel(), 5125, 'SCALAR', 34963)
while len(blob) % 4: blob.append(0)
doc = {'asset': {'version': '2.0'}, 'scene': 0, 'scenes': [{'nodes': [0]}], 'nodes': [{'mesh': 0, 'name': 'H'}], 'meshes': [{'primitives': [{'attributes': {'POSITION': pa, 'TEXCOORD_0': ua}, 'indices': ia, 'mode': 4}]}], 'accessors': accs, 'bufferViews': views, 'buffers': [{'byteLength': len(blob)}]}
j = json.dumps(doc, separators=(',', ':')).encode(); j += b' ' * (-len(j) % 4)
with open(sys.argv[2], 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, 28 + len(j) + len(blob))); f.write(struct.pack('<II', len(j), 0x4E4F534A)); f.write(j); f.write(struct.pack('<II', len(blob), 0x004E4942)); f.write(blob)
