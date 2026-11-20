"""MM6 PeasantF1 rebuild copy of mm9_peasantf1_claude/scripts/build_glb_pf.py: every joint is placed by fit_rig.py (translated, MM9 world rotations kept; arms turned by the least rotation, hand by two directions); the MM9-PF1-only ear/lid normal relaxation removed.
PeasantF1 body GLB (from the Monk's build_glb): mesh npz + weights npz + MM9 hierarchy. Bind = the A pose of the mesh. MM9's joints stay at MM9's bind (skirt chains, spine, legs), arms sit on the sleeve axis (each bone's frame is MM9's turned by the least rotation onto
our bone, the hand by two directions), Ponytail and Y chains move onto the mesh with MM9's frames, finger chains take MM9's Finger1 / Finger0 frame. Args: <mesh npz> <weights npz> <out glb>"""
import json, sys, struct
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model
from rig_bones import FINGERS, half_pairs
mesh_npz, w_npz, out = sys.argv[1:4]
R = json.load(open(__import__('os').environ.get('RIG', str(HERE / 'work/rig.json')))); JB, FB = R['joints'], R['fingers']
def g(p): return np.array([p[0], p[2], -p[1]], float)       # Blender -> glTF
src = Model(Glb(HERE / 'source/mm9/pf1b.glb')); sdoc = src.glb.json; snodes = sdoc['nodes']
sn = [n.get('name') for n in snodes]; six = {n: i for i, n in enumerate(sn)}; W0 = src.world({})
def smat(n): return W0[six[n]].copy()
parent = {sn[c]: sn[i] for i, n in enumerate(snodes) for c in n.get('children', [])}
sk = [sn[i] for i in sdoc['skins'][0]['joints']]
P = {n: g(JB[n]) for n in JB if n != 'Scene Root'}
def unit(v): return v / np.linalg.norm(v)
def least(a, b):
    a, b = unit(a), unit(b); v = np.cross(a, b); c = a @ b; s = np.linalg.norm(v)
    if s < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s ** 2)
CHILD = {}
for s in 'LR':
    CHILD.update({f'FHP {s} UpperArm': f'FHP {s} Forearm', f'FHP {s} Forearm': f'FHP {s} Hand'})
W = {'Scene Root': smat('Scene Root')}
order = []
def visit(n):
    order.append(n)
    for k in snodes[six[n]].get('children', []):
        if sn[k] in sk: visit(sn[k])
visit('Scene Root')
for n in order[1:]:
    Rm = smat(n)[:3, :3]
    if n in P:
        D = np.eye(3)
        if n in CHILD:
            c = CHILD[n]; D = least(smat(c)[:3, 3] - smat(n)[:3, 3], P[c] - P[n])
        elif n.endswith('Hand'):
            mir = -1 if ' L ' in n else 1; pre = n[:-4]
            m_d = smat(pre + 'Finger1')[:3, 3] - smat(n)[:3, 3]; m_t = smat(pre + 'Finger0')[:3, 3] - smat(n)[:3, 3]
            o_d = g([FB['Middle'][0][0] * mir, FB['Middle'][0][1], FB['Middle'][0][2]]) - P[n]; o_t = g([FB['Thumb'][0][0] * mir, FB['Thumb'][0][1], FB['Thumb'][0][2]]) - P[n]
            def frame(a, b):
                x = unit(a); z = unit(np.cross(x, b)); return np.c_[x, np.cross(z, x), z]
            D = frame(o_d, o_t) @ frame(m_d, m_t).T
        M = np.eye(4); M[:3, :3] = D @ Rm; M[:3, 3] = P[n]; W[n] = M
    else:
        pn = parent[n]
        if pn in W and pn in P:  # MM9's finger stubs under a moved hand, Ponytail12 under 11: local kept
            W[n] = W[pn] @ (np.linalg.inv(smat(pn)) @ smat(n))
        elif n.startswith('FHP') and pn.startswith('FHP') and any(k in n for k in ('Finger',)):
            W[n] = W[pn] @ (np.linalg.inv(smat(pn)) @ smat(n))
        else:
            W[n] = smat(n)
IBM_SPACE = {n: W[n] for n in order}
for h, c, pn, _ in half_pairs():
    W[h] = W[c].copy(); IBM_SPACE[h] = W[c]; order.append(h); parent[h] = pn
