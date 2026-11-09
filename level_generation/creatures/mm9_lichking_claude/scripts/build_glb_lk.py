"""Lich King body GLB (from the Evil Sorcerer's build_glb.py; no left Hand bone in MM9: L Finger0 is the left wrist) (from mm9_mummy_claude): mesh npz + weights npz + MM9 hierarchy. Bind = the A pose of the mesh: each bone's bind frame is MM9's rest frame turned by the least rotation onto our bone
(so MM9's local rotations give MM9's poses), the hand by two directions (fingers and thumb, so the palm matches MM9), finger chains take MM9's Finger1 / Finger0 frame (so its curl deltas apply). Args: <mesh npz> <weights npz> <out glb>"""
import json, sys, struct
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model
from rig_bones import bone_table, FINGERS, half_pairs, PANELS, panel_bones, COAT, COAT_Z, coat_bones, wrist
mesh_npz, w_npz, out = sys.argv[1:4]
R = json.load(open(HERE / 'work/rig.json')); JB, FB = R['joints'], R['fingers']
def g(p): return np.array([p[0], p[2], -p[1]], float)       # Blender -> glTF
# hinge pivots toward the outside of the bend, so the skin on the inside of a deep bend compresses less (second pass, collapse gate); +y is the back of the figure
for s_ in 'LR':
    JB[f'Bip01 {s_} Calf'][1] += 0.030; JB[f'Bip01 {s_} Forearm'][1] += 0.015; JB[f'Bip01 {s_} Thigh'][1] -= 0.025
src = Model(Glb(HERE / 'source/lk/lichking.glb')); sdoc = src.glb.json; snodes = sdoc['nodes']
sn = [n.get('name') for n in snodes]; six = {n: i for i, n in enumerate(sn)}; W0 = src.world({})
def smat(n): return W0[six[n]].copy()
parent = {c: sn[i] for i, n in enumerate(snodes) for c_i, c in enumerate([sn[k] for k in n.get('children', [])])}
JOINTS = [n for n in sn if n and (n.startswith('Bip01') or n == 'Bone01' or n == 'Scene Root')]
T = bone_table(JB, FB)
# world positions
P = {n: g(JB[n]) for n in JB}
P['Bip01 L Finger0'] = P.pop('Bip01 L Hand')            # MM9's left wrist bone
for s_ in 'LR': P.pop(f'Bip01 {s_} Toe0', None)
TOE = {s_: g(JB[f'Bip01 {s_} Toe0']) for s_ in 'LR'}
def unit(v): return v / np.linalg.norm(v)
def least(a, b):
    a, b = unit(a), unit(b); v = np.cross(a, b); c = a @ b; s = np.linalg.norm(v)
    if s < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s ** 2)
CHILD = {'Bip01 Spine': 'Bip01 Spine1', 'Bip01 Spine1': 'Bip01 Spine2', 'Bip01 Spine2': 'Bip01 Spine3', 'Bip01 Spine3': 'Bip01 Neck', 'Bip01 Neck': 'Bip01 Head'}
for s in 'LR':
    CHILD.update({f'Bip01 {s} Clavicle': f'Bip01 {s} UpperArm', f'Bip01 {s} UpperArm': f'Bip01 {s} Forearm', f'Bip01 {s} Forearm': wrist(s),
                  f'Bip01 {s} Thigh': f'Bip01 {s} Calf', f'Bip01 {s} Calf': f'Bip01 {s} Foot'})
W = {'Scene Root': smat('Scene Root')}
order = []
def visit(n):
    order.append(n)
    for k in snodes[six[n]].get('children', []):
        if sn[k] in JOINTS: visit(sn[k])
visit('Scene Root')
for n in order[1:]:
    Rm = smat(n)[:3, :3]
    if n in P:
        D = np.eye(3)
        if n.endswith(' Foot'):
            # feet are flat in both binds: only yaw (MM9's middle toe joint against our ball of the foot)
            sd = n.split()[1]; a_ = smat(f'Bip01 {sd} Toe22')[:3, 3] - smat(n)[:3, 3]; b_ = TOE[sd] - P[n]; a_[1] = 0; b_[1] = 0; D = least(a_, b_)
        elif n in CHILD:
            c = CHILD[n]; D = least(smat(c)[:3, 3] - smat(n)[:3, 3], P[c] - P[n])
        elif n in ('Bip01 R Hand', 'Bip01 L Finger0'):
            mir = -1 if ' L ' in n else 1
            mc = 'Bip01 R Finger0' if ' R ' in n else 'Bip01 L Finger01'
            m_d = smat(mc)[:3, 3] - smat(n)[:3, 3]
            o_d = g([FB['Middle'][0][0] * mir, FB['Middle'][0][1], FB['Middle'][0][2]]) - P[n]
            D = least(m_d, o_d)
            if ' R ' in n and 'grip' in R:
                # the staff: MM9's staff axis (rigid on Bone01 under R Hand) onto our grip axis, MM9's finger direction near ours
                def frame(x_, b_):
                    x_ = unit(x_); z_ = unit(np.cross(x_, b_)); return np.c_[x_, np.cross(z_, x_), z_]
                GR = R['grip']; D0 = D
                D = frame(g(GR['axis']), g(GR['finger_dir'])) @ frame(g(GR['mm9_axis']), g(GR['mm9_dir'])).T
                tw = np.degrees(np.arccos(np.clip((np.trace(D @ D0.T) - 1) / 2, -1, 1)))
                print('R Hand grip roll against the least rotation', round(float(tw), 1), 'deg')
        M = np.eye(4); M[:3, :3] = D @ Rm; M[:3, 3] = P[n]; W[n] = M
    else:
        # strip bones keep MM9's local transform under our parent
        pn = parent[n]; Lm = np.linalg.inv(smat(pn)) @ smat(n); W[n] = W[pn] @ Lm
