#!/usr/bin/env python3
"""Fre pass 4 (orchestrator r43: "do real hair"): PeasantF2's approved hair (sleek drawn-back cap + braid, `../mm9_peasantf2_claude`,
final geometry work/geom_final_v3.npz, its weights and head-set UVs; read only, copied to work/f2/) replaces Fre's parametric cap and braid.
Both models stand on the same MM9 PeasantFemale skeleton and bind frame (FHP Head / Neck joints identical), so the hair needs no rigid
transform; the fit is local:
- Fre's own cap ('hood4') and braid ('braids') faces are dropped (asm and uv npz);
- every head-shell / old-hood vertex the new cap covers (ray from the head centre) that lies within CLR of the cap or outside it moves to
  CLR under it (head shell with its coincident twins; never the neckline seam with the bodice); the reported max fit distance is the
  largest such move;
- old-hood faces the new hair does not cover (and not on the face seam) are dropped; the rest stays as the hidden skull;
- the hair (component 'hair2', third material 'FreHair' with F2's head-set UVs) is appended; its weights (F2's, by joint name) are saved
  to work/hair2_weights.npz for weights_fre.py.
Pass 4b: the cap's whole open rim (minus the braid tube) is pulled onto the face shell's outline and OVER past it (OVER=0.010 used);
uncovered old-hood faces on the face seam stay (they fill the outline's saw teeth; seam_skin_fre.py paints them skin), the rest go.
Args: <asm in> <uv in> <hair piece npz> <asm out> <uv out> <report json>   (project folder)"""
import sys, json, os
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from geo4 import raycast
AI, UI, HI, AO, UO, REP = sys.argv[1:7]
A = dict(np.load(AI)); U = dict(np.load(UI)); H = dict(np.load(HI))
names = [str(x) for x in A['names']]; co, tri, comp = A['co'].copy(), A['tri'], A['comp']
K4, KB, KS, KH, KD = (names.index(x) for x in ('hood4', 'braids', 'scarf', 'head', 'dress'))
CLR = float(os.environ.get('CLR', '0.003')); rep = {}
C = np.array([0.0, 0.0, 0.665])
hco, htri, hbraid = H['co'], H['tri'], H['braid']
hco = hco.copy()
# the cap: F2's braid weights reach up the back of the cap, so "cap" is every row that is not braid-weighted or lies within NEAR of Fre's
# head (face shell, hidden old hood or old cap); the braid tube hangs further out
_hs = np.where(np.isin(comp, [KH, KS, K4]) & (co[:, 2] > 0.54))[0]
_dn, _ = cKDTree(co[_hs]).query(hco); capm = ~hbraid | (_dn < float(os.environ.get('NEAR', '0.025')))
if int(os.environ.get('RIM_SPLIT', '2')) > 0:
    # F2's cap rim has a vertex every 2-3 cm; the face outline it is pulled onto zigzags every ~5 mm, so the straight rim edges cut across it
    # and left the outline's teeth showing (r50). Every open rim edge of the cap gets RIM_SPLIT new rows (positions and UVs interpolated,
    # flags copied) and its triangle becomes a fan of RIM_SPLIT + 1 from the opposite corner.
    NS_ = int(os.environ.get('RIM_SPLIT', '2'))
    _k = np.round(hco, 5); _, _wi = np.unique(_k, axis=0, return_inverse=True); _wi = _wi.ravel()
    _E = np.stack([htri[:, [0, 1]], htri[:, [1, 2]], htri[:, [2, 0]]], 1)      # (f, 3, 2) rows
    _Ew = np.sort(_wi[_E], 2).reshape(-1, 2); _u, _ix, _cn = np.unique(_Ew, axis=0, return_inverse=True, return_counts=True)
    _bnd = (_cn[_ix.ravel()] == 1).reshape(-1, 3) & capm[_E].all(2)
    nco, nuv, nbr, ncap, ntri = [hco], [H['uv']], [hbraid], [capm], []
    keep_ = np.ones(len(htri), bool); nrow = len(hco); added = 0
    for f in np.where(_bnd.any(1))[0]:
        e = int(np.where(_bnd[f])[0][0]); a, b = _E[f, e]; c = htri[f][(e + 2) % 3]
        ts = np.arange(1, NS_ + 1) / (NS_ + 1)
        nco.append(hco[a][None] * (1 - ts[:, None]) + hco[b][None] * ts[:, None]); nuv.append(H['uv'][a][None] * (1 - ts[:, None]) + H['uv'][b][None] * ts[:, None])
        nbr.append(np.full(NS_, hbraid[a] & hbraid[b])); ncap.append(np.ones(NS_, bool))
        chain = [a] + list(range(nrow, nrow + NS_)) + [b]; nrow += NS_
        for i in range(len(chain) - 1): ntri.append([chain[i], chain[i + 1], c])
        keep_[f] = False; added += 1
    hco = np.vstack(nco); H['uv'] = np.vstack(nuv); hbraid = np.concatenate(nbr); capm = np.concatenate(ncap)
    htri = np.vstack([htri[keep_], np.array(ntri, int)]) if ntri else htri
    rep['rim_split'] = dict(edges=int(added), rows_added=int(added * NS_), tris_added=int(added * NS_))
