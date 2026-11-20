#!/usr/bin/env python3
"""Keep / drop / group sets per face of work/mesh_in.npz (welded source, Blender frame) for decimate_tex.py, from the creature
project's part labels on the installed GLB (work/glb_parts.npz) and its final rest mesh (work/final_faces.npz: graft_s per vertex).
Kept exactly (prio-1 relaxed set): face/neck skin and eyes (parts 20, 22), the sleeve-end linings and the outer rings they line,
the hand-graft junction (any vertex 0 < graft_s < 0.999, or Hand/Finger and Forearm weight both > JUNC), the grip contact (hand
faces within GRIPD of a weapon face at rest: weapons are rigid to the fists), the soles (faces reaching below floor + SOLE), the
waist lap (sash and skirt faces within WAIST of the other garment), every small piece (connected component <= SMALL faces) and the
weapons (WEAPON=keep, default; WEAPON=shield: the shield's plates go to group 4).
Dropped (DROP_SKIRT_LINING=1): the skirt lining (inner flipped copy on one dark texel), rebuilt from the reduced skirt on export.
Groups (REA_GROUP_RATIOS): 1 hands, 2 helmet, 3 skirt outer, 4 shield plates, 5 boots, 6 pants; 0 = coat, sash (and what is not
grouped by SET_GROUPS).
Usage: make_sets.py <tag> -> work/keep_<tag>.npy, work/drop_<tag>.npy, work/groups_<tag>.npy, work/face_labels.npz"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
tag = sys.argv[1]
E = lambda k, v: float(os.environ.get(k, v))
SOLE, GRIPD, SMALL, JUNC, WAIST = E('SOLE', .02), E('GRIPD', .015), int(E('SMALL', 100)), E('JUNC', .02), E('WAIST', .02)
d = np.load(HERE / 'work' / 'mesh_in.npz'); V, F = d['verts'], d['faces']
mat = (d['wuv'].reshape(-1, 3, 2)[:, 0, 0] // 2).astype(int)
g = np.load(HERE / 'work' / 'glb_parts.npz')
gc = g['cen'][:, [0, 2, 1]] * [1, -1, 1]                      # glTF y-up -> Blender z-up
fc = V[F].mean(1)
off = np.median(gc, 0) - np.median(fc, 0)
for _ in range(5):
    dist, nn = cKDTree(gc).query(fc + off); off += np.median(gc[nn] - (fc + off), 0)
assert dist.max() < 1e-4, dist.max()
part, lin, weap = g['part'][nn], g['lining'][nn].astype(bool), g['weapon'][nn]
assert (g['mat'][nn] == mat).all()
P = lambda *n: np.isin(part, n)
fz = np.load(HERE / 'work' / 'final_faces.npz')
fco = fz['co'].reshape(-1, 3); fgs = fz['v_graft_s'][fz['tri'].reshape(-1)]
dd, vn = cKDTree(fco).query(V); assert dd.max() < 1e-4, dd.max()
gs = fgs[vn]
W = np.load(HERE / 'work' / 'src_weights.npz'); Wm, names = W['weights'], [str(n) for n in W['names']]
ws = lambda subs: Wm[:, [i for i, n in enumerate(names) if any(s in n for s in subs)]].sum(1)
keep = np.zeros(len(F), bool)
face = P(20, 22); keep |= face
# sleeve ends: linings and the outer rings they line
sl = P(1) & lin
outer_sl = P(1) & ~lin & (cKDTree(fc[sl]).query(fc)[0] < 0.006)
keep |= sl | outer_sl
drop = P(7) & lin if os.environ.get('DROP_SKIRT_LINING', '1') == '1' else np.zeros(len(F), bool)
keep |= P(7) & lin & ~drop
hand = P(0)
hw, fw = ws(['Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky']), ws(['Forearm'])
junction = hand & (((gs[F] > 0) & (gs[F] < 0.999)).any(1) | ((hw[F] > JUNC) & (fw[F] > JUNC)).any(1))
wv = np.unique(F[mat == 3])
contact = hand & (cKDTree(V[wv]).query(fc)[0] < GRIPD)
keep |= junction | contact
# DISTAL=1 (giant pass 2): the 2nd/3rd phalanges (the pads round the grips) stay exact; palm, back of hand and proximal phalanges are cut
import re
dom = np.array(names)[Wm.argmax(1)]
distal = hand & np.vectorize(lambda x: bool(re.search(r'(Index|Middle|Ring|Pinky|Thumb)[23]$', x)))(dom[F]).any(1)
if os.environ.get('DISTAL', '0') == '1':
    keep |= distal
floor = V[:, 2].min(); sole = V[F][:, :, 2].min(1) < floor + SOLE; keep |= sole
sash_v, skirt_v = np.unique(F[P(9)]), np.unique(F[P(7) & ~lin])
waist = (P(9) & (cKDTree(V[skirt_v]).query(fc)[0] < WAIST)) | (P(7) & ~lin & (cKDTree(V[sash_v]).query(fc)[0] < WAIST))
keep |= waist
key = np.round(V, 6); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel(); t_ = inv[F]; n_ = inv.max() + 1
r_ = np.concatenate([t_[:, 0], t_[:, 1], t_[:, 2]]); c_ = np.concatenate([t_[:, 1], t_[:, 2], t_[:, 0]])
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n_, n_)), directed=False)
fl = lab[t_[:, 0]]; cnt = np.bincount(fl); small = (cnt[fl] <= SMALL) & ~P(20, 22); keep |= small
WEAPON = os.environ.get('WEAPON', 'keep')
shield_plate = np.zeros(len(F), bool)
if WEAPON == 'keep':
    keep |= mat == 3
else:
    keep |= (mat == 3) & (weap == 1)
    # shield: its biggest piece's faces (outer and inner plates) form group 4; rim faces (the plate's open border ring) stay exact
    sh = (mat == 3) & (weap == 2)
    big = fl == np.bincount(fl[sh]).argmax()
    rimv = set()
    e = np.sort(np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])[np.repeat(sh & big, 3).reshape(3, -1).T.reshape(-1) if False else np.tile(sh & big, 3)], 1)
    u, c = np.unique(e, axis=0, return_counts=True); bv = np.unique(u[c == 1])
    rim = sh & big & np.isin(F, bv).any(1)
    shield_plate = sh & big & ~rim
    keep |= (mat == 3) & ~shield_plate
keep &= ~drop
groups = np.zeros(len(F), int)
GROUPS = os.environ.get('SET_GROUPS', '1,2,3,4,5,6').split(',')
for gid, sel in ((1, hand), (2, P(21)), (3, P(7) & ~lin), (4, shield_plate), (5, P(6)), (6, P(5))):
    if str(gid) in GROUPS:
        groups[sel & ~keep & ~drop] = gid
names_ = {0: 'coat/sash rest', 1: 'hands', 2: 'helmet', 3: 'skirt outer', 4: 'shield plates', 5: 'boots', 6: 'pants'}
for k, n in names_.items():
    print(f'group {k} {n:16s} {int(((groups == k) & ~keep & ~drop).sum()):6d}')
print('kept: face/eyes', int(face.sum()), 'sleeve linings+rings', int((sl | outer_sl).sum()), 'junction', int(junction.sum()), 'contact', int((contact & ~junction).sum()),
      'soles', int(sole.sum()), 'waist', int(waist.sum()), 'small', int(small.sum()), 'distal', int((distal & keep).sum()), 'weapons', int((keep & (mat == 3)).sum()), 'dropped skirt lining', int(drop.sum()))
print('parts free', {int(p): int((~keep & ~drop & (part == p)).sum()) for p in np.unique(part)})
print('TOTAL keep', int(keep.sum()), 'drop', int(drop.sum()), 'free', int((~keep & ~drop).sum()), 'of', len(F), f'protected share {keep.mean():.3f}')
np.save(HERE / 'work' / f'keep_{tag}.npy', keep); np.save(HERE / 'work' / f'groups_{tag}.npy', groups); np.save(HERE / 'work' / f'drop_{tag}.npy', drop)
np.savez(HERE / 'work' / 'face_labels.npz', part=part, lining=lin, weapon=weap, mat=mat, cen=fc)
