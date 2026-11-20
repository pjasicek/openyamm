#!/usr/bin/env python3
"""Keep / group / lining sets per face of the installed LOD0 (before/mm9_honkm.glb, primitive order HonkM_A, HonkMHead) for
mpqem.py, prio-1 relaxed keep set (REDUCTION_BRIEF_20261104). Male copy of mm9_honkf_reduce_claude/scripts/make_sets.py; classes
from welded connected pieces, bone weights, UV area and paint (no part labels survive in the creature's masters):
  HonkM_A (body set): lining (zero UV area: robe_lining.py's lining, hem rim and top cap, sleeve_lining.py's sleeve linings,
            all on one dark texel), lined (outer faces with a lining face 2-25 mm behind them), robe (the two big pieces: upper
            robe with sleeves, robe tube), boots (the two Foot pieces), medallion (the Spine3 disc), collar (the Neck-weighted
            neckline piece with the thin silver chain), small (buckle);
  HonkMHead (head + hands set): face (the head shell's skin paint, beard and moustache: face, ears, neck), hairshell (the head
            shell's hair paint behind the face: tier A brown, below HAIR_LUM, outside the face box), eyes (every small head
            piece: eyeballs, mouth/teeth), hands (hand pieces: faces mostly on Hand/finger bones), forearm (the forearm skin and
            graft stub of the hand pieces).
Exact: face, eyes, collar, pieces of up to SMALL faces, soles (boot faces below SOLE m), lining + lined (LINED_KEEP=1), the
hand-graft junction (hand-piece faces within JUNC m of the wrist joint), the hairline (hairshell faces within HAIRLINE m of
face skin), the neck seam (non-face faces within SEAM m of the face/hair paint border), the hat seat (hairshell faces within
HATR m of either hat at bind: mm9_honkhat.glb and mm9_elderhonkhat.glb on Bip01 Head), extra keeps (KEEP_EXTRA=a,b:
work/<a>.npy).
Groups: 1 hands, 2 hairshell, 3 sleeves (robe on the arms), 5 boots, 6 medallion, 7 forearm, 8 robe wall under the lining (LINED_KEEP=0); 0 (ladder ratio):
robe. Usage: make_sets.py <tag> -> work/glb_sets_<tag>.npz (keep, group, lining, lined, cls, mat), work/classes.json"""
import json
import os
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
from weld import weld_ids  # noqa: E402
E = lambda k, d: os.environ.get(k, d)
tag = sys.argv[1]
SMALL = int(E('SMALL', '80')); SOLE = float(E('SOLE', '0.03')); SEAM = float(E('SEAM', '0.015'))
HAIRLINE = float(E('HAIRLINE', '0.008')); JUNC = float(E('JUNC', '0.035')); HAIR_LUM = float(E('HAIR_LUM', '95'))
HATR = float(E('HATR', '0.02'))
LINED_KEEP = E('LINED_KEEP', '1') == '1'
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_honkm.glb', 'HonkM')
skin = doc['skins'][nd['skin']]; names = [doc['nodes'][j]['name'] for j in skin['joints']]
ibm = glbio.arr(doc, binary, skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
jpos = np.array([np.linalg.inv(m)[:3, 3] for m in ibm])
HANDJ = np.array([any(k in n for k in ('Hand', 'Finger', 'Index', 'Middle', 'Ring', 'Pinky', 'Thumb')) for n in names])
PR = ['HonkM_A', 'HonkMHead']
CLS = ['robe', 'lining', 'lined', 'boots', 'medallion', 'collar', 'small', 'face', 'hairshell', 'eyes', 'hands', 'forearm']
texA = np.asarray(Image.open(HERE / 'work' / 'tex_HonkMHead_0.png').convert('RGB'), np.float32)


def sample(im, uv):
    H, W = im.shape[:2]
    return im[np.clip((uv[:, 1] % 1) * H, 0, H - 1).astype(int), np.clip((uv[:, 0] % 1) * W, 0, W - 1).astype(int)]


def pieces(P, T):
    w = weld_ids(P); FT = w[T]; n = w.max() + 1
    r = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
    _, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)
    return w, FT, lab[FT[:, 0]]


def boundary_verts(FT, sel):
    F = FT[sel]; ed = np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1)
    u, cc = np.unique(ed, axis=0, return_counts=True); return np.unique(u[cc == 1].ravel())


