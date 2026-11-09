#!/usr/bin/env python3
"""Fre pass 6 (orchestrator on r72: pale angular wedges at the temples, faceted planes on the cheek sides and dark shards at the hair
edge below the ears, in front, 3/4, low 3/4 and Talk; the paint was already smooth, so geometry). With the old bob gone, the strip of
F1's face shell it hid (its folded outline, the old hood's teeth and the pressed ear plates) is bare. That strip is rebuilt on both
sides: every face-shell / old-hood face whose centroid lies in the side box (|x| > X0, Y0 < y < Y1, Z0 < z < Z1: behind the brow tail,
from the hairline back past the ear and down to the jaw angle) is deleted, and the hole is filled with an evenly spaced patch:
- shape: a smooth surface r(phi, psi) about the head centre (thin-plate RBF, smoothed) fitted to the kept face shell round the hole and
  to the hair's inner side 4 mm in, both sides pooled mirrored so the patch is symmetric about the midline; inside the hair it stays at
  least CLR under the cap;
- topology: the hole's own boundary vertices (exact positions of the kept face: the weld) plus interior points on a SP grid, Delaunay in
  (phi, psi), kept where a deleted face covered that spot, oriented outward;
- UVs: one new chart per side in a free square of the head texture (the old cap's texels), linear in (phi, psi) at about the face's
  texel density; paint comes later from the clean cheek skin (temple_skin_fre.py treats the chart as repainted).
New rows are face shell ('head'), so weights_fre.py gives them the head's own weights (Head above the jaw line).
Args: <asm in> <uv in> <asm out> <uv out>   (project folder)"""
import sys, os, json
import numpy as np
from scipy.spatial import cKDTree, Delaunay
from scipy.interpolate import RBFInterpolator
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from geo4 import raycast
AI, UI, AO, UO = sys.argv[1:5]
A = dict(np.load(AI)); U = dict(np.load(UI)); names = [str(x) for x in A['names']]
KH, KS, K2 = names.index('head'), names.index('scarf'), names.index('hair2')
X0, Y0, Y1, Z0, Z1 = (float(os.environ.get(k, v)) for k, v in (('SX0', '0.048'), ('SY0', '-0.078'), ('SY1', '0.035'), ('SZ0', '0.585'), ('SZ1', '0.76')))
SP = float(os.environ.get('SP', '0.007')); CLR = 0.003; C = np.array([0.0, 0.0, 0.665])
co, tri, comp = A['co'], A['tri'], A['comp']; nv0 = len(co)
def inbox(p): return (np.abs(p[:, 0]) > X0) & (p[:, 1] > Y0) & (p[:, 1] < Y1) & (p[:, 2] > Z0) & (p[:, 2] < Z1)
fsel = np.isin(comp[tri], [KH, KS]).all(1) & inbox(co[tri].reshape(-1, 3)).reshape(-1, 3).any(1)      # any corner in the box
# the old hood's flaps reach out of the box (r73 parts render): any old-hood face with a corner in a box 2 cm larger goes too
_big = (np.abs(co[:, 0]) > X0 - 0.01) & (co[:, 1] > Y0) & (co[:, 1] < Y1 + 0.02) & (co[:, 2] > Z0 - 0.01) & (co[:, 2] < Z1 + 0.02)
fsel |= (comp[tri] == KS).all(1) & _big[tri].any(1)
# and every old-hood face on the sides the hair does not cover (its folded flaps showed below the rim, r72)
_capT0 = tri[(comp[tri] == K2).all(1) & ~A['hair2_tube'][tri].any(1)]
_cen = co[tri].mean(1); _d = _cen - np.array([0.0, 0.0, 0.665]); _r = np.linalg.norm(_d, axis=1); _u = _d / _r[:, None]
_sc = np.where((comp[tri] == KS).all(1) & (np.abs(_cen[:, 0]) > 0.03) & (_cen[:, 2] > 0.56))[0]
_t = raycast(np.array([0.0, 0.0, 0.665]) + _u[_sc] * 0.6, -_u[_sc], co, _capT0); _cov = np.isfinite(_t) & (0.6 - _t > _r[_sc] - 0.001)
fsel[_sc[~_cov]] = True
capT = tri[(comp[tri] == K2).all(1) & ~A['hair2_tube'][tri].any(1)]
def sph(p):
    d = p - C; r = np.linalg.norm(d, axis=1); return np.arctan2(d[:, 0], -d[:, 1]), np.arcsin(np.clip(d[:, 2] / r, -1, 1)), r
def unsph(ph, ps, r):
    return C + np.c_[np.sin(ph) * np.cos(ps), -np.cos(ph) * np.cos(ps), np.sin(ps)] * r[:, None]
def hair_r(ph, ps):
    u = unsph(ph, ps, np.ones(len(ph))) - C; t = raycast(C + u * 0.6, -u, co, capT); return np.where(np.isfinite(t), 0.6 - t, np.inf)
