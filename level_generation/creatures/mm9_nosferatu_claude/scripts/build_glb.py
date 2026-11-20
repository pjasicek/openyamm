"""Nosferatu body GLB: mesh npz + weights npz + MM9 hierarchy (true handed). Bind = the A pose of the mesh: each bone's bind frame is MM9's rest frame turned onto ours (D), so MM9's local rotations give MM9's poses.
D: spine chain by its axis and the shoulder line (MM9's torso is yawed 30 deg in bind), arms by axis and the sleeve's drop, hands by fingers and thumb, fingers by direction, the rest least rotation. Args: <mesh npz> <weights npz> <out glb>"""
import json, sys, struct
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model
from rig_bones import half_pairs, robe_names, robe_bone, ROBE_ROWS, ROBE_COLS
mesh_npz, w_npz, out = sys.argv[1:4]
R = json.load(open(HERE / 'work/rig.json')); JB, FB = R['joints'], R['fingers']
MAT = 'Nosferatu'
def g(p): return np.array([p[0], p[2], -p[1]], float)       # Blender -> glTF
src = Model(Glb(HERE / 'source/n1/n1.glb')); sdoc = src.glb.json; snodes = sdoc['nodes']
sn = [n.get('name') for n in snodes]; six = {n: i for i, n in enumerate(sn)}; W0 = src.world({}); WS = src.world(src.sample('stand', 0.0))
def smat(n): return W0[six[n]].copy()
parent = {}
for i, n in enumerate(snodes):
    for c in n.get('children', []): parent[sn[c]] = sn[i]
JOINTS = [n for n in sn if n and (n.startswith('Bip01') or n == 'Scene Root') and not n.endswith('.mesh')]
P = {n: g(JB[n]) for n in JB}
for s, mir in (('L', 1), ('R', -1)):
    for f in range(5):
        pts = FB[str(f)]
        for k, sfx in enumerate(('', '1', '2')): P[f'Bip01 {s} Finger{f}{sfx}'] = g([pts[k][0] * mir, pts[k][1], pts[k][2]])
        P[f'Bip01 {s} Finger{f}tip'] = g([pts[3][0] * mir, pts[3][1], pts[3][2]])
def unit(v): return v / np.linalg.norm(v)
def least(a, b):
    a, b = unit(a), unit(b); v = np.cross(a, b); c = a @ b; s = np.linalg.norm(v)
    if s < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s ** 2)
def frame(a, b):
    x = unit(a); z = unit(np.cross(x, b)); return np.c_[x, np.cross(z, x), z]
mp = lambda n: smat(n)[:3, 3]
sh_m = mp('Bip01 L UpperArm') - mp('Bip01 R UpperArm'); sh_o = P['Bip01 L UpperArm'] - P['Bip01 R UpperArm']
SPINE = {'Bip01': 'Bip01 Spine', 'Bip01 Pelvis': 'Bip01 Spine', 'Bip01 Spine': 'Bip01 Spine1', 'Bip01 Spine1': 'Bip01 Spine2', 'Bip01 Spine2': 'Bip01 Neck', 'Bip01 Neck': 'Bip01 Head'}
CHILD = {}
for s in 'LR':
    CHILD.update({f'Bip01 {s} Clavicle': f'Bip01 {s} UpperArm', f'Bip01 {s} Thigh': f'Bip01 {s} Calf', f'Bip01 {s} Calf': f'Bip01 {s} Foot', f'Bip01 {s} Foot': f'Bip01 {s} Toe0'})
UP = np.array([0, 1.0, 0])
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
        if n in SPINE:
            c = SPINE[n]; D = frame(P[c] - P[n], sh_o) @ frame(mp(c) - mp(n), sh_m).T
        elif n.endswith(' UpperArm') or n.endswith(' Forearm'):
            c = n.replace('UpperArm', 'Forearm') if n.endswith('UpperArm') else n.replace('Forearm', 'Hand')
            a_m = mp(c) - mp(n); a_o = P[c] - P[n]
            D = frame(a_o, -UP) @ frame(a_m, -UP).T     # the sleeve's low side stays low in MM9's bind
        elif n.endswith(' Foot'):
            c = CHILD[n]; a_ = mp(c) - mp(n); b_ = P[c] - P[n]; a_[1] = 0; b_[1] = 0; D = least(a_, b_)
        elif n in CHILD:
            c = CHILD[n]; D = least(mp(c) - mp(n), P[c] - P[n])
        elif n.endswith('Hand'):
            pre = n[:-4]
            D = frame(P[pre + 'Finger2'] - P[n], P[pre + 'Finger0'] - P[n]) @ frame(mp(pre + 'Finger2') - mp(n), mp(pre + 'Finger0') - mp(n)).T
        elif 'Finger' in n:
            # from MM9's Standing pose, not its bind: the finger's rest frame is the standing one swung onto ours, so no twist hides in the blend at its root (the thumb's web flipped in every clip)
            pn = parent[n]; Rl = WS[six[pn]][:3, :3].T @ WS[six[n]][:3, :3]; Bp = W[pn][:3, :3]
            Rt = Bp @ Rl; tip = P[n[:-1] + '2'] if n[-2].isdigit() else P[n + '1']
            a_m = unit(-Rt[:, 0]); a_o = unit(tip - P[n])
            if not n[-2].isdigit() and not n.endswith('Finger0'):
                # the first knuckle takes MM9's curl, not its fan: a spread of 30 deg tore the webs of these long fingers (finger stretch 12)
                ac = unit(g(np.array(R['across']) * [1 if ' L ' in n else -1, 1, 1]))
                a_m = unit(a_m - (a_m @ ac) * ac + (a_o @ ac) * ac)
            if n.endswith('Finger01'): a_m = unit(0.55 * a_o + 0.45 * a_m)     # MM9's thumb tip curls 89 deg at Standing: on our long thumb that tears the web
            M = np.eye(4); M[:3, :3] = least(a_m, a_o) @ Rt; M[:3, 3] = P[n]; W[n] = M
            continue
        elif n.endswith('Toe0'):
            D = least(Rm[:, 0], Rm[:, 0])
        M = np.eye(4); M[:3, :3] = D @ Rm; M[:3, 3] = P[n]; W[n] = M
    else:
        pn = parent[n]; Lm = np.linalg.inv(smat(pn)) @ smat(n); W[n] = W[pn] @ Lm
