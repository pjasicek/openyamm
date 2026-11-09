#!/usr/bin/env python3
"""Per-face labels and keep masks for the Giant (mm9_giant, 15,670 LOD0 triangles in one skinned node `Giant`: body set
8,192, head set 3,972, Meshy mallet 3,506 rigid on Xhammer).
Kept exactly (work/keep.npy):
- the whole head set (material GiantHead: face, hair, eyes; per-tier head images) unless HEAD_FACES points at a
  face-only mask, then only those faces (the hair gets group 2 at its own ratio);
- both hands with the wrist graft: faces with any hand/finger weight >= 0.01 plus RING face rings around them (the
  solved palm grip and the pad-on-shaft finger poses, `fist_giant.py solve_finger_pad`);
- the soles (all three corners within SOLE_Z of the rest floor);
- the mallet pieces the fists hold: every connected mallet piece whose span along the mallet axis meets the grip band
  [GRIP_T0, GRIP_T1] (work/grip_band.json: right fist 0.79-0.99, left 0.12-0.44 in the holding clips): plain shaft,
  lower wrap, pommel and its studs.
Groups (work/groups.npy): 0 body rest (cloth, fur, skin, hair below the head set: the ladder's remaining budget),
1 mallet rest (head, spike, bosses, rivets, wraps under the head), 2 hair (with HEAD_FACES)."""
import json
import os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
SOLE_Z = float(os.environ.get('SOLE_Z', '0.04'))
RING = int(os.environ.get('RING', '1'))
GRIP_T0, GRIP_T1 = float(os.environ.get('GRIP_T0', '0.10')), float(os.environ.get('GRIP_T1', '1.0'))
d = np.load('work/mesh_in.npz'); sw = np.load('work/src_weights.npz')
f, v = d['faces'], d['verts']; mat = (d['wuv'].reshape(-1, 3, 2)[:, 0, 0] // 2).astype(int)
W = sw['weights']; names = [str(n) for n in sw['names']]
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]
hk = [i for i, s in enumerate(names) if any(k in s for k in ('Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))]
hand = (W[:, hk].sum(1)[f].max(1) >= 0.01) & (mat == 0)
for _ in range(RING):
    hv = np.zeros(n, bool); hv[f[hand].ravel()] = True
    hand |= hv[f].any(1) & (mat == 0)
z = v[:, 2]; soles = (z[f] < z.min() + SOLE_Z).all(1)
gb = json.load(open('work/grip_band.json')); ax, c = np.array(gb['axis']), np.array(gb['centre'])
grip = np.zeros(len(f), bool)
for p in np.unique(pc[mat == 2]):
    m = (pc == p) & (mat == 2); t = (v[np.unique(f[m])] - c) @ ax
    if t.max() >= GRIP_T0 and t.min() <= GRIP_T1:
        grip |= m
head = mat == 1
g = np.zeros(len(f), int); g[mat == 2] = 1
if os.environ.get('HEAD_FACES'):
    face = np.load(os.environ['HEAD_FACES']); g[head & ~face] = 2; head = head & face
# feet (config c): Foot/Toe-dominated faces kept exactly (the boot toes rounded off into bulbs at every body step of
# configs a/b; floor contact of every clip rests on them)
dom = np.load('work/faces_info.npz')['dom'].astype(str)
feet = np.array([('Foot' in x or 'Toe' in x) for x in dom]) & (mat == 0)
if os.environ.get('FEET_RATIO'):   # config g: the "bulbous toes" of configs a/b were source.blend's scrambled normals, not geometry
    g[feet & ~soles] = 4; feet = np.zeros(len(f), bool)
# hems (config d): thin flaps of the closed skin (work/thin.npy, opposite wall under 2 cm: loincloth hems and flap tips)
# plus one face ring kept exactly: at r74 the back hem's tips crossed and showed the inside as dark teeth
hem = np.load('work/thin.npy') if os.environ.get('KEEP_HEMS', '1') == '1' else np.zeros(len(f), bool)
hv = np.zeros(n, bool); hv[f[hem].ravel()] = True; hem = (hem | hv[f].any(1)) & (mat == 0)
# calves (config d): Calf-dominated faces (fur and leather shin wraps with their raised rims) at their own ratio
g[np.array([('Calf' in x) for x in dom]) & (mat == 0)] = 3
# pass 2 (prio-1 relaxed keep set, orchestrator 2026-11-04): hair shell (work/head_hair.npy from head_classes.py) at
# HAIR_RATIO; palm, back of hand and the proximal phalanges at HAND_RATIO, while the 2nd/3rd phalanges (pads on the
# shaft) and the wrist graft (any Forearm weight, plus the ring round the hand) stay exact
if os.environ.get('HAIR_RATIO'):
    hairm = np.load('work/head_hair.npy'); g[hairm] = 5; head = head & ~hairm
if os.environ.get('HAND_RATIO'):
    fw = W[:, [i for i, s_ in enumerate(names) if 'Forearm' in s_]].sum(1)[f].max(1)
    base = np.array([any(x.endswith(k) for k in (' Hand', ' Hand_h', 'Index1', 'Middle1', 'Ring1', 'Pinky1', 'Thumb1')) for x in dom])
    handcut = hand & base & (fw < 0.02) & (W[:, hk].sum(1)[f].min(1) > 0.99)
    g[handcut] = 6; hand = hand & ~handcut
keep = head | hand | soles | grip | feet | hem
np.save('work/keep_hems.npy', hem)
np.save('work/keep_feet.npy', feet)
# mallet per piece (config f): in one shared pool the quadric collapsed the small closed pieces first (tiny absolute
# error): at 0.4 the wrap rings under the head twisted into spikes and the round rivets became pyramids (r76e clay
# close-ups). Every mallet piece outside the grip now decimates on its own (group 100 + piece) at MALLET_PIECE_RATIO;
# pieces under MALLET_MIN faces are kept.
ratios = {3: float(os.environ.get('CALF_RATIO', '0.8'))}
for k_, env_ in ((5, 'HAIR_RATIO'), (6, 'HAND_RATIO')):
    if os.environ.get(env_):
        ratios[k_] = float(os.environ[env_])
if os.environ.get('FEET_RATIO'):
    ratios[4] = float(os.environ['FEET_RATIO'])
if os.environ.get('KEEP_MALLET') == '1':   # config g: every per-piece or pooled mallet cut broke its bands, rings and rivets
    keep |= mat == 2
if os.environ.get('KEEP_MALLET') == '1':
    pass
elif os.environ.get('MALLET_PIECE_RATIO'):
    mr = float(os.environ['MALLET_PIECE_RATIO']); mmin = int(os.environ.get('MALLET_MIN', '60'))
    for p in np.unique(pc[(mat == 2) & ~grip]):
        m = (pc == p) & (mat == 2) & ~grip
        if m.sum() < mmin:
            keep |= m
        else:
            g[m] = 100 + p; ratios[100 + p] = mr
else:
    ratios[1] = float(os.environ.get('MALLET_RATIO', '0.4'))
open('work/group_ratios.txt', 'w').write(','.join(f'{k}:{v}' for k, v in ratios.items()))
np.save('work/groups.npy', g); np.save('work/keep.npy', keep)
np.save('work/keep_hands.npy', hand); np.save('work/keep_grip.npy', grip); np.save('work/keep_soles.npy', soles)
print('KEEP', int(np.load('work/keep.npy').sum()), 'head', int(head.sum()), 'hands', int(hand.sum()), 'soles', int(soles.sum()), 'mallet grip', int(grip.sum()), 'feet', int(feet.sum()), 'hems', int((hem & ~hand).sum()),
      '| groups free', {int(k): int(((g == k) & ~keep).sum()) for k in sorted(set(g.tolist()))})
