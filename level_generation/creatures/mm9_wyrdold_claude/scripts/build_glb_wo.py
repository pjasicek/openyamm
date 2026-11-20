"""Wyrde body GLB (from PF1's build_glb_pf.py; PF1's eye-ledge/ear normal relax off by default, NRELAX) (from the Monk's build_glb): mesh npz + weights npz + MM9 hierarchy. Bind = the A pose of the mesh. MM9's joints stay at MM9's bind (skirt chains, spine, legs), arms sit on the sleeve axis (each bone's frame is MM9's turned by the least rotation onto
our bone, the hand by two directions), Ponytail and Y chains move onto the mesh with MM9's frames, finger chains take MM9's Finger1 / Finger0 frame. Args: <mesh npz> <weights npz> <out glb>"""
import json, sys, struct
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model
from rig_bones import FINGERS, half_pairs
mesh_npz, w_npz, out = sys.argv[1:4]
R = json.load(open(HERE / 'work/rig.json')); JB, FB = R['joints'], R['fingers']
def g(p): return np.array([p[0], p[2], -p[1]], float)       # Blender -> glTF
src = Model(Glb(HERE / 'source/mm9/wyrd_old/wyrd_old.glb')); sdoc = src.glb.json; snodes = sdoc['nodes']
sn = [n.get('name') for n in snodes]; six = {n: i for i, n in enumerate(sn)}; W0 = src.world({})
def smat(n): return W0[six[n]].copy()
parent = {sn[c]: sn[i] for i, n in enumerate(snodes) for c in n.get('children', [])}
sk = [sn[i] for i in sdoc['skins'][0]['joints']]
P = {n: g(JB[n]) for n in JB}
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
matnames = [str(x) for x in D['matnames']] if 'matnames' in D else ['Igrid']
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
# PF1 r23 (coordinator review: "pale jagged crescent under each lower lid", "the hood-edge patch in 3/4 and side"): two places where
# Meshy's surface turns at a hard step, so a light from above draws an outline whatever the paint: the lower lid's ledge in front of
# each eyeball (faces up: a pale crescent) and the clamped ear plate beside each cheek (a flat facet at an angle to the cheek). Their
# normals are relaxed toward the surrounding surface's (neighbour averaging over the head, NRELAX passes, only the zone updated, eased in
# at its edge); positions, UVs and the eyeballs (separate small pieces) are unchanged.
_hk = [str(x) for x in D['names']].index('head'); _bz = np.c_[co[:, 0], -co[:, 2], co[:, 1]]; _Z0 = -0.9297
_hp = np.zeros(nw, bool); _hp[inv[comp_v == _hk]] = True
_par = np.arange(nw)
def _fp(a):
    while _par[a] != a: _par[a] = _par[_par[a]]; a = _par[a]
    return a
for _t in inv[tri[comp_v[tri[:, 0]] == _hk]]:
    _r = _fp(_t[0]); _par[_fp(_t[1])] = _r; _par[_fp(_t[2])] = _r
_rt = np.array([_fp(i) for i in range(nw)]); _cnt = np.bincount(_rt[_hp], minlength=nw); _small = _cnt[_rt] < 400
_P = np.zeros((nw, 3)); _P[inv] = _bz
_dx = np.abs(_P[:, 0]) - 0.0287; _dz = _P[:, 2] - _Z0 - 1.6136
# (r15: NRELAX default 0 again: relaxing the mouth and nose normals in r13-r14 flattened them.) Wyrde r12 (review: a pale zig-zag fold under the painted mouth slit, a dark V under the nose from below; both shading of Meshy's folds):
# the normals of the mouth area and the nose underside are relaxed toward the surrounding surface's (positions unchanged)
_ax = np.abs(_P[:, 0])
_mouth = np.clip((0.030 - _ax) / 0.004, 0, 1) * np.clip((_P[:, 2] - 0.604) / 0.003, 0, 1) * np.clip((0.634 - _P[:, 2]) / 0.003, 0, 1) * (_P[:, 1] < -0.075)
_nose = np.clip((0.022 - _ax) / 0.004, 0, 1) * np.clip((_P[:, 2] - 0.626) / 0.003, 0, 1) * np.clip((0.650 - _P[:, 2]) / 0.003, 0, 1) * (_P[:, 1] < -0.100)
_ledge = _mouth; _ear = _nose
_wz = np.maximum(_ledge, _ear) * _hp * ~_small
if _wz.any():
    _Nn = Ns / np.maximum(np.linalg.norm(Ns, axis=1, keepdims=True), 1e-12); _N0 = _Nn.copy(); _okn = _hp & ~_small
    for _ in range(int(__import__('os').environ.get('NRELAX', '0'))):
        _A = np.zeros((nw, 3)); np.add.at(_A, ed[:, 0], _Nn[ed[:, 1]] * _okn[ed[:, 1], None]); np.add.at(_A, ed[:, 1], _Nn[ed[:, 0]] * _okn[ed[:, 0], None])
        _A /= np.maximum(np.linalg.norm(_A, axis=1, keepdims=True), 1e-12)
        _Nn = np.where((_wz > 0)[:, None], _A, _N0)
    _Nf = _N0 * (1 - _wz[:, None]) + _Nn * _wz[:, None]
    Ns = np.where((_wz > 0)[:, None], _Nf * np.maximum(np.linalg.norm(Ns, axis=1, keepdims=True), 1e-9), Ns)
    print('RELAXED normals: lower lids + ear plates', int((_wz > 0).sum()))
