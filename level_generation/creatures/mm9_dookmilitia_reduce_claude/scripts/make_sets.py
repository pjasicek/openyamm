#!/usr/bin/env python3
"""Keep / group sets per face of work/mesh_in.npz (welded source, Blender frame: z up, figure faces -y) for decimate_tex.py,
from the creature project's part labels on the installed GLB (work/glb_parts.npz) and the GLB's skin weights.
Prio-1 relaxed keep set (REDUCTION_BRIEF_20261104.md). Kept exactly:
- the face skin (part 20: face, ears, neck), eyes (22) and the old neck V (2), and body faces within NECK m of them (neck seam);
- helm faces (21) within HELM_SEAM m of the face skin (the hood's rim round the face, the cheek strip under the bars);
- the hand-graft junction (faces with a vertex 0 < graft_s < 1, plus hand and forearm weight both > JUNC), the right hand's
  grip contact (grip_contact.py) and, unless LHAND=group / RHAND=group, the whole hands;
- the sword (WEAPON=keep, default), soles (faces reaching below floor + SOLE), linings (lining flag) plus RING face rings of
  their outer shell, and every small piece (connected components of up to SMALL faces: cheek bars, studs, buckles);
- KEEP_PARTS (comma list) whole.
Groups (decimated on their own; ratios via REA_GROUP_RATIOS): 1 helm/hood shell, 2 skirt (7, Skirt_* chains), 3 left hand,
4 right hand, 5 mantle (8), 6 sword (WEAPON=reduce), 7 boots (6), 8 shoulder caps (13), 9 buckle (10).
CUFF / BOOT_TOP (m): keep sleeve faces round the wrists and the boots' top rims. 0 = the rest (tunic, sleeves, pants, belt, buckle, caps).
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
SOLE, NECK, SMALL, JUNC, HELM_SEAM, RING = E('SOLE', .06), E('NECK', .03), int(E('SMALL', 90)), E('JUNC', .02), E('HELM_SEAM', .01), int(E('RING', 1))
d = np.load(HERE / 'work' / 'mesh_in.npz'); V, F = d['verts'], d['faces']
mat = (d['wuv'].reshape(-1, 3, 2)[:, 0, 0] // 2).astype(int)
g = np.load(HERE / 'work' / 'glb_parts.npz')
gc = g['cen'][:, [0, 2, 1]] * [1, -1, 1]                      # glTF y-up -> Blender z-up
fc = V[F].mean(1)
gc = gc - [0, 0, float(os.environ.get('ZOFF', '0.99173'))]  # the import keeps the mesh in its local frame (MM9_Rig node lifts it 0.9917 m)
dist, nn = cKDTree(gc).query(fc); assert dist.max() < 1e-4, dist.max()
assert (g['mat'][nn] == mat).all()
part = g['part'][nn]; lining = g['lining'][nn] > 0; graft = g['graft_any'][nn] & (g['graft'][nn] > 0)
P = lambda *n: np.isin(part, n)
m = Model(Glb(str(HERE / 'before' / 'mm9_dookmilitia.glb')))
nm = [n.get('name') for n in m.glb.json['nodes']]; jn = [nm[j] for j in m.joints]
J = np.vstack([p['joints'] for p in m.primitives]); W = np.vstack([p['weights'] for p in m.primitives])
offs = np.cumsum([0] + [len(p['positions']) for p in m.primitives]); gt = np.vstack([np.asarray(p['triangles']) + o for p, o in zip(m.primitives, offs)])
ws = lambda subs: (np.isin(J, [i for i, n in enumerate(jn) if any(s in n for s in subs)]) * W).sum(1)[gt].max(1)[nn]
HANDJ = ['Hand', 'Index', 'Middle', 'Ring', 'Pinky', 'Thumb']
# welded connectivity
key = np.round(V, 6); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel(); t_ = inv[F]; n_ = inv.max() + 1
r_ = np.concatenate([t_[:, 0], t_[:, 1], t_[:, 2]]); c_ = np.concatenate([t_[:, 1], t_[:, 2], t_[:, 0]])
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n_, n_)), directed=False)
fl = lab[t_[:, 0]]; cnt = np.bincount(fl)


def grow(sel, rings):
    """sel plus `rings` face rings across shared (welded) vertices"""
    s = sel.copy()
    for _ in range(rings):
        vs = np.zeros(n_, bool); vs[t_[s].ravel()] = True; s = s | vs[t_].any(1)
    return s


keep = np.zeros(len(F), bool)
face = (mat == 2) & ~P(21)
keep |= face
fv = np.unique(F[face & P(20, 2)])
dn, _ = cKDTree(V[fv]).query(fc)
neck = (mat < 2) & (dn < NECK); keep |= neck
helm_seam = P(21) & (dn < HELM_SEAM); keep |= helm_seam
hand = P(0) & (ws(HANDJ) > 0.01)
junction = P(0) & (graft | ((ws(HANDJ) > JUNC) & (ws(['Forearm']) > JUNC)))
contact = np.load(HERE / 'work' / 'grip_contact.npy')[nn]
lhand = hand & (fc[:, 0] > 0) & ~junction                      # glTF +x = Blender +x = the figure's left (sword hand at -x)
rhand = hand & (fc[:, 0] < 0) & ~junction & ~contact
keep |= junction | (hand & contact)
keep |= lhand if os.environ.get('LHAND', 'keep') != 'group' else np.zeros(len(F), bool)
keep |= rhand if os.environ.get('RHAND', 'keep') != 'group' else np.zeros(len(F), bool)
floor = V[:, 2].min(); sole = V[F][:, :, 2].min(1) < floor + SOLE; keep |= sole
lin = grow(lining, RING) if os.environ.get('LININGS', 'keep') == 'keep' else np.zeros(len(F), bool); keep |= lin
small = (cnt[fl] <= SMALL); keep |= small
KEEP_PARTS = [int(x) for x in os.environ.get('KEEP_PARTS', '').split(',') if x]
keep |= P(*KEEP_PARTS)
if os.environ.get('WEAPON', 'keep') == 'keep':
    keep |= mat == 3
# sleeve cuffs: sleeve faces within CUFF m of the wrist joint (a74: the cut cuff rims dented beside both fists)
jp = np.linalg.inv(m.inverse_binds)[:, :3, 3][:, [0, 2, 1]] * [1, -1, 1] - [0, 0, float(os.environ.get('ZOFF', '0.99173'))]
J3 = lambda n: jp[jn.index(n)]
CUFF = E('CUFF', 0)
cuff = np.zeros(len(F), bool)
if CUFF > 0:
    for sd in 'LR':
        cuff |= P(3) & (np.linalg.norm(fc - J3(f'Bip01 {sd} Hand'), axis=1) < CUFF)
keep |= cuff
# boot tops: boot faces within BOOT_TOP m of each boot's highest point (a74: a dent at the boot rim below the knee)
BOOT_TOP = E('BOOT_TOP', 0)
boot_top = np.zeros(len(F), bool)
if BOOT_TOP > 0:
    for sgn in (1, -1):
        b = P(6) & (np.sign(fc[:, 0]) == sgn)
        top = V[F[b]][:, :, 2].max(); boot_top |= b & (V[F][:, :, 2].max(1) > top - BOOT_TOP)
keep |= boot_top
# knees: faces within KNEE m of the calf joints (the Cower and Running knee bends missed by 30-39 mm at 0.78)
KNEE = E('KNEE', 0)
knee = np.zeros(len(F), bool)
if KNEE > 0:
    for sd in 'LR':
        knee |= (mat < 2) & (np.linalg.norm(fc - J3(f'Bip01 {sd} Calf'), axis=1) < KNEE)
keep |= knee
glbk = os.environ.get('GLB_KEEP')                              # per-GLB-face bool .npy (arm_contact.py, grip etc.)
if glbk:
    for e in glbk.split(','):
        keep |= np.load(e)[nn]
extra = os.environ.get('EXTRA_KEEP')                            # per-face bool .npy on mesh_in faces (err-lock patches)
if extra:
    for e in extra.split(','):
        keep |= np.load(e)
groups = np.zeros(len(F), int)
GROUPS = os.environ.get('SET_GROUPS', '1,2,3,4').split(',')
for gid, sel in ((1, P(21)), (2, P(7)), (3, lhand), (4, rhand), (5, P(8)), (6, mat == 3), (7, P(6)), (8, P(13)), (9, P(10))):
    if str(gid) in GROUPS:
        groups[sel & ~keep] = gid
names = {0: 'rest', 1: 'helm', 2: 'skirt', 3: 'left hand', 4: 'right hand', 5: 'mantle', 6: 'sword', 7: 'boots', 8: 'caps', 9: 'buckle'}
for k, n in names.items():
    print(f'group {k} {n:12s} {int((groups == k)[~keep].sum()):6d}')
print('kept: face/eyes/neckV', int(face.sum()), 'neck seam', int((neck & ~face).sum()), 'helm seam', int(helm_seam.sum()),
      'junction', int(junction.sum()), 'grip contact', int((hand & contact).sum()), 'soles', int(sole.sum()),
      'linings+ring', int(lin.sum()), 'cuffs', int(cuff.sum()), 'boot tops', int(boot_top.sum()), 'knees', int(knee.sum()), 'small', int(small.sum()), 'sword', int((mat == 3).sum()), 'hands total', int(hand.sum()))
print('TOTAL keep', int(keep.sum()), 'free', int((~keep).sum()), 'of', len(F), f'protected share {keep.mean():.3f}')
np.save(HERE / 'work' / f'keep_{tag}.npy', keep); np.save(HERE / 'work' / f'groups_{tag}.npy', groups)
np.save(HERE / 'work' / 'part_mi.npy', part)
if os.environ.get('REPORT'):
    import collections
    print('small by part', sorted(collections.Counter(part[small].tolist()).items()))
    cs = collections.Counter((int(fl[i]), int(part[i])) for i in np.where(small)[0])
    print('small comps (size, part):', sorted(collections.Counter((cnt[c], p) for (c, p) in cs).items()))
    print('lining+ring by part', sorted(collections.Counter(part[lin].tolist()).items()))
