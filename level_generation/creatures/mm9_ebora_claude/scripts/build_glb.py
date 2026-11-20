"""Ebora GLB: merged mesh npz (Blender frame) + bind json -> skinned GLB with MM9's node names (no clips).
Textures: optional json {material: {base, normal, orm}} as 4th arg. Args: <mesh npz> <bind json> <out glb> [textures json]"""
import json, sys, struct
from pathlib import Path
import numpy as np
mesh_npz, bind_json, out = sys.argv[1:4]
TEX = json.load(open(sys.argv[4])) if len(sys.argv) > 4 else {}
HERE = Path(__file__).resolve().parents[1]
B = json.load(open(bind_json)); order = B['order']; parent = B['parent']; Wd = {n: np.array(m) for n, m in B['world'].items()}
idx = {n: i for i, n in enumerate(order)}
def mat2q(m):
    t = np.trace(m)
    if t > 0:
        s = np.sqrt(t + 1) * 2; q = [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, s / 4]
    else:
        i = int(np.argmax(np.diag(m))); j, k = (i + 1) % 3, (i + 2) % 3
        s = np.sqrt(1 + m[i, i] - m[j, j] - m[k, k]) * 2
        q = [0, 0, 0, 0]; q[i] = s / 4; q[j] = (m[j, i] + m[i, j]) / s; q[k] = (m[k, i] + m[i, k]) / s; q[3] = (m[k, j] - m[j, k]) / s
    q = np.array(q); return q / np.linalg.norm(q)
TRS = {}
for n in order:
    L = Wd[n] if n == 'Scene Root' else np.linalg.inv(Wd[parent[n]]) @ Wd[n]
    TRS[n] = (L[:3, 3].tolist(), mat2q(L[:3, :3]).tolist())
