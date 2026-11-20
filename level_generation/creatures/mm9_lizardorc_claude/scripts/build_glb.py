"""Lizard-Orc GLB: mesh + weights + MM9 hierarchy + added finger chains + half helpers. Nodes keep MM9's local rotations, so MM9's clips play unchanged. Bind = the fitted mesh: for MM9's bones it IS MM9's rest (the bind is symmetric and the mesh fits it); fingers, jaw and tongue
have our joints: bind frame = MM9's rest frame turned by a rotation D, so at the nodes' rest the middle finger's segments lie along MM9's; the other fingers take the middle finger's D and keep their splay. Args: <mesh npz> <weights npz> <out glb>. Mesh may carry uv, mat, matnames, textures (json)."""
import json, sys, struct, os
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
import rig_bones as RB
import mm9_joints
mesh_npz, w_npz, out = sys.argv[1:4]
Wm, par, doc0 = mm9_joints.rest()
P, tips = RB.joints()
sn = [n.get('name') for n in doc0['nodes']]
JOINTS = [n for n in sn if n and not n.endswith('.mesh')]
def unit(v): return v / np.linalg.norm(v)
def least(a, b):
    a, b = unit(a), unit(b); v = np.cross(a, b); c = a @ b; s = np.linalg.norm(v)
    if s < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s ** 2)
order = []
def visit(n):
    order.append(n)
    for k in doc0['nodes'][sn.index(n)].get('children', []):
        if sn[k] in JOINTS: visit(sn[k])
visit('Scene Root')
X = np.array([-1, 1, 1.])
BIND = {}; parent = dict(par); NEW = {}
# MM9's world rest of the finger stations for the added bones
for n in order:
    M = np.eye(4); M[:3, :3] = Wm[n][:3, :3]; M[:3, 3] = P[n] if n in P else Wm[n][:3, 3]; BIND[n] = M
D_F = {}
for s, m in (('L', np.array([1, 1, 1.])), ('R', X)):
    pre = f'Bip01 {s} '
    # middle finger Finger2 rests on MM9's Finger1 chain: segment 0 along Finger1 -> Finger11, segment 1 along Finger11 -> a continuation of it
    a0 = Wm[pre + 'Finger11'][:3, 3] - Wm[pre + 'Finger1'][:3, 3]
    b0 = P[pre + 'Finger21'] - P[pre + 'Finger2']; b1 = P[pre + 'Finger22'] - P[pre + 'Finger21']; b2 = tips['Finger2'] * m - P[pre + 'Finger22']
    D0 = least(a0, b0); D1 = least(a0, b1); D2 = D1 @ np.eye(3)     # at rest the middle joint straightens along MM9's bone
    th0 = Wm[pre + 'Finger01'][:3, 3] - Wm[pre + 'Finger0'][:3, 3]
    Dt0 = least(th0, P[pre + 'Finger01'] - P[pre + 'Finger0']); Dt1 = least(th0, P[pre + 'Finger02'] - P[pre + 'Finger01'])
    for f in ('Finger1', 'Finger2', 'Finger3'):
        n0, n1, n2 = pre + f, pre + f + '1', pre + f + '2'
        for nn, ref, Dd, pa in ((n0, pre + 'Finger1', D0, pre + 'Hand'), (n1, pre + 'Finger11', D1, n0), (n2, pre + 'Finger11', D1, n1)):
            M = np.eye(4); M[:3, :3] = Dd @ Wm[ref][:3, :3]; M[:3, 3] = P[nn]; BIND[nn] = M
            if nn not in order: NEW[nn] = (ref, pa)
            parent[nn] = pa
    n0, n1, n2 = pre + 'Finger0', pre + 'Finger01', pre + 'Finger02'
    for nn, ref, Dd, pa in ((n0, n0, Dt0, pre + 'Hand'), (n1, n1, Dt1, n0), (n2, n1, Dt1, n1)):
        M = np.eye(4); M[:3, :3] = Dd @ Wm[ref][:3, :3]; M[:3, 3] = P[nn]; BIND[nn] = M
        if nn not in order: NEW[nn] = (ref, pa)
        parent[nn] = pa