BIND = {n: W[n].copy() for n in order}                      # world bind matrix per bone
IBM_SPACE = {n: W[n] for n in order}
# tabard links and coat hinges: chained under the Spine (the thighs' parent), frames of the Spine's bind
SPN = 'Bip01 Spine'
for k in PANELS:
    y = R['panel_y'][k]; prev = SPN
    for bn, z in zip(panel_bones(k), PANELS[k]):
        M = W[SPN].copy(); M[:3, 3] = g([0.0, y, z]); W[bn] = M; IBM_SPACE[bn] = M; order.append(bn); parent[bn] = prev; prev = bn
for k in COAT:
    prev = SPN
    for bn, hp in zip(coat_bones(k), R['coat'][k]):
        M = W[SPN].copy(); M[:3, 3] = g(hp); W[bn] = M; IBM_SPACE[bn] = M; order.append(bn); parent[bn] = prev; prev = bn
# half joints: bind frame of the child, node under the parent (half_keys.py)
for h, c, pn, _ in half_pairs():
    W[h] = W[c].copy(); IBM_SPACE[h] = W[c]; order.append(h); parent[h] = pn
# fingers: MM9's distal mitten joint frame (L Finger01 under L Finger0, R Finger01 via R Finger0 under R Hand) carried to our wrist bone, so its curl deltas turn about the same axes
for s_, mir in (('L', -1), ('R', 1)):
    pre = f'Bip01 {s_} '; wr = wrist(s_); src_f = pre + 'Finger01'
    for f in FINGERS:
        pts = [g([p[0] * mir, p[1], p[2]]) for p in FB[f]]
        Rf = W[wr][:3, :3] @ smat(wr)[:3, :3].T @ smat(src_f)[:3, :3]
        for k in range(3):
            n = f'{pre}{f}{k + 1}'
            M = np.eye(4); M[:3, :3] = Rf; M[:3, 3] = pts[k]; W[n] = M; IBM_SPACE[n] = M
            order.append(n); parent[n] = wr if k == 0 else f'{pre}{f}{k}'
names = order
json.dump({n: W[n].tolist() for n in names}, open(HERE / 'work/bind_world.json', 'w'))        # glTF bind world matrices (make_staff.py, grip_keys.py)
idx = {n: i for i, n in enumerate(names)}
# local rest
TRS = {}
def mat2q(m):
    t = np.trace(m)
    if t > 0:
        s = np.sqrt(t + 1) * 2; q = [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, s / 4]
    else:
        i = int(np.argmax(np.diag(m))); j, k = (i + 1) % 3, (i + 2) % 3
        s = np.sqrt(1 + m[i, i] - m[j, j] - m[k, k]) * 2
        q = [0, 0, 0, 0]; q[i] = s / 4; q[j] = (m[j, i] + m[i, j]) / s; q[k] = (m[k, i] + m[i, k]) / s; q[3] = (m[k, j] - m[j, k]) / s
    q = np.array(q); return q / np.linalg.norm(q)
for n in names:
    L = W[n] if n == 'Scene Root' else np.linalg.inv(W[parent[n]]) @ W[n]
    TRS[n] = (L[:3, 3].tolist(), mat2q(L[:3, :3]).tolist())
# mesh
D = np.load(mesh_npz); WT = np.load(w_npz)
if 'mat' in D.files and (D['mat'] == 9).any():                  # the skull occluder of the Meshy upload
    D = dict(D); keep = D['mat'] != 9; D['tri'] = D['tri'][keep]; D['mat'] = D['mat'][keep]
    if 'lining' in D: D['lining'] = D['lining'][keep]