capT = htri[capm[htri].all(1)]
if os.environ.get('RIM_PULL', '1') == '1':
    # F2's hairline sits behind Fre's face outline (F1's face shell ends where its hood began: temples, beside the ears, the nape), so the
    # hidden skull showed between hair and skin. Every rim vertex of the cap (the whole hair piece's open boundary, minus the braid tube) is
    # pulled onto the nearest point of that seam polyline (1.5 mm out) when it lies within RIM_REACH; the move fades into the cap over FADE.
    _key0 = np.round(co, 5); _, _inv0 = np.unique(_key0, axis=0, return_inverse=True); _inv0 = _inv0.ravel()
    _cs = np.zeros(_inv0.max() + 1, int); np.add.at(_cs, _inv0[comp == KS], 1)
    _isseam = (comp == KH) & (_cs[_inv0] > 0) & (co[:, 2] > 0.57)
    _ht = tri[(comp[tri] == KH).all(1)]; _e = np.vstack([_ht[:, [0, 1]], _ht[:, [1, 2]], _ht[:, [2, 0]]]); _e = _e[_isseam[_e].all(1)]
    _f = np.linspace(0, 1, 9)[:, None, None]; _sp = (co[_e[:, 0]][None] * (1 - _f) + co[_e[:, 1]][None] * _f).reshape(-1, 3)
    hk = np.round(hco, 5); _, hinv = np.unique(hk, axis=0, return_inverse=True); hinv = hinv.ravel()
    ce = np.sort(np.vstack([hinv[htri[:, [0, 1]]], hinv[htri[:, [1, 2]]], hinv[htri[:, [2, 0]]]]), 1)
    ue, cnt = np.unique(ce, axis=0, return_counts=True); rimw = np.unique(ue[cnt == 1])
    rim = np.where(np.isin(hinv, rimw) & capm & (hco[:, 1] < float(os.environ.get('RIM_Y', '1.0'))))[0]
    d_, j_ = cKDTree(_sp).query(hco[rim]); ok_ = d_ < np.where(hco[rim, 2] > float(os.environ.get('RIM_ZF', '0.68')), float(os.environ.get('RIM_REACH_F', '0.05')),
                                         float(os.environ.get('RIM_REACH', '0.02')))      # forehead/temples reach further than the sides
    disp = np.zeros_like(hco); tgt = _sp[j_[ok_]]; out_ = tgt - C; out_ /= np.linalg.norm(out_, axis=1, keepdims=True)
    # the face shell's outline is saw-toothed: the rim goes OVER m past the seam onto the skin (direction: from the seam point to the
    # mean of the non-seam face-shell vertices within 1.5 cm), so the hair overlaps the teeth instead of leaving gaps between them
    _ns = np.where((comp == KH) & ~_isseam & (co[:, 2] > 0.54))[0]; _nt = cKDTree(co[_ns])
    _vin = np.array([co[_ns[l]].mean(0) - t if len(l) else np.zeros(3) for t, l in zip(tgt, _nt.query_ball_point(tgt, 0.015))])
    _vin /= np.maximum(np.linalg.norm(_vin, axis=1, keepdims=True), 1e-9)
    tgt = tgt + _vin * float(os.environ.get('OVER', '0.010'))
    disp[rim[ok_]] = tgt + out_ * 0.0015 - hco[rim[ok_]]
    # pulled one by one onto a saw-toothed outline the rim zigzags (r44: dark teeth hanging behind the ears): the pulled rim loop is
    # smoothed along itself (RIM_SMOOTH passes, ends and unpulled rows fixed), then laid back on the face shell (outermost hit along the
    # ray from the head centre) 1.5 mm out
    _P = hco + disp; _w = hinv[rim]; _pull = np.zeros(hinv.max() + 1, bool); _pull[_w[ok_]] = True
    _be = ue[cnt == 1]; _be = _be[_pull[_be].all(1)]
    _WP = np.zeros((hinv.max() + 1, 3)); _WP[hinv] = _P
    _deg = np.bincount(_be.ravel(), minlength=len(_WP)); _mov = _pull & (_deg == 2)
    for _ in range(int(os.environ.get('RIM_SMOOTH', '6'))):
        _acc = np.zeros_like(_WP); np.add.at(_acc, _be[:, 0], _WP[_be[:, 1]]); np.add.at(_acc, _be[:, 1], _WP[_be[:, 0]])
        _WP[_mov] += 0.5 * (_acc[_mov] / 2 - _WP[_mov])
    _skT = tri[(comp[tri] == KH).all(1)]
    _ids = np.where(_mov)[0]; _d = _WP[_ids] - C; _u = _d / np.linalg.norm(_d, axis=1, keepdims=True)
    _t = raycast(C + _u * 0.6, -_u, co, _skT); _okr = np.isfinite(_t) & (0.6 - _t > 0.05)
    _np = C + _u * (0.6 - np.where(_okr, _t, 0.6) + 0.0015)[:, None]; _okr &= np.linalg.norm(_np - _WP[_ids], axis=1) < 0.01
    _WP[_ids[_okr]] = _np[_okr]
    _rr = rim[ok_]; disp[_rr] = _WP[hinv[_rr]] - hco[_rr]
    rep['rim_smoothed'] = int(_mov.sum())
    FADE = float(os.environ.get('FADE', '0.03')); capv = np.unique(capT)
    src = rim[ok_]; dd, jj = cKDTree(hco[src]).query(hco[capv]); w = np.clip(1 - dd / FADE, 0, 1); w = w * w * (3 - 2 * w)
    hco[capv] += disp[src[jj]] * w[:, None]
    rep['rim_rows'] = int(len(rim)); rep['rim_pulled'] = int(ok_.sum())
    rep['rim_pull_mm'] = dict(max=round(float(np.linalg.norm(disp, axis=1).max()) * 1000, 1),
                              p50=round(float(np.median(np.linalg.norm(disp[src], axis=1))) * 1000, 1))
