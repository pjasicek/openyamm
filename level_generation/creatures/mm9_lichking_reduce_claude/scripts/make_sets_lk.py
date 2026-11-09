#!/usr/bin/env python3
"""Keep / group sets per installed GLB LOD0 face (work/glb_parts.npz order: LichKing_LICHKING, LichKingHead, LichKingStaff,
LichKingStaffSkull_LICHKING) for mpqem.py, written to work/glb_sets_<tag>.npz (keep, group, lining, lined, part, mat).

Keep exactly (REDUCTION_BRIEF_20261104 relaxed set; boss extras of the 2026-11-05 assignment):
- the head skull (the face: the approved Lich's skull, 3,000) and the staff skull (439): their primitives whole;
- the staff primitive (shaft 260, crown cap 84, tube caps 148: already low, and the caps are the see-through fixes);
- the crown (846, boss extra) and the collar round the neck (178, the neck seam);
- the grip contact: hand faces within GRIP m of the staff surface (the r19 staff-in-palm solve);
- the hand/bracer junction: hand faces within CUFF m of a bracer vertex;
- soles: boot faces below floor + SOLE; connected pieces of up to SMALL faces;
- FINGERTIPS=1: hand faces whose dominant joint is a distal phalanx (Thumb3, Index3, ...);
- CONTACT=<tag>: the arm and leg contact faces of contact_lk.py (set c).
The coat's inner surface (684 faces, `inner` in glb_parts.npz) is the inside of Meshy's closed coat shell, not an offset twin of
the outer faces, so it cannot be re-emitted from the outer cut: it is its own group (3) cut by the same pose-aware collapse.
Groups: 1 hands + fingers (seam slides), 2 bracers, 3 coat inner surface, 4 trousers, 5 boots above the soles, 6 upper arms,
7 tabard, 8 rigid reliefs (buckle, medallions, knee medals), 9 collar wings; 0 = torso / coat outer (the ladder ratio).
Usage: make_sets_lk.py <tag>"""
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
tag = sys.argv[1]
E = lambda k, d: os.environ.get(k, d)
GRIP = float(E('GRIP', '0.008')); CUFF = float(E('CUFF', '0.015')); SOLE = float(E('SOLE', '0.015')); SMALL = int(E('SMALL', '40'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_lichking.glb', 'LichKing')
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']; names = [str(x) for x in g['names']]; inner = g['inner'].astype(bool)
PI = {n: i for i, n in enumerate(names)}
PR = ['LichKing_LICHKING', 'LichKingHead', 'LichKingStaff', 'LichKingStaffSkull_LICHKING']
P = np.concatenate([D[k]['P'] for k in PR]); offs = np.cumsum([0] + [len(D[k]['P']) for k in PR])
T = np.concatenate([D[k]['T'] + offs[i] for i, k in enumerate(PR)])
J = np.concatenate([D[k]['J'] for k in PR]); W = np.concatenate([D[k]['W'] for k in PR])
assert len(T) == len(part), (len(T), len(part))
assert np.allclose(P[T].mean(1), g['cen'], atol=1e-6)
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][i]['name'] for i in skin['joints']]
dom = J[np.arange(len(J)), W.argmax(1)]
floor = P[:, 1].min()
V = P[T]
isp = lambda *n: np.isin(part, [PI[x] for x in n])
pv = lambda *n: np.unique(T[isp(*n)].ravel())


def surface(faces, step=0.002):
    pts = []
    for t in T[faces]:
        a, b, c = P[t]; A = np.linalg.norm(np.cross(b - a, c - a)) / 2
        k = int(np.clip(np.sqrt(max(A, 1e-12)) / step, 1, 40))
        i, j = np.meshgrid(np.arange(k + 1), np.arange(k + 1)); m = i + j <= k
        w = np.stack([i[m], j[m], k - i[m] - j[m]], 1) / k
        pts.append(w @ P[t])
    return np.concatenate(pts)


near_pts = lambda pts, r: cKDTree(pts).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < r
keep = isp('skull', 'sskull', 'staff', 'cap', 'tubecap', 'crown', 'collar')
grip = isp('hands') & near_pts(surface(np.flatnonzero(isp('staff'))), GRIP)
cuff = isp('hands') & near_pts(P[pv('bracers')], CUFF)
sole = isp('boots') & (V[:, :, 1].min(1) < floor + SOLE)
tipj = np.array([any(s in n for s in ('Thumb3', 'Index3', 'Middle3', 'Ring3', 'Pinky3')) for n in jn])
tips = isp('hands') & tipj[dom[T]].all(1) if E('FINGERTIPS', '0') == '1' else np.zeros(len(T), bool)
keep |= grip | cuff | sole | tips
# CONTACT=<tag>: body faces the hands/bracers and the legs come near in the clips (contact_lk.py; set c after set a's gates)
contact = np.zeros(len(T), bool)
if E('CONTACT', ''):
    C = np.load(HERE / 'work' / f"contact_{E('CONTACT', '')}.npz"); nb = len(C['arm'])
    contact[:nb] = C['arm'] | C['leg']
    keep |= contact
# KEEP_PARTS=uarms,inner (set d, after c r50's see-through gate: sleeve holes 3,561 -> 3,891 px, torso inside 14,577 -> 17,737 px):
# whole parts kept exact; 'inner' = the coat's inner surface
# SHOULDER=1 (set f, after d r50: sleeve see-through holes 3,561 -> 3,896 px with the upper arms exact, and a larger sheen on the
# shoulder plate in Running): coat/torso outer faces with two or more corners dominated by a Clavicle or UpperArm bone (the shoulder
# plates of the torso shell) stay exact
if E('SHOULDER', '0') == '1':
    armj = np.array([any(x in n for x in ('Clavicle', 'UpperArm')) for n in jn])
    keep |= isp('torso') & ~inner & (armj[dom[T]].sum(1) >= 2)
for kp in [x for x in E('KEEP_PARTS', '').split(',') if x]:
    keep |= (isp('torso') & inner) if kp == 'inner' else isp(kp)
# connected pieces (welded by position)
_, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl); small = cnt[fl] <= SMALL; keep |= small
for p_ in np.unique(part):
    s = part == p_; sz = np.bincount(fl[s]); print(f'  part {names[p_]:7s} pieces {sorted(sz[sz > 0].tolist(), reverse=True)[:12]}')
group = np.zeros(len(T), int)
group[isp('hands')] = 1; group[isp('bracers')] = 2; group[isp('torso') & inner] = 3; group[isp('pants')] = 4
group[isp('boots')] = 5; group[isp('uarms')] = 6; group[isp('tabard')] = 7
group[isp('buckle', 'medal', 'kneemed', 'medalsF', 'medalsB')] = 8; group[isp('wings')] = 9
group[keep] = 0
for p_ in np.unique(part):
    s = part == p_
    print(f'part {p_:2d} {names[p_]:7s} {s.sum():5d} keep {int((s & keep).sum()):5d} free {int((s & ~keep).sum()):5d} groups',
          {int(k): int((group[s & ~keep] == k).sum()) for k in np.unique(group[s & ~keep])})
print('contact', int((contact & ~isp('crown')).sum()), 'grip', int(grip.sum()), 'cuff', int(cuff.sum()), 'soles', int(sole.sum()), 'tips', int(tips.sum()),
      'small', int((small & ~isp('skull', 'sskull', 'staff', 'cap', 'tubecap', 'crown', 'collar')).sum()))
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'free', int((~keep).sum()), 'of', len(T))
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=np.zeros(len(T), bool),
         lined=np.zeros(len(T), bool), part=part, mat=g['mat'])
