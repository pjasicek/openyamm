#!/usr/bin/env python3
"""See-through fixes on the painted mesh npz (positions and faces ADDED only; every existing vertex, face, UV and weight is kept, so the
paid paints stay valid). After mm9_peasantdm2_claude's neck_cap.py / rim_lining.py, for this npz pipeline (weights follow `orig`):
  caps   - open boundary loops closed with a fan to the loop's centroid, facing away from the part's centroid: the head's open neck bottom
           inside the dress, the bare arms' open tops inside the puffed sleeves, the hand stubs' open ends inside the forearms and the arms'
           4-edge pinholes. Cap texels: the UV of the loop vertex nearest the loop's median colour (neck skin, sleeve cloth); the centre
           vertex takes the weights of the loop vertex nearest the centroid (orig).
  collar - the dress faces within BAND m of the neck opening duplicated INSET m behind themselves along the vertex normal, flipped, and the
           neck rim joined to its twin by a strip facing out of the garment: views down the collar of the lying corpse meet cloth. Lining
           and rim on one dark gown texel (region R, so tier B recolours it).
Args: <in npz> <out npz> <body colour png> <body mask png> [band 0.10] [inset 0.003] [extra parts to line, comma list, by loop: puffs]"""
import sys, json
import numpy as np
from PIL import Image
from collections import defaultdict
IN, OUT, BODYPNG, MASKPNG = sys.argv[1:5]
BAND = float(sys.argv[5]) if len(sys.argv) > 5 else 0.10
INSET = float(sys.argv[6]) if len(sys.argv) > 6 else 0.003
D = dict(np.load(IN)); co, tri, uv, orig, comp, mat, inner = D['co'], D['tri'], D['uv'], D['orig'], D['comp'], D['mat'], D['inner']
names = [str(x) for x in D['names']]; pid = {n: i for i, n in enumerate(names)}
NV, NF = len(co), len(tri)
new_co, new_uv, new_orig, new_comp = [], [], [], []; new_tri, new_mat, new_inner = [], [], []
def addv(p, u, o, c):
    new_co.append(p); new_uv.append(u); new_orig.append(o); new_comp.append(c); return NV + len(new_co) - 1
def allco(): return np.vstack([co, np.array(new_co).reshape(-1, 3)])
# welded topology per part (by orig): boundary loops
def loops(part):
    k = pid[part]; F = np.where(comp[tri[:, 0]] == k)[0]; T = orig[tri[F]]
    e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]); s = np.sort(e, axis=1)
    u, inv, cnt = np.unique(s, axis=0, return_inverse=True, return_counts=True); b = e[cnt[inv.ravel()] == 1]
    nb = defaultdict(list)
    for a_, b_ in b: nb[a_].append(b_); nb[b_].append(a_)
    seen, out = set(), []
    for v in nb:
        if v in seen: continue
        if len(nb[v]) != 2: continue
        L = [v]; seen.add(v); prev, cur = None, v
        while True:
            nx = [w for w in nb[cur] if w != prev]
            if not nx: break
            n_ = nx[0]
            if n_ == v: break
            if n_ in seen or len(nb[n_]) != 2: L = None; break
            seen.add(n_); L.append(n_); prev, cur = cur, n_
        if L and len(L) >= 3: out.append(L)
    return F, out
A = np.load('work/asm_f6.npz'); aco = A['co']
rep = {'caps': [], 'collar': {}}
# representative split vertex (uv npz index) per asm vertex within a part
def rep_vertex(part):
    k = pid[part]; m = np.where(comp == k)[0]; d = {}
    for i in m: d.setdefault(int(orig[i]), int(i))
    return d
img = np.asarray(Image.open(BODYPNG).convert('RGB'), np.float32)
def cap(part, L, M, face_dir=None):
    rv = rep_vertex(part); P = aco[L]; c = P.mean(0)
    vids = [rv[v] for v in L]
    if M == 1:   # head material: colour from the head image is not loaded; take the loop's lowest-index split vertex UV (neck skin)
        u0 = uv[vids[0]]
    else:
        S = img.shape[0]; cols = np.array([img[int((1 - uv[i, 1]) * (S - 1)), int(uv[i, 0] * (S - 1))] for i in vids]); med = np.median(cols, 0)
        u0 = uv[vids[int(np.argmin(np.linalg.norm(cols - med, axis=1)))]]
    o_c = L[int(np.argmin(np.linalg.norm(P - c, axis=1)))]
    cv = addv(c, u0, o_c, pid[part])
    ring = [addv(aco[v], u0, v, pid[part]) for v in L]
    pc = aco[np.unique(orig[comp == pid[part]])].mean(0)
    fs = [[cv, ring[i], ring[(i + 1) % len(ring)]] for i in range(len(ring))]
    n = np.cross(aco[L[0]] - c, aco[L[1]] - c)
    if n @ (c - pc) < 0: fs = [f[::-1] for f in fs]
    # the fan's normal must point away from the part's centroid; check by the summed area vector
    allc = allco(); av = sum(np.cross(allc[f[1]] - allc[f[0]], allc[f[2]] - allc[f[0]]) for f in fs)
    want = (c - pc) if face_dir is None else np.asarray(face_dir, float)
    if av @ want < 0: fs = [f[::-1] for f in fs]
    for f in fs: new_tri.append(f); new_mat.append(M); new_inner.append(True)
    rep['caps'].append(dict(part=part, n=len(L), centre=np.round(c, 3).tolist(), r=round(float(np.linalg.norm(P - c, axis=1).mean()), 3)))
