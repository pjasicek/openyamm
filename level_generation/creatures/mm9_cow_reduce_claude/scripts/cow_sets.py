#!/usr/bin/env python3
"""Per-face keep / group sets on the installed Cow LOD0 (one primitive Cow_A; Cow_B is the same mesh with other ramps) for
mpqem.py: work/glb_sets_<tag>.npz (keep, group, lining, lined, plus labels). Animal reading of the face rule: the head stays
exact (eyes, muzzle, nostrils, mouth cavity, ears, poll):
- exact: separate small pieces (2 eyeballs, 4 teats; the tassel too unless TASSEL_GROUP), the face = head-weighted skin
  (Xheadpiv, Xhead, Xjawpiv, Xearpiv, Xearpiv01 summed weight > 0.5) in front of z FACE_Z (the ears' roots lie at z 0.83-0.93,
  the eyes at 0.995, the muzzle tip at 1.25), plus every ear face, plus FACE_RING rings; hooves (dominant Xffoot*/Xbfoot*,
  rigid on the foot bones) plus one ring; soles (faces within SOLE of the floor);
- group NECK_GROUP: the head-weighted skin behind FACE_Z (the dense upper neck, 14-19 mm edges against 50-70 mm on the body);
- group TASSEL_GROUP (if set): the tail tassel piece; group 0: the rest (body, legs, tail tube).
Optional extra keep files work/keep_extra_<name>.npy (one entry per GLB face; err_lock.py).
Usage: cow_sets.py <tag> [extra names...]   (env FACE_Z, FACE_RING, SOLE, NECK_GROUP, TASSEL_GROUP, TEAT_GROUP)"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
E = lambda k, d: os.environ.get(k, d)
FACE_Z = float(E('FACE_Z', '0.80')); FACE_RING = int(E('FACE_RING', '2')); SOLE = float(E('SOLE', '0.03'))
NECK_GROUP = int(E('NECK_GROUP', '1')); TASSEL_GROUP = int(E('TASSEL_GROUP', '0')); TEAT_GROUP = int(E('TEAT_GROUP', '0'))
tag = sys.argv[1]; extras = sys.argv[2:]
doc, b = gb.read(HERE / 'before' / 'mm9_cow.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Cow' and 'mesh' in n)
pr = gb.prims(doc, b, node['mesh']); assert [p['material'] for p in pr] == ['Cow_A']
pr = pr[0]
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
fw /= 3
dom = fw.argmax(1); cen = P[T].mean(1)


def grow(sel, rings):
    sel = sel.copy()
    for _ in range(rings):
        vm = np.zeros(nW, bool); vm[FT[sel].ravel()] = True; sel |= vm[FT].any(1) & main
    return sel


ji = lambda names: [joints.index(n) for n in names]
headw = fw[:, ji(('Xheadpiv', 'Xhead', 'Xjawpiv', 'Xearpiv', 'Xearpiv01'))].sum(1)
head = (headw > 0.5) & main
ears = np.isin(dom, ji(('Xearpiv', 'Xearpiv01'))) & main
face = grow((head & (cen[:, 2] > FACE_Z)) | ears, FACE_RING)
hoof = grow(np.isin(dom, ji(('Xffoot', 'Xffoot01', 'Xbfoot', 'Xbfoot01'))) & main, 1)
floor = P[:, 1].min(); sole = (P[T][:, :, 1].min(1) < floor + SOLE) & main
tassel = small & np.isin(dom, ji(('XtailE',)))
teats = small & np.isin(dom, ji(('XbackC',)))
eyes = small & ~tassel & ~teats
keep = eyes | face | hoof | sole
if not TASSEL_GROUP:
    keep |= tassel
if not TEAT_GROUP:
    keep |= teats
for name in extras:
    k = np.load(HERE / 'work' / f'keep_extra_{name}.npy'); keep |= k; print('extra', name, int(k.sum()))
group = np.zeros(nF, int)
group[head & ~face] = NECK_GROUP
if TASSEL_GROUP:
    group[tassel] = TASSEL_GROUP
if TEAT_GROUP:
    group[teats] = TEAT_GROUP
print(f'faces {nF}: eyes {int(eyes.sum())}, teats {int(teats.sum())}, tassel {int(tassel.sum())}, head {int(head.sum())} '
      f'(face exact {int(face.sum())}, neck behind z {FACE_Z} {int((head & ~face).sum())}), hooves {int(hoof.sum())}, '
      f'soles {int(sole.sum())} (floor {floor:.4f})')
for gl in np.unique(group):
    print(f'group {gl}: free {int(((group == gl) & ~keep).sum())} (of {int((group == gl).sum())})')
print(f'protected share {keep.sum() / nF * 100:.1f} % ({int(keep.sum())} of {nF})')
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=np.zeros(nF, bool), lined=np.zeros(nF, bool),
         face=face, head=head, eyes=eyes, teats=teats, tassel=tassel, hoof=hoof, sole=sole)
