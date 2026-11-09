#!/usr/bin/env python3
"""Per-face keep mask and ratio groups for the Evil Sorcerer (mm9_evilsorcerer, 13,348 LOD0 triangles in one skinned
node `Sorcerer`: Up set 4,850, Low set 4,916, head set 3,582). Parts from work/parts.npz (parts_map.py).
Prio-1 relaxed keep set (REDUCTION_BRIEF_20261104.md):
Kept exactly (work/keep.npy):
- the face skin: head-part faces at the face texel density (uv_es.py gave the face 1.7x and the helmet's back neck
  guard "flap" 0.55x; work/texel_ratio.npy separates them: face > 0.6), and both eyes;
- the neck seam: torso and yoke faces within NECK m of a head vertex under NECK_ZMAX (the collar the closed neck sits in);
- the soles: shoe faces with every corner under SOLE_Z;
- the hand-graft junction: hand faces with any Forearm/XhalfForearm weight, plus RING face rings round the open wrist
  rim; the finger phalanges 2 and 3 (pads and tips) unless FINGER_RATIO puts them in their own group;
- small separate pieces (connected components under SMALL faces: the crown's jewel piece).
Groups (work/groups.npy, ratios in work/group_ratios.txt): 0 the rest (ladder budget), 1 head flap (neck guard)
FLAP_RATIO, 2 crown CROWN_RATIO, 3 palm/back of hand and proximal phalanges HAND_RATIO, 4 finger phalanges 2-3
(FINGER_RATIO, optional), 5 panels (PANEL_RATIO, optional), 6 rigid plates (pauldrons, bracers, greaves, boots;
PLATE_RATIO, optional)."""
import os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
E = os.environ.get
SOLE_Z, NECK, RING, SMALL = float(E('SOLE_Z', '0.04')), float(E('NECK', '0.03')), int(E('RING', '1')), int(E('SMALL', '80'))
d = np.load('work/mesh_in.npz'); sw = np.load('work/src_weights.npz'); P = np.load('work/parts.npz')
f, v = d['faces'], d['verts']; W = sw['weights']; bn = [str(x) for x in sw['names']]
pn = [str(x) for x in P['names']]; part = P['part']; isp = lambda *n: np.isin(part, [pn.index(x) for x in n])
tr = np.load('work/texel_ratio.npy')
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]
# open rim vertices
ek = np.sort(e, 1); u, inv, cnt = np.unique(ek, axis=0, return_inverse=True, return_counts=True)
rimv = np.zeros(n, bool); rimv[u[cnt == 1].ravel()] = True


def grow(m, rings, within):
    for _ in range(rings):
        hv = np.zeros(n, bool); hv[f[m].ravel()] = True; m = m | (hv[f].any(1) & within)
    return m


head = isp('head'); face = head & (tr > 0.6); flap = head & ~face
eyes = isp('eyes')
# neck seam: torso faces near the head's open rim
from scipy.spatial import cKDTree  # noqa: E402
# the head's neck is closed and sits in the collar: torso/yoke faces within NECK of a head vertex under the jaw
hv = np.unique(f[head].ravel()); hv = hv[v[hv, 2] < float(E('NECK_ZMAX', '1.74'))]
dist, _ = cKDTree(v[hv]).query(v[f].mean(1))
neck = isp('torso', 'yokeF', 'yokeB') & (dist < NECK)
soles = isp('shoes') & (v[f][:, :, 2] < v[:, 2].min() + SOLE_Z).all(1)
hands = isp('hands')
col = lambda *keys: W[:, [i for i, s in enumerate(bn) if any(k in s for k in keys)]].sum(1)
fw = col('Forearm')[f].max(1)
wrist = hands & (fw > 0.001)
wr = np.unique(f[hands].ravel()); wr = wr[rimv[wr]]; wm = np.zeros(n, bool); wm[wr] = True
wrist |= hands & wm[f].any(1)
wrist = grow(wrist, RING, hands)
tips = col('Index2', 'Index3', 'Middle2', 'Middle3', 'Ring2', 'Ring3', 'Pinky2', 'Pinky3', 'Thumb2', 'Thumb3')
fing = hands & (tips[f].max(1) > 0.5) & ~wrist
small = np.zeros(len(f), bool)
for p in np.unique(pc):
    m = pc == p
    if m.sum() < SMALL and not (eyes[m].any()):
        small |= m
