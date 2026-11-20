#!/usr/bin/env python3
"""Per-face keep / group sets on the installed LOD0 (primitive order Trog_A body, TrogHead_A head) for mpqem.py:
work/glb_sets_<tag>.npz (keep, group, lining, lined; one entry per GLB face). Prio-1 relaxed keep set
(REDUCTION_BRIEF_20261104):
- head primitive (face skin, mouth, palate, tongue, teeth, eyes, neck strip): kept whole in mpqem (KEPT_PRIMS);
- exact on the body: the neck seam (body faces with a vertex within NECK m of a head vertex: the ring the head meets),
  soles (faces within SOLE m of the floor), claws (region-mask blue at any corner or the centroid: thin tips),
  connected pieces of up to SMALL faces (calf spines), optional extra keep files work/keep_extra_<name>.npy (GLB faces);
- group 1: hands and fingers (dominant Hand/Finger weight), ratio MP_GROUPS 1:<r>;
- group 0: the rest of the body (torso, tail, arms, legs), the ladder ratio.
Usage: trog_sets.py <tag> [extra keep names...]"""
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
NECK = float(E('NECK', '0.03')); SOLE = float(E('SOLE', '0.03')); SMALL = int(E('SMALL', '60'))
tag = sys.argv[1]; extras = sys.argv[2:]
doc, b = gb.read(HERE / 'before' / 'mm9_troglodyte.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Troglodyte' and 'mesh' in n)
pr = gb.prims(doc, b, node['mesh']); assert [p['material'] for p in pr] == ['Trog_A', 'TrogHead_A']
joints = [doc['nodes'][j]['name'] for j in doc['skins'][node['skin']]['joints']]
body, head = pr
P, T, J, W, UV = body['POSITION'].astype(float), body['T'], body['JOINTS_0'], body['WEIGHTS_0'].astype(float), body['TEXCOORD_0']
nF = len(T)
# dominant bone per face
acc = {}
fw = np.zeros((nF, len(joints)))
for k in range(3):
    for c in range(4):
        np.add.at(fw, (np.arange(nF), J[T[:, k], c]), W[T[:, k], c])
dom = np.array([joints[i] for i in fw.argmax(1)])
handw = fw[:, [i for i, n in enumerate(joints) if 'Hand' in n or 'Finger' in n]].sum(1) / 3
hand = handw > 0.5
# welded topology
key = np.round(P, 6); _, wv = np.unique(key, axis=0, return_inverse=True); wv = wv.ravel(); FT = wv[T]; nW = wv.max() + 1
r_ = np.concatenate([FT[:, 0], FT[:, 1], FT[:, 2]]); c_ = np.concatenate([FT[:, 1], FT[:, 2], FT[:, 0]])
ncomp, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(nW, nW)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl)
small = cnt[fl] <= SMALL
print('components', sorted(np.bincount(fl).tolist(), reverse=True)[:20])
# neck seam
hd = cKDTree(head['POSITION'].astype(float)).query(P)[0]
neck = (hd[T] < NECK).any(1)
floor = P[:, 1].min(); sole = P[T][:, :, 1].min(1) < floor + SOLE
# claws from the region mask (blue)
mask = np.asarray(Image.open(HERE / 'work' / 'tex_Trog_A.png').convert('RGB'), np.float32)
H_, W_ = mask.shape[:2]
def samp(uv):
    x = np.clip((uv[..., 0] % 1) * W_, 0, W_ - 1).astype(int); y = np.clip((uv[..., 1] % 1) * H_, 0, H_ - 1).astype(int)
    return mask[y, x]
cs = np.concatenate([samp(UV[T]), samp(UV[T].mean(1))[:, None]], 1)       # (f,4,3)
claw = (cs[..., 2] > 128).any(1)
keep = neck | sole | small | claw
for name in extras:
    k = np.load(HERE / 'work' / f'keep_extra_{name}.npy'); keep |= k; print('extra', name, int(k.sum()))
group = np.zeros(nF, int); group[hand & ~keep] = 1
print(f'body faces {nF}: neck {int(neck.sum())}, soles {int(sole.sum())}, small {int(small.sum())}, claws {int(claw.sum())}'
      f' (in hands {int((claw & hand).sum())}), hands {int(hand.sum())}')
print(f'keep {int(keep.sum())}, hands free {int((group == 1).sum())}, rest free {int(((group == 0) & ~keep).sum())}')
print(f'head {len(head["T"])} kept whole; protected share {(keep.sum() + len(head["T"])) / (nF + len(head["T"])) * 100:.1f} %')
from collections import Counter
print('dominant bones of free faces', Counter(dom[~keep]).most_common(30))
nH = len(head['T'])
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=np.r_[keep, np.ones(nH, bool)], group=np.r_[group, np.zeros(nH, int)],
         lining=np.zeros(nF + nH, bool), lined=np.zeros(nF + nH, bool), hand=np.r_[hand, np.zeros(nH, bool)],
         claw=np.r_[claw, np.zeros(nH, bool)])