IBM_SPACE = {n: W[n] for n in order}
# third finger joints: the middle joint's frame, keyed by finger_keys.py
for s in 'LR':
    for f in range(5):
        n = f'Bip01 {s} Finger{f}2'; pn = n[:-1] + '1'
        M = W[pn].copy(); M[:3, 3] = P[n]; W[n] = M; IBM_SPACE[n] = M; order.append(n); parent[n] = pn
# half joints: bind frame of the child, node under the parent (half_keys.py)
for h, c, pn, _ in half_pairs():
    W[h] = W[c].copy(); IBM_SPACE[h] = W[c]; order.append(h); parent[h] = pn
# robe lattice: world frames at the lattice points (robe_keys.py)
grid = np.load(HERE / 'work' / 'asm_robegrid.npy')
LAT = {}
GZ = grid[:, 0, 2]; nc = grid.shape[1]
for c in range(ROBE_COLS):
    ci = int(round(c / ROBE_COLS * nc)) % nc
    for r, z in enumerate(ROBE_ROWS):
        j = int(np.argmin(np.abs(GZ - z))); p = grid[j, ci]
        n = robe_bone(c, r); M = np.eye(4); M[:3, 3] = g(p); W[n] = M; IBM_SPACE[n] = M; order.append(n); parent[n] = 'Bip01'
        LAT[n] = p.tolist()
json.dump(LAT, open(HERE / 'work/lattice.json', 'w'))
names = order
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
co = np.c_[D['co'][:, 0], D['co'][:, 2], -D['co'][:, 1]]; tri = D['tri']
pn_ = [str(x) for x in D['names']]; drop_ = D['comp'][tri[:, 0]] == pn_.index('feet')    # MM9's robe hides no feet: Sphere05b has none, and ours cut the cloth
tri = tri[~drop_]
WJ_names = [str(x) for x in WT['wnames']]; wj, ww = WT['wj'], WT['ww']
if 'orig' in D.files: wj, ww = wj[D['orig']], ww[D['orig']]            # vertices split at UV seams
vmap = np.array([idx[WJ_names[i]] for i in range(len(WJ_names))])
J0 = vmap[wj]
uv = D['uv'] if 'uv' in D else np.zeros((len(co), 2))
uv = uv * [1, -1] + [0, 1]            # Blender v up -> glTF v down
mats = (D['mat'][~drop_]) if 'mat' in D else np.zeros(len(tri), int)
matnames = [str(x) for x in D['matnames']] if 'matnames' in D else [MAT]
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
nodes.append({'name': MAT, 'mesh': 0, 'skin': 0})
doc = {'asset': {'version': '2.0', 'generator': 'mm9_nosferatu build_glb'}, 'scene': 0, 'scenes': [{'nodes': [0, mesh_node]}], 'nodes': nodes,
       'meshes': [{'name': MAT, 'primitives': prims}], 'skins': [{'joints': list(range(len(names))), 'inverseBindMatrices': ib, 'skeleton': 0}],
       'accessors': accs, 'bufferViews': views, 'buffers': [{'byteLength': 0}], 'materials': [{'name': m, 'pbrMetallicRoughness': {'baseColorFactor': [.7, .65, .55, 1], 'metallicFactor': 0, 'roughnessFactor': .8}} for m in matnames]}
if 'textures' in D.files:
    tex = json.loads(str(D['textures']))     # material -> {base, normal, orm}
    images = []; textures = []
    def addimg(path):
        data = Path(path).read_bytes()
        while len(blob) % 4: blob.append(0)
        o = len(blob); blob.extend(data); views.append({'buffer': 0, 'byteOffset': o, 'byteLength': len(data)})
        images.append({'bufferView': len(views) - 1, 'mimeType': 'image/png', 'name': Path(path).stem})
        textures.append({'source': len(images) - 1, 'sampler': 0}); return len(textures) - 1
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