# Igrid 2026-11-04 (head paint v2 review): the rebuilt mouth patch (face_geo_wo.py, symmetric lattice) leaves a shallow crease along its
# upper rim, between the nose and the upper lip; in the viewer's top light it draws a dark moustache-like band although the paint is clean
# (work/hv2/raster.png: unlit texture vs Lambert shading). The normals of that band only (|x| < 3 cm, z 0.4885-0.4995, the face front,
# eased in over 2 mm; not the lips, not the nose) are relaxed toward their neighbours' (ULRELAX passes); positions and UVs unchanged.
_ulp = int(__import__('os').environ.get('ULRELAX', '4'))
if _ulp > 0:
    _Pc = np.zeros((nw, 3)); _Pc[inv] = D['co']      # the mesh npz's own frame (x, y back, z up)
    _ul = np.clip((0.030 - np.abs(_Pc[:, 0])) / 0.004, 0, 1) * np.clip((_Pc[:, 2] - 0.4885) / 0.002, 0, 1) * np.clip((0.4995 - _Pc[:, 2]) / 0.002, 0, 1) * (_Pc[:, 1] < -0.29)
    _ul = _ul * _hp * ~_small
    _Nn = Ns / np.maximum(np.linalg.norm(Ns, axis=1, keepdims=True), 1e-12); _N0 = _Nn.copy(); _okn = _hp & ~_small
    for _ in range(_ulp):
        _A = np.zeros((nw, 3)); np.add.at(_A, ed[:, 0], _Nn[ed[:, 1]] * _okn[ed[:, 1], None]); np.add.at(_A, ed[:, 1], _Nn[ed[:, 0]] * _okn[ed[:, 0], None])
        _A /= np.maximum(np.linalg.norm(_A, axis=1, keepdims=True), 1e-12)
        _Nn = np.where((_ul > 0)[:, None], _A, _N0)
    _Nf = _N0 * (1 - _ul[:, None]) + _Nn * _ul[:, None]
    Ns = np.where((_ul > 0)[:, None], _Nf * np.maximum(np.linalg.norm(Ns, axis=1, keepdims=True), 1e-9), Ns)
    print('RELAXED normals: upper-lip band', int((_ul > 0).sum()))
# Igrid 2026-11-04 (orchestrator pre-screen of r15): from below the nose tip read as a dark brown blot although its paint is skin
# (work/hv2/raster_low.png): her head is tilted forward, so the nose underside is a large downward-facing plane that the viewer's and the
# game's lights (all from above) leave to the dark ground term of the hemisphere. Only the normals of that underside (|x| < 2.2 cm,
# z 0.497-0.52, in front, normal more than ~27 deg below horizontal) are turned toward the front, at most to 20 deg below horizontal
# (NOSETILT, eased by how far down they point); the nostril pits keep 70 % of their own normal; positions, UVs and the rest of the nose
# (bridge, tip front, wings) are unchanged.
if __import__('os').environ.get('NOSETILT', '1') == '1':
    _Pc = np.zeros((nw, 3)); _Pc[inv] = D['co']
    _Nn = Ns / np.maximum(np.linalg.norm(Ns, axis=1, keepdims=True), 1e-12)
    _zone = np.clip((0.022 - np.abs(_Pc[:, 0])) / 0.004, 0, 1) * np.clip((_Pc[:, 2] - 0.497) / 0.003, 0, 1) * np.clip((0.520 - _Pc[:, 2]) / 0.003, 0, 1) * (_Pc[:, 1] < -0.30)
    _down = np.clip((-_Nn[:, 1] - 0.45) / 0.25, 0, 1)
    _pit = np.exp(-(((np.abs(_Pc[:, 0]) - 0.0065) / 0.0028) ** 2 + ((_Pc[:, 2] - 0.5045) / 0.0018) ** 2))
    _w = _zone * _down * (1 - 0.7 * _pit) * _hp * ~_small
    _f = np.c_[_Nn[:, 0], np.full(nw, -0.34), np.sqrt(np.clip(1 - _Nn[:, 0] ** 2 - 0.34 ** 2, 0.05, 1))]
    _f /= np.linalg.norm(_f, axis=1, keepdims=True)
    _Nf = _Nn * (1 - _w[:, None]) + _f * _w[:, None]
    Ns = np.where((_w > 0)[:, None], _Nf * np.maximum(np.linalg.norm(Ns, axis=1, keepdims=True), 1e-9), Ns)
    print('TILTED normals: nose underside', int((_w > 0.05).sum()))
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
mesh_node = len(nodes); nodes.append({'name': 'Igrid', 'mesh': 0, 'skin': 0})
doc = {'asset': {'version': '2.0', 'generator': 'mm9_wyrdold build_glb_wo'}, 'scene': 0, 'scenes': [{'nodes': [0, mesh_node]}], 'nodes': nodes, 'meshes': [{'name': 'Igrid', 'primitives': prims}], 'skins': [{'joints': list(range(len(names))), 'inverseBindMatrices': ib, 'skeleton': 0}],
       'accessors': accs, 'bufferViews': views, 'buffers': [{'byteLength': 0}], 'materials': [{'name': m, 'pbrMetallicRoughness': {'baseColorFactor': [.6, .5, .4, 1], 'metallicFactor': 0, 'roughnessFactor': .9}} for m in matnames]}
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