def hat_points():
    """Both hats' LOD0 vertices in the body's bind space (hat node = child of Bip01 Head, identity local transform)."""
    head = np.linalg.inv(ibm[names.index('Bip01 Head')])
    out = []
    for f in ('mm9_honkhat.glb', 'mm9_elderhonkhat.glb'):
        hd, hb = glbio.read_glb(REPO / 'assets_source' / 'worlds' / 'mm9' / 'models' / f)
        hn = next(n for n in hd['nodes'] if n.get('name') == 'Hat' and 'mesh' in n)
        for p in hd['meshes'][hn['mesh']]['primitives']:
            v = glbio.arr(hd, hb, p['attributes']['POSITION']).astype(float)
            out.append((head @ np.c_[v, np.ones(len(v))].T).T[:, :3])
    return np.concatenate(out)


cls_all, small_all = [], []
info = {}
for k, name in enumerate(PR):
    P, T, UV, J, W = (D[name][x] for x in ('P', 'T', 'UV', 'J', 'W'))
    w, FT, fl = pieces(P, T); cnt = np.bincount(fl); big = int(np.argmax(cnt))
    cen = P[T].mean(1)
    e1 = UV[T[:, 1]] - UV[T[:, 0]]; e2 = UV[T[:, 2]] - UV[T[:, 0]]; uvarea = np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0])

    def wsum(mask):
        return (W * mask[J]).sum(1)
    cls = np.full(len(T), -1)
    if k == 0:
        foot = np.array(['Foot' in n or 'Toe' in n or 'Calf' in n for n in names])
        neckj = np.array([n == 'Bip01 Neck' for n in names])
        robes = []
        for comp in np.unique(fl):
            s = fl == comp; v = np.unique(T[s])
            if wsum(foot)[v].mean() > 0.5:
                cls[s] = CLS.index('boots')
            elif cnt[comp] > 400:
                cls[s] = CLS.index('robe'); robes.append(comp)
            elif wsum(neckj)[v].mean() > 0.4 and cnt[comp] > SMALL:
                cls[s] = CLS.index('collar')
            elif cnt[comp] > SMALL:
                cls[s] = CLS.index('medallion')
            else:
                cls[s] = CLS.index('small')
        inrobe = np.isin(fl, robes)
        lining = (uvarea < 1e-10) & inrobe
        fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-20)
        lt = cKDTree(cen[lining]); li = np.flatnonzero(lining)
        lined = np.zeros(len(T), bool)
        for f in np.flatnonzero(~lining & inrobe):
            for j in lt.query_ball_point(cen[f], 0.025):
                g = li[j]; dv = cen[f] - cen[g]
                if np.dot(fn[f], fn[g]) < -0.8 and 0.002 < np.dot(dv, fn[f]) < 0.025 and np.linalg.norm(dv - np.dot(dv, fn[f]) * fn[f]) < 0.01:
                    lined[f] = True; break
        out_ = ~lining; Ns = np.zeros((w.max() + 1, 3)); fa = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
        for c in range(3):
            np.add.at(Ns, w[T[out_, c]], fa[out_])
        nv = Ns[w] / (np.linalg.norm(Ns[w], axis=1, keepdims=True) + 1e-20); lv = cKDTree(P[np.unique(T[lining])])
        tw = np.minimum(lv.query(P - 0.003 * nv)[0], lv.query(P - 0.012 * nv)[0]) < 0.0015
        lined |= out_ & tw[T].all(1) & inrobe
        cls[lined] = CLS.index('lined'); cls[lining] = CLS.index('lining')
    else:
        hw = wsum(HANDJ)
        for comp in np.unique(fl):
            s = fl == comp; v = np.unique(T[s])
            if comp == big:
                cls[s] = CLS.index('face')
            elif hw[v].max() > 0.5 and cnt[comp] > 300:
                cls[s] = CLS.index('forearm')
                cls[s & (hw[T].mean(1) > 0.5)] = CLS.index('hands')
            else:
                cls[s] = CLS.index('eyes')
        # hair paint (tier A brown), only outside the face box: beard and moustache stay face skin
        hs = cls == CLS.index('face')
        lumA = sample(texA, UV[T].mean(1)).mean(1)
        hair = hs & (lumA < HAIR_LUM)
        for _ in range(2):
            vh = np.zeros(w.max() + 1); vc = np.zeros(w.max() + 1)
            for c in range(3):
                np.add.at(vh, FT[hs, c], hair[hs]); np.add.at(vc, FT[hs, c], 1)
            frac = (vh / np.maximum(vc, 1))[FT].mean(1)
            hair = hs & (frac > 0.5)
        head = jpos[names.index('Bip01 Head')]
        rel = cen - head
        FZ = float(E('FACE_Z', '0.035')); FX = float(E('FACE_X', '0.075')); FY = float(E('FACE_Y', '0.075'))
        facebox = (rel[:, 2] > FZ) & (np.abs(rel[:, 0]) < FX) & (rel[:, 1] < FY)
        hair &= ~facebox
        cls[hair] = CLS.index('hairshell')
        info['head_lumA'] = np.percentile(lumA[hs], [5, 25, 50, 75, 95]).round(1).tolist()
        info['head_joint'] = head.round(3).tolist()
    small_all.append(cnt[fl] <= SMALL); cls_all.append(cls)
    for ci in np.unique(cls):
        print(f'  {name:10s} {CLS[ci]:10s} {int((cls == ci).sum()):5d}')