for s_, mir in (('L', -1), ('R', 1)):
    pre = f'FHP {s_} '
    for f in FINGERS:
        pts = [g([p[0] * mir, p[1], p[2]]) for p in FB[f]]
        src_f = pre + ('Finger0' if f == 'Thumb' else 'Finger1')
        Rf = W[pre + 'Hand'][:3, :3] @ smat(pre + 'Hand')[:3, :3].T @ smat(src_f)[:3, :3]
        for k in range(3):
            n = f'{pre}{f}{k + 1}'
            M = np.eye(4); M[:3, :3] = Rf; M[:3, 3] = pts[k]; W[n] = M; IBM_SPACE[n] = M
            order.append(n); parent[n] = pre + 'Hand' if k == 0 else f'{pre}{f}{k}'
names = order; idx = {n: i for i, n in enumerate(names)}
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
for n in names:
    L = W[n] if n == 'Scene Root' else np.linalg.inv(W[parent[n]]) @ W[n]
    TRS[n] = (L[:3, 3].tolist(), mat2q(L[:3, :3]).tolist())
D = np.load(mesh_npz); WT = np.load(w_npz)
co = np.c_[D['co'][:, 0], D['co'][:, 2], -D['co'][:, 1]]; tri = D['tri']
WJ_names = [str(x) for x in WT['wnames']]; wj, ww = WT['wj'], WT['ww']
if 'orig' in D.files: wj, ww = wj[D['orig']], ww[D['orig']]
vmap = np.array([idx[WJ_names[i]] for i in range(len(WJ_names))]); J0 = vmap[wj]
uv = D['uv'] if 'uv' in D else np.zeros((len(co), 2)); uv = uv * [1, -1] + [0, 1]
mats = D['mat'] if 'mat' in D else np.zeros(len(tri), int)
matnames = [str(x) for x in D['matnames']] if 'matnames' in D else ['PeasantF1']
# Blender faces -> glTF: the frame change is a proper rotation, windings carry over
fn = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]])
key = np.round(co, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel(); Ns = np.zeros((inv.max() + 1, 3))
for c in range(3): np.add.at(Ns, inv[tri[:, c]], fn)
N = Ns[inv]; N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
# skirt normals smoothed along the surface: the cut rows leave a patchwork of face sizes
comp_v = D['comp']; rid = [str(x) for x in D['names']].index('skirt')
ed = np.vstack([inv[tri[:, [0, 1]]], inv[tri[:, [1, 2]]], inv[tri[:, [2, 0]]]]); nw = inv.max() + 1
robew = np.zeros(nw, bool); robew[inv[comp_v == rid]] = True
for _ in range(3):
    Ac = np.zeros((nw, 3)); cnt = np.zeros(nw)
    np.add.at(Ac, ed[:, 0], Ns[ed[:, 1]] / np.maximum(np.linalg.norm(Ns[ed[:, 1]], axis=1, keepdims=True), 1e-12)); np.add.at(cnt, ed[:, 0], 1)
    np.add.at(Ac, ed[:, 1], Ns[ed[:, 0]] / np.maximum(np.linalg.norm(Ns[ed[:, 0]], axis=1, keepdims=True), 1e-12)); np.add.at(cnt, ed[:, 1], 1)
    Nw = Ns / np.maximum(np.linalg.norm(Ns, axis=1, keepdims=True), 1e-12)
    Nw[robew] = (Nw + Ac / np.maximum(cnt, 1)[:, None])[robew]; Ns = Nw
# PF1 (face fix 2026-11-02): positions where folded faces cancel (the pressed-in ear plates beside the cheeks: summed normal under 35 % of
# the summed face areas) drew a dark speck; they take their neighbours' normals
_sa = np.zeros(nw); [np.add.at(_sa, inv[tri[:, c_]], np.linalg.norm(fn, axis=1)) for c_ in range(3)]
_bad2 = np.linalg.norm(Ns, axis=1) < 0.35 * _sa
if _bad2.any():
    _Nn = Ns / np.maximum(np.linalg.norm(Ns, axis=1, keepdims=True), 1e-12)
    for _ in range(4):
        _A = np.zeros((nw, 3)); np.add.at(_A, ed[:, 0], _Nn[ed[:, 1]] * ~_bad2[ed[:, 1], None]); np.add.at(_A, ed[:, 1], _Nn[ed[:, 0]] * ~_bad2[ed[:, 0], None])
        _ok = np.linalg.norm(_A, axis=1) > 1e-9; _upd = _bad2 & _ok
        _Nn[_upd] = _A[_upd] / np.linalg.norm(_A[_upd], axis=1, keepdims=True)
    Ns = np.where(_bad2[:, None], _Nn * _sa[:, None], Ns); print('CANCELLED normals replaced', int(_bad2.sum()))
# positions whose faces are all zero-area (midline slivers snapped by tweak_pf.py) take the nearest real normal
_ln = np.linalg.norm(Ns, axis=1); _bad = _ln < 1e-10
if _bad.any():
    from scipy.spatial import cKDTree as _K
    _pos = np.zeros((len(Ns), 3)); _pos[inv] = co
    _ok = np.where(~_bad)[0]; _, _nn = _K(_pos[_ok]).query(_pos[_bad]); Ns[_bad] = Ns[_ok[_nn]]
    print('ZERO normals fixed', int(_bad.sum()))
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
    t, q = TRS[n]; nodes.append({'name': n, 'translation': t, 'rotation': q, 'children': []})
for n in names[1:]: nodes[idx[parent[n]]]['children'].append(idx[n])
for x in nodes:
    if not x['children']: del x['children']
prims = []
for m in range(len(matnames)):
    t_ = tri[mats == m]; used, inv_ = np.unique(t_.ravel(), return_inverse=True)
    pa = add(co[used].astype('f4'), 5126, 'VEC3', 34962, True); na = add(N[used].astype('f4'), 5126, 'VEC3', 34962); ua = add(uv[used].astype('f4'), 5126, 'VEC2', 34962)
    ja = add(J0[used].astype('u2'), 5123, 'VEC4', 34962); wa = add(ww[used].astype('f4'), 5126, 'VEC4', 34962); ind = add(inv_.astype('u4'), 5125, 'SCALAR', 34963)
    prims.append({'attributes': {'POSITION': pa, 'NORMAL': na, 'TEXCOORD_0': ua, 'JOINTS_0': ja, 'WEIGHTS_0': wa}, 'indices': ind, 'material': m, 'mode': 4})
ibm = np.array([np.linalg.inv(IBM_SPACE[n]).T.ravel() for n in names], 'f4'); ib = add(ibm, 5126, 'MAT4')
mesh_node = len(nodes); nodes.append({'name': 'PeasantF1', 'mesh': 0, 'skin': 0})
doc = {'asset': {'version': '2.0', 'generator': 'mm9_peasantf1 build_glb_pf'}, 'scene': 0, 'scenes': [{'nodes': [0, mesh_node]}], 'nodes': nodes, 'meshes': [{'name': 'PeasantF1', 'primitives': prims}], 'skins': [{'joints': list(range(len(names))), 'inverseBindMatrices': ib, 'skeleton': 0}],
       'accessors': accs, 'bufferViews': views, 'buffers': [{'byteLength': 0}], 'materials': [dict({'name': m, 'pbrMetallicRoughness': {'baseColorFactor': [.6, .5, .4, 1], 'metallicFactor': 0, 'roughnessFactor': .9}}) for m in matnames]}
if 'textures' in D.files:
    tex = json.loads(str(D['textures'])); images = []; textures = []
    def addimg(path):
        data = Path(path).read_bytes()
        while len(blob) % 4: blob.append(0)
        o = len(blob); blob.extend(data); views.append({'buffer': 0, 'byteOffset': o, 'byteLength': len(data)})
        images.append({'bufferView': len(views) - 1, 'mimeType': 'image/png', 'name': Path(path).stem}); textures.append({'source': len(images) - 1, 'sampler': 0}); return len(textures) - 1
    for m, nm in enumerate(matnames):
        t = tex.get(nm)
        if not t: continue
        pb = doc['materials'][m]['pbrMetallicRoughness']; pb.pop('baseColorFactor', None)
        pb['baseColorTexture'] = {'index': addimg(HERE / t['base'])}; pb.pop('roughnessFactor', None); pb.pop('metallicFactor', None)
        if t.get('orm'): pb['metallicRoughnessTexture'] = {'index': addimg(HERE / t['orm'])}
        if t.get('normal'): doc['materials'][m]['normalTexture'] = {'index': addimg(HERE / t['normal'])}
    doc['images'] = images; doc['textures'] = textures; doc['samplers'] = [{'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497, 'wrapT': 10497}]
while len(blob) % 4: blob.append(0)
doc['buffers'][0]['byteLength'] = len(blob)
j = json.dumps(doc, separators=(',', ':')).encode(); j += b' ' * (-len(j) % 4)
with open(out, 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(j) + 8 + len(blob))); f.write(struct.pack('<II', len(j), 0x4E4F534A)); f.write(j); f.write(struct.pack('<II', len(blob), 0x004E4942)); f.write(blob)
print('GLB', out, len(co), len(tri), len(names), 'joints')
