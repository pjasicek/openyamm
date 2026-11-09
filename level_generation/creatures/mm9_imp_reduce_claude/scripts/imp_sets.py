#!/usr/bin/env python3
"""Per-face keep / group sets on the installed Imp LOD0 (primitive order Imp_A body, ImpHead_A head) for mpqem.py:
work/glb_sets_<tag>.npz (keep, group, lining, lined, plus labels; one entry per GLB face). Prio-1 relaxed keep set
(REDUCTION_BRIEF_20261104), adapted from mm9_bigfoot_reduce_claude/scripts/bf_sets.py. imp-reduce-20261104.
Head primitive (one shell: face, cranium, ears, horns; separate eyes, teeth and mouth pieces):
- exact: separate pieces (eyes, teeth, gums), the face (every shell face that is not cranium), the ears (box |x| > EAR_X,
  EAR_Y0 < y < EAR_Y1, grown EAR_RING rings), the horns and every other no-region face (mask RGB <= 128: horns, brows,
  mouth cavity), grown HORN_RING rings, the neck seam (head faces with a vertex within NECK of a body vertex);
- group 4: the cranium (top and back of the skull: centroid y > CR_Y, or z < CR_Z and y > CR_Y2), ratio MP_GROUPS 4:<r>.
Body primitive (one skin, Meshy digits by connectivity; belt, buckle, flap and wrist bands as separate pieces):
- exact: pieces of up to SMALL faces (wrist bands, buckle, flap) and BIG_KEEP pieces (the belt), the neck seam, soles,
  claw tips (body mask G, grown CLAW_RING rings), the wrist junction (WRIST rings round the hand/forearm border), the
  tail's spade tip (Tail4 weight > TAILTIP), the
  trident grip contact (work/keep_extra_grip.npy, grip_contact.py) and the skin under the shin wraps (keep_extra_wrap.npy);
- group 1: left hand, group 5: right hand (dominant Hand/Finger weight), group 3: feet (Foot/Toe dominant),
  group 6: tail (Tail dominant), group 0: the rest (ladder ratio).
Optional extra keep files work/keep_extra_<name>.npy (one entry per GLB face of both primitives).
Usage: imp_sets.py <tag> [extra keep names...]"""
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
NECK = float(E('NECK', '0.03')); SOLE = float(E('SOLE', '0.012')); SMALL = int(E('SMALL', '200'))
EAR_RING = int(E('EAR_RING', '2')); HORN_RING = int(E('HORN_RING', '2')); CLAW_RING = int(E('CLAW_RING', '1'))
EAR_X = float(E('EAR_X', '0.105')); EAR_Y0 = float(E('EAR_Y0', '0.98')); EAR_Y1 = float(E('EAR_Y1', '1.14'))
CR_Y = float(E('CR_Y', '1.10')); CR_Z = float(E('CR_Z', '0.17')); CR_Y2 = float(E('CR_Y2', '0.97'))
WRIST = int(E('WRIST', '1'))
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
    m = np.asarray(Image.open(HERE / 'work' / f'tex_{base}_A.png').convert('RGBA'), np.float32); H_, W_ = m.shape[:2]
    def s(uv):
        x = np.clip((uv[..., 0] % 1) * W_, 0, W_ - 1).astype(int); y = np.clip((uv[..., 1] % 1) * H_, 0, H_ - 1).astype(int)
        return m[y, x]
    return np.concatenate([s(UV[T]), s(UV[T].mean(1))[:, None]], 1)      # (f, 4, 4)


def jsum(fw, pred):
    return fw[:, [i for i, n in enumerate(joints) if pred(n)]].sum(1)


body, head = pr
# ---- head
P, T, UV = head['POSITION'].astype(float), head['T'], head['TEXCOORD_0']
nH = len(T); FT, nW, fl = topo(P, T); cnt = np.bincount(fl); shell = fl == cnt.argmax()
small_h = ~shell
ms = mask_samples('ImpHead', UV, T)
cen = P[T].mean(1)
ear = grow(FT, nW, (np.abs(cen[:, 0]) > EAR_X) & (cen[:, 1] > EAR_Y0) & (cen[:, 1] < EAR_Y1), EAR_RING) & shell
noreg = grow(FT, nW, ((ms[:, 3, :3] <= 128).all(1) | (ms[:, 3, 1] > 128)) & shell, HORN_RING) & shell     # centroid only: island padding is black
bd = cKDTree(body['POSITION'].astype(float)).query(P)[0]
neck_h = (bd[T] < NECK).any(1)
cran0 = shell & ((cen[:, 1] > CR_Y) | ((cen[:, 2] < CR_Z) & (cen[:, 1] > CR_Y2)))
cranium = cran0 & ~ear & ~noreg & ~neck_h
keep_h = ~cranium
group_h = np.where(keep_h, 0, 4)
face = shell & ~cranium & ~ear & ~neck_h
print(f'head faces {nH}: pieces {int(small_h.sum())}, ears {int(ear.sum())}, horns/no-region {int(noreg.sum())}, '
      f'neck {int(neck_h.sum())}, cranium free {int(cranium.sum())} -> keep {int(keep_h.sum())}')
