#!/usr/bin/env python3
"""Keep / group / drop sets per face of work/mesh_in.npz (welded source, Blender frame) from the finished master's part labels on
the installed GLB (work/glb_parts.npz, glb_parts.py). Copied from mm9_highwayman_reduce_claude; Guard parts (clean_guard NAMES):
0 hands (MPFB graft), 1 tunic, 2 face/neck skin, 3 helmet, 5 pants, 6 boot, 7 skirt, 8 gauntlet, 9 belt, 10 buckle, 11 badge,
13 brooch, 14 fin, 15 bit.
Prio-1 relaxed keep set (REDUCTION_BRIEF_20261104):
- exact: face/neck skin (2: the face of the head set and the neck seam), soles (boot faces within SOLE m of the floor), the
  hand-graft junction (hand faces within JRINGS face rings of the MPFB wrist opening or a non-hand face), the grip contact
  (work/grip_contact.npy: hand faces within 1.5 cm of the halberd at 6 times of every clip), the body under resting hands and
  beside the halberd (work/contact.npy, contact.py; CONTACT=0 skips it), the buckle (BUCKLE=1), the right hand's 2nd/3rd
  phalanges (DISTAL=1: the grip wrap; the Clan Soldier's lesson), the helmet rim on the face (helmet faces within RIM m of a
  face-skin vertex), the helmet under the cheek/eye plates (helmet faces within PLATE m of either plate attachment, so the
  plates' 7 mm clearance holds), the shoulder fans (finish_guard's dark fans over the cap openings), the belt (BELT=1),
  connected pieces of up to SMALL faces;
- dropped and re-emitted from the reduced outer shell's twins (mpqem.py): every lining face (finish_guard's inner copies);
- groups (own ratio): 1 hands, 2 helmet, 3 skirt, 4 boots above the soles, 5 pants, 6 gauntlets (b55 detached them at the shared cut);
- label 0: tunic and anything else not kept (the shared cut).
Also writes work/lined_<tag>.npy (outer faces with a lining twin). Usage: make_sets.py <tag>"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio  # noqa: E402
tag = sys.argv[1]
E = lambda k, d: os.environ.get(k, d)
SMALL = int(E('SMALL', '60')); SOLE = float(E('SOLE', '0.03')); JRINGS = int(E('JRINGS', '2'))
RIM = float(E('RIM', '0.012')); PLATE = float(E('PLATE', '0.012'))
d = np.load(HERE / 'work' / 'mesh_in.npz'); V, F = d['verts'], d['faces']
g = np.load(HERE / 'work' / 'glb_parts.npz')
gc = g['cen'][:, [0, 2, 1]] * [1, -1, 1]                      # glTF y-up -> Blender z-up
gc[:, 2] += V[:, 2].min()                                      # GLB mesh stands on y = 0; the Blender mesh is in the rig frame
fc = V[F].mean(1)
dist, nn = cKDTree(gc).query(fc); print('face match max', dist.max()); assert dist.max() < 1e-4
part = g['part'][nn]; lining = g['lining'][nn].astype(bool)
P = lambda *n: np.isin(part, n)
key = np.round(V, 6); _, wv = np.unique(key, axis=0, return_inverse=True); wv = wv.ravel(); FT = wv[F]; nW = wv.max() + 1
# shoulder fans: lining faces that share a vertex position with the outer surface (the inner copies sit 3 mm inside)
outerv = np.zeros(nW, bool); outerv[FT[~lining].ravel()] = True
fan = lining & outerv[FT].any(1)
print('fans', int(fan.sum()))
lining &= ~fan
keep = np.zeros(len(F), bool)
keep |= P(2) | fan
floor = V[:, 2].min(); sole = P(6) & (V[F][:, :, 2].min(1) < floor + SOLE); keep |= sole
# hand-graft junction: hand faces on an open edge of the hand piece or touching a non-hand face, JRINGS rings
hand = P(0)
ed = np.sort(np.vstack([FT[hand][:, [0, 1]], FT[hand][:, [1, 2]], FT[hand][:, [2, 0]]]), 1)
u, c = np.unique(ed, axis=0, return_counts=True)
other = np.zeros(nW, bool); other[u[c == 1].ravel()] = True; other[FT[~hand].ravel()] = True
junc = hand & other[FT].any(1)
for _ in range(JRINGS):
    hot = np.zeros(nW, bool); hot[FT[junc].ravel()] = True; junc |= hand & hot[FT].any(1)
keep |= junc
for name in ('grip_contact', 'contact'):
    f = HERE / 'work' / f'{name}.npy'
    if f.exists() and E(name.upper(), '1') == '1':
        m = np.load(f); src = gc[m]
        hit = cKDTree(src).query(fc)[0] < 1e-4 if len(src) else np.zeros(len(F), bool)
        keep |= hit; print(name, int(hit.sum()))
# right-hand 2nd/3rd phalanges (dominant joint) from the installed GLB weights, mapped by face centroid
doc, binary = bglbio.read(HERE / 'before' / 'mm9_guard.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Guard' and 'mesh' in n)
jn = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
pr = bglbio.prims(doc, binary, node['mesh'])[0]
dom = np.array(jn)[pr['JOINTS_0'][np.arange(len(pr['JOINTS_0'])), pr['WEIGHTS_0'].argmax(1)].astype(int)]
distal_names = [f'Bip01 {s} {f}{k}' for s in E('DISTAL_SIDES', 'R') for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky') for k in (2, 3)]
if E('DISTAL', '1') == '1':
    dv = np.isin(dom, distal_names)
    gf = dv[pr['T']].all(1)                      # GLB Guard_A faces whose three vertices are distal-dominant
    nA = len(pr['T'])
    hit = cKDTree(gc[:nA][gf]).query(fc)[0] < 1e-4
    keep |= hit & hand; print('distal phalanges', int((hit & hand).sum()))
# helmet rim on the face skin
skinv = np.unique(F[P(2)].ravel())
rim = P(3) & ~lining & (cKDTree(V[skinv]).query(V[F].reshape(-1, 3))[0].reshape(-1, 3).min(1) < RIM)
keep |= rim; print('helmet rim on face', int(rim.sum()))
# helmet under the plates (attachments on Bip01 Head, in its joint space -> bind space -> Blender frame)
ibm = bglbio.acc(doc, binary, doc['skins'][0]['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)[jn.index('Bip01 Head')]
bind = np.linalg.inv(ibm.astype(np.float64)); pts = []
for nm in ('mm9_guard_plate_a', 'mm9_guard_plate_c'):
    pd_, pb_ = bglbio.read(HERE / 'before' / f'{nm}.glb')
    pp = bglbio.prims(pd_, pb_, pd_['nodes'][0]['mesh'])[0]['POSITION'].astype(np.float64)
    pts.append((np.c_[pp, np.ones(len(pp))] @ bind.T)[:, :3])
pts = np.vstack(pts); pts = pts[:, [0, 2, 1]] * [1, -1, 1]; pts[:, 2] += V[:, 2].min()
under = P(3) & ~lining & (cKDTree(pts).query(V[F].reshape(-1, 3))[0].reshape(-1, 3).min(1) < PLATE)
keep |= under; print('helmet under the plates', int(under.sum()))
if E('BELT', '1') == '1':
    keep |= P(9); print('belt kept', int(P(9).sum()))
if E('GAUNTLET', '0') == '1':
    # d55: the cut gauntlets came 0.9-1.1 cm off the sleeve in 5-10 of 663 poses (detached_parts_audit); keep them and the
    # sleeve within GSLEEVE m of them exactly
    gv = np.unique(F[P(8) & ~lining].ravel()); GS = float(E('GSLEEVE', '0.025'))
    near = P(1) & ~lining & (cKDTree(V[gv]).query(V[F].reshape(-1, 3))[0].reshape(-1, 3).min(1) < GS)
    keep |= (P(8) & ~lining) | near; print('gauntlets kept', int((P(8) & ~lining).sum()), 'sleeve beside them', int(near.sum()))
if E('BUCKLE', '1') == '1':
    keep |= P(10); print('buckle kept', int(P(10).sum()))
# connected pieces (by welded position)
r_ = np.concatenate([FT[:, 0], FT[:, 1], FT[:, 2]]); c_ = np.concatenate([FT[:, 1], FT[:, 2], FT[:, 0]])
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(nW, nW)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl)
small = (cnt[fl] <= SMALL) & ~lining; keep |= small
for p in np.unique(part):
    s = part == p; sizes = sorted(np.bincount(fl[s])[np.bincount(fl[s]) > 0].tolist(), reverse=True)
    print(f'  part {p:2d} pieces {sizes[:14]}')
drop = lining.copy()
outer = ~lining
lined = np.zeros(len(F), bool)
for p in np.unique(part[lining]):
    o = np.where(outer & (part == p) & ~fan)[0]; l = np.where(lining & (part == p))[0]
    dd, k = cKDTree(fc[o]).query(fc[l]); lined[o[k]] = True
    # nearest centroids pair a few lining faces with the same outer face; also mark every outer face whose 3 mm inward copy
    # (face normal) lands on a lining centroid
    fn = np.cross(V[F[o, 1]] - V[F[o, 0]], V[F[o, 2]] - V[F[o, 0]]); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-20)
    d2, _ = cKDTree(fc[l]).query(fc[o] - 0.003 * fn); add = o[d2 < 0.0008]; n0 = int(lined.sum()); lined[add] = True
    print(f'  lining part {p}: {len(l)} faces -> outer twins {len(np.unique(k))} (+{int(lined.sum()) - n0} by offset), centroid gap median {np.median(dd)*1000:.2f} mm max {dd.max()*1000:.2f}')
keep &= ~drop
groups = np.zeros(len(F), int)
groups[P(0) & ~keep] = 1; groups[P(3) & ~keep & ~drop] = 2; groups[P(7) & ~keep] = 3; groups[P(6) & ~keep] = 4
groups[P(5) & ~keep] = 5; groups[P(8) & ~keep & ~drop] = 6
for p in np.unique(part):
    s = part == p
    print(f'part {p:2d} {s.sum():6d} keep {int((s & keep).sum()):5d} drop {int((s & drop).sum()):5d} free {int((s & ~keep & ~drop).sum()):5d} lined {int((s & lined).sum()):4d}')
print('soles', int(sole.sum()), 'junction', int(junc.sum()), 'small', int(small.sum()))
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'drop', int(drop.sum()), 'free', int((~keep & ~drop).sum()), 'of', len(F),
      '| groups', {k: int((groups == k).sum()) for k in (1, 2, 3, 4, 5, 6)}, '| shared', int(((groups == 0) & ~keep & ~drop).sum()))
for n, a in (('keep', keep), ('groups', groups), ('drop', drop), ('lined', lined), ('fan', fan)):
    np.save(HERE / 'work' / f'{n}_{tag}.npy', a)
np.save(HERE / 'work' / 'face_part.npy', part)
