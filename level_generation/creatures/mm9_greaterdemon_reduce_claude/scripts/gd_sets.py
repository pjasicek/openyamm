#!/usr/bin/env python3
"""Per-face keep / group / lining sets on the installed Greater Demon LOD0 (primitive order GreaterDemon body,
GreaterDemon_Wing membrane, GreaterDemonHead) for mpqem.py: work/glb_sets_<tag>.npz (one entry per GLB face).
Prio-1 relaxed keep set (REDUCTION_BRIEF_20261104):
- head primitive (main head with face, mouth, teeth, eyes, horns and horn roots; both arm heads with jaws, tongues, teeth;
  the wrist bands): kept whole in mpqem (KEPT_PRIMS);
- body, exact: every connected piece that is not a wing bone and has at most SMALL faces (spikes, claws, toe nails, the
  belt piece), the neck and wrist seams (body faces with a vertex within NECK m of a head-primitive vertex), soles (faces
  within SOLE m of the rest floor), optional extra keep files work/keep_extra_<name>.npy (GLB faces, all primitives);
- group 0: the two big skin pieces (torso + arms, pelvis + legs + tail), the ladder ratio;
- group 2: the wing bones (tubes along Xwing* and the finger spars along Xwarm*; build_wings_v2.py), MP_GROUPS 2:<r>;
- membrane: rim faces (an edge of ~8 mm across the shell) exact; per wing one sheet is 'lined' (group 3, MP_GROUPS 3:<r>)
  and the other its 'lining', re-emitted by mpqem from the cut sheet's twins (the Highwayman's lining route).
Usage: gd_sets.py <tag> [extra keep names...]"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
E = lambda k, d: os.environ.get(k, d)
NECK = float(E('NECK', '0.03')); SOLE = float(E('SOLE', '0.03')); SMALL = int(E('SMALL', '300'))
tag = sys.argv[1]; extras = sys.argv[2:]
doc, b = gb.read(HERE / 'before' / 'mm9_greaterdemon.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'GreaterDemon' and 'mesh' in n)
pr = gb.prims(doc, b, node['mesh']); assert [p['material'] for p in pr] == ['GreaterDemon', 'GreaterDemon_Wing', 'GreaterDemonHead']
joints = [doc['nodes'][j]['name'] for j in doc['skins'][node['skin']]['joints']]
body, wing, head = pr


def comps(P, T):
    _, wv = np.unique(np.round(P, 5), axis=0, return_inverse=True); wv = wv.ravel(); FT = wv[T]; n = wv.max() + 1
    r = np.concatenate([FT[:, 0], FT[:, 1], FT[:, 2]]); c = np.concatenate([FT[:, 1], FT[:, 2], FT[:, 0]])
    _, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)
    return lab[FT[:, 0]], wv, FT


# ---- body
P, T, J, W = body['POSITION'].astype(float), body['T'], body['JOINTS_0'], body['WEIGHTS_0'].astype(float)
nB = len(T)
fl, _, _ = comps(P, T); cnt = np.bincount(fl)
fw = np.zeros((nB, len(joints)))
for k in range(3):
    for c in range(4):
        np.add.at(fw, (np.arange(nB), J[T[:, k], c]), W[T[:, k], c])
dom = np.array([joints[i] for i in fw.argmax(1)])
cdom = {c: dom[fl == c][np.unique(dom[fl == c], return_inverse=True)[1].ravel()] for c in []}
wingc = np.zeros(len(cnt), bool)
for c in range(len(cnt)):
    names, k = np.unique(dom[fl == c], return_counts=True)
    wingc[c] = names[k.argmax()].startswith(('Xwing', 'Xwarm'))
is_wing = wingc[fl]
small = (cnt[fl] <= SMALL) & ~is_wing
hd = cKDTree(head['POSITION'].astype(float)).query(P)[0]
neck = (hd[T] < NECK).any(1)
floor = P[:, 1].min(); sole = P[T][:, :, 1].min(1) < floor + SOLE
keepB = small | neck | sole
groupB = np.where(is_wing, 2, 0); groupB[keepB] = 0
print(f'body {nB}: wing bones {int(is_wing.sum())}, small pieces {int(small.sum())}, neck/wrist seam {int(neck.sum())} '
      f'(on wing {int((neck & is_wing).sum())}), soles {int(sole.sum())}; kept {int(keepB.sum())}, '
      f'free skin {int(((groupB == 0) & ~keepB).sum())}, free wing bones {int(((groupB == 2) & ~keepB).sum())}')
# ---- membrane
Pw, Tw = wing['POSITION'].astype(float), wing['T']
_, wv, FT = comps(Pw, Tw)
X = np.zeros((wv.max() + 1, 3)); X[wv] = Pw
el = np.linalg.norm(X[FT[:, [1, 2, 0]]] - X[FT], axis=2)
rim = (el < 0.011).any(1)
nWf = len(Tw)
F = FT[~rim]; n = wv.max() + 1
r = np.concatenate([F[:, 0], F[:, 1], F[:, 2]]); c = np.concatenate([F[:, 1], F[:, 2], F[:, 0]])
_, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)
sheet = -np.ones(nWf, int); sheet[~rim] = lab[F[:, 0]]
lined = np.zeros(nWf, bool); lining = np.zeros(nWf, bool)
cen = X[FT].mean(1)
for side in (-1, 1):
    ids = [s for s in np.unique(sheet[sheet >= 0]) if np.sign(cen[sheet == s, 0].mean()) == side]
    assert len(ids) == 2, ids
    # lined = the sheet whose area-weighted normal points to the back (-z in glTF: the demon faces +z); either works
    nz = []
    for s in ids:
        m = sheet == s; nn = np.cross(X[FT[m, 1]] - X[FT[m, 0]], X[FT[m, 2]] - X[FT[m, 0]]); nz.append(nn.sum(0)[2])
    a, bb = (ids[0], ids[1]) if nz[0] < nz[1] else (ids[1], ids[0])
    lined |= sheet == a; lining |= sheet == bb
    print(f'membrane side {side}: lined sheet {int((sheet == a).sum())} (normal z {min(nz):.3f}), lining {int((sheet == bb).sum())}')
keepW = rim.copy(); groupW = np.where(lined, 3, 0)
print(f'membrane {nWf}: rim {int(rim.sum())} kept, lined {int(lined.sum())}, lining {int(lining.sum())}')
# ---- head
nH = len(head['T'])
keep = np.r_[keepB, keepW, np.ones(nH, bool)]
group = np.r_[groupB, groupW, np.zeros(nH, int)]
for name in extras:
    k = np.load(HERE / 'work' / f'keep_extra_{name}.npy'); keep |= k; print('extra', name, int(k.sum()))
tot = len(keep)
print(f'protected share {(keep.sum() + lining.sum()) / tot * 100:.1f} % (kept {int(keep.sum())} + lining {int(lining.sum())} of {tot})')
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=np.r_[np.zeros(nB, bool), lining, np.zeros(nH, bool)],
         lined=np.r_[np.zeros(nB, bool), lined, np.zeros(nH, bool)], wingbone=np.r_[is_wing, np.zeros(nWf + nH, bool)])
