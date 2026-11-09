#!/usr/bin/env python3
"""Keep / group sets per installed LOD0 face (work/glb_parts.npz order, cfg.PR) for mpqem.py -> work/glb_sets_<tag>.npz.
Copy of the PeasantM1 reduce project's make_sets_pm1.py, adapted to Tryggva's and then Sven's parts (scripts/cfg.py). Keep exactly
(REDUCTION_BRIEF_20261104 relaxed set, face exact):
- face shell (20: face, ears' rims, scalp under the hair, neck) and the small head pieces (22: mouth, braid ends/ties) whole;
- the ears Meshy fused into the hair shell: hair-shell faces with the centroid in cfg's ear box;
- hairline: hair-shell and braid faces within HAIREDGE m of their open rim vertices that lie on the skin (within SKIN m of a
  face-shell vertex);
- collar: body faces within COLLAR m of a face-shell vertex (the head/body seam on the collar cloth); cuffs: tunic faces within
  CUFF m of the tunic's open rim near the hands; soles (part 5 below floor + SOLE); the small body pieces (9);
- RIM=<m>: faces within RIM m of the open rims of the tunic (hem), collar, shoulder fur and trousers (openings the see-through
  gate looks into), the sleeve ends excluded (they are the cuffs);
- CONTACT=<m>: hair-shell (fur lapels, back hair) faces within CONTACT m of a body vertex (the layer resting on the tunic);
- EXTRA=<npy,...> extra keep masks.
Sven: cuffs = the bare-arm/bracer piece (2) at its rim by the hands; soles on the boots (6); openings of the tunic, arms,
trousers and boots. Groups: 1 hand + fingers (seam slides), 5 forearm skin of the MPFB hand piece, 2 hair shell, 3 braids,
4 boots, 6 belt, 7 arms + bracers, 8 trousers, 0 = tunic (the ladder ratio).
Usage: make_sets_sven.py <tag>  (env HAIREDGE, SKIN, COLLAR, CUFF, SOLE, RIM, SHOULDER, CONTACT, EXTRA)"""
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio, cfg  # noqa: E402
tag = sys.argv[1]
E = lambda k, d: os.environ.get(k, d)
HAIREDGE = float(E('HAIREDGE', '0.012')); COLLAR = float(E('COLLAR', '0.015')); CUFF = float(E('CUFF', '0.04'))
SOLE = float(E('SOLE', '0.012'))
doc, binary, nd, D = glbio.load(HERE / 'before' / cfg.GLB, cfg.NODE)
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']; jn = [str(x) for x in g['jnames']]; joint = g['joint']
PR = cfg.PR
P = np.concatenate([D[k]['P'] for k in PR]); offs = g['voff']
T = np.concatenate([D[k]['T'] + offs[i] for i, k in enumerate(PR)])
assert len(T) == len(part)
floor = P[:, 1].min(); V = P[T]; cen = V.mean(1)
pv = lambda m: np.unique(T[m].ravel())
dist_to = lambda pts: cKDTree(P[pts]).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1)
_, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]
rep = np.zeros(w.max() + 1, np.int64); rep[w] = np.arange(len(w))


def rim(mask):
    ec = {}
    for f in np.flatnonzero(mask):
        for a, b in ((0, 1), (1, 2), (2, 0)):
            e = (min(FT[f, a], FT[f, b]), max(FT[f, a], FT[f, b])); ec[e] = ec.get(e, 0) + 1
    ids = np.unique(np.array([x for e, c in ec.items() if c == 1 for x in e], np.int64))
    return P[rep[ids]]


def near_pts(pts, r):
    if not len(pts):
        return np.zeros(len(T), bool)
    return cKDTree(pts).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < r


body = np.isin(part, (1, 2, 3, 5, 6, 9)); face = part == 20
keep = np.isin(part, (20, 22))
box = (part == 21) & (np.abs(cen[:, 0]) > cfg.EAR_X) & (cen[:, 1] > cfg.EAR_Y[0]) & (cen[:, 1] < cfg.EAR_Y[1]) & \
      (cen[:, 2] > cfg.EAR_Z[0]) & (cen[:, 2] < cfg.EAR_Z[1])
# ear faces: box faces at least SKINFRAC skin-coloured in the installed head colour (fix_ear_try.py's test: lum > 80, R > 1.3 B;
# 12-step barycentric samples of each face's UV triangle), plus the box faces within EARPAD m of them (the hair framing the ear)
from PIL import Image  # noqa: E402
hi = np.asarray(Image.open(HERE / 'work' / f'tex_{PR[1]}_A.png').convert('RGB'), np.float64); hh, ww = hi.shape[:2]
UVh = D[PR[1]]['UV']; Th = D[PR[1]]['T']; fo = g['foff'][1]
k_ = 12; ii, jj = np.meshgrid(np.arange(k_ + 1), np.arange(k_ + 1)); mm = ii + jj <= k_
BW = np.stack([ii[mm], jj[mm], k_ - ii[mm] - jj[mm]], 1) / k_
skinfrac = np.zeros(len(T))
for f in np.flatnonzero(box):
    uv = BW @ UVh[Th[f - fo]]; px = hi[np.clip((uv[:, 1] % 1 * hh).astype(int), 0, hh - 1), np.clip((uv[:, 0] % 1 * ww).astype(int), 0, ww - 1)]
    lum = px @ [0.299, 0.587, 0.114]; skinfrac[f] = ((lum > 80) & (px[:, 0] > 1.3 * px[:, 2])).mean()