cls = np.concatenate(cls_all); small = np.concatenate(small_all)
mat = np.concatenate([np.full(len(D[n]['T']), i) for i, n in enumerate(PR)])
C = lambda *ns: np.isin(cls, [CLS.index(x) for x in ns])
FV = np.concatenate([D[n]['P'][D[n]['T']] for n in PR])
lining = C('lining'); lined = C('lined')
keep = C('face', 'eyes', 'collar') | (small & ~lining)
if LINED_KEEP:
    keep |= lined
sole = C('boots') & (FV[:, :, 1].max(1) < SOLE); keep |= sole
junc = np.zeros(len(cls), bool)
for side in ('L', 'R'):
    j = jpos[names.index(f'Bip01 {side} Hand')]
    junc |= C('hands', 'forearm') & (np.linalg.norm(FV - j, axis=2).min(1) < JUNC)
keep |= junc
ft = cKDTree(FV[C('face')].reshape(-1, 3))
hl = C('hairshell') & (ft.query(FV.reshape(-1, 3))[0].reshape(-1, 3).min(1) < HAIRLINE); keep |= hl
hp = cKDTree(hat_points())
hat = C('hairshell') & (hp.query(FV.reshape(-1, 3))[0].reshape(-1, 3).min(1) < HATR); keep |= hat
P1, T1 = D['HonkMHead']['P'], D['HonkMHead']['T']; o1 = len(D['HonkM_A']['T'])
w1 = weld_ids(P1); FT1 = w1[T1]; rep = np.zeros(w1.max() + 1, np.int64); rep[w1] = np.arange(len(P1))
ring = P1[rep[boundary_verts(FT1, C('face', 'hairshell')[o1:])]]
seam = (cKDTree(ring).query(FV.reshape(-1, 3))[0].reshape(-1, 3).min(1) < SEAM) & ~C('face', 'lining'); keep |= seam
for nm in [x for x in E('KEEP_EXTRA', '').split(',') if x]:
    ex = np.load(HERE / 'work' / f'{nm}.npy'); keep |= ex; print('extra keep', nm, int(ex.sum()))
if LINED_KEEP:   # linings kept exactly with their outer faces: mpqem sees them as kept faces, nothing re-emitted
    keep |= lining; lining = np.zeros_like(lining); lined = np.zeros_like(lined)