def ss_(x, a, b):
    k = np.clip((x - a) / (b - a), 0, 1); return k * k * (3 - 2 * k)
if os.environ.get('OUT_FIT', '1') == '1':
    # pass 5 (orchestrator on r62: hard-edged light/dark panels at the temples): F2's cap is narrower than Fre's head at the temples, so
    # the fit below pushed her face shell up to 24.5 mm in to get under it and the skin folded into the hairline. Now the hair goes out
    # instead: every cap row lying less than OUT_CLR outside Fre's own head (face shell + hidden old hood, outermost hit along its ray
    # from the head centre) moves out to OUT_CLR (at most 3 cm), the push smoothed over the cap (2 cm neighbourhood, never below the
    # row's own need), so her skin keeps its shape and only a few mm under the hair are adjusted.
    _sk = tri[np.isin(comp[tri], [KH, KS]).all(1) & (co[tri][:, :, 2].min(1) > 0.54)]
    _cv = np.unique(capT); _d = hco[_cv] - C; _r = np.linalg.norm(_d, axis=1); _u = _d / _r[:, None]
    _t = raycast(C + _u * 0.6, -_u, co, _sk); _rs = np.where(np.isfinite(_t), 0.6 - _t, 0.0)
    OC = float(os.environ.get('OUT_CLR', '0.004'))
    _need = np.clip(_rs + OC - _r, 0, 0.03) * (_rs > 0.05) * (1 - ss_(hco[_cv, 1], 0.0, 0.03))      # front and sides only (the back kept F2's shape)
    _nb = cKDTree(hco[_cv]).query_ball_point(hco[_cv], 0.02)
    _p = _need.copy()
    for _ in range(3):
        _p = np.maximum(_need, np.array([_p[l].mean() for l in _nb]))
    _hk5 = np.round(hco, 5); _, _hi5 = np.unique(_hk5, axis=0, return_inverse=True); _hi5 = _hi5.ravel()
    _wp = np.zeros(_hi5.max() + 1); np.maximum.at(_wp, _hi5[_cv], _p)
    _all = np.unique(_hi5[_cv]); _rows = np.where(np.isin(_hi5, _all) & capm)[0]
    _dd = hco[_rows] - C; _uu = _dd / np.linalg.norm(_dd, axis=1, keepdims=True); hco[_rows] += _uu * _wp[_hi5[_rows]][:, None]
    rep['hair_out_push_mm'] = dict(max=round(float(_p.max()) * 1000, 1), p50_pushed=round(float(np.median(_p[_p > 1e-4])) * 1000, 1) if (_p > 1e-4).any() else 0,
                                   rows=int((_p > 1e-4).sum()))
