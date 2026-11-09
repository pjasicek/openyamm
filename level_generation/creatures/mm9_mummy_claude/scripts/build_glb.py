"""Mummy body GLB: mesh (joined.npz or final dump) + weights + MM9 hierarchy + strips. Bind = the mesh's master pose: each bone's bind frame is MM9's rest frame
turned by the least rotation onto our bone (so MM9's local rotations give MM9's poses), inverse bind matrices from that; strips bind in MM9's own space.
Args: <mesh npz> <out glb> [--no-tex]"""
import json, sys, struct
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model
from rig_bones import bone_table, FINGERS, half_pairs
import strips
mesh_npz, out = sys.argv[1:3]
R = json.load(open(HERE / 'work/rig.json')); JB, FB = R['joints'], R['fingers']
def g(p): return np.array([p[0], p[2], -p[1]], float)       # Blender -> glTF
# hinge pivots toward the outside of the bend, so the skin on the inside of a deep bend compresses less (second pass, collapse gate); +y is the back of the figure
for s_ in 'LR':
    JB[f'Bip01 {s_} Calf'][1] += 0.030; JB[f'Bip01 {s_} Forearm'][1] += 0.015; JB[f'Bip01 {s_} Thigh'][1] -= 0.025
src = Model(Glb(HERE / 'source/mummy1/mummy1.glb')); sdoc = src.glb.json; snodes = sdoc['nodes']
sn = [n.get('name') for n in snodes]; six = {n: i for i, n in enumerate(sn)}; W0 = src.world({})
def smat(n): return W0[six[n]].copy()
parent = {c: sn[i] for i, n in enumerate(snodes) for c_i, c in enumerate([sn[k] for k in n.get('children', [])])}
JOINTS = [n for n in sn if n and (n.startswith('Bip01') or n.startswith('Bone') or n == 'Scene Root')]
T = bone_table(JB, FB)
# world positions
P = {n: g(JB[n]) for n in JB}
def unit(v): return v / np.linalg.norm(v)
def least(a, b):
    a, b = unit(a), unit(b); v = np.cross(a, b); c = a @ b; s = np.linalg.norm(v)
    if s < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s ** 2)
CHILD = {'Bip01 Spine': 'Bip01 Spine1', 'Bip01 Spine1': 'Bip01 Spine2', 'Bip01 Spine2': 'Bip01 Spine3', 'Bip01 Spine3': 'Bip01 Neck', 'Bip01 Neck': 'Bip01 Head'}
for s in 'LR':
    CHILD.update({f'Bip01 {s} Clavicle': f'Bip01 {s} UpperArm', f'Bip01 {s} UpperArm': f'Bip01 {s} Forearm', f'Bip01 {s} Forearm': f'Bip01 {s} Hand',
                  f'Bip01 {s} Thigh': f'Bip01 {s} Calf', f'Bip01 {s} Calf': f'Bip01 {s} Foot', f'Bip01 {s} Foot': f'Bip01 {s} Toe0'})
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
            # feet are flat in both binds: only yaw, or the sole would carry a pitch offset through every clip (orientation gate: 10 deg before)
            c = CHILD[n]; a_ = smat(c)[:3, 3] - smat(n)[:3, 3]; b_ = P[c] - P[n]; a_[1] = 0; b_[1] = 0; D = least(a_, b_)
        elif n in CHILD:
            c = CHILD[n]; D = least(smat(c)[:3, 3] - smat(n)[:3, 3], P[c] - P[n])
        elif n.endswith('Hand'):
            mir = 1 if ' L ' in n else -1; m = FB['Middle'][0]; D = least(Rm[:, 0], g([m[0] * mir, m[1], m[2]]) - P[n])
        elif n.endswith('Toe0'):
            mir = 1 if ' L ' in n else -1; D = least(Rm[:, 0], np.array([-0.08 * mir, 0, 1.0]))
        M = np.eye(4); M[:3, :3] = D @ Rm; M[:3, 3] = P[n]; W[n] = M
    else:
        # strip bones keep MM9's local transform under our parent
        pn = parent[n]; Lm = np.linalg.inv(smat(pn)) @ smat(n); W[n] = W[pn] @ Lm
BIND = {n: W[n].copy() for n in order}                      # world bind matrix per bone
IBM_SPACE = {n: W[n] for n in order}
for n in ('Bone01', 'Bone02', 'Bone04', 'Bone05', 'Bone06', 'Bone07', 'Bone08', 'Bone24'):
    IBM_SPACE[n] = smat(n)                                  # strips are authored in MM9's bind space
