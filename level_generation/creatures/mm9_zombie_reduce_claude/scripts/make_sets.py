#!/usr/bin/env python3
"""Keep / group / lining sets per face of the installed LOD0 (before/mm9_zombie.glb, primitive order Zombie_A, ZombieHead_A,
ZombieTorso) for mpqem.py, prio-1 relaxed keep set (REDUCTION_BRIEF_20261104). Classes per connected piece (welded by
position inside a primitive; faces3 labels by majority, glb_parts.py), then per face:
  Zombie_A: trousers (the legs, left foot), arms (+ hands: faces whose vertices are mostly on Hand/finger bones),
            footbone (the bony right foot), shinbone, neck bits (pieces at the neck ring);
  ZombieHead_A: head skin (the big piece) split by the head region mask (R hair, G skin, B crown; tier_ramps.py) into face
            (skin-painted: face, ears, jaw, chin, neck) and scalp (hair/crown-painted skin under the locks); plug (the dark
            skull plug), teeth, eyes, hair (the locks and the tie);
  ZombieTorso: chest, tatter (outer), lining (export_zombie's reversed copy 1.5 mm inside), rope pieces.
Exact: face, plug, teeth, eyes, neck bits, rope, pieces of up to SMALL faces, soles (all vertices below SOLE m), the neck seam
(faces with a vertex within SEAM m of a head-skin boundary vertex, all primitives), the hairline (scalp/hair faces with a vertex
within HAIRLINE m of a face vertex), and optional extra keeps (work/<name>.npy per GLB face, env KEEP_EXTRA=a,b).
Groups (MP_GROUPS ratios): 1 hands, 2 hair, 3 scalp, 4 tatter (lining re-emitted from it), 5 footbone + shinbone;
label 0 (ladder ratio): trousers, arms, chest.
Usage: make_sets.py <tag>  -> work/glb_sets_<tag>.npz (keep, group, lining, lined, cls) and work/classes.json"""
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
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
from weld import weld_ids  # noqa: E402
E = lambda k, d: os.environ.get(k, d)
tag = sys.argv[1]
SMALL = int(E('SMALL', '60')); SOLE = float(E('SOLE', '0.02')); SEAM = float(E('SEAM', '0.02'))
HAIRLINE = float(E('HAIRLINE', '0.008')); SKIN_G = float(E('SKIN_G', '0.5'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_zombie.glb', 'Zombie')
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
HANDJ = np.array([any(k in n for k in ('Hand', 'Finger', 'Index', 'Middle', 'Ring', 'Pinky', 'Thumb')) for n in names])
g = np.load(HERE / 'work' / 'glb_parts.npz')
PR = ['Zombie_A', 'ZombieHead_A', 'ZombieTorso']
CLS = ['trousers', 'arms', 'hands', 'footbone', 'shinbone', 'neck', 'face', 'scalp', 'plug', 'teeth', 'eyes', 'hair',
       'chest', 'tatter', 'lining', 'rope']
mask = np.asarray(Image.open(HERE / 'work' / 'tex_ZombieHead_A_1.png').convert('RGB'), np.float32) / 255
cls_all, keep_all, small_all, cen_all = [], [], [], []
off = 0
for k, name in enumerate(PR):
    P, T, UV, J, W = (D[name][x] for x in ('P', 'T', 'UV', 'J', 'W'))
    part = g['part'][off:off + len(T)]; lin = g['lining'][off:off + len(T)]; off += len(T)
    w = weld_ids(P); FT = w[T]; n = w.max() + 1
    r = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
    _, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)
    fl = lab[FT[:, 0]]; cnt = np.bincount(fl); big = np.argsort(-cnt)
    cls = np.full(len(T), -1)
    cen = P[T].mean(1)
    for comp in np.unique(fl):
        s = fl == comp; vals = part[s]; vals = vals[vals != 20] if (vals != 20).any() else vals
        maj = np.bincount(vals).argmax()
        if k == 0:
            c_ = {1: 'trousers', 0: 'arms', 5: 'footbone', 4: 'shinbone'}.get(maj, 'neck') if cnt[comp] > 100 else 'neck'
        elif k == 1:
            if comp == big[0]:
                c_ = 'face'
            elif cnt[comp] == 80 and abs(cen[s][:, 0].mean()) < 0.01 and (part[s] == 20).all():
                c_ = 'plug'
            else:
                c_ = {12: 'teeth', 13: 'eyes'}.get(maj, 'hair')
        else:
            if comp == big[0]:
                c_ = 'chest'
            elif maj == 2 and cnt[comp] > 200:
                # outer shell faces away from the body axis, the lining towards it
                nrm = np.cross(P[T[s, 1]] - P[T[s, 0]], P[T[s, 2]] - P[T[s, 0]])
                radial = cen[s] - np.array([0.0, 0.0, 0.0]); radial[:, 1] = 0
                c_ = 'tatter' if (nrm * radial).sum(1).mean() > 0 else 'lining'
            else:
                c_ = 'rope'
        cls[s] = CLS.index(c_)
    if k == 0:
        hw = (W * HANDJ[J]).sum(1)
        hand = (cls == CLS.index('arms')) & (hw[T].mean(1) > 0.5)
        cls[hand] = CLS.index('hands')
    if k == 1:
        hs = cls == CLS.index('face')
        uvc = np.einsum('fkc->fc', UV[T]) / 3
        H, Wd = mask.shape[:2]
        samp = []
        for b_ in ([1, 1, 1], [4, 1, 1], [1, 4, 1], [1, 1, 4]):
            b_ = np.array(b_, float) / sum(b_); u = np.einsum('k,fkc->fc', b_, UV[T])
            samp.append(mask[np.clip((u[:, 1] % 1) * H, 0, H - 1).astype(int), np.clip((u[:, 0] % 1) * Wd, 0, Wd - 1).astype(int)])
        m = np.mean(samp, 0)
        scalp = hs & (m[:, 1] < SKIN_G)
        cls[scalp] = CLS.index('scalp')
        print('head skin mask G quantiles', np.percentile(m[hs, 1], [5, 25, 50, 75, 95]).round(2), 'scalp', int(scalp.sum()),
              'face', int((hs & ~scalp).sum()))
    small = cnt[fl] <= SMALL
    cls_all.append(cls); small_all.append(small); cen_all.append(cen)
    for ci in np.unique(cls):
        print(f'  {name:13s} {CLS[ci]:9s} {int((cls == ci).sum()):5d}')
cls = np.concatenate(cls_all); small = np.concatenate(small_all); cen = np.concatenate(cen_all)
C = lambda *ns: np.isin(cls, [CLS.index(x) for x in ns])
allP = [D[nm]['P'] for nm in PR]; allT = [D[nm]['T'] for nm in PR]
FV = np.concatenate([p[t] for p, t in zip(allP, allT)])            # (F,3,3) rest corners, glTF y-up
keep = C('face', 'plug', 'teeth', 'eyes', 'neck', 'rope') | (small & ~C('lining', 'tatter'))
sole = FV[:, :, 1].max(1) < SOLE; keep |= sole
# neck seam: the head skin's open boundary at the neck (the ring welded onto the body ring)
P1, T1 = allP[1], allT[1]; o1 = len(allT[0])
hsel = np.flatnonzero(C('face', 'scalp')[o1:o1 + len(T1)])
w1 = weld_ids(P1); F1 = w1[T1[hsel]]
ed = np.sort(np.vstack([F1[:, [0, 1]], F1[:, [1, 2]], F1[:, [2, 0]]]), 1); u, ccount = np.unique(ed, axis=0, return_counts=True)
bv = np.unique(u[ccount == 1].ravel()); rep = np.zeros(w1.max() + 1, np.int64); rep[w1] = np.arange(len(P1))
ring = P1[rep[bv]]
# only the ring welded onto the body: the head skin has other open edges (the scalp under the locks is open in places)
other = np.vstack([allP[0], allP[2]]); ring = ring[cKDTree(other).query(ring)[0] < 1e-4]
print('head skin boundary verts', len(ring), 'y range', ring[:, 1].min().round(3), ring[:, 1].max().round(3))
dseam = cKDTree(ring).query(FV.reshape(-1, 3))[0].reshape(-1, 3).min(1)
seam = dseam < SEAM; keep |= seam
facev = FV[C('face')].reshape(-1, 3)
hl = C('scalp', 'hair') & (cKDTree(facev).query(FV.reshape(-1, 3))[0].reshape(-1, 3).min(1) < HAIRLINE); keep |= hl
for nm in [x for x in E('KEEP_EXTRA', '').split(',') if x]:
    ex = np.load(HERE / 'work' / f'{nm}.npy'); keep |= ex; print('extra keep', nm, int(ex.sum()))
lining = C('lining'); lined = C('tatter')
keep &= ~lining
group = np.zeros(len(cls), int)
for gi, ns in ((1, ('hands',)), (2, ('hair',)), (3, ('scalp',)), (4, ('tatter',)), (5, ('footbone', 'shinbone'))):
    group[C(*ns) & ~keep] = gi
mat = np.concatenate([np.full(len(t), i) for i, t in enumerate(allT)])
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=lining, lined=lined, cls=cls, mat=mat)
rows = {}
for ci, cn in enumerate(CLS):
    s = cls == ci
    if s.any():
        rows[cn] = dict(faces=int(s.sum()), keep=int((s & keep).sum()), free=int((s & ~keep & ~lining).sum()))
        print(f'{cn:9s} {s.sum():5d} keep {int((s & keep).sum()):5d} free {int((s & ~keep & ~lining).sum()):5d}')
print('soles', int(sole.sum()), 'seam', int(seam.sum()), 'hairline', int(hl.sum()), 'small', int(small.sum()))
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'lining', int(lining.sum()),
      'free', int((~keep & ~lining).sum()), 'of', len(cls), '| groups', {k: int((group == k).sum()) for k in range(6)})
(HERE / 'work' / 'classes.json').write_text(json.dumps(dict(names=CLS, rows=rows), indent=1))
