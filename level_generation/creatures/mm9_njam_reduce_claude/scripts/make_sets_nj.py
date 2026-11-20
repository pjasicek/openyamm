#!/usr/bin/env python3
"""Keep / group / lining sets per installed LOD0 face (glb_parts order: Njam limbs, NjTorso, NjHead) for mpqem.py, from the
finished master's part labels (work/glb_parts.npz). Njam parts (finish/clean_nj): 0 MPFB hands, 1 coat with sleeves and fur,
5 hose, 6 boots, 7 coat skirt (lining 1 = finish_nj's inner copy, lining 2 = the dark cap), 9 belt band, 10 buckle/brooch pieces,
20 head skin (face, ears, scalp, neck tube), 21 hair helmet, 23 hair lip (the rolled rim's underside).
Townsfolk relaxed keep set (REDUCTION_AGENT_TOWNSFOLK.md), exact:
- the whole head skin (20: face, ears, neck and its seam), the hair lip (23) and the hairline (hair faces with a vertex within
  HAIRLINE m of a lip vertex), the belt (9) and the buckle pieces (10), the cap, soles (boot faces within SOLE m of the floor),
  the hand-graft junction (hand faces on an open edge of the hands or sharing a vertex with a non-hand face, + JRINGS rings),
  the neck seam (body faces with a vertex within NECK m of a head-set vertex), connected pieces of up to SMALL faces;
- optional (gate_keeps.py style): SHOULDER=1 faces with a Clavicle/UpperArm-dominated vertex; CONTACT=1 faces within R m of the
  other hand in CLIPS.
Groups (own ratio in mpqem MP_GROUPS): 1 hands, 2 hair, 3 skirt outer, 4 boots above the soles, 5 hose; 0 coat (ladder ratio).
Linings (lining 1) are dropped and re-emitted by mpqem from the cut skirt; lined = the skirt's outer faces.
Usage: make_sets_nj.py <tag> -> work/glb_sets_<tag>.npz"""
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
tag = sys.argv[1]
E = lambda k, d: os.environ.get(k, d)
SMALL = int(E('SMALL', '60')); SOLE = float(E('SOLE', '0.012')); JRINGS = int(E('JRINGS', '2'))
HL = float(E('HAIRLINE', '0.012')); NECK = float(E('NECK', '0.015'))
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part'].copy(); lin = g['lining']; mat = g['mat']
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_njam.glb', 'Njam')
PR = ['Njam', 'NjTorso', 'NjHead']; nf = [len(D[k]['T']) for k in PR]; off = np.cumsum([0] + nf)
assert off[-1] == len(part)
N = off[-1]; keep = np.zeros(N, bool); group = np.zeros(N, int)
lining = lin == 1; cap = lin == 2
Pm = lambda *n: np.isin(part, n)
keep |= Pm(20, 23, 9, 10) | cap
if E('SKIRT', '1') == '0':
    keep |= Pm(7) & ~lining                                    # set b: the skirt exact (skirt gate, a50 CowerLoop 0.6 -> 6.5 cm)
# per primitive welded topology
FT = np.zeros((N, 3), np.int64); base = 0; PP = []
for k, name in enumerate(PR):
    P, T = D[name]['P'], D[name]['T']
    _, wv = np.unique(np.round(P, 6), axis=0, return_inverse=True); wv = wv.ravel()
    FT[off[k]:off[k + 1]] = wv[T] + base; q = np.zeros((wv.max() + 1, 3)); q[wv] = P; PP.append(q); base += wv.max() + 1
nW = base; allP = np.vstack(PP)
floor = min(D[n]['P'][:, 1].min() for n in PR)
sole = Pm(6) & (allP[FT][:, :, 1].min(1) < floor + SOLE); keep |= sole
# hairline: hair faces near the lip
lipv = np.unique(FT[Pm(23)].ravel())
hl = Pm(21) & (cKDTree(allP[lipv]).query(allP[FT].reshape(-1, 3))[0].reshape(-1, 3).min(1) < HL); keep |= hl
# hand-graft junction
hand = Pm(0)
ed = np.sort(np.vstack([FT[hand][:, [0, 1]], FT[hand][:, [1, 2]], FT[hand][:, [2, 0]]]), 1)
u, c = np.unique(ed, axis=0, return_counts=True)
other = np.zeros(nW, bool); other[u[c == 1].ravel()] = True; other[FT[~hand].ravel()] = True
junc = hand & other[FT].any(1)
for _ in range(JRINGS):
    hot = np.zeros(nW, bool); hot[FT[junc].ravel()] = True; junc |= hand & hot[FT].any(1)
keep |= junc
# neck seam
headP = D['NjHead']['P']; tree = cKDTree(headP)
neck = np.zeros(N, bool)
for k, name in enumerate(PR[:2]):
    P, T = D[name]['P'], D[name]['T']; d, _ = tree.query(P); neck[off[k]:off[k + 1]] = (d < NECK)[T].any(1)