# jaw and tongue: rotation as MM9, joints ours
def mat2q(m):
    t = np.trace(m)
    if t > 0:
        s = np.sqrt(t + 1) * 2; q = [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, s / 4]
    else:
        i = int(np.argmax(np.diag(m))); j, k = (i + 1) % 3, (i + 2) % 3
        s = np.sqrt(1 + m[i, i] - m[j, j] - m[k, k]) * 2
        q = [0, 0, 0, 0]; q[i] = s / 4; q[j] = (m[j, i] + m[i, j]) / s; q[k] = (m[k, i] + m[i, k]) / s; q[3] = (m[k, j] - m[j, k]) / s
    q = np.array(q); return q / np.linalg.norm(q)
names = list(order) + list(NEW)
TRS = {}
for n in names:
    if parent.get(n) is None:
        TRS[n] = (Wm[n][:3, 3].tolist(), mat2q(Wm[n][:3, :3]).tolist()); continue
    pn = parent[n]; ref = NEW[n][0] if n in NEW else n
    rp = NEW[pn][0] if pn in NEW else pn
    Lm = np.linalg.inv(Wm[rp]) @ Wm[ref]
    t = (np.linalg.inv(BIND[pn]) @ BIND[n])[:3, 3]
    TRS[n] = (t.tolist(), mat2q(Lm[:3, :3]).tolist())
pairs = RB.half_pairs()
IBM_SPACE = dict(BIND)
for h, c, pn, _ in pairs:
    names.append(h); parent[h] = pn; IBM_SPACE[h] = BIND[c]; TRS[h] = (TRS[c][0], TRS[c][1])
# flap hinge at the belt: keyed by flap_keys.py so the front flap stays in front of the leading thigh
Mf = np.eye(4); Mf[:3, :3] = Wm['Bip01 Spine'][:3, :3]; Mf[:3, 3] = [0, .095, .115]
names.append('XFlap'); parent['XFlap'] = 'Bip01 Spine'; IBM_SPACE['XFlap'] = Mf; TRS['XFlap'] = ((np.linalg.inv(BIND['Bip01 Spine']) @ Mf)[:3, 3].tolist(), [0, 0, 0, 1])
idx = {n: i for i, n in enumerate(names)}
nodes = []
for n in names:
    t, q = TRS[n]; nodes.append({'name': n, 'translation': t, 'rotation': q, 'children': []})
for n in names[1:]:
    if parent.get(n) is not None: nodes[idx[parent[n]]]['children'].append(idx[n])
for x in nodes:
    if not x['children']: del x['children']
D = np.load(mesh_npz); co, tri = D['co'].astype('f8'), D['tri']
W = np.load(w_npz); wnames = [str(x) for x in W['wnames']]; vmap = np.array([idx[n] for n in wnames]); J0 = vmap[W['wj']]; ww = W['ww']
uv = D['uv'] if 'uv' in D else np.zeros((len(co), 2))
mats = D['mat'] if 'mat' in D else np.zeros(len(tri), int)
matnames = [str(x) for x in D['matnames']] if 'matnames' in D else ['Liz']
fn = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]])
key = np.round(co, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
Ns = np.zeros((inv.max() + 1, 3))
for c in range(3): np.add.at(Ns, inv[tri[:, c]], fn)
N = Ns[inv]; N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
if 'hard' in D.files:   # per-vertex flat shading for rigid pieces with hard edges
    pass
if 'ringv' in D:
    from scipy.spatial import cKDTree
    ids = np.where(D['ringv'])[0]; tr = cKDTree(co[ids]); nn = tr.query_ball_point(co[ids], .02)
    Nr = np.array([N[ids[q]].mean(0) for q in nn]); N[ids] = Nr / np.maximum(np.linalg.norm(Nr, axis=1, keepdims=True), 1e-12)
if 'part' in D:
    # run 2, crease under the chin: at the back of the jaw's underside long fan triangles fold onto each other (140-175 deg), and their flipped
    # normals cancel in the vertex sum: a bright V line. In that zone the vertex normals sum only faces that face down or forward, then average over 2 cm.
    pz = D['part']; zc = co
    zone = (pz == 1) & (np.abs(zc[:, 0]) < .055) & (zc[:, 1] > .59) & (zc[:, 1] < .70) & (zc[:, 2] > .07) & (zc[:, 2] < .24)
    if zone.any():
        dref = np.array([0, -.7, .7]) / np.sqrt(.98); ok = (fn @ dref) > 0
        Nz = np.zeros((inv.max() + 1, 3))
        for c in range(3): np.add.at(Nz, inv[tri[ok, c]], fn[ok])
        ids = np.where(zone)[0]; Nn = Nz[inv[ids]]; Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-12)
        from scipy.spatial import cKDTree
        nn = cKDTree(co[ids]).query_ball_point(co[ids], .02); Nr = np.array([Nn[q].mean(0) for q in nn])
        ln = np.linalg.norm(Nr, axis=1); g_ = ln > .3; N[ids[g_]] = Nr[g_] / ln[g_, None]; print('chin crease normals', int(g_.sum()), 'of', len(ids))
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
prims = []
for m in range(len(matnames)):
    t_ = tri[mats == m]
    if not len(t_): continue
    used, inv_ = np.unique(t_.ravel(), return_inverse=True)
    pa = add(co[used].astype('f4'), 5126, 'VEC3', 34962, True); na = add(N[used].astype('f4'), 5126, 'VEC3', 34962); ua = add(uv[used].astype('f4'), 5126, 'VEC2', 34962)
    ja = add(J0[used].astype('u2'), 5123, 'VEC4', 34962); wa = add(ww[used].astype('f4'), 5126, 'VEC4', 34962)
    ind = add(inv_.astype('u4'), 5125, 'SCALAR', 34963)
    prims.append({'attributes': {'POSITION': pa, 'NORMAL': na, 'TEXCOORD_0': ua, 'JOINTS_0': ja, 'WEIGHTS_0': wa}, 'indices': ind, 'material': m, 'mode': 4})
