#!/usr/bin/env python3
"""Keep / group sets per face of work/mesh_in.npz (welded source, Blender frame) for decimate_tex.py, from the creature
project's part labels on the installed GLB (work/glb_parts.npz, glb_parts.py) and the GLB's skin weights.
Kept exactly: the whole head primitive (LizHead: face, helm, teeth, tongue, neck strip; it is not even swapped on export),
the hands (hide faces with any Hand/Finger weight, plus 3 cm of wrist), the cutlass grip (blade within GRIP m of the fist)
or the whole cutlass (WEAPON=keep), body faces within NECK m of the neck ring, the soles (faces reaching below floor + SOLE),
the chest shell (part 11, clipped to its paint), the hip plates (part 15: plate_gate.py's shell points) and every small piece (connected components of up to SMALL faces: pauldron
lames, thigh straps, flap, belt pieces).
Groups (decimated on their own, ratios from REA_GROUP_RATIOS; SET_GROUPS selects which of 1-4, 6 are used, 5 and 7 always are): 1 pauldrons (16), 2 bracers (23), 3 greaves (17),
4 belt skirt + hip plates + belt (13, 15, 10), 5 cutlass blade (30 outside the grip band), 6 tail (hide behind the pelvis
below the waist), 7 left (empty) hand with LHAND=group, 8 right hand with RHAND=group (wrist junction and grip contact kept). 0 = the rest of the hide.
Usage: make_sets.py <tag>  -> work/keep_<tag>.npy, work/groups_<tag>.npy"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
tag = sys.argv[1]
E = lambda k, v: float(os.environ.get(k, v))
SOLE, NECK, GRIP, SMALL = E('SOLE', .06), E('NECK', .04), E('GRIP', .10), int(E('SMALL', 90))
d = np.load(HERE / 'work' / 'mesh_in.npz'); V, F = d['verts'], d['faces']
mat = (d['wuv'].reshape(-1, 3, 2)[:, 0, 0] // 2).astype(int)
g = np.load(HERE / 'work' / 'glb_parts.npz')
gc = g['cen'][:, [0, 2, 1]] * [1, -1, 1]                      # glTF y-up -> Blender z-up
fc = V[F].mean(1)
dist, nn = cKDTree(gc).query(fc); assert dist.max() < 1e-5, dist.max()
part = g['part'][nn]; ring = g['ring'][nn]
assert (g['mat'][nn] == mat).all()
P = lambda *n: np.isin(part, n)
m = Model(Glb(str(HERE / 'before' / 'mm9_lizardorc.glb')))
nm = [n.get('name') for n in m.glb.json['nodes']]; jn = [nm[j] for j in m.joints]
J = np.vstack([p['joints'] for p in m.primitives]); W = np.vstack([p['weights'] for p in m.primitives])
offs = np.cumsum([0] + [len(p['positions']) for p in m.primitives]); gt = np.vstack([np.asarray(p['triangles']) + o for p, o in zip(m.primitives, offs)])
ws = lambda subs: (np.isin(J, [i for i, n in enumerate(jn) if any(s in n for s in subs)]) * W).sum(1)[gt].max(1)[nn]
jp = np.linalg.inv(m.inverse_binds)[:, :3, 3][:, [0, 2, 1]] * [1, -1, 1]
J3 = lambda n: jp[jn.index(n)]
keep = np.zeros(len(F), bool)
keep |= mat == 2                                              # head primitive
hand = P(0) & (ws(['Hand', 'Finger']) > 0.01)
for s in 'LR':
    hand |= P(0) & (np.linalg.norm(fc - J3(f'Bip01 {s} Hand'), axis=1) < 0.03)
LHAND = os.environ.get('LHAND', 'keep')                       # 'group': left (empty) hand as group 7, wrist junction kept
JUNC = E('JUNC', .02)
junction = P(0) & (ws(['Hand', 'Finger']) > JUNC) & (ws(['Forearm']) > JUNC)
lhand = hand & (fc[:, 0] > 0) & ~junction                      # Blender +x = glTF +x = figure's left (cutlass hand at -x)
contact = np.load(HERE / 'work' / 'grip_contact.npy')[nn] if (HERE / 'work' / 'grip_contact.npy').exists() else np.zeros(len(F), bool)
rhand = hand & (fc[:, 0] < 0) & ~junction & ~contact           # RHAND=group: right hand as group 8, grip contact (grip_contact.py) kept
keep |= hand & ~(lhand if LHAND == 'group' else np.zeros(len(F), bool)) & ~(rhand if os.environ.get('RHAND') == 'group' else np.zeros(len(F), bool))
floor = V[:, 2].min(); sole = V[F][:, :, 2].min(1) < floor + SOLE; keep |= sole
rv = np.unique(F[(mat < 2) & ring]); neck = np.zeros(len(F), bool)
if len(rv):
    dd, _ = cKDTree(V[rv]).query(fc); neck = (mat < 2) & (dd < NECK); keep |= neck
KEEP_PARTS = [int(x) for x in os.environ.get('KEEP_PARTS', '11,15').split(',')]  # chest shell (clipped to its paint), hip plates (plate_gate.py shell points)
keep |= P(*KEEP_PARTS)
key = np.round(V, 6); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel(); t_ = inv[F]; n_ = inv.max() + 1
r_ = np.concatenate([t_[:, 0], t_[:, 1], t_[:, 2]]); c_ = np.concatenate([t_[:, 1], t_[:, 2], t_[:, 0]])
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n_, n_)), directed=False)
fl = lab[t_[:, 0]]; cnt = np.bincount(fl); small = (cnt[fl] <= SMALL) & (mat < 2); keep |= small
# cutlass: grip band round the fist (finger joints of the right hand at bind), the rest is group 5 or kept
fing = np.array([J3(n) for n in jn if n.startswith('Bip01 R Finger') or n == 'Bip01 R Hand'])
dg, _ = cKDTree(fing).query(fc); grip = (mat == 3) & (dg < GRIP)
if os.environ.get('WEAPON', 'reduce') == 'keep':
    keep |= mat == 3
else:
    keep |= grip
groups = np.zeros(len(F), int)
pel = J3('Bip01 Pelvis')
tail = P(0) & (fc[:, 1] > pel[1] + 0.12) & (fc[:, 2] < pel[2] + 0.05)  # Blender: -y is front (glTF +z), tail behind
GROUPS = os.environ.get('SET_GROUPS', '1,2,3,4,5,6,7').split(',')
for gid, sel in ((1, P(16)), (2, P(23)), (3, P(17)), (4, P(13, 15, 10)), (5, mat == 3), (6, tail), (7, lhand), (8, rhand)):
    if str(gid) not in GROUPS and gid not in (5, 7, 8):
        continue
    groups[sel & ~keep] = gid
names = {0: 'hide', 1: 'pauldrons', 2: 'bracers', 3: 'greaves', 4: 'belt/skirt/hips', 5: 'blade', 6: 'tail', 7: 'left hand', 8: 'right hand'}
for k, n in names.items():
    print(f'group {k} {n:16s} {int((groups == k)[~keep].sum()):6d}')
print('junction', int(junction.sum()), 'left hand free', int((lhand & ~keep).sum()), 'right hand free', int((rhand & ~keep).sum()), 'grip contact', int((contact & hand).sum()))
print('kept: head', int((mat == 2).sum()), 'hands', int(hand.sum()), 'soles', int((sole & ~hand).sum()), 'neck', int((neck & ~sole).sum()),
      'parts ' + str(KEEP_PARTS), int(P(*KEEP_PARTS).sum()), 'small', int(small.sum()), 'grip', int(grip.sum()))
print('TOTAL keep', int(keep.sum()), 'free', int((~keep).sum()), 'of', len(F), f'protected share {keep.mean():.3f}')
np.save(HERE / 'work' / f'keep_{tag}.npy', keep); np.save(HERE / 'work' / f'groups_{tag}.npy', groups)
np.save(HERE / 'work' / 'part_mi.npy', part)