g = np.zeros(len(f), int); ratios = {}
g[flap] = 1; ratios[1] = float(E('FLAP_RATIO', '0.7'))
g[isp('crown')] = 2; ratios[2] = float(E('CROWN_RATIO', '0.75'))
g[hands & ~wrist & ~fing] = 3; ratios[3] = float(E('HAND_RATIO', '0.65'))
keep = face | eyes | neck | soles | wrist | small
if E('FINGER_RATIO'):
    g[fing] = 4; ratios[4] = float(E('FINGER_RATIO'))
else:
    keep |= fing
if E('PANEL_RATIO'):
    g[isp('panelF', 'panelB')] = 5; ratios[5] = float(E('PANEL_RATIO'))
if E('PLATE_RATIO'):
    g[isp('pauldrons', 'bracers', 'greaves', 'boots')] = 6; ratios[6] = float(E('PLATE_RATIO'))
# config b (a r70 GLB clay close-ups, review/s_a70_det_clay.png): the belt went lumpy with a torn lower rim, the hip
# flaps' teeth showed through the flattened panel tops, a flap opened a dark slot, and the bracer's wrist rim pulled
# off the hand. KEEP_PARTS keeps whole parts; panel faces within PANEL_NEAR of a flap vertex and bracer faces within
# BRACER_NEAR of a hand vertex are kept exactly.
if E('KEEP_PARTS'):
    keep |= isp(*E('KEEP_PARTS').split(','))
if E('PANEL_NEAR'):
    fv = np.unique(f[isp('flapF', 'flapB')].ravel()); dd, _ = cKDTree(v[fv]).query(v[f].mean(1))
    keep |= isp('panelF', 'panelB') & (dd < float(E('PANEL_NEAR')))
# config c (b r72 clay close-ups, review/s_b72_panels_clay.png): the panels are thin closed slabs (walls under 6 mm
# apart); their walls crossed at the hem teeth, the back slit and the edges (dark wedges). The rim strip (panel faces
# whose inward ray finds no wall within 6 mm: the slab's side walls, work/thin_0.006.npy) plus PANEL_RIM face rings on
# the walls is kept exactly, so the two walls decimate between fixed edges.
if E('PANEL_RIM'):
    pnl = isp('panelF', 'panelB'); rim = pnl & ~np.load('work/thin_0.006.npy')
    keep |= grow(rim, int(E('PANEL_RIM')), pnl)
if E('BRACER_NEAR'):
    hv_ = np.unique(f[hands].ravel()); dd, _ = cKDTree(v[hv_]).query(v[f].mean(1))
    keep |= isp('bracers') & (dd < float(E('BRACER_NEAR')))
if E('EXTRA_KEEP'):
    for x in E('EXTRA_KEEP').split(','):
        keep |= np.load(x)
open('work/group_ratios.txt', 'w').write(','.join(f'{k}:{r}' for k, r in ratios.items()))
np.save('work/groups.npy', g); np.save('work/keep.npy', keep)
np.save('work/keep_face.npy', face | eyes); np.save('work/keep_neck.npy', neck); np.save('work/keep_wrist.npy', wrist)
np.save('work/fingers.npy', fing); np.save('work/keep_soles.npy', soles)
print('KEEP', int(keep.sum()), 'face', int(face.sum()), 'eyes', int(eyes.sum()), 'neck', int(neck.sum()), 'soles',
      int(soles.sum()), 'wrist', int(wrist.sum()), 'fingers', int(fing.sum()), 'small', int((small & ~eyes).sum()),
      '| groups free', {int(k): int(((g == k) & ~keep).sum()) for k in sorted(set(g.tolist()))}, ratios)
