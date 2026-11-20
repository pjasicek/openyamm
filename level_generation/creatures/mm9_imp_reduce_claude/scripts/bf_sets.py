#!/usr/bin/env python3
"""Per-face keep / group sets on the installed Imp LOD0 (primitive order Imp_A body, ImpHead_A head) for mpqem.py:
work/glb_sets_<tag>.npz (keep, group, lining, lined, plus labels; one entry per GLB face). Prio-1 relaxed keep set
(REDUCTION_BRIEF_20261104), adapted from mm9_gezzampt_reduce_claude/scripts/gezz_sets.py.
Head primitive (one wrapped head shell: face, hood, crown, ears; two separate eyes):
- exact: separate pieces (eyes), the face skin (head region mask B = face at any corner or the centroid, grown FACE_RING
  rings), the ears (box |x| > EAR_X, EAR_Y0 < y < EAR_Y1, EAR_Z0 < z < EAR_Z1, grown EAR_RING rings), faces with no region
  (all mask RGB <= 128), the neck seam (head faces with a vertex within NECK of a body vertex) and, with RIM=1, the neck rim
  (mask alpha: the r9 band that carries the body's grain);
- group 2: the hood (mask R: sides and back of the head), group 4: the crown (mask G), ratios MP_GROUPS 2:<r>,4:<r>.
Body primitive (one wrapped skin with the MPFB hands zipped at the wrists):
- exact: the neck seam (body faces with a vertex within NECK of a head vertex), soles (faces within SOLE of the floor), the
  hand-graft junction (WRIST rings of faces round the border between hand-dominant and arm faces);
- group 1: hands (dominant Hand/Hand_h/Finger weight), group 3: feet (body region mask B off the hands; FEET=1),
  group 0: the rest (ladder ratio).
Optional extra keep files work/keep_extra_<name>.npy (one entry per GLB face of both primitives).
Usage: bf_sets.py <tag> [extra keep names...]"""
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
NECK = float(E('NECK', '0.03')); SOLE = float(E('SOLE', '0.012')); SMALL = int(E('SMALL', '120'))
EAR_RING = int(E('EAR_RING', '2')); FACE_RING = int(E('FACE_RING', '2')); RIM = E('RIM', '1') == '1'
EAR_X = float(E('EAR_X', '0.15')); EAR_Y0 = float(E('EAR_Y0', '2.245')); EAR_Y1 = float(E('EAR_Y1', '2.42'))
EAR_Z0 = float(E('EAR_Z0', '0.28')); EAR_Z1 = float(E('EAR_Z1', '0.38'))
WRIST = int(E('WRIST', '2')); HOOF_SPLIT = E('FEET', '1') == '1'
tag = sys.argv[1]; extras = sys.argv[2:]
doc, b = gb.read(HERE / 'before' / 'mm9_imp.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Imp' and 'mesh' in n)
pr = gb.prims(doc, b, node['mesh']); assert [p['material'] for p in pr] == ['Imp_A', 'ImpHead_A']
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
    m = np.asarray(Image.open(HERE / 'work' / f'tex_{base}_A{"raw" if base == "Imp" else ""}.png').convert('RGBA'), np.float32); H_, W_ = m.shape[:2]
    def s(uv):
        x = np.clip((uv[..., 0] % 1) * W_, 0, W_ - 1).astype(int); y = np.clip((uv[..., 1] % 1) * H_, 0, H_ - 1).astype(int)
        return m[y, x]
    return np.concatenate([s(UV[T]), s(UV[T].mean(1))[:, None]], 1)      # (f, 4, 3)


