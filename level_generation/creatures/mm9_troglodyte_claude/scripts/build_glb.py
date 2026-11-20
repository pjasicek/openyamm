"""Troglodyte GLB: mesh + weights + MM9 hierarchy. Nodes keep MM9's names and local rotations, so MM9's clips play unchanged. Bind = the fitted symmetric mesh: each bone's bind frame is MM9's rest frame turned by the least
rotation onto our bone, inverse binds from that; a node's local translation is our joint in the parent's bind frame. Args: <mesh npz> <weights npz> <out glb>. Mesh may carry uv, mat, matnames, textures (json)."""
import json, sys, struct, os
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model
import rig_bones as RB
import mm9_joints
mesh_npz, w_npz, out = sys.argv[1:4]
Wm, par, doc0 = mm9_joints.rest()
P, tips = RB.joints()
PIV = json.loads(os.environ.get('PIVOTS', '{}'))       # joint -> offset, in the glTF frame (left side; mirrored)
sn = [n.get('name') for n in doc0['nodes']]
JOINTS = [n for n in sn if n and n not in ('trog', 'trog.mesh')]
def unit(v): return v / np.linalg.norm(v)
def least(a, b):
    a, b = unit(a), unit(b); v = np.cross(a, b); c = a @ b; s = np.linalg.norm(v)
    if s < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s ** 2)
CHILD = {}
for n, (p, h, t) in RB.table().items():
    if p: CHILD.setdefault(p, []).append(n)
TIP = {}
X = np.array([-1, 1, 1.])
for s in 'LR':
    for f in RB.FN:
        TIP[f'Bip02 {s} {RB.fk(f, 2)}'] = tips[f] * (X if s == 'R' else 1)
def mm9_dir_our_dir(n):
    pre = n.split(' ')[0]
    t = RB.table().get(n)
    return t
TB = RB.table()
BIND = {}
order = []
def visit(n):
    order.append(n)
    for k in doc0['nodes'][sn.index(n)].get('children', []):
        if sn[k] in JOINTS: visit(sn[k])
visit('Scene Root')
# jaw: mesh bind is open by JAW_OPEN deg about the hinge axis (x) relative to MM9's rest
JAW = float(os.environ.get('JAW_OPEN', 0))
for n in order:
    Rm = Wm[n][:3, :3]; M = np.eye(4)
    if n in P:
        D = np.eye(3)
        ours_tail = TB[n][2] if n in TB else None
        if n.endswith(' Foot'):
            c = n.replace('Foot', 'Toe0'); a_ = Wm[c][:3, 3] - Wm[n][:3, 3]; b_ = P[c] - P[n]; a_[1] = 0; b_[1] = 0; D = least(a_, b_)
        elif n == 'Box05':
            c_, s_ = np.cos(np.radians(JAW)), np.sin(np.radians(JAW)); D = np.array([[1, 0, 0], [0, c_, s_], [0, -s_, c_]])      # jaw down (toward -y) at the front (+z)
        elif n in ('Bip01 Head',) or n.endswith('Toe0'):
            D = np.eye(3)
        elif n == 'Box04' or n == 'Box06':
            D = None
        elif n in TB:
            ch = None
            # MM9's direction to the same child
            if n.endswith('Hand'): ch = n.replace('Hand', 'Finger2')
            elif n.endswith(' Clavicle'): ch = n.replace('Clavicle', 'UpperArm')
            elif n in ('Bip01 Pelvis', 'Bip02 Spine', 'Bip01 Spine1', 'Bip02 Spine2', 'Bip02 Spine3', 'Bip02 Neck', 'Box01', 'Box02', 'Box03'):
                ch = {'Bip01 Pelvis': 'Bip02 Spine', 'Bip02 Spine': 'Bip01 Spine1', 'Bip01 Spine1': 'Bip02 Spine2', 'Bip02 Spine2': 'Bip02 Spine3', 'Bip02 Spine3': 'Bip02 Neck', 'Bip02 Neck': 'Bip01 Head', 'Box01': 'Box02', 'Box02': 'Box03', 'Box03': 'Box04'}[n]
            elif n.endswith('UpperArm'): ch = n.replace('UpperArm', 'Forearm')
            elif n.endswith('Forearm'): ch = n.replace('Forearm', 'Hand')
            elif n.endswith('Thigh'): ch = n.replace('Thigh', 'Calf')
            elif n.endswith('Calf'): ch = n.replace('Calf', 'Foot')
            else:
                # fingers
                base = n.split(' ')[-1]
                if base in ('Finger1', 'Finger2', 'Finger3'): ch = n.replace(base, base + '1')
                elif base in ('Finger11', 'Finger21', 'Finger31'): ch = n[:-1] + '2'
                else: ch = None
            if ch:
                D = least(Wm[ch][:3, 3] - Wm[n][:3, 3], P[ch] - P[n])
            else:   # last finger bone: MM9's own continuation
                pr = par[n]; a_ = Wm[n][:3, 3] - Wm[pr][:3, 3]; b_ = TIP[n] - P[n]; D = least(a_, b_)
        if D is not None:
            M[:3, :3] = D @ Rm; M[:3, 3] = P[n]; BIND[n] = M; continue
    pn = par.get(n)
    if pn is None or pn not in BIND: BIND[n] = Wm[n].copy()
    else:
        L = np.linalg.inv(Wm[pn]) @ Wm[n]; BIND[n] = BIND[pn] @ L; 
        if n in P: BIND[n][:3, 3] = P[n]
