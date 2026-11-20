#!/usr/bin/env python3
"""Per-face keep / group sets on the installed LOD0 (primitive order Gezzampt_A body, GezzamptHead_A head) for mpqem.py:
work/glb_sets_<tag>.npz (keep, group, lining, lined, plus labels; one entry per GLB face). Prio-1 relaxed keep set
(REDUCTION_BRIEF_20261104):
Head primitive (one wrapped skin: face, mane, ears, horns; separate eyes and teeth/tusks):
- exact: separate pieces (eyes, teeth, tusks), the ears (any corner Ponytail-weighted > EARW, plus EAR_RING rings round them),
  the horns (head region mask G at any corner or the centroid, plus one ring: thin painted spirals), every face with a corner
  outside the hide region (mouth carve, plug), the neck seam (head faces with a vertex within NECK of a body vertex) and the
  face skin: faces in front of the mane boundary (centroid z > FACE_Z below the hairline y < HAIR_Y, or below the brow line y < BROW_Y with z > CHIN_Z),
  grown by FACE_RING rings;
- group 2: the mane (the rest of the head skin: crown, back of the skull, nape), ratio MP_GROUPS 2:<r>.
Body primitive (one wrapped skin with the MPFB fists zipped at the wrists):
- exact: the neck seam (body faces with a vertex within NECK of a head vertex), soles (faces within SOLE of the floor), the
  hand-graft junction (WRIST rings of faces round the border between hand-dominant and arm faces);
- group 1: fists (dominant Hand/Hand_h/Finger weight), group 3: hooves (body region mask G), group 0: the rest (ladder ratio).
Optional extra keep files work/keep_extra_<name>.npy (one entry per GLB face of both primitives).
Usage: gezz_sets.py <tag> [extra keep names...]"""
import os, sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
E = lambda k, d: os.environ.get(k, d)
NECK = float(E('NECK', '0.03')); SOLE = float(E('SOLE', '0.03')); SMALL = int(E('SMALL', '120'))
EARW = float(E('EARW', '0.3')); EAR_RING = int(E('EAR_RING', '2')); FACE_RING = int(E('FACE_RING', '2'))
HAIR_Y = float(E('HAIR_Y', '9')); FACE_Z = float(E('FACE_Z', '0.2')); BROW_Y = float(E('BROW_Y', '2.29')); CHIN_Z = float(E('CHIN_Z', '0.05'))
WRIST = int(E('WRIST', '2')); HOOF_SPLIT = E('HOOF', '1') == '1'
tag = sys.argv[1]; extras = sys.argv[2:]
doc, b = gb.read(HERE / 'before' / 'mm9_gezzampt.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Gezzampt' and 'mesh' in n)
pr = gb.prims(doc, b, node['mesh']); assert [p['material'] for p in pr] == ['Gezzampt_A', 'GezzamptHead_A']
joints = [doc['nodes'][j]['name'] for j in doc['skins'][node['skin']]['joints']]


def topo(P, T):
    key = np.round(P, 6); _, wv = np.unique(key, axis=0, return_inverse=True); wv = wv.ravel(); FT = wv[T]
    nW = wv.max() + 1
    r_ = np.concatenate([FT[:, 0], FT[:, 1], FT[:, 2]]); c_ = np.concatenate([FT[:, 1], FT[:, 2], FT[:, 0]])
    ncomp, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(nW, nW)), directed=False)
    return FT, nW, lab[FT[:, 0]]


def grow(FT, nW, sel, rings):
    sel = sel.copy()
    for _ in range(rings):
        vm = np.zeros(nW, bool); vm[FT[sel].ravel()] = True; sel |= vm[FT].any(1)
    return sel


def face_weights(J, W, T):
    fw = np.zeros((len(T), len(joints)))
    for k in range(3):
        for c in range(4):
            np.add.at(fw, (np.arange(len(T)), J[T[:, k], c]), W[T[:, k], c])
    return fw / 3


def mask_samples(base, UV, T):
    m = np.asarray(Image.open(HERE / 'work' / f'tex_{base}_A.png').convert('RGB'), np.float32); H_, W_ = m.shape[:2]
    def s(uv):
        x = np.clip((uv[..., 0] % 1) * W_, 0, W_ - 1).astype(int); y = np.clip((uv[..., 1] % 1) * H_, 0, H_ - 1).astype(int)
        return m[y, x]
    return np.concatenate([s(UV[T]), s(UV[T].mean(1))[:, None]], 1)      # (f, 4, 3)


