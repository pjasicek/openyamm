"""Retexture uploads from work/uv.npz (pose: Meshy's, so the masters line up). texturing/body.glb (body UV, cut-off neck and jaw on one point), head.glb."""
import sys, json, struct, numpy as np
from pathlib import Path
J = np.load('work/joined.npz'); U = np.load('work/uv.npz'); C = np.load('work/cutoff.npz')
up = J['co_up']; Cu = C['co_up']
Path('texturing').mkdir(exist_ok=True)
def write(path, P, Uv, T):
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    key = np.round(P, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
    Ns = np.zeros((inv.max() + 1, 3))
    for c in range(3): np.add.at(Ns, inv[T[:, c]], fn)
    N = Ns[inv]; N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    blob = bytearray(); views = []; accs = []
    def add(arr, ct, typ, tgt, mm=False):
        while len(blob) % 4: blob.append(0)
        o = len(blob); b = arr.tobytes(); blob.extend(b); views.append({'buffer': 0, 'byteOffset': o, 'byteLength': len(b), 'target': tgt})
        a = {'bufferView': len(views) - 1, 'componentType': ct, 'count': len(arr), 'type': typ}
        if mm: a['min'] = arr.min(0).tolist(); a['max'] = arr.max(0).tolist()
        accs.append(a); return len(accs) - 1
    pa = add(P.astype('f4'), 5126, 'VEC3', 34962, True); na = add(N.astype('f4'), 5126, 'VEC3', 34962); ua = add((Uv * [1, -1] + [0, 1]).astype('f4'), 5126, 'VEC2', 34962); ia = add(T.astype('u4').ravel(), 5125, 'SCALAR', 34963)
    accs[ia]['type'] = 'SCALAR'
    doc = {'asset': {'version': '2.0'}, 'scene': 0, 'scenes': [{'nodes': [0]}], 'nodes': [{'mesh': 0, 'name': 'liz'}], 'meshes': [{'primitives': [{'attributes': {'POSITION': pa, 'NORMAL': na, 'TEXCOORD_0': ua}, 'indices': ia, 'material': 0}]}],
           'materials': [{'name': 'm', 'pbrMetallicRoughness': {'baseColorFactor': [.7, .7, .7, 1]}}], 'accessors': accs, 'bufferViews': views, 'buffers': [{'byteLength': len(blob)}]}
    while len(blob) % 4: blob.append(0)
    doc['buffers'][0]['byteLength'] = len(blob)
    j = json.dumps(doc, separators=(',', ':')).encode(); j += b' ' * (-len(j) % 4)
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 28 + len(j) + len(blob))); f.write(struct.pack('<II', len(j), 0x4E4F534A)); f.write(j); f.write(struct.pack('<II', len(blob), 0x004E4942)); f.write(blob)
    print(path, len(P), len(T), 'size', Path(path).stat().st_size)
def split(pos, fo, uv):
    """per-corner -> unique (vertex, uv)"""
    k = np.c_[fo.ravel(), np.round(uv.reshape(-1, 2) * 2 ** 20).astype(np.int64)]
    u, idx, inv = np.unique(k, axis=0, return_index=True, return_inverse=True); inv = inv.ravel()
    return pos[fo.ravel()[idx]], uv.reshape(-1, 2)[idx], inv.reshape(-1, 3)
Pb, Ub, Tb = split(up, U['ob'], U['ub'])
Ph, Uh, Th = split(up, U['oh'], U['uh'])
# an unused point of the body atlas for the occluder
R = 512; im = np.zeros((R, R), bool)
q = (U['ub'].reshape(-1, 2) * (R - 1)).astype(int); im[q[:, 1], q[:, 0]] = True
from scipy import ndimage as ndi
dd = ndi.distance_transform_edt(~ndi.binary_dilation(im, iterations=2)); yy, xx = np.unravel_index(dd.argmax(), dd.shape); pt = np.array([xx, yy]) / (R - 1); print('empty point', pt, dd.max())
nC = len(Cu)
Pa = np.vstack([Pb, Cu]); Ua = np.vstack([Ub, np.repeat(pt[None], nC, 0)]); Ta = np.vstack([Tb, C['tri'] + len(Pb)])
write('texturing/body.glb', Pa, Ua, Ta)
write('texturing/head.glb', Ph, Uh, Th)
