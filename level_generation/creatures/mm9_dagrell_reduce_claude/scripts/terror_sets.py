#!/usr/bin/env python3
"""Per-face keep / group sets on the installed Terror LOD0 (one primitive, Terror_A) for mpqem.py: work/glb_sets_<tag>.npz
(keep, group, lining, lined, plus labels). Prio-1 relaxed keep set (REDUCTION_BRIEF_20261104), Terror reading:
- exact: separate pieces (4 eyeballs, 12 teeth/fangs, the tongue), the mouth bag (head_fix.py cavity, found by its atlas
  island via ../mm9_terror_claude/work/uv_v3_bag.npz), the face skin (main-surface faces dominated by Bip01 Head / the jaw
  bones Bone35/37/38 in front of z FACE_Z: lids, brows, snout, lips, chin; plus every main face within EYE eyeball radii of
  an eye centre and LIP of the bag), FACE_RING rings round all of it, the tentacle-tip mouths (red region on the last chain
  bones Bone24/Bone33, plus TIP_RING rings), claws (bone region at any corner of a foot/toe/calf face, plus one ring), soles (faces within SOLE of
  the floor);
- group 1: tentacle shafts (dominant bone in a tentacle chain), group 2: cranium (the head/jaw skin behind FACE_Z), group LEG_GROUP (if set): calves, feet and toes,
  group 0: the rest (torso, legs).
Optional extra keep files work/keep_extra_<name>.npy (one entry per GLB face). Usage: terror_sets.py <tag> [extra names...]"""
import os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
E = lambda k, d: os.environ.get(k, d)
FACE_Z = float(E('FACE_Z', '0.2')); EYE = float(E('EYE', '2.0')); LIP = float(E('LIP', '0.06')); FACE_RING = int(E('FACE_RING', '1'))
TIP_RING = int(E('TIP_RING', '2')); SOLE = float(E('SOLE', '0.03')); SMALL = int(E('SMALL', '300'))
TENT_GROUP = int(E('TENT_GROUP', '1'))
tag = sys.argv[1]; extras = sys.argv[2:]
doc, b = gb.read(HERE / 'before' / 'mm9_terror.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Terror' and 'mesh' in n)
pr = gb.prims(doc, b, node['mesh']); assert [p['material'] for p in pr] == ['Terror_A']
pr = pr[0]
joints = [doc['nodes'][j]['name'] for j in doc['skins'][node['skin']]['joints']]
P, T, J, W, UV = pr['POSITION'].astype(float), pr['T'], pr['JOINTS_0'], pr['WEIGHTS_0'].astype(float), pr['TEXCOORD_0'].astype(float)
nF = len(T)
key = np.round(P, 6); _, wv = np.unique(key, axis=0, return_inverse=True); wv = wv.ravel(); FT = wv[T]; nW = wv.max() + 1
r_ = np.concatenate([FT[:, 0], FT[:, 1], FT[:, 2]]); c_ = np.concatenate([FT[:, 1], FT[:, 2], FT[:, 0]])
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(nW, nW)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl); small = cnt[fl] <= SMALL; main = ~small


def grow(sel, rings):
    sel = sel.copy()
    for _ in range(rings):
        vm = np.zeros(nW, bool); vm[FT[sel].ravel()] = True; sel |= vm[FT].any(1) & main
    return sel


fw = np.zeros((nF, len(joints)))
for k in range(3):
    for c in range(4):
        np.add.at(fw, (np.arange(nF), J[T[:, k], c]), W[T[:, k], c])
dom = fw.argmax(1)
bag = np.load(HERE.parent / 'mm9_terror_claude' / 'work' / 'uv_v3_bag.npz')
d, _ = cKDTree(bag['uv_new'].mean(1) * [1, -1] + [0, 1]).query(UV[T].mean(1)); cav = (d < 2e-4) & main
m = np.asarray(Image.open(HERE / 'work' / 'tex_Terror_A.png').convert('RGB'), np.float32); H_, W_ = m.shape[:2]


def sample(uv):
    x = np.clip((uv[..., 0] % 1) * W_, 0, W_ - 1).astype(int); y = np.clip((uv[..., 1] % 1) * H_, 0, H_ - 1).astype(int)
    return m[y, x]


ms = np.concatenate([sample(UV[T]), sample(UV[T].mean(1))[:, None]], 1)      # (f, 4, [R, B, bone])
cen = P[T].mean(1)
headj = [joints.index(n) for n in ('Bip01 Head', 'Bone35', 'Bone37', 'Bone38')]
headskin = np.isin(dom, headj) & main & ~cav
face0 = headskin & (cen[:, 2] > FACE_Z)
eyes = []
for c in np.unique(fl[small]):
    v = np.unique(T[fl == c]); ext = np.ptp(P[v], 0)
    if len(v) > 80 and ext.max() / ext.min() < 1.3:
        eyes.append((P[v].mean(0), np.linalg.norm(P[v] - P[v].mean(0), axis=1).mean()))
lid = np.zeros(nF, bool)
for c, r in eyes:
    lid |= np.linalg.norm(cen - c, axis=1) < EYE * r
lid &= main
lip = (cKDTree(P[np.unique(T[cav])]).query(cen)[0] < LIP) & main
face = grow(face0 | (lid & ~cav) | (lip & ~cav), FACE_RING) & ~cav
tentj = [joints.index(f'Bone{i:02d}') for i in (1, 2, 3, 4, 21, 22, 23, 24, 26, 27, 28, 29, 30, 31, 32, 33, 9, 10, 11, 13, 18, 19,
                                                 5, 6, 7, 14, 15, 16)]
tent = np.isin(dom, tentj) & main
tipj = [joints.index('Bone24'), joints.index('Bone33')]
tip = grow(np.isin(dom, tipj) & main & ((ms[..., 0] > 128).sum(1) >= 2), TIP_RING)
footj = [joints.index(n) for n in ('Bip01 L Foot', 'Bip01 R Foot', 'Bip01 L Toe0', 'Bip01 R Toe0', 'Bip01 L Calf', 'Bip01 R Calf')]
claw = grow((ms[..., 2] > 128).any(1) & main & np.isin(dom, footj), 1)   # the bone region also paints pale tentacle spots
floor = P[:, 1].min(); sole = (P[T][:, :, 1].min(1) < floor + SOLE) & main
keep = small | cav | face | tip | claw | sole
group = np.zeros(nF, int)
group[tent] = TENT_GROUP
group[headskin & ~face] = 2
if E('LEG_GROUP', '0') != '0':   # calves, feet and toes (the ladder's worst share): group 3
    group[np.isin(dom, footj) & main] = int(E('LEG_GROUP', '0'))
for name in extras:
    k = np.load(HERE / 'work' / f'keep_extra_{name}.npy'); keep |= k; print('extra', name, int(k.sum()))
print(f'faces {nF}: pieces {int(small.sum())}, cavity {int(cav.sum())}, face {int(face.sum())} (head front {int(face0.sum())}, '
      f'lids {int((lid & ~cav).sum())}, lips {int((lip & ~cav).sum())}), tentacle tips {int(tip.sum())}, claws {int(claw.sum())}, '
      f'soles {int(sole.sum())}')
for gl in np.unique(group):
    print(f'group {gl}: free {int(((group == gl) & ~keep).sum())} (of {int((group == gl).sum())})')
print(f'protected share {keep.sum() / nF * 100:.1f} % ({int(keep.sum())} of {nF})')
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=np.zeros(nF, bool), lined=np.zeros(nF, bool),
         face=face, cav=cav, small=small, tip=tip, claw=claw, sole=sole, tent=tent, headskin=headskin)
