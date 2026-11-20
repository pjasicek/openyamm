#!/usr/bin/env python3
"""Kira (2026-11-05): keep / group sets per installed LOD0 face (work/glb_parts.npz order: prims Kira, KiraHead) for mpqem.py
-> work/glb_sets_<tag>.npz. Relaxed keep set of REDUCTION_AGENT_TOWNSFOLK.md (uniques reduced on the user's "do all", face exact).
Kept exactly:
- face and neck skin (20) and eyes (22) whole (the r8 jaw rigidity, chin fold and UV-sliver fixes live there);
- hairline: hair faces with a corner within HAIRSKIN m of a face-skin vertex (fringe edge, temples, scalp contact);
  braid root: braid faces within BROOT m of a hair or face vertex (behind the right ear);
- collar: armour-shell faces within COLLAR m of a face-skin vertex (neck seam);
- HW > 0: armour, lame and medallion faces within HW m of a hair or braid vertex (the hair's clearance over the armour);
- wrist: armour faces within WRIST m of a hand vertex (vambrace rim, its inner wall and the rim caps of wrist_fill.py: the
  sleeve gate and the r8 wrist-hole fix); the hand-graft junction: hand faces whose dominant joint is not a hand/finger joint
  (glove stub tucked inside the vambrace) and hand faces within JUNC m of an armour vertex;
- fingertips: hand faces within TIP m of each finger's tip vertex (every finger keeps its length);
- CONTACT > 0: body faces (armour, belt, tasset, skirt, legs) whose posed centroid comes within CONTACT m of a posed hand vertex
  in any sampled frame of CLIPS (hands on the hips in Standing/Fidget, the seated hands on the thighs);
- KNEE > 0: leg faces within KNEE m of a knee cop (bent-knee contact);
- soles (leg faces below floor + SOLE) and pieces of up to SMALL faces (two smallest pauldron lames, belt buckle).
Groups: 1 hand + fingers (seam slides), 2 hair, 3 braid, 4 mail skirt, 5 plates (belt, medallion, knee cops, lames, tasset),
6 legs and boots, 0 armour shell (the ladder ratio). Usage: make_sets_kira.py <tag>  (env as above; EXTRA=<npy,...>)"""
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
HAIREDGE = float(E('HAIREDGE', '0.012')); SKIN = float(E('SKIN', '0.005')); BROOT = float(E('BROOT', '0.015'))
COLLAR = float(E('COLLAR', '0.012')); HW = float(E('HW', '0')); WRIST = float(E('WRIST', '0.04'))
JUNC = float(E('JUNC', '0.012')); TIP = float(E('TIP', '0.006')); CONTACT = float(E('CONTACT', '0'))
SOLE = float(E('SOLE', '0.012')); SMALL = int(E('SMALL', '80'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_kira.glb', 'Kira')
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']; jn = [str(x) for x in g['jnames']]; joint = g['joint']
PR = ['Kira', 'KiraHead']
P = np.concatenate([D[k]['P'] for k in PR]); offs = g['voff']
T = np.concatenate([D[k]['T'] + offs[i] for i, k in enumerate(PR)])
J = np.concatenate([D[k]['J'] for k in PR]); W = np.concatenate([D[k]['W'] for k in PR])
assert len(T) == len(part)
floor = P[:, 1].min(); V = P[T]; nf = len(T)
pv = lambda m: np.unique(T[m].ravel())
dmin = lambda pts, faces=None: cKDTree(pts).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1)
_, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]
rep = np.zeros(w.max() + 1, np.int64); rep[w] = np.arange(len(w))


def rim(mask):
    ec = {}
    for f in np.flatnonzero(mask):
        for a, b in ((0, 1), (1, 2), (2, 0)):
            e = (min(FT[f, a], FT[f, b]), max(FT[f, a], FT[f, b])); ec[e] = ec.get(e, 0) + 1
    return P[rep[np.unique([x for e, c in ec.items() if c == 1 for x in e])]]


