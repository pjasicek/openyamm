#!/usr/bin/env python3
"""Per-face keep / group sets on the installed Goat LOD0 (one primitive Goat) for mpqem.py: work/glb_sets_<tag>.npz.
Animal reading of the face rule (assignment: eyes, muzzle, nostrils, horns, ears, beard exact):
- exact: the small pieces (2 eye pieces, the beard), the head = head-weighted skin (Xheadpiv, Xhead, Xjawpiv, Xjaw, ears summed
  weight > 0.5: cranium, eyes, muzzle, nostrils, lips, mouth cavity, horns (rigid on Xheadpiv), ears) grown FACE_RING rings;
  hooves (dominant Xffoot*/Xbfoot*) plus HOOF_RING rings; soles (faces within SOLE of the floor);
- group BACK_GROUP (if set): head-weighted skin behind z BACK_Z that is neither horn nor ear (the back of the skull/poll);
- group 0: the rest (neck, body, legs, tail).
Optional work/keep_extra_<name>.npy. Usage: goat_sets.py <tag> [extras...]  (env FACE_RING, HOOF_RING, SOLE, BACK_GROUP, BACK_Z)"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
E = lambda k, d: os.environ.get(k, d)
FACE_RING = int(E('FACE_RING', '2')); HOOF_RING = int(E('HOOF_RING', '1')); SOLE = float(E('SOLE', '0.02'))
BACK_GROUP = int(E('BACK_GROUP', '0')); BACK_Z = float(E('BACK_Z', '0.47'))
tag = sys.argv[1]; extras = sys.argv[2:]
doc, b = gb.read(HERE / 'before' / 'mm9_goat.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Goat' and 'mesh' in n)
pr = gb.prims(doc, b, node['mesh']); assert [p['material'] for p in pr] == ['Goat']; pr = pr[0]
joints = [doc['nodes'][j]['name'] for j in doc['skins'][node['skin']]['joints']]
P, T, J, W = pr['POSITION'].astype(float), pr['T'], pr['JOINTS_0'], pr['WEIGHTS_0'].astype(float)
nF = len(T)
key = np.round(P, 6); _, wv = np.unique(key, axis=0, return_inverse=True); wv = wv.ravel(); FT = wv[T]; nW = wv.max() + 1
r_ = np.concatenate([FT[:, 0], FT[:, 1], FT[:, 2]]); c_ = np.concatenate([FT[:, 1], FT[:, 2], FT[:, 0]])
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(nW, nW)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl); main = cnt[fl] == cnt.max(); small = ~main
fw = np.zeros((nF, len(joints)))
for k in range(3):
    for c in range(4):
        np.add.at(fw, (np.arange(nF), J[T[:, k], c]), W[T[:, k], c])
fw /= 3; dom = fw.argmax(1); cen = P[T].mean(1)


def grow(sel, rings):
    sel = sel.copy()
    for _ in range(rings):
        vm = np.zeros(nW, bool); vm[FT[sel].ravel()] = True; sel |= vm[FT].any(1) & main
    return sel


ji = lambda names: [joints.index(n) for n in names]
headw = fw[:, ji(('Xheadpiv', 'Xhead', 'Xjawpiv', 'Xjaw', 'Xearpiv', 'Xear', 'Xearpiv01', 'Xear01'))].sum(1)
head = (headw > 0.5) & main
ears = np.isin(dom, ji(('Xearpiv', 'Xear', 'Xearpiv01', 'Xear01'))) & main
# horns: rigid on Xheadpiv and above the skull top (Xhead skin tops out about y 0.85)
horn = main & (fw[:, ji(('Xheadpiv',))[0]] > 0.9) & (cen[:, 1] > 0.80)
back = head & ~grow(horn | ears, 2) & (cen[:, 2] < BACK_Z) if BACK_GROUP else np.zeros(nF, bool)
face = grow(head & ~back, FACE_RING) & ~back
hoof = grow(np.isin(dom, ji(('Xffoot', 'Xffoot01', 'Xbfoot', 'Xbfoot01'))) & main, HOOF_RING)
floor = P[:, 1].min(); sole = (P[T][:, :, 1].min(1) < floor + SOLE) & main
keep = small | face | hoof | sole
for name in extras:
    k = np.load(HERE / 'work' / f'keep_extra_{name}.npy'); keep |= k; print('extra', name, int(k.sum()))
group = np.zeros(nF, int)
if BACK_GROUP:
    group[back & ~keep] = BACK_GROUP
print(f'faces {nF}: small pieces {int(small.sum())}, head {int(head.sum())} (horns {int(horn.sum())}, ears {int(ears.sum())}, '
      f'back of skull {int(back.sum())}), face exact {int(face.sum())}, hooves {int(hoof.sum())}, soles {int(sole.sum())}')
for gl in np.unique(group):
    print(f'group {gl}: free {int(((group == gl) & ~keep).sum())} (of {int((group == gl).sum())})')
print(f'protected share {keep.sum() / nF * 100:.1f} % ({int(keep.sum())} of {nF}); free {int((~keep).sum())}; '
      f'-15 % = {int(round(0.15 * nF))} tris = {0.15 * nF / max(1, (~keep).sum()) * 100:.0f} % of the free faces')
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=np.zeros(nF, bool), lined=np.zeros(nF, bool),
         face=face, head=head, horn=horn, ears=ears, back=back, hoof=hoof, sole=sole, small=small)
