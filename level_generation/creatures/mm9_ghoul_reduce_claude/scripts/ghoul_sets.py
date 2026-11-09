#!/usr/bin/env python3
"""Per-face keep / group sets on the installed LOD0 (prims Ghoul_A body, GhoulHead_A head) for mpqem.py:
work/glb_sets_<tag>.npz (keep, group, lining, lined; one entry per GLB face, body then head). Prio-1 relaxed keep set
(REDUCTION_BRIEF_20261104), labels from ghoul_labels.py:
- head set: face skin (part 10: eyes' lids, brows, nose, mouth, lips, ears, jaw, chin; one shell), teeth, eyes and the skull
  plug exact; hair (part 11) group 2 (MP_GROUPS 2:<r>), with the hair faces within HAIRSKIN m of face skin kept (hairline);
- body set exact: both flaps with their lining and rim (helper-driven, already low grids), the neck seam (body faces with a
  vertex within NECK m of a head-set vertex: the neck tube under the jaw), soles (SOLE m), the claws (hand/finger faces outside
  the hide region at any corner or the centroid: finish_tex.py painted them black, the region mask leaves them out), distal
  finger segments (dominant Finger02/12/22/32/42), connected pieces of up to SMALL faces, optional extra keep files
  work/keep_extra_<name>.npy (per body face);
- group 1: hands and the rest of the fingers (hand + finger weight > 0.5);
- group 0: the rest of the body skin (torso, arms, legs, neck below the seam): the ladder ratio.
Usage: ghoul_sets.py <tag> [extra keep names...]"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
E = lambda k, d: os.environ.get(k, d)
NECK = float(E('NECK', '0.03')); SOLE = float(E('SOLE', '0.012')); SMALL = int(E('SMALL', '60'))
HAIRSKIN = float(E('HAIRSKIN', '0.0')); DISTAL1 = E('DISTAL1', '0') == '1'
tag = sys.argv[1]; extras = sys.argv[2:]
doc, b = gb.read(HERE / 'before' / 'mm9_ghoul.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Ghoul' and 'mesh' in n)
pr = gb.prims(doc, b, node['mesh']); assert [p['material'] for p in pr] == ['Ghoul_A', 'GhoulHead_A']
joints = [doc['nodes'][j]['name'] for j in doc['skins'][node['skin']]['joints']]
L = np.load(HERE / 'work' / 'labels.npz'); lb, lh = L['body'], L['head']
body, head = pr
P, T, J, W = body['POSITION'].astype(float), body['T'], body['JOINTS_0'], body['WEIGHTS_0'].astype(float)
nF = len(T)
fw = np.zeros((nF, len(joints)))
for k in range(3):
    for c in range(4):
        np.add.at(fw, (np.arange(nF), J[T[:, k], c]), W[T[:, k], c])
fw /= 3
dom = np.array([joints[i] for i in fw.argmax(1)])
hand = fw[:, [i for i, n in enumerate(joints) if 'Hand' in n or 'Finger' in n]].sum(1) > 0.5
dist_names = ('Finger02', 'Finger12', 'Finger22', 'Finger32', 'Finger42') + (('Finger01',) if DISTAL1 else ())
distal = np.array([d.endswith(dist_names) for d in dom])
key = np.round(P, 6); _, wv = np.unique(key, axis=0, return_inverse=True); wv = wv.ravel(); FT = wv[T]; nW = wv.max() + 1
r_ = np.concatenate([FT[:, 0], FT[:, 1], FT[:, 2]]); c_ = np.concatenate([FT[:, 1], FT[:, 2], FT[:, 0]])
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(nW, nW)), directed=False)
fl = lab[FT[:, 0]]; small = np.bincount(fl)[fl] <= SMALL
print('body components', sorted(np.bincount(fl).tolist(), reverse=True)[:12])
hd = cKDTree(head['POSITION'].astype(float)).query(P)[0]
neck = (hd[T] < NECK).any(1) & (lb == 0)
floor = P[:, 1].min(); sole = P[T][:, :, 1].min(1) < floor + SOLE
flap = np.isin(lb, (6, 7, 20, 21))
from PIL import Image
mask = np.asarray(Image.open(HERE / 'work' / 'tex_Ghoul_A.png').convert('RGB'), np.float32); H_, W_ = mask.shape[:2]
UV = body['TEXCOORD_0'].astype(float)
def samp(uv):
    x = np.clip((uv[..., 0] % 1) * W_, 0, W_ - 1).astype(int); y = np.clip((uv[..., 1] % 1) * H_, 0, H_ - 1).astype(int)
    return mask[y, x]
cs = np.concatenate([samp(UV[T]), samp(UV[T].mean(1))[:, None]], 1)
claw = hand & (cs[..., 0] < 50).any(1)
distal |= claw
keep = flap | neck | sole | small | distal
for name in extras:
    k = np.load(HERE / 'work' / f'keep_extra_{name}.npy'); keep |= k; print('extra', name, int(k.sum()), 'new', int((k & ~(flap | neck | sole | small | distal)).sum()))
group = np.zeros(nF, int); group[hand & ~keep] = 1
print(f'body faces {nF}: flaps+lining+rim {int(flap.sum())}, neck {int(neck.sum())}, soles {int(sole.sum())}, small {int(small.sum())}, '
      f'distal+claws {int(distal.sum())} (claws {int(claw.sum())}), hands {int(hand.sum())}')
print(f'body keep {int(keep.sum())}, hands free {int((group == 1).sum())}, rest free {int(((group == 0) & ~keep).sum())}')
# head set
Ph, Th = head['POSITION'].astype(float), head['T']; nH = len(Th)
hair = lh == 11
skinv = np.unique(Th[lh == 10])
hairline = np.zeros(nH, bool)
if HAIRSKIN > 0:
    dsk = cKDTree(Ph[skinv]).query(Ph)[0]; hairline = hair & (dsk[Th] < HAIRSKIN).any(1)
hkeep = ~hair | hairline
hgroup = np.where(hair & ~hairline, 2, 0)
print(f'head faces {nH}: hair {int(hair.sum())} (hairline kept {int(hairline.sum())}), kept {int(hkeep.sum())}')
K = np.r_[keep, hkeep]
print(f'protected share {K.sum() / len(K) * 100:.1f} % ({int(K.sum())} of {len(K)})')
from collections import Counter
print('dominant bones of free body faces', Counter(dom[~keep]).most_common(14))
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=K, group=np.r_[group, hgroup], lining=np.zeros(len(K), bool),
         lined=np.zeros(len(K), bool), hand=np.r_[hand, np.zeros(nH, bool)])