# welded view of the kept surface
key = np.round(co, 5); _, wi = np.unique(key, axis=0, return_inverse=True); wi = wi.ravel()
kept = np.isin(comp[tri], [KH, KS]).all(1) & ~fsel
used_k = np.zeros(wi.max() + 1, bool); used_k[wi[tri[kept]].ravel()] = True
dv = np.unique(tri[fsel]); bnd = dv[used_k[wi[dv]]]      # deleted faces' vertices still used by kept faces: the weld
rep = {'deleted_faces': int(fsel.sum())}
newco, newtri, newuv_side = [], [], []
# head-set UV occupancy after the deletion (mat 1), for free squares
ut, um = U['tri'], U['mat']; uco = A['co'][U['orig']]
udel = (um == 1) & np.isin(U['comp'][ut], [KH, KS]).all(1) & inbox(uco[ut].mean(1))
R = 512; occ = np.zeros((R, R), bool)
for t in ut[(um == 1) & ~udel]:
    q = U['uv'][t] * R; x0, y0 = np.maximum(np.floor(q.min(0)).astype(int) - 2, 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int) + 2, R - 1)
    occ[y0:y1 + 1, x0:x1 + 1] = True      # bounding boxes: conservative
from scipy.ndimage import distance_transform_edt
free = distance_transform_edt(~occ)
patches = []
for side in (1, -1):
    fs = fsel & (np.sign(co[tri].mean(1)[:, 0]) == side)
    if not fs.any(): continue
    ph_f, ps_f, _ = sph(co[tri[fs]].reshape(-1, 3)); PT = np.c_[ph_f, ps_f].reshape(-1, 3, 2)
    b = bnd[np.sign(co[bnd, 0]) == side]; bph, bps, br = sph(co[b])
    # samples: kept face shell within 3 cm of the hole (and its mirror), hair inner side 4 mm in over the hole
    kv = np.unique(tri[kept & (comp[tri] == KH).all(1)].ravel()); dk, _ = cKDTree(co[b]).query(co[kv]); kv = kv[dk < 0.03]
    S = np.vstack([co[kv], co[kv] * [-1, 1, 1]]); sph_, sps_, sr = sph(S)
    gph = np.linspace(ph_f.min(), ph_f.max(), 24); gps = np.linspace(ps_f.min(), ps_f.max(), 24); GP, GS = np.meshgrid(gph, gps)
    hr = hair_r(GP.ravel(), GS.ravel()); hm = np.isfinite(hr)
    sph2 = np.r_[np.abs(sph_), np.abs(GP.ravel()[hm])]; sps2 = np.r_[sps_, GS.ravel()[hm]]; sr2 = np.r_[sr, hr[hm] - 0.004]
    # mirrored pooling: fit in |phi| so both sides share one surface
    keep_s = (sph2 > np.abs(ph_f).min() - 0.4) & (sph2 < np.abs(ph_f).max() + 0.4) & (sps2 > ps_f.min() - 0.4) & (sps2 < ps_f.max() + 0.4)
    rbf = RBFInterpolator(np.c_[np.abs(sph2[keep_s]), sps2[keep_s]], sr2[keep_s], kernel='thin_plate_spline', smoothing=float(os.environ.get('SMOOTH', '0.3')), degree=1)
    # interior grid (spacing SP at the local radius) inside the deleted faces' footprint
    rr = np.median(br); st = SP / rr
    IP, IS = np.meshgrid(np.arange(ph_f.min(), ph_f.max(), st), np.arange(ps_f.min(), ps_f.max(), st))
    ip = np.c_[IP.ravel(), IS.ravel()]
    # the hole in direction space: inside the deleted faces' (phi, psi) range and not covered by a kept face-shell face (ray from the
    # head centre meets no kept head face); folded deleted faces do not matter
    keptT = tri[kept]      # kept face shell and hidden skull
    phr = (ph_f.min(), ph_f.max()); psr = (ps_f.min(), ps_f.max())
    keptH = tri[kept & (comp[tri] == KH).all(1)]
    def inside(pts):
        u = unsph(pts[:, 0], pts[:, 1], np.ones(len(pts))) - C
        q = C + u * 0.085; res = (np.abs(q[:, 0]) > X0 - 0.012) & (q[:, 1] > Y0 - 0.004) & (q[:, 1] < Y1 + 0.004) & (q[:, 2] > Z0 - 0.004) & (q[:, 2] < Z1 + 0.004)
        res &= np.sign(q[:, 0]) == side
        t = raycast(C + u * 0.6, -u, co, keptH); hitf = np.isfinite(t) & (0.6 - t > 0.05)
        return res & ~hitf
    ip = ip[inside(ip)]
    db, _ = cKDTree(np.c_[bph, bps]).query(ip); ip = ip[db > 0.6 * st]
    ir = rbf(np.c_[np.abs(ip[:, 0]), ip[:, 1]]); hr2 = hair_r(ip[:, 0], ip[:, 1]); ir = np.minimum(ir, hr2 - CLR)
    P2 = np.vstack([np.c_[bph, bps], ip]); P3 = np.vstack([co[b], unsph(ip[:, 0], ip[:, 1], ir)])
    tri2 = Delaunay(P2).simplices; cen2 = P2[tri2].mean(1)
    ok = inside(cen2)
    el = np.max(np.linalg.norm(P3[tri2] - P3[np.roll(tri2, 1, 1)], axis=2), 1); ok &= el < 3.0 * SP
    tri2 = tri2[ok]
    fn = np.cross(P3[tri2[:, 1]] - P3[tri2[:, 0]], P3[tri2[:, 2]] - P3[tri2[:, 0]]); out = ((P3[tri2].mean(1) - C) * fn).sum(1) < 0
    tri2[out] = tri2[out][:, [0, 2, 1]]
    # rows: boundary points reuse their asm vertex, interior points are new asm rows
    nb = len(b); ids = np.r_[b, nv0 + sum(len(x) for x in newco) + np.arange(len(ip))]
    newco.append(P3[nb:]); newtri.append(ids[tri2])
    # UV chart: a free square, linear in (phi, psi)
    span = np.array([np.ptp(P2[:, 0]), np.ptp(P2[:, 1])]) * rr
    dens = float(os.environ.get('UVDENS', '600'))      # px per m at 1024
    need = int(np.ceil(span.max() * dens / 1024 * R)) + 4
    cand = np.argwhere(free > need / 2 + 1)
    if not len(cand): raise SystemExit('no free UV square of %d px' % need)
    cy, cx = cand[np.argmax(free[cand[:, 0], cand[:, 1]])]
    occ_box = (slice(max(cy - need, 0), cy + need), slice(max(cx - need, 0), cx + need)); free[occ_box] = 0
    s = (need - 4) / R / max(np.ptp(P2[:, 0]), np.ptp(P2[:, 1]))
    uvp = np.c_[(P2[:, 0] - P2[:, 0].mean()) * s * side + cx / R, (P2[:, 1] - P2[:, 1].mean()) * s + cy / R]
    patches.append(dict(ids=ids, tri=ids[tri2], uv=uvp, P3=P3))
    rep[f'side{side:+d}'] = dict(boundary=int(nb), interior=int(len(ip)), tris=int(len(tri2)), uv_px=need * 1024 // R)
newco = np.vstack(newco) if newco else np.zeros((0, 3)); nnew = len(newco)
# ---- asm
keepf = ~fsel; A['co'] = np.vstack([co, newco]); A['comp'] = np.r_[comp, np.full(nnew, KH)]
for k, v in list(A.items()):
    if k in ('co', 'comp', 'tri'): continue
    if hasattr(v, 'shape') and v.shape and v.shape[0] == nv0:
        fill = -1 if k in ('f4_twin_v', 'fre_braid_s', 'fre_braid_uv') else 0
        A[k] = np.concatenate([v, np.full((nnew,) + v.shape[1:], fill, v.dtype)])
nf0 = len(tri); addf = np.vstack([p['tri'] for p in patches])
A['tri'] = np.vstack([tri[keepf], addf])
for k in ('f4_inner', 'f4_rim'): A[k] = np.r_[A[k][keepf], np.zeros(len(addf), bool)]
tw = A['f4_twin_face']; nidx = -np.ones(nf0, int); nidx[keepf] = np.arange(keepf.sum())
twk = tw[keepf]; A['f4_twin_face'] = np.r_[np.where(twk >= 0, nidx[np.maximum(twk, 0)], -1), -np.ones(len(addf), int)]
np.savez(AO, **A)
# ---- uv npz: drop the deleted faces, add each patch with its own rows
U['tri'] = ut[~udel]; U['mat'] = um[~udel]; U['inner'] = U['inner'][~udel]
for p in patches:
    r0 = len(U['co']); U['co'] = np.vstack([U['co'], A['co'][p['ids']]]); U['uv'] = np.vstack([U['uv'], p['uv']])
    U['orig'] = np.r_[U['orig'], p['ids']]; U['comp'] = np.r_[U['comp'], np.full(len(p['ids']), KH)]
    loc = {g: i for i, g in enumerate(p['ids'])}; lt = np.vectorize(loc.get)(p['tri'])
    U['tri'] = np.vstack([U['tri'], r0 + lt]); U['mat'] = np.r_[U['mat'], np.ones(len(lt), int)]; U['inner'] = np.r_[U['inner'], np.zeros(len(lt), bool)]
used = np.unique(U['tri']); remap = -np.ones(len(U['co']), int); remap[used] = np.arange(len(used))
for k in ('co', 'uv', 'orig', 'comp'): U[k] = U[k][used]
U['tri'] = remap[U['tri']]; U['co'] = A['co'][U['orig']]
np.savez(UO, **U)
rep['tris'] = dict(asm=int(len(A['tri'])), uv=int(len(U['tri'])), added=int(len(addf)))
json.dump(rep, open('work/strip_report.json', 'w'), indent=1); print('STRIP', json.dumps(rep))