ibm = np.array([np.linalg.inv(IBM_SPACE[n]).T.ravel() for n in names], 'f4')
ib = add(ibm, 5126, 'MAT4')
mesh_node = len(nodes)
nodes.append({'name': 'LizardOrc', 'mesh': 0, 'skin': 0})
docj = {'asset': {'version': '2.0', 'generator': 'mm9_lizardorc build_glb'}, 'scene': 0, 'scenes': [{'nodes': [0, mesh_node]}], 'nodes': nodes,
        'meshes': [{'name': 'LizardOrc', 'primitives': prims}], 'skins': [{'joints': list(range(len(names))), 'inverseBindMatrices': ib, 'skeleton': 0}],
        'accessors': accs, 'bufferViews': views, 'buffers': [{'byteLength': 0}], 'materials': [{'name': m, 'pbrMetallicRoughness': {'baseColorFactor': [.45, .5, .32, 1], 'metallicFactor': 0, 'roughnessFactor': .7}, 'doubleSided': True} for m in matnames]}
if 'textures' in D.files:
    tex = json.loads(str(D['textures'])); images = []; textures = []
    def addimg(path):
        data = (HERE / path).read_bytes()
        while len(blob) % 4: blob.append(0)
        o = len(blob); blob.extend(data); views.append({'buffer': 0, 'byteOffset': o, 'byteLength': len(data)})
        images.append({'bufferView': len(views) - 1, 'mimeType': 'image/png', 'name': Path(path).stem}); textures.append({'source': len(images) - 1, 'sampler': 0}); return len(textures) - 1
    for m, nm in enumerate(matnames):
        t = tex.get(nm)
        if not t: continue
        mt = docj['materials'][m]; pb = mt['pbrMetallicRoughness']; pb.pop('baseColorFactor', None); pb['baseColorTexture'] = {'index': addimg(t['base'])}
        pb.pop('roughnessFactor', None); pb.pop('metallicFactor', None)
        if t.get('orm'): pb['metallicRoughnessTexture'] = {'index': addimg(t['orm'])}
        if t.get('normal'): mt['normalTexture'] = {'index': addimg(t['normal'])}
    docj['images'] = images; docj['textures'] = textures; docj['samplers'] = [{'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497, 'wrapT': 10497}]
while len(blob) % 4: blob.append(0)
docj['buffers'][0]['byteLength'] = len(blob)
j = json.dumps(docj, separators=(',', ':')).encode(); j += b' ' * (-len(j) % 4)
with open(out, 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(j) + 8 + len(blob)))
    f.write(struct.pack('<II', len(j), 0x4E4F534A)); f.write(j)
    f.write(struct.pack('<II', len(blob), 0x004E4942)); f.write(blob)
print('GLB', out, len(co), len(tri), len(names), 'joints')