body, head = pr
# ---- head
P, T, J, W, UV = head['POSITION'].astype(float), head['T'], head['JOINTS_0'], head['WEIGHTS_0'].astype(float), head['TEXCOORD_0']
nH = len(T); FT, nW, fl = topo(P, T); cnt = np.bincount(fl)
small_h = cnt[fl] <= SMALL
ms = mask_samples('ImpHead', UV, T)                       # (f, 4, 4) RGBA at corners + centroid
facem = grow(FT, nW, (ms[..., 2] > 128).any(1), FACE_RING) & ~small_h
cen = P[T].mean(1)
ear0 = (np.abs(cen[:, 0]) > EAR_X) & (cen[:, 1] > EAR_Y0) & (cen[:, 1] < EAR_Y1) & (cen[:, 2] > EAR_Z0) & (cen[:, 2] < EAR_Z1)
ear = grow(FT, nW, ear0, EAR_RING) & ~small_h
nonhide = (ms[:, :, :3] <= 128).all(2).any(1) & ~small_h
bd = cKDTree(body['POSITION'].astype(float)).query(P)[0]
neck_h = (bd[T] < NECK).any(1)
rim = (ms[..., 3] > 128).any(1) if RIM else np.zeros(nH, bool)
keep_h = small_h | facem | ear | nonhide | neck_h | rim
crown = (ms[:, 3, 1] > 128)
group_h = np.where(keep_h, 0, np.where(crown, 4, 2))
face = facem
print(f'head faces {nH}: small pieces {int(small_h.sum())}, face {int(facem.sum())}, ears {int(ear.sum())}, '
      f'no region {int(nonhide.sum())}, neck {int(neck_h.sum())}, rim {int(rim.sum())} -> keep {int(keep_h.sum())}, '
      f'hood free {int((group_h == 2).sum())}, crown free {int((group_h == 4).sum())}')
# ---- body
P, T, J, W, UV = body['POSITION'].astype(float), body['T'], body['JOINTS_0'], body['WEIGHTS_0'].astype(float), body['TEXCOORD_0']
nF = len(T); FT, nW, fl = topo(P, T)
fw = face_weights(J, W, T)
hand = fw[:, [i for i, n in enumerate(joints) if any(k in n for k in ('Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))]].sum(1) > 0.5
vh = np.zeros(nW, bool); vh[FT[hand].ravel()] = True; va = np.zeros(nW, bool); va[FT[~hand].ravel()] = True
wrist = grow(FT, nW, (vh & va)[FT].any(1), WRIST - 1)
hd = cKDTree(head['POSITION'].astype(float)).query(P)[0]
neck = (hd[T] < NECK).any(1)
floor = P[:, 1].min(); sole = P[T][:, :, 1].min(1) < floor + SOLE
ms = mask_samples('Imp', UV, T)
hoof = (ms[..., 2] > 128).sum(1) >= 2
keep = neck | sole | wrist
group = np.zeros(nF, int); group[hand] = 1
if HOOF_SPLIT:
    group[hoof & ~hand] = 3
print(f'body faces {nF}: neck {int(neck.sum())}, soles {int(sole.sum())}, wrist junction {int(wrist.sum())}, '
      f'hands {int(hand.sum())}, feet {int(hoof.sum())}')
print(f'body keep {int(keep.sum())}, hands free {int(((group == 1) & ~keep).sum())}, feet free {int(((group == 3) & ~keep).sum())}, '
      f'rest free {int(((group == 0) & ~keep).sum())}')
K = np.r_[keep, keep_h]; G = np.r_[group, group_h]
for name in extras:
    k = np.load(HERE / 'work' / f'keep_extra_{name}.npy'); K |= k; print('extra', name, int(k.sum()))
print(f'protected share {K.sum() / len(K) * 100:.1f} % ({int(K.sum())} of {len(K)})')
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=K, group=G, lining=np.zeros(len(K), bool), lined=np.zeros(len(K), bool),
         hand=np.r_[hand, np.zeros(nH, bool)], face=np.r_[np.zeros(nF, bool), face], ear=np.r_[np.zeros(nF, bool), ear],
         rim=np.r_[np.zeros(nF, bool), rim], sole=np.r_[sole, np.zeros(nH, bool)], wristj=np.r_[wrist, np.zeros(nH, bool)], hoof=np.r_[hoof, np.zeros(nH, bool)])