# helper bones: rigid on a body bone, strips in MM9 space
HELP = {'XstripRoot': 'Bip01 Spine1', 'XstripTip': 'Bip01 R Forearm', 'XarmStrip': 'Bip01 R UpperArm', 'XthighStrip': 'Bip01 R Thigh'}
for h, b in HELP.items():
    W[h] = W[b].copy(); IBM_SPACE[h] = smat(b); order.append(h); parent[h] = b
# band bones, one per knot, children of Spine1, all motion in their keys (band_sim.py)
strips.refine_band()
for k_, b in zip(strips.STRIPS['band']['k'], strips.STRIPS['band']['b']):
    if b.startswith('Xband'):
        W[b] = W['Bip01 Spine1'].copy(); M = np.eye(4); M[:3, 3] = k_; IBM_SPACE[b] = M; order.append(b); parent[b] = 'Bip01 Spine1'
# half joints: bind frame of the child, node under the parent (half_keys.py)
for h, c, pn, _ in half_pairs():
    W[h] = W[c].copy(); IBM_SPACE[h] = W[c]; order.append(h); parent[h] = pn
# fingers: X along the finger, Z the curl axis (palm side, about the across-hand axis)
curl = {}
for s, mir in (('L', 1), ('R', -1)):
    pre = f'Bip01 {s} '
    for f in FINGERS:
        pts = [g([p[0] * mir, p[1], p[2]]) for p in FB[f]]
        for k in range(3):
            n = f'{pre}{f}{k + 1}'; x = unit(pts[k + 1] - pts[k])
            hand_x = W[pre + 'Hand'][:3, 0]
            # the curl axis: across the hand. Palm normal from the hand bone frame, fixed per side below
            ax = unit(g(R['across']) * np.array([mir, 1, 1]))
            if f == 'Thumb': ax = unit(np.cross(x, unit(g(np.array(FB['Middle'][0]) * [mir, 1, 1]) - W[pre + 'Hand'][:3, 3])))
            z = unit(ax - x * (ax @ x)); y = np.cross(z, x)
            M = np.eye(4); M[:3, 0] = x; M[:3, 1] = y; M[:3, 2] = z; M[:3, 3] = pts[k]; W[n] = M; IBM_SPACE[n] = M
            p_ = pre + 'Hand' if k == 0 else f'{pre}{f}{k}'
            order.append(n); parent[n] = p_
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
# finger relaxed curl: rest local rotation of the node (clips hold it), the inverse bind stays open
CURL = {'Thumb': (8, 12, 10), 'Index': (22, 28, 18), 'Middle': (26, 32, 20), 'Ring': (30, 34, 22), 'Pinky': (32, 36, 22)}
def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return [w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2]
SIGN = json.load(open(HERE / 'scripts/curl_sign.json')) if (HERE / 'scripts/curl_sign.json').exists() else {'L': 1, 'R': 1}
for s in 'LR':
    for f in FINGERS:
        for k in range(3):
            n = f'Bip01 {s} {f}{k + 1}'; a = np.radians(CURL[f][k]) * SIGN[s]
            TRS[n] = (TRS[n][0], qmul(TRS[n][1], [0, 0, np.sin(a / 2), np.cos(a / 2)]))
# mesh
D = np.load(mesh_npz)
co = np.c_[D['co'][:, 0], D['co'][:, 2], -D['co'][:, 1]]; tri = D['tri']
if 'wj' in D:
    WJ_names = [str(x) for x in D['wnames']]; wj, ww = D['wj'], D['ww']
else:
    raise SystemExit('run weights.py first')
vmap = np.array([idx[WJ_names[i]] for i in range(len(WJ_names))])
J0 = vmap[wj]
uv = D['uv'] if 'uv' in D else np.zeros((len(co), 2))
uv = uv * [1, -1] + [0, 1]            # Blender v up -> glTF v down
mats = D['mat'] if 'mat' in D else np.zeros(len(tri), int)
matnames = [str(x) for x in D['matnames']] if 'matnames' in D else ['Mummy']
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
nodes.append({'name': 'Mummy', 'mesh': 0, 'skin': 0})
doc = {'asset': {'version': '2.0', 'generator': 'mm9_mummy build_glb'}, 'scene': 0, 'scenes': [{'nodes': [0, mesh_node]}], 'nodes': nodes,
       'meshes': [{'name': 'Mummy', 'primitives': prims}], 'skins': [{'joints': list(range(len(names))), 'inverseBindMatrices': ib, 'skeleton': 0}],
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
