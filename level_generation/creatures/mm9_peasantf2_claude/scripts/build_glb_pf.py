"""PeasantF2 body GLB (from the Monk's build_glb): mesh npz + weights npz + MM9 hierarchy. Bind = the A pose of the mesh. MM9's joints stay at MM9's bind (skirt chains, spine, legs), arms sit on the sleeve axis (each bone's frame is MM9's turned by the least rotation onto
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
src = Model(Glb(HERE / 'source/mm9/pf2a.glb')); sdoc = src.glb.json; snodes = sdoc['nodes']
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
_cob = D['co'].copy()
# NECK (user review 2026-11-04, "soldered on"): the dress's neck loop and the head's outer neck ring disagree at the front midline (the
# dress has 4 extra mirror-seam vertices up to 1.1 mm off and its own midline vertex 0.2 mm from the head's), so a sub-mm crack showed the
# head's neck cap there. Dress neck-loop vertices that no head ring vertex shares are projected onto the head's outer ring (the head's
# boundary without its `inner` cap faces), moves <= NECK_SNAP; the head does not move.
if 'comp' in D.files and 'names' in D.files and 'inner' in D.files:
    _nm = [str(x) for x in D['names']]
    if 'head' in _nm and 'dress' in _nm:
        from collections import Counter as _Cn
        _hk0, _dk0 = _nm.index('head'), _nm.index('dress'); _cmp = D['comp']; _tr = D['tri']; _fc0 = _cmp[_tr[:, 0]]
        _k0 = np.round(_cob, 5); _, _i0 = np.unique(_k0, axis=0, return_inverse=True); _i0 = _i0.ravel()
        _P0 = np.zeros((_i0.max() + 1, 3)); _P0[_i0] = _cob
        def _bnd(sel):
            t = _i0[_tr[sel]]; E = np.sort(np.vstack([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), 1)
            c = _Cn(map(tuple, E)); return np.array([e for e, n in c.items() if n == 1])
        def _zone(v): return (_P0[v, 2] > 0.45) & (_P0[v, 2] < 0.60) & (np.abs(_P0[v, 0]) < 0.09)
        _hr = _bnd((_fc0 == _hk0) & ~D['inner']); _hr = _hr[_zone(_hr[:, 0]) & _zone(_hr[:, 1])]
        _dr = _bnd(_fc0 == _dk0); _sv = np.unique(_dr.ravel()); _sv = _sv[_zone(_sv) & ~np.isin(_sv, _hr.ravel())]
        _SN = float(__import__('os').environ.get('NECK_SNAP', '0.002')); _nsn = 0; _mx = 0.0
        for _q in _sv:
            _p = _P0[_q]; _best = None
            for _a, _b in _hr:
                _A, _B = _P0[_a], _P0[_b]; _t = np.clip(np.dot(_p - _A, _B - _A) / max(np.dot(_B - _A, _B - _A), 1e-12), 0, 1); _c = _A + _t * (_B - _A)
                _d = np.linalg.norm(_p - _c)
                if _best is None or _d < _best[0]: _best = (_d, _c)
            if _best is not None and _best[0] <= _SN:
                _cob[_i0 == _q] = _best[1]; _nsn += 1; _mx = max(_mx, _best[0])
        print('NECK crack: dress loop vertices snapped onto the head ring', _nsn, 'of', len(_sv), 'max mm', round(_mx * 1000, 2))
# MOUTH unfold (F2, orchestrator pre-screen 2026-11-04: F2's slit has the same fold as F7's had; F7's text follows): at the closed slit's tubercle and two spots 14 mm aside the
# surface folds over itself - 30 front faces (57 mm2) face backward (normal y > 0) though they are seen from the front, so the engine draws
# their back side (doubleSided head set, normal flipped): the black triangle and the black slit. The vertices of those faces (welded
# positions) are relaxed toward their neighbours' mean, MOUTH_UNFOLD passes, until no front face in the band faces backward; each moves
# at most MOUTH_CAP. Their texels (lip red) are unchanged. A post-paint move confined to the fold, as F7's pass-2 nose-underside smoothing.
_MU = int(__import__('os').environ.get('MOUTH_UNFOLD', '0'))
if _MU > 0 and 'comp' in D.files:
    _tr = D['tri']; _hk2 = [str(x) for x in D['names']].index('head'); _inn2 = D['inner'].astype(bool) if 'inner' in D.files else np.zeros(len(_tr), bool)
    _k2 = np.round(_cob, 5); _, _i2 = np.unique(_k2, axis=0, return_inverse=True); _i2 = _i2.ravel(); _P2 = np.zeros((_i2.max() + 1, 3)); _P2[_i2] = _cob
    _P20 = _P2.copy(); _ht = _i2[_tr[(D['comp'][_tr[:, 0]] == _hk2) & ~_inn2]]
    _E2 = np.unique(np.sort(np.vstack([_ht[:, [0, 1]], _ht[:, [1, 2]], _ht[:, [2, 0]]]), 1), axis=0)
    _CAP = float(__import__('os').environ.get('MOUTH_CAP', '0.0015')); _SZ2 = float(__import__('os').environ.get('MOUTH_SLZ', '0.6220'))
    def _back():
        a = _P2[_ht]; n = np.cross(a[:, 1] - a[:, 0], a[:, 2] - a[:, 0]); c = a.mean(1)
        return (np.abs(c[:, 0]) < 0.022) & (c[:, 2] > _SZ2 - 0.004) & (c[:, 2] < _SZ2 + 0.008) & (c[:, 1] < float(__import__('os').environ.get('MOUTH_FRONT_Y', '-0.094'))) & (n[:, 1] > 0)
    _b0 = int(_back().sum())
    for _it in range(_MU):
        _bf = _back()
        if not _bf.any(): break
        _mv = np.unique(_ht[_bf].ravel())
        _sum = np.zeros_like(_P2); _cnt = np.zeros(len(_P2))
        np.add.at(_sum, _E2[:, 0], _P2[_E2[:, 1]]); np.add.at(_cnt, _E2[:, 0], 1); np.add.at(_sum, _E2[:, 1], _P2[_E2[:, 0]]); np.add.at(_cnt, _E2[:, 1], 1)
        _new = _P2[_mv] + 0.5 * (_sum[_mv] / np.maximum(_cnt[_mv], 1)[:, None] - _P2[_mv])
        _dv = _new - _P20[_mv]; _dl = np.linalg.norm(_dv, axis=1, keepdims=True); _new = _P20[_mv] + _dv * np.minimum(1, _CAP / np.maximum(_dl, 1e-12))
        _P2[_mv] = _new
    _cob = _P2[_i2]; _md = np.linalg.norm(_P2 - _P20, axis=1)
    if __import__('os').environ.get('MOUTH_DBG'):
        _a = _P2[_ht]; _n = np.cross(_a[:, 1] - _a[:, 0], _a[:, 2] - _a[:, 0]); _c = _a.mean(1)
        for _q in np.where(_back())[0]: print('  left', np.round(_c[_q], 4), np.round(_n[_q] / np.linalg.norm(_n[_q]), 2), round(float(np.linalg.norm(_n[_q])) / 2 * 1e6, 2))
    print('MOUTH unfold: back-facing front faces', _b0, '->', int(_back().sum()), 'passes', _it + 1, 'moved', int((_md > 1e-7).sum()), 'max mm', round(float(_md.max()) * 1000, 2))
co = np.c_[_cob[:, 0], _cob[:, 2], -_cob[:, 1]]; tri = D['tri']
WJ_names = [str(x) for x in WT['wnames']]; wj, ww = WT['wj'], WT['ww']
if 'orig' in D.files: wj, ww = wj[D['orig']], ww[D['orig']]
vmap = np.array([idx[WJ_names[i]] for i in range(len(WJ_names))]); J0 = vmap[wj]
uv = D['uv'] if 'uv' in D else np.zeros((len(co), 2)); uv = uv * [1, -1] + [0, 1]
mats = D['mat'] if 'mat' in D else np.zeros(len(tri), int)
_innA = D['inner'].astype(bool) if 'inner' in D.files else np.zeros(len(tri), bool)
# NECK: the head's neck-bottom cap (line_rims_pf2.py) is not needed - the head's ring is welded to the dress's neck loop - and its rim edges
# coincide with the seam, so they z-fought into a thin dotted dark line along the graft (viewer test 2026-11-04): dropped (NECK_CAP=1 keeps it)
if __import__('os').environ.get('NECK_CAP', '0') == '0' and 'comp' in D.files:
    _hk1 = [str(x) for x in D['names']].index('head'); _cz = _cob[tri].mean(1)[:, 2]
    _keep = ~(_innA & (D['comp'][tri[:, 0]] == _hk1) & (_cz < 0.56)); tri = tri[_keep]; mats = mats[_keep]; _innA = _innA[_keep]
    print('NECK cap faces dropped', int((~_keep).sum()))
matnames = [str(x) for x in D['matnames']] if 'matnames' in D else ['PeasantF2']
# Blender faces -> glTF: the frame change is a proper rotation, windings carry over
fn = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]])
key = np.round(co, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel(); Ns = np.zeros((inv.max() + 1, 3))
for c in range(3): np.add.at(Ns, inv[tri[:, c]], fn)
# NECK (user review 2026-11-04): the closing caps and linings (`inner` faces from line_rims_pf2.py) share their rim positions with the
# outer surface; the head's neck-bottom cap (large down-facing fan) turned every head/dress seam normal down (median z -0.93 instead of
# +0.65), which drew the dark jagged band along the graft. Positions that have outer faces take the outer faces' normal only.
if 'inner' in D.files:
    _inn = _innA; _No = np.zeros_like(Ns)
    for c in range(3): np.add.at(_No, inv[tri[~_inn, c]], fn[~_inn])
    _has = np.linalg.norm(_No, axis=1) > 0; _chg = _has & (np.linalg.norm(Ns - _No, axis=1) > 1e-12); Ns[_has] = _No[_has]; print('OUTER normals at shared rim positions', int(_chg.sum()))
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
if 'inner' in D.files:      # NECK: areas of the outer faces only where the normal is the outer faces' (see OUTER normals)
    _sao = np.zeros(nw); [np.add.at(_sao, inv[tri[~_inn, c_]], np.linalg.norm(fn[~_inn], axis=1)) for c_ in range(3)]; _sa = np.where(_has, _sao, _sa)
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
_ledge = np.clip((0.016 - np.abs(_dx)) / 0.004, 0, 1) * np.clip((-0.0015 - _dz) / 0.002, 0, 1) * np.clip((_dz + 0.017) / 0.003, 0, 1) * (_P[:, 1] < -0.09)
_ear = np.clip((np.abs(_P[:, 0]) - 0.048) / 0.004, 0, 1) * ((_P[:, 2] - _Z0) > 1.525) * ((_P[:, 2] - _Z0) < 1.635) * (_P[:, 1] > -0.08) * (_P[:, 1] < 0.02)
# face pass 2: the forehead midline band (the mirrored halves meet at a slight ridge whose faces turn up and read as a pale band); normals only
_fhd = np.clip((0.013 - np.abs(_P[:, 0])) / 0.004, 0, 1) * np.clip((_P[:, 2] - 0.6884 - 0.006) / 0.006, 0, 1) * (_P[:, 1] < -0.05)
_wz = np.maximum(np.maximum(_ledge, _ear), _fhd) * _hp * ~_small
if _wz.any():
    _Nn = Ns / np.maximum(np.linalg.norm(Ns, axis=1, keepdims=True), 1e-12); _N0 = _Nn.copy(); _okn = _hp & ~_small
    for _ in range(int(__import__('os').environ.get('NRELAX', '30'))):
        _A = np.zeros((nw, 3)); np.add.at(_A, ed[:, 0], _Nn[ed[:, 1]] * _okn[ed[:, 1], None]); np.add.at(_A, ed[:, 1], _Nn[ed[:, 0]] * _okn[ed[:, 0], None])
        _A /= np.maximum(np.linalg.norm(_A, axis=1, keepdims=True), 1e-12)
        _Nn = np.where((_wz > 0)[:, None], _A, _N0)
    _Nf = _N0 * (1 - _wz[:, None]) + _Nn * _wz[:, None]
    Ns = np.where((_wz > 0)[:, None], _Nf * np.maximum(np.linalg.norm(Ns, axis=1, keepdims=True), 1e-9), Ns)
    print('RELAXED normals: lower lids + ear plates', int((_wz > 0).sum()))
# NECK + midline (user review 2026-11-04: "a thin vertical midline line down the forehead, nose bridge and neck"; F7's pass-3 SEAM normals):
# within SEAM_W of the midline the normal is the blend of the normals at |x| = SEAM_W on both sides (matched by height and depth), feathered
# over the outer half; on the neck (graft seam up to z 0.575, below the under-chin: blending there darkened the chin front) and on the bridge/forehead (above the nose tip to the hairline). The
# nose tip (z 0.645-0.66), nostrils, mouth and chin (z 0.575-0.668) are left alone. Positions unchanged.
from scipy.spatial import cKDTree as _Ks
SW = float(__import__('os').environ.get('SEAM_W', '0.007'))
_ok3 = _hp & ~_small & (((_P[:, 1] < -0.02) & (_P[:, 2] > 0.515) & (_P[:, 2] < float(__import__('os').environ.get('SEAM_NECK_TOP', '0.575')))) | ((_P[:, 1] < -0.05) & (_P[:, 2] > 0.668) & (_P[:, 2] < 0.785)))
_bandv = np.where(_ok3 & (np.abs(_P[:, 0]) < SW))[0]
_er = np.where(_ok3 & (np.abs(_P[:, 0] - SW) < 0.0015))[0]; _el = np.where(_ok3 & (np.abs(_P[:, 0] + SW) < 0.0015))[0]
if len(_bandv) and len(_er) and len(_el):
    _Nu = Ns / np.maximum(np.linalg.norm(Ns, axis=1, keepdims=True), 1e-12)
    _, _ir = _Ks(_P[_er][:, 1:]).query(_P[_bandv][:, 1:]); _, _il = _Ks(_P[_el][:, 1:]).query(_P[_bandv][:, 1:])
    _nr = _Nu[_er[_ir]]; _nl = _Nu[_el[_il]]
    _t = np.clip((_P[_bandv, 0] + SW) / (2 * SW), 0, 1)[:, None]
    _nb = _nl * (1 - _t) + _nr * _t; _nb /= np.maximum(np.linalg.norm(_nb, axis=1, keepdims=True), 1e-12)
    _ax = np.abs(_P[_bandv, 0]) / SW; _wf = np.clip((1 - _ax) / 0.5, 0, 1)[:, None]; _wf = _wf * _wf * (3 - 2 * _wf)
    _n0 = _Nu[_bandv]; _nb = _n0 * (1 - _wf) + _nb * _wf; _nb /= np.maximum(np.linalg.norm(_nb, axis=1, keepdims=True), 1e-12)
    Ns[_bandv] = _nb * np.maximum(np.linalg.norm(Ns[_bandv], axis=1, keepdims=True), 1e-9)
    print('SEAM normals averaged', len(_bandv))
# MOUTH (user review 2026-11-04, "the black stuff on her upper lip"): the closed slit is a V groove whose upper side faces 45 deg down
# (normal (0, -0.71, -0.70) at the tubercle), so any light from above drew a black band and a black triangle there; paint lifts did not
# change it. Front-facing positions in the groove band (|x| < 20 mm, z SLIT-0.5..+6 mm) are turned MOUTH_NRM of the way toward straight
# forward (eased out at the band's edges); positions and the lip volume are unchanged. A deviation from "no normal edits on the mouth",
# made because the defect is the groove's shading, not its paint.
_MN = float(__import__('os').environ.get('MOUTH_NRM', '0'))
if _MN > 0:
    _SZ = float(__import__('os').environ.get('MOUTH_SLZ', '0.6220'))
    _Nu = Ns / np.maximum(np.linalg.norm(Ns, axis=1, keepdims=True), 1e-12)
    _wm = (np.clip((float(__import__('os').environ.get('MOUTH_NRM_W', '0.020')) - np.abs(_P[:, 0])) / 0.004, 0, 1) * np.clip((_P[:, 2] - (_SZ - 0.0015)) / 0.001, 0, 1)
           * np.clip(((_SZ + 0.007) - _P[:, 2]) / 0.001, 0, 1) * (_P[:, 1] < -0.085) * (_Nu[:, 2] > 0.2) * _hp)      # Ns is in glTF axes: forward = +z, up = +y
    _fw = np.array([0.0, 0.0, 1.0]); _nm = _Nu * (1 - _MN * _wm[:, None]) + _fw * (_MN * _wm[:, None])
    _nm /= np.maximum(np.linalg.norm(_nm, axis=1, keepdims=True), 1e-12)
    _sel = _wm > 0; Ns[_sel] = _nm[_sel] * np.maximum(np.linalg.norm(Ns[_sel], axis=1, keepdims=True), 1e-9)
    print('MOUTH groove normals turned forward', int(_sel.sum()))
# NOSETILT / CHINTILT (orchestrator pre-screen 2026-11-04; Igrid's accepted fix, mm9_wyrdold_claude README "Pre-screen pass"): the dark
# brown T under the nose in every front close-up and the dark wedge under the chin from below are the viewer's/engine's dark ground term
# on large downward-facing surfaces, not paint. Only the downward-facing normals of the nose underside (eased by how far down they point)
# are turned toward the front, to at most 20 deg below horizontal; the real nostril pits keep 70 % of their own normal; bridge, tip front and
# wings untouched. The under-chin's downward normals likewise, to at most CHIN_DEG below horizontal. Ns is in glTF axes (up +y, front +z);
# zones by Blender position _P. Positions unchanged.
import os as _os2
def _tilt(zone, deg, pitx, pitz, label, nxk=1.0):
    _Nn = Ns / np.maximum(np.linalg.norm(Ns, axis=1, keepdims=True), 1e-12)
    _sy = -np.sin(np.radians(deg))
    _down = np.clip((-_Nn[:, 1] + _sy - 0.10) / 0.25, 0, 1)                    # pointing further down than the target
    _pit = np.exp(-(((np.abs(_P[:, 0]) - pitx) / 0.0028) ** 2 + ((_P[:, 2] - pitz) / 0.0018) ** 2)) if pitx else 0.0
    _w = zone * _down * (1 - 0.7 * _pit) * _hp * ~_small
    _nx = _Nn[:, 0] * nxk      # nxk < 1: the narrow septum's side facets turned toward the front too (F2 v3 columella)
    _hz = np.sqrt(np.clip(1 - _nx ** 2 - _sy ** 2, 0.05, 1))
    _f = np.c_[_nx, np.full(nw, _sy), _hz]; _f /= np.linalg.norm(_f, axis=1, keepdims=True)
    _Nf = _Nn * (1 - _w[:, None]) + _f * _w[:, None]
    return np.where((_w > 0)[:, None], _Nf * np.maximum(np.linalg.norm(Ns, axis=1, keepdims=True), 1e-9), Ns), int((_w > 0.05).sum())
def _box(x0, z0, z1, ymax):
    return np.clip((x0 - np.abs(_P[:, 0])) / 0.004, 0, 1) * np.clip((_P[:, 2] - z0) / 0.003, 0, 1) * np.clip((z1 - _P[:, 2]) / 0.003, 0, 1) * (_P[:, 1] < ymax)
if _os2.environ.get('NOSETILT', '1') == '1':
    _nz = [float(v) for v in _os2.environ.get('NOSE_ZONE', '0.020,0.632,0.656,-0.085,0.0074,0.6485').split(',')]      # x half, z0, z1, y max, pit x, pit z
    Ns, _n1 = _tilt(_box(_nz[0], _nz[1], _nz[2], _nz[3]), float(_os2.environ.get('NOSE_DEG', '20')), _nz[4], _nz[5], 'nose', float(_os2.environ.get('NOSE_NXK', '1.0'))); print('TILTED normals: nose underside', _n1)
if _os2.environ.get('CHINTILT', '1') == '1':
    _cz = [float(v) for v in _os2.environ.get('CHIN_ZONE', '0.050,0.560,0.600,-0.030').split(',')]       # x half, z0, z1, y max
    Ns, _n2 = _tilt(_box(_cz[0], _cz[1], _cz[2], _cz[3]), float(_os2.environ.get('CHIN_DEG', '35')), 0.0, 0.0, 'chin'); print('TILTED normals: under-chin', _n2)
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
mesh_node = len(nodes); nodes.append({'name': 'PeasantF2', 'mesh': 0, 'skin': 0})
doc = {'asset': {'version': '2.0', 'generator': 'mm9_peasantf2 build_glb_pf'}, 'scene': 0, 'scenes': [{'nodes': [0, mesh_node]}], 'nodes': nodes, 'meshes': [{'name': 'PeasantF2', 'primitives': prims}], 'skins': [{'joints': list(range(len(names))), 'inverseBindMatrices': ib, 'skeleton': 0}],
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
