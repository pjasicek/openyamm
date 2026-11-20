#!/usr/bin/env python3
"""See-through fixes for PF7/PF2 (after mm9_peasantf6_claude/scripts/line_rims.py, generalised). Faces and vertices ADDED only; every existing
vertex, face, UV and weight is kept (the paid paints stay valid; new vertices take an existing `orig`, so they get its weights).
  caps   - the head shell's open boundary loops (the neck bottom inside the collar, the skull opening under the hair that MM9's Wince/Fidget
           expose by flinging the hair up), except the eye sockets and the mouth: a fan to the loop centroid facing away from the head's centre,
           on the loop texel nearest the loop's median colour. The dress's open waist loop (inside the skirt): a fan facing down.
  sleeves- dress faces within BAND of each open dress loop at |x| > SLEEVE_X (the sleeve hems round the bare arm) duplicated INSET behind
           themselves along the vertex normal, flipped, joined to the hem by a rim strip; on one dark dress texel (region R recolours it).
Args: <in npz> <out npz> <head base png> <body png> <body mask png> [band 0.06] [inset 0.003] [sleeve_x 0.17]"""
import sys, json
import numpy as np
from PIL import Image
from collections import defaultdict
IN, OUT, HEADPNG, BODYPNG, MASKPNG = sys.argv[1:6]
BAND = float(sys.argv[6]) if len(sys.argv) > 6 else 0.06; INSET = float(sys.argv[7]) if len(sys.argv) > 7 else 0.003
SX = float(sys.argv[8]) if len(sys.argv) > 8 else 0.17
D = dict(np.load(IN)); co, tri, uv, orig, comp, mat, inner = D['co'], D['tri'], D['uv'], D['orig'], D['comp'], D['mat'], D['inner']
names = [str(x) for x in D['names']]; pid = {n: i for i, n in enumerate(names)}
NV = len(co); add_co, add_uv, add_orig, add_comp = [], [], [], []; add_tri, add_mat, add_inner = [], [], []
def addv(p, u, o, c):
    add_co.append(p); add_uv.append(u); add_orig.append(o); add_comp.append(c); return NV + len(add_co) - 1
# welded positions per orig (uv_tex2 positions after the face tweak)
P0 = np.zeros((orig.max() + 1, 3)); P0[orig] = co
def loops(part):
    F = np.where(comp[tri[:, 0]] == pid[part])[0]; T = orig[tri[F]]
    e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]); s = np.sort(e, axis=1)
    u, inv, cnt = np.unique(s, axis=0, return_inverse=True, return_counts=True); b = e[cnt[inv.ravel()] == 1]
    nb = defaultdict(list)
    for a_, b_ in b: nb[a_].append(b_); nb[b_].append(a_)
    seen, out = set(), []
    for v in list(nb):
        if v in seen or len(nb[v]) != 2: continue
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
def rep_vertex(part):
    d = {}
    for i in np.where(comp == pid[part])[0]: d.setdefault(int(orig[i]), int(i))
    return d
def texel(img, u): S = img.shape[0]; return img[int((1 - u[1]) * (S - 1)), int(u[0] * (S - 1))]
rep = {'caps': [], 'sleeves': []}
def cap(part, L, M, img, face_dir=None):
    rv = rep_vertex(part); P = P0[L]; c = P.mean(0); vids = [rv[v] for v in L]
    cols = np.array([texel(img, uv[i]) for i in vids]); med = np.median(cols, 0); u0 = uv[vids[int(np.argmin(np.linalg.norm(cols - med, axis=1)))]]
    o_c = L[int(np.argmin(np.linalg.norm(P - c, axis=1)))]
    cv = addv(c, u0, o_c, pid[part]); ring = [addv(P0[v], u0, v, pid[part]) for v in L]
    pc = P0[np.unique(orig[comp == pid[part]])].mean(0)
    fs = [[cv, ring[i], ring[(i + 1) % len(ring)]] for i in range(len(ring))]
    allc = np.vstack([co, np.array(add_co)]); av = sum(np.cross(allc[f[1]] - allc[f[0]], allc[f[2]] - allc[f[0]]) for f in fs)
    want = (c - pc) if face_dir is None else np.asarray(face_dir, float)
    if av @ want < 0: fs = [f[::-1] for f in fs]
    for f in fs: add_tri.append(f); add_mat.append(M); add_inner.append(True)
    rep['caps'].append(dict(part=part, n=len(L), centre=np.round(c, 3).tolist(), r=round(float(np.linalg.norm(P - c, axis=1).mean()), 3)))