body, head = pr
# ---- head
P, T, J, W, UV = head['POSITION'].astype(float), head['T'], head['JOINTS_0'], head['WEIGHTS_0'].astype(float), head['TEXCOORD_0']
nH = len(T); FT, nW, fl = topo(P, T); cnt = np.bincount(fl)
small_h = cnt[fl] <= SMALL
fw = face_weights(J, W, T)
pt = [joints.index('Bip01 Ponytail1'), joints.index('Bip01 Ponytail2')]
vear = sum((W * (J == i)).sum(1) for i in pt) > EARW
ear = grow(FT, nW, vear[T].any(1), EAR_RING)
ms = mask_samples('GezzamptHead', UV, T)
horn = grow(FT, nW, (ms[..., 1] > 128).any(1), 1) & ~small_h
nonhide = (ms[:, :3, 0] <= 128).any(1) & ~small_h
bd = cKDTree(body['POSITION'].astype(float)).query(P)[0]
neck_h = (bd[T] < NECK).any(1)
cen = P[T].mean(1)
face0 = (((cen[:, 2] > FACE_Z) & (cen[:, 1] < HAIR_Y)) | ((cen[:, 1] < BROW_Y) & (cen[:, 2] > CHIN_Z))) & ~small_h
face = grow(FT, nW, face0, FACE_RING) & ~small_h
keep_h = small_h | ear | horn | nonhide | neck_h | face
group_h = np.where(keep_h, 0, 2)
print(f'head faces {nH}: small pieces {int(small_h.sum())}, ears {int(ear.sum())}, horns {int(horn.sum())}, '
      f'non-hide {int(nonhide.sum())}, neck {int(neck_h.sum())}, face {int(face.sum())} -> keep {int(keep_h.sum())}, '
      f'mane free {int((~keep_h).sum())}')
# ---- body
P, T, J, W, UV = body['POSITION'].astype(float), body['T'], body['JOINTS_0'], body['WEIGHTS_0'].astype(float), body['TEXCOORD_0']
nF = len(T); FT, nW, fl = topo(P, T)
fw = face_weights(J, W, T)
hand = fw[:, [i for i, n in enumerate(joints) if 'Hand' in n or 'Finger' in n]].sum(1) > 0.5
vh = np.zeros(nW, bool); vh[FT[hand].ravel()] = True; va = np.zeros(nW, bool); va[FT[~hand].ravel()] = True
wrist = grow(FT, nW, (vh & va)[FT].any(1), WRIST - 1)
hd = cKDTree(head['POSITION'].astype(float)).query(P)[0]
neck = (hd[T] < NECK).any(1)
floor = P[:, 1].min(); sole = P[T][:, :, 1].min(1) < floor + SOLE
ms = mask_samples('Gezzampt', UV, T)
hoof = (ms[..., 1] > 128).sum(1) >= 2
keep = neck | sole | wrist
group = np.zeros(nF, int); group[hand] = 1
if HOOF_SPLIT:
    group[hoof & ~hand] = 3
print(f'body faces {nF}: neck {int(neck.sum())}, soles {int(sole.sum())}, wrist junction {int(wrist.sum())}, '
      f'hands {int(hand.sum())}, hooves {int(hoof.sum())}')
print(f'body keep {int(keep.sum())}, hands free {int(((group == 1) & ~keep).sum())}, hooves free {int(((group == 3) & ~keep).sum())}, '
      f'rest free {int(((group == 0) & ~keep).sum())}')
K = np.r_[keep, keep_h]; G = np.r_[group, group_h]
for name in extras:
    k = np.load(HERE / 'work' / f'keep_extra_{name}.npy'); K |= k; print('extra', name, int(k.sum()))
print(f'protected share {K.sum() / len(K) * 100:.1f} % ({int(K.sum())} of {len(K)})')
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=K, group=G, lining=np.zeros(len(K), bool), lined=np.zeros(len(K), bool),
         hand=np.r_[hand, np.zeros(nH, bool)], face=np.r_[np.zeros(nF, bool), face], ear=np.r_[np.zeros(nF, bool), ear],
         horn=np.r_[np.zeros(nF, bool), horn], hoof=np.r_[hoof, np.zeros(nH, bool)])