# ---- body
P, T, J, W, UV = body['POSITION'].astype(float), body['T'], body['JOINTS_0'], body['WEIGHTS_0'].astype(float), body['TEXCOORD_0']
nF = len(T); FT, nW, fl = topo(P, T); cnt = np.bincount(fl)
pieces = fl != cnt.argmax()
fw = face_weights(J, W, T)
handL = jsum(fw, lambda n: n.startswith('Bip01 L Hand') or n.startswith('Bip01 L Finger')) > 0.5
handR = jsum(fw, lambda n: n.startswith('Bip01 R Hand') or n.startswith('Bip01 R Finger')) > 0.5
hand = handL | handR
foot = (jsum(fw, lambda n: 'Foot' in n or 'Toe' in n) > 0.5) & ~pieces
tail = (jsum(fw, lambda n: 'Tail' in n) > 0.5) & ~pieces
vh = np.zeros(nW, bool); vh[FT[hand].ravel()] = True; va = np.zeros(nW, bool); va[FT[~hand & ~pieces].ravel()] = True
wrist = grow(FT, nW, (vh & va)[FT].all(1) | ((vh & va)[FT].sum(1) >= 2), WRIST - 1) & ~pieces
hd = cKDTree(head['POSITION'].astype(float)).query(P)[0]
neck = (hd[T] < NECK).any(1)
floor = P[:, 1].min(); sole = P[T][:, :, 1].min(1) < floor + SOLE
ms = mask_samples('Imp', UV, T)
claw = grow(FT, nW, ms[:, 3, 1] > 128, CLAW_RING) & ~pieces
tailtip = (jsum(fw, lambda n: n == 'Bip01 Tail4') > float(E('TAILTIP', '0.3'))) & ~pieces   # the spade tip: 32 mm off at 0.6
keep = pieces | neck | sole | wrist | claw | tailtip
group = np.zeros(nF, int); group[handL] = 1; group[handR] = 5; group[foot & ~hand] = 3; group[tail] = 6
print(f'body faces {nF}: pieces {int(pieces.sum())}, neck {int(neck.sum())}, soles {int(sole.sum())}, wrist {int(wrist.sum())}, '
      f'claws {int(claw.sum())}, tail tip {int(tailtip.sum())}, handL {int(handL.sum())}, handR {int(handR.sum())}, feet {int(foot.sum())}, tail {int(tail.sum())}')
for g_ in (0, 1, 3, 5, 6):
    print(f'  body group {g_} free {int(((group == g_) & ~keep).sum())}')
K = np.r_[keep, keep_h]; G = np.r_[group, group_h]
for name in extras:
    k = np.load(HERE / 'work' / f'keep_extra_{name}.npy'); print('extra', name, int(k.sum()), 'new', int((k & ~K).sum())); K |= k
print(f'protected share {K.sum() / len(K) * 100:.1f} % ({int(K.sum())} of {len(K)})')
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=K, group=G, lining=np.zeros(len(K), bool), lined=np.zeros(len(K), bool),
         hand=np.r_[hand, np.zeros(nH, bool)], face=np.r_[np.zeros(nF, bool), face], ear=np.r_[np.zeros(nF, bool), ear],
         cranium=np.r_[np.zeros(nF, bool), cranium], horn=np.r_[np.zeros(nF, bool), noreg], sole=np.r_[sole, np.zeros(nH, bool)],
         wristj=np.r_[wrist, np.zeros(nH, bool)], claw=np.r_[claw, np.zeros(nH, bool)], tail=np.r_[tail, np.zeros(nH, bool)],
         foot=np.r_[foot, np.zeros(nH, bool)], pieces=np.r_[pieces, small_h])