else:
    # only the robe wall's lining whose every vertex is a 12 mm twin of an outer robe vertex is re-emitted by mpqem from the
    # cut outer faces; the hem rim, the top cap, the sleeve linings and their outer faces stay exact
    P0, T0 = D['HonkM_A']['P'], D['HonkM_A']['T']; n0 = len(T0); w0 = weld_ids(P0); cls0 = cls[:n0]
    out0 = (cls0 == CLS.index('lined')) | (cls0 == CLS.index('robe'))
    fa = np.cross(P0[T0[:, 1]] - P0[T0[:, 0]], P0[T0[:, 2]] - P0[T0[:, 0]]); Ns = np.zeros((w0.max() + 1, 3))
    for c in range(3):
        np.add.at(Ns, w0[T0[out0, c]], fa[out0])
    nv = Ns[w0] / (np.linalg.norm(Ns[w0], axis=1, keepdims=True) + 1e-20)
    lv = np.unique(T0[cls0 == CLS.index('lining')])
    # robe_lining.py puts the robe wall's lining 12 mm behind, sleeve_lining.py the sleeve linings 3 mm behind: each outer
    # vertex takes the offset whose prediction lands nearest a lining vertex
    ok = np.zeros(len(P0), bool); ov = np.unique(T0[out0]); lt0 = cKDTree(P0[lv])
    res = [lt0.query(P0[ov] - float(o) * nv[ov]) for o in E('LINING_OFFS', '0.012,0.003').split(',')]
    best = np.argmin(np.stack([r[0] for r in res]), 0)
    dd = np.stack([r[0] for r in res])[best, np.arange(len(ov))]; q = np.stack([r[1] for r in res])[best, np.arange(len(ov))]
    ok[ov] = dd < 0.0005
    rd = np.zeros(len(cls), bool); rd[:n0] = out0 & ok[T0].all(1)
    back = -np.ones(len(P0), np.int64); good = dd < 0.0005; back[lv[q[good]]] = w0[ov[good]]
    rdkeys = {tuple(sorted(w0[t])) for t in T0[rd[:n0]]}
    li0 = np.flatnonzero(cls0 == CLS.index('lining')); rl = np.zeros(len(cls), bool)
    for f in li0:
        bt = back[T0[f]]
        if (bt >= 0).all() and tuple(sorted(bt)) in rdkeys:
            rl[f] = True
    keptdark = (cls0 == CLS.index('lining')) & ~rl[:n0]; kv = np.zeros(w0.max() + 1, bool); kv[w0[T0[keptdark]].ravel()] = True
    edge_l = rl[:n0] & kv[w0[T0]].any(1)
    edge_keys = {tuple(sorted(back[t])) for t in T0[edge_l]}
    edge_o = np.zeros(n0, bool)
    for f in np.flatnonzero(rd[:n0]):
        if tuple(sorted(w0[T0[f]])) in edge_keys:
            edge_o[f] = True
    rl[:n0] &= ~edge_l; rd[:n0] &= ~edge_o
    rd &= ~keep
    rl_ok = np.zeros(len(cls), bool)
    rdkeys = {tuple(sorted(w0[t])) for t in T0[rd[:n0]]}
    for f in np.flatnonzero(rl[:n0]):
        if tuple(sorted(back[T0[f]])) in rdkeys:
            rl_ok[f] = True
    rl = rl_ok
    print('robe wall border kept: lining', int(edge_l.sum()), 'outer', int(edge_o.sum()))
    print('robe wall: lined outer', int(rd.sum()), 'lining', int(rl.sum()), 'twinned outer vertices', int((dd < 0.0005).sum()), 'of', len(dd))
    keep |= (lining & ~rl) | (C('lined') & ~rd) | (C('robe') & ~rd & np.r_[edge_o, np.zeros(len(cls) - n0, bool)]); lining = rl; lined = rd
keep &= ~lining
group = np.zeros(len(cls), int)
for gi, ns in ((1, ('hands',)), (2, ('hairshell',)), (5, ('boots',)), (6, ('medallion',)), (int(E('FOREARM_GROUP', '7')), ('forearm',)),
               (8, ('lined',))):
    group[C(*ns) & ~keep] = gi
# group 3: robe faces on the arms (UpperArm/Forearm/Clavicle weight > SLEEVE_W): the sleeves are already lean and fold at the
# elbow (b r60: 45.8 mm at the right sleeve in Fidget)
_P0, _T0, _J0, _W0 = (D['HonkM_A'][x] for x in ('P', 'T', 'J', 'W'))
_arm = np.array([any(k in n for k in ('UpperArm', 'Forearm', 'Clavicle')) for n in names])
_aw = np.zeros(len(cls)); _aw[:len(_T0)] = (_W0 * _arm[_J0]).sum(1)[_T0].mean(1)
group[C('robe') & ~keep & (_aw > float(E('SLEEVE_W', '0.3')))] = 3
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=lining, lined=lined, cls=cls, mat=mat)
rows = {}
for ci, cn in enumerate(CLS):
    s = cls == ci
    if s.any():
        rows[cn] = dict(faces=int(s.sum()), keep=int((s & keep).sum()), free=int((s & ~keep & ~lining).sum()))
        print(f'{cn:10s} {s.sum():5d} keep {int((s & keep).sum()):5d} free {int((s & ~keep & ~lining).sum()):5d}')
print('soles', int(sole.sum()), 'junction', int(junc.sum()), 'hairline', int(hl.sum()), 'hatseat', int(hat.sum()), 'seam',
      int(seam.sum()), 'small', int(small.sum()), info)
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'lining', int(lining.sum()),
      'free', int((~keep & ~lining).sum()), 'of', len(cls), '| groups', {k: int((group == k).sum()) for k in range(10)})
(HERE / 'work' / 'classes.json').write_text(json.dumps(dict(names=CLS, rows=rows), indent=1))