# ---- caps
_, hl = loops('head')
for L in hl:
    P = aco[L]; c = P.mean(0); r = np.linalg.norm(P - c, axis=1).mean()
    if c[2] < 0.56 and r > 0.04: cap('head', L, 1)
_, al = loops('arms')
for L in al:
    P = aco[L]; c = P.mean(0); r = np.linalg.norm(P - c, axis=1).mean()
    if (r > 0.03 and abs(c[0]) < 0.35) or len(L) <= 6: cap('arms', L, 0)
_, hal = loops('hands')
for L in hal: cap('hands', L, 0)
# ---- waist: the skirt lining's open top (inside the dress at the waist) capped facing down, so a view up the skirt of the lying corpse
# meets the lining's dark cloth instead of the bodice's culled inside (see-through gate: Death/Dead from the feet, 1100-2200 px)
_, ll = loops('lining')
for L in ll:
    P = aco[L]; c = P.mean(0); r = np.linalg.norm(P - c, axis=1).mean()
    if c[2] > 0.1 and r > 0.08: cap('lining', L, 0, face_dir=(0, 0, -1))
# ---- mouth backing (coordinator review r13: specks in the lip slit): the slit is open into the head, so the nape's inside showed through
# it. A small plate 8 mm behind the lips (|x| < 2.8 cm, z 0.594..0.618), facing forward, on the head material at the lip texel nearest the
# slit centre; its vertices take the nearest lip vertex's weights (the head is rigid on Head there)
from scipy.spatial import cKDTree
hk_ = pid['head']; hvv = np.where(comp == hk_)[0]
slit_c = np.array([0.0, -0.124, 0.606])
_hi = np.asarray(Image.open('textures/pf_head_a_face.png').convert('RGB'), np.float32); _HS = _hi.shape[0]
_near = hvv[np.linalg.norm(co[hvv] - slit_c, axis=1) < 0.012]
_cols = np.array([_hi[int((1 - uv[i, 1]) * (_HS - 1)), int(uv[i, 0] * (_HS - 1))] for i in _near])
lv = _near[np.argmin(np.linalg.norm(_cols - np.array([150, 85, 70.]), axis=1))]      # a shaded lip texel (lip-shadow tone)
NX_, NZ_ = 6, 3; xs_ = np.linspace(-0.019, 0.019, NX_ + 1); zs_ = np.linspace(0.598, 0.614, NZ_ + 1)
ids_ = {}
kd_h = cKDTree(aco[np.unique(orig[hvv])]); hv_orig = np.unique(orig[hvv])
for i_, x_ in enumerate(xs_):
    for j_, z_ in enumerate(zs_):
        p_ = np.array([x_, -0.115 + 0.012 * (abs(x_) / 0.019) ** 2, z_])
        o_ = hv_orig[kd_h.query(p_)[1]]
        ids_[(i_, j_)] = addv(p_, uv[lv], o_, hk_)
for i_ in range(NX_):
    for j_ in range(NZ_):
        a_, b_, c_, d_ = ids_[(i_, j_)], ids_[(i_ + 1, j_)], ids_[(i_, j_ + 1)], ids_[(i_ + 1, j_ + 1)]
        new_tri += [[a_, b_, d_], [a_, d_, c_]]; new_mat += [1, 1]; new_inner += [True, True]
# facing forward (-y): check the first quad's normal
_P = allco(); _t = new_tri[-2]; _n = np.cross(_P[_t[1]] - _P[_t[0]], _P[_t[2]] - _P[_t[0]])
if _n[1] > 0:
    for k_ in range(1, 2 * NX_ * NZ_ + 1): new_tri[-k_] = new_tri[-k_][::-1]
