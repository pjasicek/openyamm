#!/usr/bin/env python3
"""Yrsa (2026-11-05): keep / group sets per installed LOD0 face (work/glb_parts.npz order: prims Yrsa, YrsaHead) for mpqem.py
-> work/glb_sets_<tag>.npz. Relaxed keep set of REDUCTION_AGENT_TOWNSFOLK.md (uniques reduced on the user's "do all", face exact).
Kept exactly:
- face and neck skin (20: every visible skin-coloured face of the head shell, with the upper braids) and every other head piece (23:
  eyes, mouth, neck ring, white hair fringe, braid ends, forehead bead band, earrings);
- hairline: hood / hair / hidden-shell faces with a corner within HAIRSKIN m of a face-skin or fringe vertex;
- collar: body faces within COLLAR m of a head-shell / neck-ring vertex (neck seam);
- HW > 0: body faces within HW m of a hood (tail), braid or fringe vertex (the headwear's clearance over the dress);
- forearm extension + stub (10: hand faces dominated by a Forearm joint) and hand faces within JUNC m of a body vertex (graft
  junction inside the cuff); WRIST > 0: sleeve faces within WRIST m of a hand vertex (cuff, lining border);
- fingertips: hand faces within TIP m of each finger's tip vertex (every finger keeps its length);
- CONTACT > 0: body faces whose posed centroid comes within CONTACT m of a posed hand vertex in any sampled frame;
- lining rims + Meshy's darkened inner layer (3), unpaired lining faces (and outer faces touching their twins), small pieces (9),
  soles (boot faces below floor + SOLE).
Linings (2, paired) are re-emitted by mpqem.py from the twins of the surviving outer faces.
Groups: 1 hands, 2 hood + hair + hidden shell, 3 skirt, 4 boots, 5 belt + chest panel, 0 bodice + sleeves (the ladder ratio).
Usage: make_sets_yrsa.py <tag>  (env as above; EXTRA=<npy,...>)"""
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts')); sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
import glbio  # noqa: E402
tag = sys.argv[1]
E = lambda k, d: os.environ.get(k, d)
HAIRSKIN = float(E('HAIRSKIN', '0.008')); COLLAR = float(E('COLLAR', '0.012')); HW = float(E('HW', '0'))
WRIST = float(E('WRIST', '0.03')); JUNC = float(E('JUNC', '0.012')); TIP = float(E('TIP', '0.006'))
CONTACT = float(E('CONTACT', '0')); SOLE = float(E('SOLE', '0.012'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_yrsa.glb', 'Yrsa')
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']; jn = [str(x) for x in g['jnames']]
PR = ['Yrsa', 'YrsaHead']
P = np.concatenate([D[k]['P'] for k in PR]); offs = g['voff']
T = np.concatenate([D[k]['T'] + offs[i] for i, k in enumerate(PR)])
J = np.concatenate([D[k]['J'] for k in PR]); W = np.concatenate([D[k]['W'] for k in PR])
assert len(T) == len(part)
floor = P[:, 1].min(); V = P[T]; nf = len(T); nb = g['foff'][1]
isbody = np.arange(nf) < nb
pv = lambda m: np.unique(T[m].ravel())
dmin = lambda pts: cKDTree(pts).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1)
face_v = P[pv(np.isin(part, (20, 23)))]; hand_v = P[pv(np.isin(part, (0, 10)))]; body_v = P[pv(isbody)]
shell_v = P[pv(np.isin(part, (20, 21, 22, 23, 24, 26)))]
rep = {}
keep = np.isin(part, (20, 23, 24, 10, 3, 9)); rep['face, head pieces, forearm, rims, small'] = int(keep.sum())
lining, lined = g['lining'], g['lined']
unp = (part == 2) & ~lining
tw = g['twin']; unp_v = set(pv(unp).tolist())
near_unp = isbody & np.array([any(int(tw[v]) in unp_v for v in t) for t in T]) & (part == 1)
hairline = np.isin(part, (21, 22, 26)) & (dmin(face_v) < HAIRSKIN)
collar = isbody & (dmin(P[pv(np.isin(part, (20, 23, 26)))]) < COLLAR)
clear = isbody & np.isin(part, (1, 7, 8)) & (dmin(P[pv(np.isin(part, (22, 23, 24)))]) < HW) if HW > 0 else np.zeros(nf, bool)
junction = (part == 0) & (dmin(body_v) < JUNC)
wrist = (part == 1) & (dmin(hand_v) < WRIST) if WRIST > 0 else np.zeros(nf, bool)
ibm = np.array(glbio.arr(doc, binary, doc['skins'][nd['skin']]['inverseBindMatrices'])).reshape(-1, 4, 4).transpose(0, 2, 1)
jpos = np.linalg.inv(ibm)[:, :3, 3]
dom = J[np.arange(len(J)), W.argmax(1)]
tips = []
hv_all = pv(part == 0)
for s in ('L', 'R'):
    for f in ('Index3', 'Middle3', 'Ring3', 'Pinky3', 'Thumb3'):
        ji = jn.index(f'FHP {s} {f}'); vs = np.flatnonzero(dom == ji); vs = vs[np.isin(vs, hv_all)]
        if len(vs):
            tips.append(P[vs[np.linalg.norm(P[vs] - jpos[ji], axis=1).argmax()]])
tips = np.array(tips); print('fingertips', len(tips))
tip = (part == 0) & (dmin(tips) < TIP)
contact = np.zeros(nf, bool)
if CONTACT > 0:
    from glb_pose import Glb, Model
    m = Model(Glb(str(HERE / 'before' / 'mm9_yrsa.glb')))
    hv = pv(np.isin(part, (0, 10))); target = isbody & ~np.isin(part, (2, 3))
    for c in E('CLIPS', 'Standing,Fidget,Walking,Running,Hit,Death,Dead').split(','):
        ts = m.clip_times(c); ts = ts[::max(1, len(ts) // 24)]
        for t in ts:
            PS = np.concatenate([np.asarray(x[0]) for x in m.skinned_positions(m.world(m.sample(c, t)))[:2]])
            d, _ = cKDTree(PS[hv]).query(PS[T].mean(1), distance_upper_bound=CONTACT)
            contact |= target & (d < CONTACT)
sole = (part == 6) & (V[:, :, 1].max(1) < floor + SOLE)
# THIGH: boot faces with a vertex more than THIGH m above the floor (root_shoes.py's stretched band, poke_gate.py's test set)
thigh = (part == 6) & (V[:, :, 1].max(1) > floor + float(E('THIGH', '9')))
for nm_, m_ in (('unpaired lining', unp), ('outer at unpaired lining', near_unp), ('hairline', hairline), ('collar', collar),
                ('headwear clearance', clear), ('junction', junction), ('wrist', wrist), ('fingertips', tip), ('contact', contact),
                ('soles', sole), ('boot thigh band', thigh)):
    rep[nm_] = int((m_ & ~keep).sum()); keep |= m_
if E('EXTRA', ''):
    for x in E('EXTRA', '').split(','):
        ex = np.load(x); rep[x] = int((ex & ~keep).sum()); keep |= ex
keep &= ~lining          # paired linings: re-emitted from the surviving outer faces' twins
group = np.zeros(nf, int)
group[part == 0] = 1; group[np.isin(part, (21, 22, 26))] = 2; group[part == 5] = 3 if E("SKIRTG", "0") == "1" else 0; group[part == 6] = 4
group[np.isin(part, (7, 8))] = 5
group[keep] = 0
# a lined outer face that is kept: its lining must be kept too (mpqem emits the installed lining of an unchanged lined face)
print('kept (added in order):', rep)
for p_ in np.unique(part):
    s = part == p_
    print(f'part {p_:2d} {s.sum():5d} keep {int((s & keep).sum()):5d} free {int((s & ~keep & ~lining).sum()):5d} lining {int((s & lining).sum())} groups',
          {int(k): int((group[s & ~keep & ~lining] == k).sum()) for k in np.unique(group[s & ~keep & ~lining])})
free = ~keep & ~lining
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'lining', int(lining.sum()), 'free', int(free.sum()),
      f'({free.mean() * 100:.1f} %)', 'of', nf)
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=lining, lined=lined, pair=g['pair'],
         twin=g['twin'], part=part, mat=g['mat'])