face_v = P[pv(part == 20)]; hand_v = P[pv(part == 0)]; arm_v = P[pv(part == 1)]
hairbraid_v = P[pv(np.isin(part, (21, 23)))]
rep_keep = {}
keep = np.isin(part, (20, 22)); rep_keep['face+eyes'] = int(keep.sum())
# Kira's hair is a near-closed cap (43 rim vertices, 5-27 mm off the skin): the hairline is the hair whose corners come within
# HAIRSKIN m of the face skin (fringe edge on the forehead, temples, nape: the scalp must not poke through the cut cap)
hairline = (part == 21) & (dmin(face_v) < float(E('HAIRSKIN', '0.006')))
broot = (part == 23) & (dmin(np.vstack([face_v, P[pv(part == 21)]])) < BROOT)
collar = (part == 1) & (dmin(face_v) < COLLAR)
clear = np.isin(part, (1, 10, 12)) & (dmin(hairbraid_v) < HW) if HW > 0 else np.zeros(nf, bool)
wrist = (part == 1) & (dmin(hand_v) < WRIST)
handj = np.array([any(t in x for t in (' Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'hand1')) for x in jn])
junction = (part == 0) & (~handj[joint] | (dmin(arm_v) < JUNC))
# fingertips: per distal joint, the dominated vertex farthest from the joint's rest position
ibm = np.array(glbio.arr(doc, binary, doc['skins'][nd['skin']]['inverseBindMatrices'])).reshape(-1, 4, 4).transpose(0, 2, 1)
jpos = np.linalg.inv(ibm)[:, :3, 3]
dom = J[np.arange(len(J)), W.argmax(1)]
tips = []
for s in ('L', 'R'):
    for f in ('Index3', 'Middle3', 'Ring3', 'Pinky3', 'Thumb3'):
        ji = jn.index(f'Bip01 {s} {f}'); vs = np.flatnonzero(dom == ji)
        vs = vs[np.isin(vs, pv(part == 0))]
        if len(vs):
            tips.append(P[vs[np.linalg.norm(P[vs] - jpos[ji], axis=1).argmax()]])
tips = np.array(tips); print('fingertips', len(tips))
tip = (part == 0) & (dmin(tips) < TIP)
contact = np.zeros(nf, bool)
if CONTACT > 0:
    from glb_pose import Glb, Model
    m = Model(Glb(str(HERE / 'before' / 'mm9_kira.glb')))
    hv = pv(part == 0); target = np.isin(part, (1, 5, 7, 9, 13))
    for c in E('CLIPS', 'Standing,Fidget,Walking,Running,AttackMelee,Hit,Sit,Sc2_Kira9b,Sc2_KIRA12,Sc2_KIRA14,Sc2_KIRA20_23').split(','):
        ts = m.clip_times(c); ts = ts[::max(1, len(ts) // 24)]
        for t in ts:
            PS = np.concatenate([np.asarray(x[0]) for x in m.skinned_positions(m.world(m.sample(c, t)))[:2]])
            d, _ = cKDTree(PS[hv]).query(PS[T].mean(1), distance_upper_bound=CONTACT)
            contact |= target & (d < CONTACT)
sole = (part == 5) & (V[:, :, 1].max(1) < floor + SOLE)
# KNEE > 0: leg faces within KNEE m of a knee-cop vertex (set c: at 0.6 the bent knee of the seated clips let the greave/knee-cop
# inside show through the cut thigh, Sc2_KIRA16b)
knee = (part == 5) & (dmin(P[pv(part == 11)]) < float(E('KNEE', '0'))) if float(E('KNEE', '0')) > 0 else np.zeros(nf, bool)
comp = g['comp']; small = (np.bincount(comp)[comp] <= SMALL) & ~np.isin(part, (20, 21, 22, 23))
for nm_, m_ in (('hairline', hairline), ('braid root', broot), ('collar', collar), ('hair clearance', clear), ('wrist', wrist),
                ('junction', junction), ('fingertips', tip), ('contact', contact), ('soles', sole), ('knee', knee), ('small', small)):
    rep_keep[nm_] = int((m_ & ~keep).sum()); keep |= m_
if E('EXTRA', ''):
    for x in E('EXTRA', '').split(','):
        ex = np.load(x); rep_keep[x] = int((ex & ~keep).sum()); keep |= ex
group = np.zeros(nf, int)
group[part == 0] = 1; group[part == 21] = 2; group[part == 23] = 3; group[part == 7] = 4
group[np.isin(part, (9, 10, 11, 12, 13))] = 5; group[part == 5] = 6
group[keep] = 0
print('kept (added in order):', rep_keep)
for p_ in np.unique(part):
    s = part == p_
    print(f'part {p_:2d} {s.sum():5d} keep {int((s & keep).sum()):5d} free {int((s & ~keep).sum()):5d} groups',
          {int(k): int((group[s & ~keep] == k).sum()) for k in np.unique(group[s & ~keep])})
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'free', int((~keep).sum()), 'of', nf)
z = np.zeros(nf, bool)
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=z, lined=z, pair=g['pair'],
         twin=g['twin'], part=part, mat=g['mat'])