himg = np.asarray(Image.open(HEADPNG).convert('RGB'), np.float32); bimg = np.asarray(Image.open(BODYPNG).convert('RGB'), np.float32)
EYES = [np.array([s_ * 0.0275, -0.080, 0.6884]) for s_ in (1, -1)]
_, hl = loops('head')
for L in hl:
    P = P0[L]; c = P.mean(0); r = np.linalg.norm(P - c, axis=1).mean()
    if min(np.linalg.norm(c - e_) for e_ in EYES) < 0.025: continue                         # eye sockets
    if abs(c[0]) < 0.03 and 0.595 < c[2] < 0.645 and c[1] < -0.06: continue                 # mouth
    if r < 0.006:
        if len(L) <= 8: cap('head', L, 1, himg)      # face pass 2: pinholes left by the dropped needle slivers (midline, < 6 mm)
        continue
    cap('head', L, 1, himg)
if 'hair' in pid:
    _, hpl = loops('hair')
    for L in hpl:
        P = P0[L]; c = P.mean(0); r = np.linalg.norm(P - c, axis=1).mean()
        if r < 0.006 and len(L) <= 8: cap('hair', L, 1, himg)
_, dl = loops('dress')
for L in dl:
    P = P0[L]; c = P.mean(0); r = np.linalg.norm(P - c, axis=1).mean()
    if abs(c[0]) < 0.05 and c[2] < 0.30 and r > 0.06: cap('dress', L, 0, bimg, face_dir=(0, 0, -1))      # the waist, inside the skirt
for part_ in ('hands',):      # the MPFB arm's open upper-arm stub inside the sleeve
    if part_ not in pid: continue
    _, al = loops(part_)
    for L in al: cap(part_, L, 0, bimg)
# face pass 2: the columella-base hole (figure-8 boundary the loop walker skips): head boundary vertices in the box |x| < 6 mm,
# z 0.633..0.646, y < -0.096 ordered by angle round their centroid in the front (x, z) plane, fanned, facing forward
_Fh = np.where(comp[tri[:, 0]] == pid['head'])[0]; _Th = orig[tri[_Fh]]
_e = np.sort(np.vstack([_Th[:, [0, 1]], _Th[:, [1, 2]], _Th[:, [2, 0]]]), 1); _u, _c = np.unique(_e, axis=0, return_counts=True)
_bv = np.unique(_u[_c == 1]); _pb = P0[_bv]
_z0, _z1, _y0 = 0.633,0.646,-0.096
_sel = _bv[(np.abs(_pb[:, 0]) < 0.006) & (_pb[:, 2] > _z0) & (_pb[:, 2] < _z1) & (_pb[:, 1] < _y0)]
if len(_sel) >= 3:
    _kk = {}
    for o_ in _sel: _kk.setdefault(tuple(np.round(P0[o_], 6)), o_)
    _L = list(_kk.values()); _P = P0[_L]; _c0 = _P.mean(0); _ang = np.arctan2(_P[:, 2] - _c0[2], _P[:, 0] - _c0[0]); _L = [_L[i] for i in np.argsort(_ang)]
    _rv = rep_vertex('head'); _u0 = uv[_rv[_L[0]]]
    _cv = addv(_c0, _u0, _L[0], pid['head']); _ring = [addv(P0[v], _u0, v, pid['head']) for v in _L]
    _fs = [[_cv, _ring[i], _ring[(i + 1) % len(_ring)]] for i in range(len(_ring))]
    _allc = np.vstack([co, np.array(add_co)]); _av = sum(np.cross(_allc[f[1]] - _allc[f[0]], _allc[f[2]] - _allc[f[0]]) for f in _fs)
    if _av[1] > 0: _fs = [f[::-1] for f in _fs]
    for f in _fs: add_tri.append(f); add_mat.append(1); add_inner.append(True)
    rep['caps'].append(dict(part='columella', n=len(_L), centre=np.round(_c0, 4).tolist(), r=0))