# the slit's own sliver faces have UVs lying in another chart (they sampled hair/neck paint: a gold line in the lip slit): they get their
# own vertex copies (same positions and orig, so the same weights) on the backing's lip-shadow texel
_c = co[tri].mean(1); _n = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]]); _n /= np.maximum(np.linalg.norm(_n, axis=1, keepdims=True), 1e-12)
_sf = np.where((comp[tri[:, 0]] == hk_) & (np.abs(_c[:, 0]) < 0.024) & (_c[:, 2] > 0.597) & (_c[:, 2] < 0.614) & (_c[:, 1] < -0.09) & (_n[:, 1] > -0.55))[0]
_slit_faces = _sf
rep['slit_faces_reuv'] = int(len(_sf))
rep['mouth_backing'] = dict(faces=2 * NX_ * NZ_, uv=np.round(uv[lv], 4).tolist())
# ---- collar lining
Fd, dl = loops('dress')
neck = [L for L in dl if aco[L].mean(0)[2] > 0.5]
assert len(neck) == 1, [aco[L].mean(0) for L in dl]
neck = neck[0]
from scipy.spatial import cKDTree
kd = cKDTree(aco[neck]); fd = kd.query(aco[orig[tri[Fd]]].reshape(-1, 3))[0].reshape(-1, 3).max(1)
band = Fd[fd < BAND]
# vertex normals (welded by orig) over the dress
Tn = orig[tri[Fd]]; fn = np.cross(aco[Tn[:, 1]] - aco[Tn[:, 0]], aco[Tn[:, 2]] - aco[Tn[:, 0]])
Nw = np.zeros_like(aco)
for c_ in range(3): np.add.at(Nw, Tn[:, c_], fn)
Nw /= np.maximum(np.linalg.norm(Nw, axis=1, keepdims=True), 1e-12)
# one dark gown texel: the darkest 10 % of band-face texels whose region mask R > 0.9, then the median of those
mk = np.asarray(Image.open(MASKPNG).convert('RGBA'), np.float32) / 255; S = img.shape[0]; Sm = mk.shape[0]
cand = []
for f in band:
    u_ = uv[tri[f]].mean(0); px, py = int(u_[0] * (S - 1)), int((1 - u_[1]) * (S - 1))
    if mk[int((1 - u_[1]) * (Sm - 1)), int(u_[0] * (Sm - 1)), 0] > 0.9: cand.append((img[py, px].mean(), tuple(u_)))
cand.sort(); dark_uv = np.array(cand[max(0, len(cand) // 20)][1]) if cand else uv[tri[band[0], 0]]
tw = {}
bv = np.unique(orig[tri[band]])
for v in bv: tw[v] = addv(aco[v] - Nw[v] * INSET, dark_uv, v, pid['dress'])
for f in band:
    a, b, c = orig[tri[f]]; new_tri.append([tw[a], tw[c], tw[b]]); new_mat.append(0); new_inner.append(True)
# rim: the neck loop edges (as oriented in their band face) to their twins
loopset = set(neck); rv = rep_vertex('dress'); nrim = 0
for f in band:
    t3 = orig[tri[f]]
    for i in range(3):
        a, b = t3[i], t3[(i + 1) % 3]
        if a in loopset and b in loopset and (abs(neck.index(a) - neck.index(b)) in (1, len(neck) - 1)):
            A_, B_ = addv(aco[a], dark_uv, a, pid['dress']), addv(aco[b], dark_uv, b, pid['dress'])
            new_tri += [[B_, A_, tw[a]], [B_, tw[a], tw[b]]]; new_mat += [0, 0]; new_inner += [True, True]; nrim += 2
rep['collar'] = dict(band_faces=int(len(band)), rim_faces=nrim, neck_loop=len(neck), dark_uv=np.round(dark_uv, 4).tolist())
D['co'] = allco(); D['uv'] = np.vstack([uv, np.array(new_uv)]); D['orig'] = np.r_[orig, np.array(new_orig, int)]; D['comp'] = np.r_[comp, np.array(new_comp, int)]
D['tri'] = np.vstack([tri, np.array(new_tri, int)]); D['mat'] = np.r_[mat, np.array(new_mat, int)]; D['inner'] = np.r_[inner, np.array(new_inner, bool)]
_T = D['tri']; _co = D['co']; _uv = D['uv']; _or = D['orig']; _cp = D['comp']; _add = []
for f in _slit_faces:
    for k_ in range(3):
        v = _T[f, k_]; _add.append((_co[v], _uv[lv], _or[v], _cp[v])); _T[f, k_] = len(_co) + len(_add) - 1
if _add:
    D['co'] = np.vstack([_co, np.array([a[0] for a in _add])]); D['uv'] = np.vstack([_uv, np.array([a[1] for a in _add])])
    D['orig'] = np.r_[_or, np.array([a[2] for a in _add], int)]; D['comp'] = np.r_[_cp, np.array([a[3] for a in _add], int)]; D['tri'] = _T
rep['faces'] = [int(NF), int(len(D['tri']))]
np.savez(OUT, **D); print('LINE_RIMS', json.dumps(rep))