keep |= neck
# connected pieces
r_ = np.concatenate([FT[:, 0], FT[:, 1], FT[:, 2]]); c_ = np.concatenate([FT[:, 1], FT[:, 2], FT[:, 0]])
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(nW, nW)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl)
small = (cnt[fl] <= SMALL) & ~lining; keep |= small
for p in np.unique(part):
    s = part == p; b = np.bincount(fl[s]); print(f'  part {p:2d} pieces {sorted(b[b > 0].tolist(), reverse=True)[:12]}')
extra = {}
if E('SHOULDER', '0') == '1' or E('CONTACT', '0') == '1':
    from glb_pose import Glb, Model  # noqa: E402
    m = Model(Glb(str(HERE / 'before' / 'mm9_njam.glb')))
    names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
    MP = m.primitives; assert [len(p['triangles']) for p in MP] == nf
    dom = [np.array([jn[p['joints'][v][np.argmax(p['weights'][v])]] for v in range(len(p['positions']))]) for p in MP]
    if E('SHOULDER', '0') == '1':
        sh = np.zeros(N, bool)
        for k, p in enumerate(MP):
            sv = np.array([d.endswith('Clavicle') or d.endswith('UpperArm') for d in dom[k]])
            sh[off[k]:off[k + 1]] = sv[p['triangles']].any(1)
        sh &= ~lining & ~Pm(20, 21, 23); extra['shoulder'] = sh
    if E('CONTACT', '0') == '1':
        R = float(E('R', '0.03')); clips = E('CLIPS', 'Fidget').split(','); hit = np.zeros(N, bool)
        isarm = lambda d, side: f' {side} ' in d and any(x in d for x in ('Hand', 'Forearm', 'UpperArm', 'Clavicle', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))
        ishand = lambda d, side: f' {side} ' in d and not any(d.endswith(x) for x in ('Forearm', 'UpperArm', 'Clavicle')) and \
            any(x in d for x in ('Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))
        own = {s: [np.array([isarm(d, s) for d in dk]) for dk in dom] for s in 'LR'}
        hv = {s: [np.array([ishand(d, s) for d in dk]) for dk in dom] for s in 'LR'}
        FPS = float(E('FPS', '0'))
        for cl in clips:
            t1 = m.clip_times(cl)[-1]
            for t in (np.append(np.arange(0, t1, 1 / FPS), t1) if FPS else m.clip_times(cl)[::2]):
                P = [x[0] for x in m.skinned_positions(m.world(m.sample(cl, t)))]
                for s in 'LR':
                    H = np.vstack([P[k][hv[s][k]] for k in range(len(MP))]); tr = cKDTree(H)
                    for k, p in enumerate(MP):
                        T = p['triangles']; d, _ = tr.query(P[k][T].mean(1), distance_upper_bound=R)
                        hit[off[k]:off[k + 1]] |= (d < R) & ~own[s][k][T].all(1)
        cen = np.vstack([MP[k]['positions'][MP[k]['triangles']].mean(1) for k in range(len(MP))])
        mir = cKDTree(cen).query(cen[hit] * [-1, 1, 1]); hit[mir[1][mir[0] < 0.004]] = True
        hit &= ~lining; extra['contact'] = hit
    for k_, v_ in extra.items():
        print(k_, 'faces', int(v_.sum()), 'new', int((v_ & ~keep).sum())); keep |= v_
for f in E('EXTRA', '').split(','):   # e.g. work/fingertips.npy (fingertips.py), work/collapse_keep.npy (collapse_keep.py)
    if f:
        x = np.load(HERE / f); print('EXTRA', f, int(x.sum()), 'new', int((x & ~keep).sum())); keep |= x & ~lining
keep &= ~lining
# lined outer faces: the skirt's outer face nearest each lining face's centroid
cen = g['cen']; o = np.flatnonzero(Pm(7) & ~lining & ~cap); l = np.flatnonzero(lining)
dd, kk = cKDTree(cen[o]).query(cen[l]); lined = np.zeros(N, bool); lined[o] = True    # finish_nj lined the whole skirt (part 7)
print(f'lining {len(l)} -> outer twins {len(np.unique(kk))} of {len(o)}, centroid gap median {np.median(dd)*1000:.2f} max {dd.max()*1000:.2f} mm')
group[Pm(0)] = 1; group[Pm(21)] = 2; group[Pm(7)] = 3; group[Pm(6)] = 4; group[Pm(5)] = 5
group[keep | lining] = 0
for p in np.unique(part):
    s = part == p
    print(f'part {p:2d} {s.sum():6d} keep {int((s & keep).sum()):5d} lining {int((s & lining).sum()):4d} free {int((s & ~keep & ~lining).sum()):5d} lined {int((s & lined).sum()):4d}')
print('soles', int(sole.sum()), 'junction', int(junc.sum()), 'hairline', int(hl.sum()), 'neck', int(neck.sum()), 'small', int(small.sum()))
print('TOTAL keep', int(keep.sum()), f'({keep.mean()*100:.1f} %)', 'lining', int(lining.sum()), 'free', int((~keep & ~lining).sum()), 'of', N,
      '| groups', {k: int(((group == k) & ~keep & ~lining).sum()) for k in range(6)})
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=lining, lined=lined, part=part, mat=mat, **extra)
