#!/usr/bin/env python3
"""Keep / group sets per face of the installed Mummy LOD0 (before/mm9_mummy.glb, primitive order Mummy, MummyHead) for mpqem.py,
prio-1 relaxed keep set (REDUCTION_BRIEF_20261104). Written for the Mummy after the Zombie's make_sets.py.
Classes (connected pieces welded by position inside a primitive):
  Mummy: body (the main piece), hands (main-piece faces whose vertices are mostly on Hand/finger bones), neck (main-piece faces
         above the hood rim, inside the hood), strips (every other piece: the two-sided band, thigh and arm strips; band_sim and
         the skin-laid strips depend on their exact vertices);
  MummyHead: face (the head shell in front: centroid z > FACE_Z and y < FACE_Y, or z > FACE_ZF; the dense sculpted face with
         brows, eyes, nose, mouth, lips, chin, jaw and cheeks), hood (the coarse wrapped crown, back and sides), eyes (the two
         58-face pieces).
Exact: face, eyes, strips, soles (every vertex below the main piece's lowest point + SOLE), the neck seam (head and body faces
with a vertex within SEAM of the hood's open lower rim, y < RIM_LO), optional extra keeps (work/<name>.npy per GLB face, env KEEP_EXTRA=a,b).
Groups (MP_GROUPS ratios): 1 hands, 2 hood, 3 neck (hidden inside the hood); label 0 (the ladder ratio): body.
Usage: make_sets.py <tag>  -> work/glb_sets_<tag>.npz (keep, group, lining, lined, cls, mat) and work/classes.json"""
import json
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
from weld import weld_ids  # noqa: E402
E = lambda k, d: os.environ.get(k, d)
tag = sys.argv[1]
SOLE = float(E('SOLE', '0.02')); SEAM = float(E('SEAM', '0.02'))
FACE_Z = float(E('FACE_Z', '-0.01')); FACE_Y = float(E('FACE_Y', '1.805')); FACE_ZF = float(E('FACE_ZF', '0.07'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_mummy.glb', 'Mummy')
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
HANDJ = np.array([any(k in n for k in ('Hand', 'Finger', 'Index', 'Middle', 'Ring', 'Pinky', 'Thumb')) for n in names])
PR = ['Mummy', 'MummyHead']
CLS = ['body', 'hands', 'neck', 'strips', 'face', 'hood', 'eyes']
allP = [D[nm]['P'] for nm in PR]; allT = [D[nm]['T'] for nm in PR]
FV = np.concatenate([p[t] for p, t in zip(allP, allT)])            # (F,3,3) rest corners, glTF y-up
# hood rim: open boundary of the head shell (the big head piece)
P1, T1 = allP[1], allT[1]
w1 = weld_ids(P1); F1 = w1[T1]
ed = np.sort(np.vstack([F1[:, [0, 1]], F1[:, [1, 2]], F1[:, [2, 0]]]), 1); u, ccount = np.unique(ed, axis=0, return_counts=True)
bv = np.unique(u[ccount == 1].ravel()); rep = np.zeros(w1.max() + 1, np.int64); rep[w1] = np.arange(len(P1))
ring = P1[rep[bv]]
# the shell is also open round the eye sockets and where hidden hood walls were deleted (y 1.70-1.82): the neck rim is the part
# below RIM_LO (chin 1.64 in front, 1.615 at the back)
RIM_LO = float(E('RIM_LO', '1.70'))
print('head open-boundary verts', len(ring), 'below', RIM_LO, int((ring[:, 1] < RIM_LO).sum()))
ring = ring[ring[:, 1] < RIM_LO]
RIM_Y = float(ring[:, 1].max())
cls_all = []
for k, name in enumerate(PR):
    P, T, J, W = (D[name][x] for x in ('P', 'T', 'J', 'W'))
    w = weld_ids(P); FT = w[T]; n = w.max() + 1
    r = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
    _, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)
    fl = lab[FT[:, 0]]; cnt = np.bincount(fl); big = np.argmax(cnt)
    cen = P[T].mean(1)
    cls = np.full(len(T), -1)
    if k == 0:
        cls[:] = CLS.index('strips'); main = fl == big; cls[main] = CLS.index('body')
        hw = (W * HANDJ[J]).sum(1)
        cls[main & (hw[T].mean(1) > 0.5)] = CLS.index('hands')
        cls[main & (P[T][:, :, 1].min(1) > RIM_Y)] = CLS.index('neck')
        sole_ref = P[T[main]][:, :, 1].min()
    else:
        cls[:] = CLS.index('eyes'); main = fl == big
        face = ((cen[:, 2] > FACE_Z) & (cen[:, 1] < FACE_Y)) | (cen[:, 2] > FACE_ZF)
        cls[main & face] = CLS.index('face'); cls[main & ~face] = CLS.index('hood')
    cls_all.append(cls)
    for ci in np.unique(cls):
        print(f'  {name:10s} {CLS[ci]:7s} {int((cls == ci).sum()):5d}')
cls = np.concatenate(cls_all)
C = lambda *ns: np.isin(cls, [CLS.index(x) for x in ns])
keep = C('face', 'eyes', 'strips')
sole = C('body') & (FV[:, :, 1].max(1) < sole_ref + SOLE); keep |= sole
dseam = cKDTree(ring).query(FV.reshape(-1, 3))[0].reshape(-1, 3).min(1)
seam = (dseam < SEAM) & C('body', 'neck', 'hood'); keep |= seam
for nm in [x for x in E('KEEP_EXTRA', '').split(',') if x]:
    ex = np.load(HERE / 'work' / f'{nm}.npy'); keep |= ex; print('extra keep', nm, int(ex.sum()))
lining = np.zeros(len(cls), bool); lined = np.zeros(len(cls), bool)
group = np.zeros(len(cls), int)
for gi, ns in ((1, ('hands',)), (2, ('hood',)), (3, ('neck',))):
    group[C(*ns) & ~keep] = gi
mat = np.concatenate([np.full(len(t), i) for i, t in enumerate(allT)])
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=lining, lined=lined, cls=cls, mat=mat)
rows = {}
for ci, cn in enumerate(CLS):
    s = cls == ci
    if s.any():
        rows[cn] = dict(faces=int(s.sum()), keep=int((s & keep).sum()), free=int((s & ~keep).sum()))
        print(f'{cn:7s} {s.sum():5d} keep {int((s & keep).sum()):5d} free {int((s & ~keep).sum()):5d}')
print('soles', int(sole.sum()), 'seam', int(seam.sum()), 'rim y90', round(RIM_Y, 3))
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'free', int((~keep).sum()), 'of', len(cls),
      '| groups', {k: int((group == k).sum()) for k in range(4)})
(HERE / 'work' / 'classes.json').write_text(json.dumps(dict(names=CLS, rows=rows), indent=1))