# pivot offsets go on the bind frames' positions only
for n in order:
    k = n.replace('Bip02 ', '').replace('Bip01 ', '')
    for side in ('L ', 'R '):
        if k.startswith(side) and k[2:] in PIV:
            d = np.array(PIV[k[2:]], float); d[0] *= 1 if side == 'L ' else -1; BIND[n] = BIND[n].copy(); BIND[n][:3, 3] += d
def mat2q(m):
    t = np.trace(m)
    if t > 0:
        s = np.sqrt(t + 1) * 2; q = [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, s / 4]
    else:
        i = int(np.argmax(np.diag(m))); j, k = (i + 1) % 3, (i + 2) % 3
        s = np.sqrt(1 + m[i, i] - m[j, j] - m[k, k]) * 2
        q = [0, 0, 0, 0]; q[i] = s / 4; q[j] = (m[j, i] + m[i, j]) / s; q[k] = (m[k, i] + m[i, k]) / s; q[3] = (m[k, j] - m[j, k]) / s
    q = np.array(q); return q / np.linalg.norm(q)
names = list(order)
parent = dict(par)
nodes = []
idx = {n: i for i, n in enumerate(names)}
TRS = {}
for n in names:
    if n == 'Scene Root' or parent.get(n) is None:
        TRS[n] = (Wm[n][:3, 3].tolist(), mat2q(Wm[n][:3, :3]).tolist()); continue
    pn = parent[n]
    Lm = np.linalg.inv(Wm[pn]) @ Wm[n]           # MM9's local rotation
    t = (np.linalg.inv(BIND[pn]) @ BIND[n])[:3, 3]
    TRS[n] = (t.tolist(), mat2q(Lm[:3, :3]).tolist())
# helpers: half joints (frame of the child, node under the parent)
pairs = RB.half_pairs()
IBM_SPACE = dict(BIND)
for h, c, pn, _ in pairs:
    names.append(h); idx[h] = len(names) - 1; parent[h] = pn; IBM_SPACE[h] = BIND[c]; TRS[h] = (TRS[c][0], TRS[c][1])
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
matnames = [str(x) for x in D['matnames']] if 'matnames' in D else ['Trog']
fn = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]])
key = np.round(co, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
Ns = np.zeros((inv.max() + 1, 3))
for c in range(3): np.add.at(Ns, inv[tri[:, c]], fn)
N = Ns[inv]; N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
if 'ringv' in D:
    # the head and body rings are two chains on one curve: shared normals over the join
    from scipy.spatial import cKDTree
    ids = np.where(D['ringv'])[0]; tr = cKDTree(co[ids]); nn = tr.query_ball_point(co[ids], .02)
    Nr = np.array([N[ids[q]].mean(0) for q in nn]); N[ids] = Nr / np.maximum(np.linalg.norm(Nr, axis=1, keepdims=True), 1e-12)
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
nodes.append({'name': 'Troglodyte', 'mesh': 0, 'skin': 0})
docj = {'asset': {'version': '2.0', 'generator': 'mm9_troglodyte build_glb'}, 'scene': 0, 'scenes': [{'nodes': [0, mesh_node]}], 'nodes': nodes,
        'meshes': [{'name': 'Troglodyte', 'primitives': prims}], 'skins': [{'joints': list(range(len(names))), 'inverseBindMatrices': ib, 'skeleton': 0}],
        'accessors': accs, 'bufferViews': views, 'buffers': [{'byteLength': 0}], 'materials': [{'name': m, 'pbrMetallicRoughness': {'baseColorFactor': [.45, .5, .32, 1], 'metallicFactor': 0, 'roughnessFactor': .7}} for m in matnames]}
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