co = np.c_[D['co'][:, 0], D['co'][:, 2], -D['co'][:, 1]]; tri = D['tri']
WJ_names = [str(x) for x in WT['wnames']]; wj, ww = WT['wj'], WT['ww']
if 'orig' in D: wj, ww = wj[D['orig']], ww[D['orig']]            # vertices split at UV seams
vmap = np.array([idx[WJ_names[i]] for i in range(len(WJ_names))])
J0 = vmap[wj]
uv = D['uv'] if 'uv' in D else np.zeros((len(co), 2))
uv = uv * [1, -1] + [0, 1]            # Blender v up -> glTF v down
mats = D['mat'] if 'mat' in D else np.zeros(len(tri), int)
matnames = [str(x) for x in D['matnames']] if 'matnames' in D else ['LichKing']
# normals: smooth by shared position
fn = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]])
N = np.zeros_like(co)
key = np.round(co, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
Ns = np.zeros((inv.max() + 1, 3))
for c in range(3): np.add.at(Ns, inv[tri[:, c]], fn)
N = Ns[inv]; N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
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
for n in names:
    t, q = TRS[n]
    nodes.append({'name': n, 'translation': t, 'rotation': q, 'children': []})
for n in names[1:]: nodes[idx[parent[n]]]['children'].append(idx[n])
for x in nodes:
    if not x['children']: del x['children']
prims = []
for m in range(len(matnames)):
    t_ = tri[mats == m]
    used, inv_ = np.unique(t_.ravel(), return_inverse=True)
    pa = add(co[used].astype('f4'), 5126, 'VEC3', 34962, True); na = add(N[used].astype('f4'), 5126, 'VEC3', 34962); ua = add(uv[used].astype('f4'), 5126, 'VEC2', 34962)
    ja = add(J0[used].astype('u2'), 5123, 'VEC4', 34962); wa = add(ww[used].astype('f4'), 5126, 'VEC4', 34962)
    ind = add(inv_.astype('u4'), 5125, 'SCALAR', 34963)
    prims.append({'attributes': {'POSITION': pa, 'NORMAL': na, 'TEXCOORD_0': ua, 'JOINTS_0': ja, 'WEIGHTS_0': wa}, 'indices': ind, 'material': m, 'mode': 4})
ibm = np.array([np.linalg.inv(IBM_SPACE[n]).T.ravel() for n in names], 'f4')
ib = add(ibm, 5126, 'MAT4')
mesh_node = len(nodes)
nodes.append({'name': 'LichKing', 'mesh': 0, 'skin': 0})
doc = {'asset': {'version': '2.0', 'generator': 'mm9_lichking build_glb'}, 'scene': 0, 'scenes': [{'nodes': [0, mesh_node]}], 'nodes': nodes,
       'meshes': [{'name': 'LichKing', 'primitives': prims}], 'skins': [{'joints': list(range(len(names))), 'inverseBindMatrices': ib, 'skeleton': 0}],
       'accessors': accs, 'bufferViews': views, 'buffers': [{'byteLength': 0}], 'materials': [{'name': m, 'pbrMetallicRoughness': {'baseColorFactor': [.7, .65, .55, 1], 'metallicFactor': 0, 'roughnessFactor': .8}} for m in matnames]}
if 'textures' in D:
    tex = json.loads(str(D['textures']))     # material -> {base, normal, orm}
    images = []; textures = []
    _cache = {}
    def addimg(path):
        if str(path) in _cache: return _cache[str(path)]          # r9: shared images (head set on two materials) stored once
        data = Path(path).read_bytes()
        while len(blob) % 4: blob.append(0)
        o = len(blob); blob.extend(data); views.append({'buffer': 0, 'byteOffset': o, 'byteLength': len(data)})
        images.append({'bufferView': len(views) - 1, 'mimeType': 'image/png', 'name': Path(path).stem})
        textures.append({'source': len(images) - 1, 'sampler': 0}); _cache[str(path)] = len(textures) - 1; return len(textures) - 1
    for m, nm in enumerate(matnames):
        t = tex.get(nm)
        if not t: continue
        pb = doc['materials'][m]['pbrMetallicRoughness']; pb.pop('baseColorFactor', None)
        pb['baseColorTexture'] = {'index': addimg(HERE / t['base'])}
        pb.pop('roughnessFactor', None); pb.pop('metallicFactor', None)
        if t.get('orm'): pb['metallicRoughnessTexture'] = {'index': addimg(HERE / t['orm'])}
        if t.get('normal'): doc['materials'][m]['normalTexture'] = {'index': addimg(HERE / t['normal'])}
    doc['images'] = images; doc['textures'] = textures; doc['samplers'] = [{'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497, 'wrapT': 10497}]
while len(blob) % 4: blob.append(0)
doc['buffers'][0]['byteLength'] = len(blob)
j = json.dumps(doc, separators=(',', ':')).encode(); j += b' ' * (-len(j) % 4)
with open(out, 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(j) + 8 + len(blob)))
    f.write(struct.pack('<II', len(j), 0x4E4F534A)); f.write(j)
    f.write(struct.pack('<II', len(blob), 0x004E4942)); f.write(blob)
print('GLB', out, len(co), len(tri), len(names), 'joints')
