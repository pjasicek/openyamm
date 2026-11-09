#!/usr/bin/env python3
"""Part labels and keep/group sets for the ladder, per face of work/mesh_in.npz (welded source, same order as the GLB).
Labels come from the creature's final rest mesh (work/final_faces.npz, dump_parts_blend.py), matched by centroid after
fitting the offset (export_dwarf.py lifted the rig so the soles sit at 0). Beard vs face skin from the head region mask
(R = beard), sampled at each head face's UV centroid.
Keep exactly (brief): face skin, eyes, neck tube (head parts 20 non-beard, 22, 24), gloves/hands (part 0), linings
(skirt 220, boot cuffs 304) and the whole boot cuff (11), belt (9), shoulder plates/trims (12), the whole skirt (7: hem,
SkirtLeg/hinge gates), the axe (30, grip and thin blade), the bracer's end round the glove (part 1 faces
whose vertices carry any hand weight, about its last 3.5 cm, or lie within WRIST_CM of a glove vertex: the wrist-gap gate), soles (boot faces
below SOLE_CM), small pieces (connected components up to 80 faces).
Groups (REA_GROUPS): 1 beard, 2 helmet, 3 horns, 4 pants, 5 hands (CUT_HANDS=1); label 0 = voxel skin (tunic, sleeves, forearms), boots.
Env: WRIST_CM (1), SOLE_CM (6), KEEP_BEARD/KEEP_HELMET/KEEP_HORNS=1 to keep a head layer exactly.
Writes work/keep.npy, work/groups.npy, work/labels.npz and prints the protected share."""
import os
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

HERE = Path(__file__).resolve().parents[1]
W = HERE / 'work'
m = np.load(W / 'mesh_in.npz'); F = np.load(W / 'final_faces.npz'); sw = np.load(W / 'src_weights.npz')
V, T = m['verts'], m['faces']; wuv = m['wuv'].reshape(-1, 3, 2)
mat = (wuv[:, 0, 0] // 2).astype(int)
cen = V[T].mean(1)
fc = F['cen']
off = np.median(cen, 0) - np.median(fc, 0)
for _ in range(6):
    d, nn = cKDTree(cen).query(fc + off); off += np.median(cen[nn] - (fc + off), 0)
d, nn = cKDTree(fc + off).query(cen)
print('MAP offset', np.round(off, 4), 'median', np.median(d), 'p99', np.percentile(d, 99), 'max', d.max(),
      'unique', len(np.unique(nn)), 'of', len(cen), 'mat agree', (F['mat'][nn] == mat).mean())
part, lining = F['part'][nn].copy(), F['lining'][nn].astype(bool)
# beard by the head region mask (R) at the UV centroid
mask = np.asarray(Image.open(HERE.parent / 'mm9_dwarf_claude' / 'textures' / 'dwarf_head_region_mask.png').convert('RGB'), np.float32) / 255
uvc = wuv.mean(1); uvc[:, 0] -= 2 * mat
h, w_ = mask.shape[:2]
px = np.clip((uvc[:, 0] % 1) * w_, 0, w_ - 1).astype(int); py = np.clip((1 - uvc[:, 1] % 1) * h, 0, h - 1).astype(int)
beardv = mask[py, px, 0]
beard = (part == 20) & (beardv > 0.5)
# hand weight per vertex
names = [str(n) for n in sw['names']]; Wt = sw['weights']
handcols = [i for i, n in enumerate(names) if any(k in n for k in (' Hand', 'Index', 'Middle', 'Ring', 'Pinky', 'Thumb'))]
handw = Wt[:, handcols].sum(1)
WRIST = float(os.environ.get('WRIST_CM', '1')) / 100
glove_v = np.unique(T[part == 0])
dg, _ = cKDTree(V[glove_v]).query(V)
wrist = (part == 1) & ((handw[T].max(1) > 1e-3) | (dg[T].min(1) < WRIST))
floor = V[:, 2].min(); SOLE = float(os.environ.get('SOLE_CM', '6')) / 100
sole = (part == 6) & (V[T][:, :, 2].max(1) < floor + SOLE)
# connected components by shared vertices
n = len(T); rows = np.repeat(np.arange(n), 3); A = coo_matrix((np.ones(3 * n), (rows, T.ravel())), shape=(n, len(V))).tocsr()
ncomp, comp = connected_components(A @ A.T, directed=False)
csize = np.bincount(comp)[comp]
small = csize <= 80
# prio-1 relaxed set (brief, 2026-11-04): hands may be cut (0.6-0.75) keeping the graft junction (glove top inside the
# bracer: faces within JUNCTION_CM of the voxel skin) and the grip contact (work/grip_contact.npy: faces within 1.5 cm of the axe
# in any clip, posed; the rest pose holds an open hand)
skin_v = np.unique(T[part == 1]); ds, _ = cKDTree(V[skin_v]).query(V)
junction = (part == 0) & (ds[T].min(1) < float(os.environ.get('JUNCTION_CM', '2')) / 100)
contact = (part == 0) & (np.load(W / 'grip_contact.npy') if (W / 'grip_contact.npy').exists() else False)  # posed, grip_contact.py
cut_hands = os.environ.get('CUT_HANDS') == '1'
keep = ((part == 0) & ((not cut_hands) | junction | contact)) | ((part == 20) & ~beard) | np.isin(part, (22, 24, 11, 9, 12, 7, 30)) | lining | wrist | sole | small
groups = np.zeros(n, int)
groups[beard] = 1; groups[part == 0] = 5; groups[part == 21] = 2; groups[part == 23] = 3; groups[part == 5] = 4
for g, env in ((1, 'KEEP_BEARD'), (2, 'KEEP_HELMET'), (3, 'KEEP_HORNS')):
    if os.environ.get(env) == '1':
        keep |= groups == g
groups[keep] = 0
np.save(W / 'keep.npy', keep); np.save(W / 'groups.npy', groups)
print('HANDS junction', int(junction.sum()), 'contact', int(contact.sum()), 'cut' if cut_hands else 'kept')
np.savez(W / 'labels.npz', junction=junction, contact=contact, part=part, lining=lining, beard=beard, wrist=wrist, sole=sole, small=small, comp=comp, mat=mat)
NAMES = {0: 'hands', 1: 'voxel skin', 5: 'pants', 6: 'boots', 7: 'skirt', 9: 'belt', 11: 'boot cuff', 12: 'plates',
         20: 'face+beard', 21: 'helmet', 22: 'eyes', 23: 'horns', 24: 'neck', 30: 'axe'}
print(f'{"part":12s} {"faces":>6s} {"kept":>6s}  notes')
for k in np.unique(part):
    s = part == k
    print(f'{NAMES.get(k, k):12s} {s.sum():6d} {(s & keep).sum():6d}  lining {(s & lining).sum()} beard {(s & beard).sum()} '
          f'wrist {(s & wrist).sum()} sole {(s & sole).sum()} small {(s & small).sum()}')
print('KEEP', int(keep.sum()), 'of', n, f'({keep.mean() * 100:.1f} %)', 'groups', np.bincount(groups[~keep]),
      'free (label 0)', int(((groups == 0) & ~keep).sum()))
print('components', ncomp, 'small', int(small.sum()))