ear0 = box & (skinfrac >= float(E('SKINFRAC', '0.10')))
ear = box & near_pts(P[pv(ear0)], float(E('EARPAD', '0.01'))) if ear0.any() else ear0
print('ear box', int(box.sum()), 'skin faces', int(ear0.sum()), 'with pad', int(ear.sum()))
fk = cKDTree(P[pv(face)])
hairline = np.zeros(len(T), bool)
for p_ in (21, 23):
    r_ = rim(part == p_); r_ = r_[fk.query(r_)[0] < float(E('SKIN', '0.005'))]
    hairline |= (part == p_) & near_pts(r_, HAIREDGE); print('rim verts on the skin', p_, len(r_))
collar = body & (dist_to(pv(face)) < COLLAR)
handP = P[pv(part == 0)]
srim = rim(part == 2); rim_cuff = srim[cKDTree(handP).query(srim)[0] < 0.12]
cuff = (part == 2) & near_pts(rim_cuff, CUFF)
sole = (part == 6) & (V[:, :, 1].min(1) < floor + SOLE)
small = part == 9
keep |= ear | hairline | collar | cuff | sole | small
openings = np.zeros(len(T), bool)
if float(E('RIM', '0')) > 0:
    for p_ in (1, 2, 5, 6):
        r_ = rim(part == p_)
        if p_ == 2:
            r_ = r_[(cKDTree(handP).query(r_)[0] >= 0.12) & (fk.query(r_)[0] >= 0.03)]
        openings |= (part == p_) & near_pts(r_, float(E('RIM', '0')))
    keep |= openings
    print('openings kept', int(openings.sum()), {int(p_): int((openings & (part == p_)).sum()) for p_ in (1, 2, 5, 6)})
# SHOULDER=1 (PeasantM2d/PM1 rule; Sven a75 failed the jitter gate's shoulder-skin sample, AttackMelee R 0.2 -> 2.19 mm/f2): every
# face touching a vertex dominated by a Clavicle or UpperArm joint (the gate's sample) is kept
shoulder = np.zeros(len(T), bool)
if E('SHOULDER', '0') == '1':
    Jc = np.concatenate([D[k]['J'] for k in PR]); Wc = np.concatenate([D[k]['W'] for k in PR])
    dom = Jc[np.arange(len(Jc)), Wc.argmax(1)]
    sj = np.array([('Clavicle' in x or 'UpperArm' in x) for x in jn])
    shoulder = sj[dom[T]].any(1); keep |= shoulder
    print('shoulder keep', int(shoulder.sum()), {int(p_): int((shoulder & (part == p_)).sum()) for p_ in np.unique(part[shoulder])})
contact = np.zeros(len(T), bool)
if float(E('CONTACT', '0')) > 0:
    contact = (part == 21) & (dist_to(pv(body)) < float(E('CONTACT', '0'))); keep |= contact
if E('EXTRA', ''):
    for x in E('EXTRA', '').split(','):
        ex = np.load(x); keep |= ex; print('extra keep', x, int(ex.sum()))
handj = np.array([any(t in x for t in (' Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')) for x in jn])
group = np.zeros(len(T), int)
group[(part == 0) & handj[joint]] = 1; group[(part == 0) & ~handj[joint]] = 5
group[part == 21] = 2; group[part == 23] = 3; group[part == 6] = 4; group[part == 3] = 6; group[part == 2] = 7
group[part == 5] = 8
group[keep] = 0
for p_ in np.unique(part):
    s = part == p_
    print(f'part {p_:2d} {s.sum():5d} keep {int((s & keep).sum()):5d} free {int((s & ~keep).sum()):5d} groups',
          {int(k): int((group[s & ~keep] == k).sum()) for k in np.unique(group[s & ~keep])})
print('ear', int(ear.sum()), 'hairline', int(hairline.sum()), 'collar', int(collar.sum()), 'cuff', int(cuff.sum()),
      'soles', int(sole.sum()), 'small', int(small.sum()), 'contact', int((contact & ~(ear | hairline)).sum()))
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'free', int((~keep).sum()), 'of', len(T),
      '| -15 % needs', f'{0.15 * len(T) / max((~keep).sum(), 1) * 100:.0f} % of the free part')
z = np.zeros(len(T), bool)
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=z, lined=z, pair=g['pair'],
         twin=g['twin'], part=part, mat=g['mat'])