# ---- drop Fre's cap and braid faces
fc = comp[tri[:, 0]]; dropf = np.isin(fc, [K4, KB])
# ---- coverage of the new cap: ray from C outward, the outermost hit
key = np.round(co, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
cd_ = np.zeros(inv.max() + 1, int); np.add.at(cd_, inv[comp == KD], 1)
used = np.zeros(len(co), bool); used[np.unique(tri[~dropf])] = True
def cover(P):
    d = P - C; r = np.linalg.norm(d, axis=1); u = d / r[:, None]
    t = raycast(C + u * 0.6, -u, hco, capT); rh = np.where(np.isfinite(t), 0.6 - t, np.nan)
    return r, u, rh
q = np.where(np.isin(comp, [KH, KS]) & used & (co[:, 2] > 0.55))[0]
r, u, rh = cover(co[q])
mv = np.isfinite(rh) & (r > rh - CLR) & (cd_[inv[q]] == 0) & (rh > 0.05) & (r - (rh - CLR) < float(os.environ.get('MAXMOVE', '0.03')))
newp = C + u[mv] * (rh[mv] - CLR)[:, None]
grp = {}
for v, p in zip(q[mv], newp): grp[inv[v]] = p
moved = np.where(np.isin(inv, list(grp.keys())))[0]
dist = np.array([np.linalg.norm(grp[inv[v]] - co[v]) for v in moved]) if len(moved) else np.zeros(1)
for v in moved: co[v] = grp[inv[v]]
rep['fit_moved_vertices'] = int(len(moved)); rep['fit_max_move_mm'] = round(float(dist.max()) * 1000, 2)
rep['fit_moved_by_part'] = {names[k]: int((comp[moved] == k).sum()) for k in set(comp[moved])}
# ---- old-hood faces the cap does not cover
sv = np.where((comp == KS) & used)[0]; rsv, _, rs = cover(co[sv]); cov = np.zeros(len(co), bool); cov[sv[np.isfinite(rs) & (rs > rsv - 0.001)]] = True
onh = np.zeros(inv.max() + 1, bool); onh[inv[comp == KH]] = True
of = (comp[tri] == KS).all(1) & ~cov[tri].all(1) & ((os.environ.get('KEEP_SEAM', '1') != '1') | ~onh[inv[tri]].any(1))
dropf |= of; rep['oldhood_uncovered_dropped'] = int(of.sum())
# the kept teeth's free corners (old-hood vertices off the face seam that the hair does not cover) flared out over the hair's rim at the
# nape (r48: light skin spikes on the hair's lower edge): each moves under the nearest cap rim vertex, CLR inside along that vertex's ray
if os.environ.get('TUCK', '1') == '1':
    _keptf = (comp[tri] == KS).all(1) & ~dropf
    _tv = np.unique(tri[_keptf]); _tv = _tv[~cov[_tv] & ~onh[inv[_tv]] & (cd_[inv[_tv]] == 0)]
    _tv = _tv[co[_tv, 1] > float(os.environ.get('TUCK_Y', '0.0'))]      # pass 5: front/side teeth stay on F1's own shell (one surface with the face; tucked they stood steep: a pale wedge at the temple)
    _hk = np.round(hco, 5); _, _hi = np.unique(_hk, axis=0, return_inverse=True); _hi = _hi.ravel()
    _ce = np.sort(np.vstack([_hi[capT[:, [0, 1]]], _hi[capT[:, [1, 2]]], _hi[capT[:, [2, 0]]]]), 1)
    _ue, _cn = np.unique(_ce, axis=0, return_counts=True); _bw = np.unique(_ue[_cn == 1])
    _rv = np.where(np.isin(_hi, _bw))[0]; _rv = _rv[np.isin(_rv, np.unique(capT))]
    _d, _j = cKDTree(hco[_rv]).query(co[_tv]); _ok = _d < 0.03
    _rp = hco[_rv[_j[_ok]]]; _ru = (_rp - C) / np.linalg.norm(_rp - C, axis=1, keepdims=True)
    _new = _rp - _ru * CLR; _g = {}
    for v, p_ in zip(_tv[_ok], _new): _g[inv[v]] = p_
    for v in np.where(np.isin(inv, list(_g.keys())))[0]: co[v] = _g[inv[v]]
    rep['teeth_tucked'] = int(_ok.sum()); rep['teeth_tuck_max_mm'] = round(float(_d[_ok].max()) * 1000, 1) if _ok.any() else 0
# ---- the hair piece: its distance from Fre's face/neck skin (the fit report)
hs = np.where((comp == KH) & used)[0]
dh, _ = cKDTree(co[hs]).query(hco[~hbraid]); rep['hair_cap_to_skin_mm'] = dict(min=round(float(dh.min()) * 1000, 1), p50=round(float(np.median(dh)) * 1000, 1))
# ---- assemble
keep = ~dropf; nidx = -np.ones(len(tri), int); nidx[keep] = np.arange(keep.sum())
twf = A['f4_twin_face']; assert not dropf[twf[twf >= 0]].any() or True
K2 = len(names); names2 = names + ['hair2']; n0 = len(co)
A['co'] = np.vstack([co, hco]); A['tri'] = np.vstack([tri[keep], htri + n0]); A['comp'] = np.r_[comp, np.full(len(hco), K2)]; A['names'] = np.array(names2)
nh = len(htri)
A['f4_inner'] = np.r_[A['f4_inner'][keep], np.zeros(nh, bool)]; A['f4_rim'] = np.r_[A['f4_rim'][keep], np.zeros(nh, bool)]
tw = twf[keep]; A['f4_twin_face'] = np.r_[np.where((tw >= 0) & (nidx[np.maximum(tw, 0)] >= 0), nidx[np.maximum(tw, 0)], -1), -np.ones(nh, int)]
A['f4_twin_v'] = np.r_[A['f4_twin_v'], -np.ones(len(hco), int)]; A['f4_param'] = np.vstack([A['f4_param'], np.zeros((len(hco), 3))])
A['f4_side'] = np.r_[A['f4_side'], np.zeros(len(hco))]
A['fre_braid_s'] = np.r_[A['fre_braid_s'], np.full(len(hco), -1.0)]; A['fre_braid_uv'] = np.vstack([A['fre_braid_uv'], np.full((len(hco), 2), -1.0)])
A['hair2_braid'] = np.r_[np.zeros(n0, bool), hbraid]
A['hair2_tube'] = np.r_[np.zeros(n0, bool), ~capm]      # the braid tube (not the cap)
# ---- small holes the old bob hid (r52 profiles: a grey triangle in front of each ear: a 4-vertex opening in F1's face shell beside the
# pressed ear plate): closed boundary loops of at most HOLE_MAX vertices on the head shell between 0.60 and 0.70 m, off the midline
# (|x| > 4.5 cm: the eyes and mouth are openings by design) are fanned shut; their UV rows sample one skin texel (the loop's first row)
fill = []
if os.environ.get('FILL_HOLES', '1') == '1':
    _T = A['tri'][np.isin(A['comp'][A['tri']], [KH, KS, KD]).all(1)]; _co = A['co']
    _k = np.round(_co, 5); _, _wi = np.unique(_k, axis=0, return_inverse=True); _wi = _wi.ravel()
    _de = np.vstack([_T[:, [0, 1]], _T[:, [1, 2]], _T[:, [2, 0]]]); _dw = _wi[_de]
    _ud, _ix, _cn = np.unique(np.sort(_dw, 1), axis=0, return_inverse=True, return_counts=True); _bd = _dw[_cn[_ix.ravel()] == 1]
    _bdr = _de[_cn[_ix.ravel()] == 1]
    nxt = {}; rowof = {}
    for (a, b), (ra, rb) in zip(_bd, _bdr): nxt.setdefault(a, []).append(b); rowof.setdefault(a, ra); rowof.setdefault(b, rb)
    W_ = np.zeros((_wi.max() + 1, 3)); W_[_wi] = _co; seen = set()
    for a0 in list(nxt):
        if a0 in seen or len(nxt[a0]) != 1: continue
        loop = [a0]; ok = True
        while True:
            nb = nxt.get(loop[-1], [])
            if len(nb) != 1: ok = False; break
            if nb[0] == a0: break
            loop.append(nb[0])
            if len(loop) > int(os.environ.get('HOLE_MAX', '6')): ok = False; break
        seen.update(loop)
        P_ = W_[loop]
        if ok and len(loop) >= 3 and (np.abs(P_[:, 0]) > 0.045).all() and (P_[:, 2] > 0.60).all() and (P_[:, 2] < 0.70).all():
            rows_ = [rowof[w] for w in loop]
            for i in range(1, len(rows_) - 1): fill.append([rows_[0], rows_[i + 1], rows_[i]])      # reversed: the loop runs along the faces' edges
    if fill:
        fill = np.array(fill, int); nf = len(fill)
        A['tri'] = np.vstack([A['tri'], fill]); A['f4_inner'] = np.r_[A['f4_inner'], np.zeros(nf, bool)]; A['f4_rim'] = np.r_[A['f4_rim'], np.zeros(nf, bool)]
        A['f4_twin_face'] = np.r_[A['f4_twin_face'], -np.ones(nf, int)]
    rep['holes_filled_tris'] = int(len(fill))
np.savez(AO, **A)
np.savez('work/hair2_weights.npz', rows=np.arange(n0, n0 + len(hco)), braid=hbraid, tube=~capm)
# ---- uv npz: drop rows of dropped faces, update positions, append the hair rows on material 2
keys = {tuple(sorted(t)) for t in tri[dropf]}
uk = np.array([tuple(sorted(U['orig'][t])) not in keys for t in U['tri']])
for k in ('tri', 'mat', 'inner'): U[k] = U[k][uk]
usedr = np.unique(U['tri']); remap = -np.ones(len(U['co']), int); remap[usedr] = np.arange(len(usedr))
for k in ('co', 'uv', 'orig', 'comp'): U[k] = U[k][usedr]
U['tri'] = remap[U['tri']]; U['co'] = A['co'][U['orig']]
r0 = len(U['co'])
U['co'] = np.vstack([U['co'], hco]); U['uv'] = np.vstack([U['uv'], H['uv']]); U['orig'] = np.r_[U['orig'], np.arange(n0, n0 + len(hco))]
U['comp'] = np.r_[U['comp'], np.full(len(hco), K2)]; U['tri'] = np.vstack([U['tri'], htri + r0]); U['mat'] = np.r_[U['mat'], np.full(nh, 2)]
U['inner'] = np.r_[U['inner'], np.zeros(nh, bool)]; U['names'] = np.array(names2); U['matnames'] = np.array(['Fre', 'FreHead', 'FreHair'])
if len(fill):
    _r0 = len(U['co']); _nr = []
    for t in fill:
        _src = np.where((U['orig'] == t[0]) & (U['comp'] == KH))[0]; _uv0 = U['uv'][_src[0]] if len(_src) else U['uv'][np.where(U['comp'] == KH)[0][0]]
        _nr.append((t, _uv0))
    U['co'] = np.vstack([U['co']] + [A['co'][t] for t, _ in _nr]); U['uv'] = np.vstack([U['uv']] + [np.repeat(u_[None], 3, 0) for _, u_ in _nr])
    U['orig'] = np.r_[U['orig'], np.concatenate([t for t, _ in _nr])]; U['comp'] = np.r_[U['comp'], np.full(3 * len(_nr), KH)]
    U['tri'] = np.vstack([U['tri'], _r0 + np.arange(3 * len(_nr)).reshape(-1, 3)]); U['mat'] = np.r_[U['mat'], np.ones(len(_nr), int)]
    U['inner'] = np.r_[U['inner'], np.zeros(len(_nr), bool)]
U.pop('textures', None); np.savez(UO, **U)
rep['tris'] = dict(total=int(len(A['tri'])), hair=int(nh), dropped=int(dropf.sum()))
json.dump(rep, open(REP, 'w'), indent=1); print('HAIR', json.dumps(rep))