# ---- sleeve linings
mk = np.asarray(Image.open(MASKPNG).convert('RGBA'), np.float32) / 255
Fd, _ = loops('dress')
Tn = orig[tri[Fd]]; fn = np.cross(P0[Tn[:, 1]] - P0[Tn[:, 0]], P0[Tn[:, 2]] - P0[Tn[:, 0]]); Nw = np.zeros_like(P0)
for c_ in range(3): np.add.at(Nw, Tn[:, c_], fn)
Nw /= np.maximum(np.linalg.norm(Nw, axis=1, keepdims=True), 1e-12)
from scipy.spatial import cKDTree
for L in dl:
    P = P0[L]; c = P.mean(0)
    if abs(c[0]) < SX: continue
    kd = cKDTree(P); fd_ = kd.query(P0[Tn].reshape(-1, 3))[0].reshape(-1, 3).max(1); band = Fd[fd_ < BAND]
    cand = []
    for f in band:
        u_ = uv[tri[f]].mean(0)
        if texel(mk, u_)[0] > 0.9: cand.append((texel(bimg, u_).mean(), tuple(u_)))
    cand.sort(); duv = np.array(cand[max(0, len(cand) // 20)][1]) if cand else uv[tri[band[0], 0]]
    tw = {}
    def twin(o):
        if o not in tw: tw[o] = addv(P0[o] - Nw[o] * INSET, duv, o, pid['dress'])
        return tw[o]
    for f in band:
        a_, b_, c2 = orig[tri[f]]; add_tri.append([twin(c2), twin(b_), twin(a_)]); add_mat.append(0); add_inner.append(True)
    rv = rep_vertex('dress'); Ls = set(L)
    # rim strip along the hem: hem edges oriented as in the band faces
    T2 = orig[tri[band]]
    for t_ in T2:
        for k in range(3):
            a_, b_ = t_[k], t_[(k + 1) % 3]
            if a_ in Ls and b_ in Ls and (L.index(a_) - L.index(b_)) % len(L) in (1, len(L) - 1):
                ra, rb = addv(P0[a_], duv, a_, pid['dress']), addv(P0[b_], duv, b_, pid['dress'])
                add_tri += [[rb, ra, twin(a_)], [rb, twin(a_), twin(b_)]]; add_mat += [0, 0]; add_inner += [True, True]
    rep['sleeves'].append(dict(centre=np.round(c, 3).tolist(), band_faces=int(len(band)), uv=np.round(duv, 4).tolist()))
# ---- hair rim lining: the hair shell is one-sided; its open rim (the cap's lower edge over the ears, the sheet's edges) is lined like the
# sleeve hems: hair faces within HAIR_BAND of each large open loop duplicated 2 mm inside, flipped, joined by a rim strip, on a dark hair texel
import os as _os
HB_ = float(_os.environ.get('HAIR_BAND', '0.008'))
if 'hair' in pid:
    Fh, hl2 = loops('hair'); Th = orig[tri[Fh]]
    fnh = np.cross(P0[Th[:, 1]] - P0[Th[:, 0]], P0[Th[:, 2]] - P0[Th[:, 0]]); Nh = np.zeros_like(P0)
    for c_ in range(3): np.add.at(Nh, Th[:, c_], fnh)
    Nh /= np.maximum(np.linalg.norm(Nh, axis=1, keepdims=True), 1e-12)
    for L in hl2:
        P = P0[L]; c = P.mean(0); r = np.linalg.norm(P - c, axis=1).mean()
        if r < float(_os.environ.get('HAIR_RMIN', '0.03')): continue
        kd = cKDTree(P); fd_ = kd.query(P0[Th].reshape(-1, 3))[0].reshape(-1, 3).max(1); band = Fh[fd_ < HB_]
        cols = sorted((texel(himg, uv[tri[f]].mean(0)).mean(), tuple(uv[tri[f]].mean(0))) for f in band)
        duv = np.array(cols[max(0, len(cols) // 5)][1]) if cols else uv[tri[band[0], 0]]
        tw = {}
        def twin(o):
            if o not in tw: tw[o] = addv(P0[o] - Nh[o] * 0.002, duv, o, pid['hair'])
            return tw[o]
        for f in band:
            a_, b_, c2 = orig[tri[f]]; add_tri.append([twin(c2), twin(b_), twin(a_)]); add_mat.append(1); add_inner.append(True)
        Ls = set(L); n_ = 0
        for t_ in orig[tri[band]]:
            for k in range(3):
                a_, b_ = t_[k], t_[(k + 1) % 3]
                if a_ in Ls and b_ in Ls and (L.index(a_) - L.index(b_)) % len(L) in (1, len(L) - 1):
                    ra, rb = addv(P0[a_], duv, a_, pid['hair']), addv(P0[b_], duv, b_, pid['hair'])
                    add_tri += [[rb, ra, twin(a_)], [rb, twin(a_), twin(b_)]]; add_mat += [1, 1]; add_inner += [True, True]; n_ += 1
        rep.setdefault('hair', []).append(dict(centre=np.round(c, 3).tolist(), n=len(L), band_faces=int(len(band)), rim=n_))
D['co'] = np.vstack([co, np.array(add_co)]); D['uv'] = np.vstack([uv, np.array(add_uv)]); D['orig'] = np.r_[orig, np.array(add_orig, int)]
D['comp'] = np.r_[comp, np.array(add_comp, int)]; D['tri'] = np.vstack([tri, np.array(add_tri)]); D['mat'] = np.r_[mat, np.array(add_mat, int)]
D['inner'] = np.r_[inner, np.array(add_inner, bool)]
np.savez(OUT, **D); json.dump(rep, open(OUT.replace('.npz', '.json'), 'w'), indent=1)
print('HAIR linings', [(h_['n'], h_['band_faces'], h_['rim']) for h_ in rep.get('hair', [])]); print('LINE_RIMS caps', [(c_['part'], c_['n'], c_['r']) for c_ in rep['caps']], 'sleeves', [(s_['centre'], s_['band_faces']) for s_ in rep['sleeves']], 'new faces', len(add_tri))