D = np.load(mesh_npz)
co = np.c_[D['co'][:, 0], D['co'][:, 2], -D['co'][:, 1]]; tri = D['tri']
names = [str(x) for x in D['names']]; W = D['W']
o4 = np.argsort(-W, axis=1)[:, :4]; w4 = np.take_along_axis(W, o4, 1); w4 = np.where(w4 < 0.01, 0, w4); w4 /= w4.sum(1, keepdims=True)
J0 = np.array([idx[names[k]] for k in range(len(names))])[o4]
uv = D['uv'] * [1, -1] + [0, 1]
mats = D['mat']; matnames = [str(x) for x in D['matnames']]
# normals: smooth by shared position within a material (wing shell layers keep their own side by orientation)
fn = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]])
key = np.round(co, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
N = np.zeros_like(co)
Ns = np.zeros((inv.max() + 1, 3))
for c in range(3): np.add.at(Ns, inv[tri[:, c]], fn)
N = Ns[inv]
# vertices whose position-merged normal cancels (thin shells) use their own faces' normal
own = np.zeros_like(co)
for c in range(3): np.add.at(own, tri[:, c], fn)
nl = np.linalg.norm(N, axis=1); ol = np.linalg.norm(own, axis=1)
bad = (nl < 0.5 * ol) | ((N * own).sum(1) < 0)
N[bad] = own[bad]
N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
# nose ridge (head material, |x| < 7 mm, z 0.845-0.925 Blender): the mirrored mesh meets in a sharp ridge; smooth its normals
# with the face beside it (coordinator, 2026-11-01: bright streak down the bridge)
Pb = D['co']; hm = matnames.index('EboraHead') if 'EboraHead' in matnames else -1
if hm >= 0:
    hv = np.unique(tri[mats == hm])
    rid = hv[(np.abs(Pb[hv, 0]) < 0.007) & (Pb[hv, 2] > 0.845) & (Pb[hv, 2] < 0.925) & (Pb[hv, 1] < 0.0)]
    if len(rid):
        from scipy.spatial import cKDTree as _K
        kd = _K(Pb[hv]); Nn = N.copy()
        for v in rid:
            nb = hv[kd.query_ball_point(Pb[v], 0.012)]; Nn[v] = N[nb].mean(0)
        N = Nn; print('nose ridge normals smoothed', len(rid))
# Wing membranes (merge.py comp 100/101): a thin skin lit through itself. Both shell layers take a bent normal tilted along
# the membrane's in-plane up axis (bind +z, glTF +y, carried by the wing bones), so the underside of a raised wing catches
# the top light like the upper side and shows the tier colour from both sides (spread wings read maroon from the front).
import os
BEND = float(os.environ.get('MEMBRANE_BEND', '1.6'))
if 'comp' in D.files and BEND > 0:
    mem = np.isin(D['comp'], (100, 101))
    U = np.array([0.0, 1.0, 0.0])
    Nm = N[mem] + BEND * (U - (N[mem] @ U)[:, None] * N[mem])
    N[mem] = Nm / np.maximum(np.linalg.norm(Nm, axis=1, keepdims=True), 1e-12)
    print('membrane normals bent', int(mem.sum()), 'x', BEND)
blob = bytearray(); views = []; accs = []
def add(arr, ctype, typ, target=None, mm=False):
    while len(blob) % 4: blob.append(0)
    o = len(blob); b = arr.tobytes(); blob.extend(b)
    v = {'buffer': 0, 'byteOffset': o, 'byteLength': len(b)}
    if target: v['target'] = target
    views.append(v)
    a = {'bufferView': len(views) - 1, 'componentType': ctype, 'count': len(arr), 'type': typ}
    if mm: a['min'] = arr.min(0).astype(float).tolist(); a['max'] = arr.max(0).astype(float).tolist()
    accs.append(a); return len(accs) - 1
nodes = []
for n in order:
    t, q = TRS[n]; nodes.append({'name': n, 'translation': t, 'rotation': q, 'children': []})
for n in order[1:]: nodes[idx[parent[n]]]['children'].append(idx[n])
for x in nodes:
    if not x['children']: del x['children']
prims = []
for m in range(len(matnames)):
    t_ = tri[mats == m]
    if not len(t_): continue
    used, inv_ = np.unique(t_.ravel(), return_inverse=True)
    pa = add(co[used].astype('f4'), 5126, 'VEC3', 34962, True); na = add(N[used].astype('f4'), 5126, 'VEC3', 34962); ua = add(uv[used].astype('f4'), 5126, 'VEC2', 34962)
    ja = add(J0[used].astype('u2'), 5123, 'VEC4', 34962); wa = add(w4[used].astype('f4'), 5126, 'VEC4', 34962)
    ind = add(inv_.astype('u4'), 5125, 'SCALAR', 34963)
    prims.append({'attributes': {'POSITION': pa, 'NORMAL': na, 'TEXCOORD_0': ua, 'JOINTS_0': ja, 'WEIGHTS_0': wa}, 'indices': ind, 'material': m, 'mode': 4})
ibm = np.array([np.linalg.inv(Wd[n]).T.ravel() for n in order], 'f4')
ib = add(ibm, 5126, 'MAT4')
mesh_node = len(nodes)
nodes.append({'name': 'Ebora', 'mesh': 0, 'skin': 0})
doc = {'asset': {'version': '2.0', 'generator': 'mm9_ebora build_glb'}, 'scene': 0, 'scenes': [{'nodes': [0, mesh_node]}], 'nodes': nodes,
       'meshes': [{'name': 'Ebora', 'primitives': prims}], 'skins': [{'joints': list(range(len(order))), 'inverseBindMatrices': ib, 'skeleton': 0}],
       'accessors': accs, 'bufferViews': views, 'buffers': [{'byteLength': 0}],
       'materials': [{'name': m, 'pbrMetallicRoughness': {'baseColorFactor': [.7, .65, .6, 1] if 'Wing' not in m else [.55, .2, .15, 1], 'metallicFactor': 0, 'roughnessFactor': .8}} for m in matnames]}
images = []; textures = []
def addimg(path):
    data = Path(path).read_bytes()
    while len(blob) % 4: blob.append(0)
    o = len(blob); blob.extend(data); views.append({'buffer': 0, 'byteOffset': o, 'byteLength': len(data)})
    images.append({'bufferView': len(views) - 1, 'mimeType': 'image/png', 'name': Path(path).stem})
    textures.append({'source': len(images) - 1, 'sampler': 0}); return len(textures) - 1
for m, nm in enumerate(matnames):
    t = TEX.get(nm)
    if not t: continue
    pb = doc['materials'][m]['pbrMetallicRoughness']; pb.pop('baseColorFactor', None)
    pb['baseColorTexture'] = {'index': addimg(HERE / t['base'])}
    pb.pop('roughnessFactor', None); pb.pop('metallicFactor', None)
    if t.get('orm'): pb['metallicRoughnessTexture'] = {'index': addimg(HERE / t['orm'])}
    if t.get('normal'): doc['materials'][m]['normalTexture'] = {'index': addimg(HERE / t['normal'])}
if images:
    doc['images'] = images; doc['textures'] = textures; doc['samplers'] = [{'magFilter': 9729, 'minFilter': 9987, 'wrapS': 33071, 'wrapT': 33071}]
while len(blob) % 4: blob.append(0)
doc['buffers'][0]['byteLength'] = len(blob)
j = json.dumps(doc, separators=(',', ':')).encode(); j += b' ' * (-len(j) % 4)
with open(out, 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(j) + 8 + len(blob)))
    f.write(struct.pack('<II', len(j), 0x4E4F534A)); f.write(j)
    f.write(struct.pack('<II', len(blob), 0x004E4942)); f.write(blob)
print('GLB', out, len(co), len(tri), len(order), 'joints')
