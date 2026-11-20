#!/usr/bin/env python3
"""Keep set and region groups for the m286 ladder (work/pieces.npy, garments.npy, soles.npy, headset.npy, horns.npy,
visible_all.npy, groups.npz from dump_groups.py).
Kept exactly: the right hand and every face touching a vertex with right hand + finger weight > 0.3 (the solved axe
fist); the
eyes, ears, nose ring, snout piece, brows and forelock (3, 7-11, 14, 19, 20); the wrist bands and their spikes (4, 5,
garment 8); the belt, buckle and beads (6, 13, garment 4); every other small separate piece of up to M286_SMALL
(default 80) faces (mane and crown cards: their ends taper into points at any cut); the hoof soles (faces below 6 cm);
the face front (head-set faces within M286_FACE_R, default 0.11 m, of the muzzle/eye centre and in front of
y = -0.12); the horn tips (horn faces above M286_TIP_Z, default 2.06 m).
Groups (decimated on their own; ratios in run_ladder.sh): 1 head set rest (skull, jaw, neck top, traps; not hidden),
2 horns, 3 kilt and front flap, 4 mane sheet, 5 hidden faces (never seen in work/visible_all.npy), 6 the free left
hand (faces touching left hand + finger weight > 0.3), 9 the face front skin with M286_FACE_GROUP=1 (else kept); with M286_SPLIT_BODY=1 the body skin is split into 7
torso (rest z 0.98-1.5 m, |x| < 0.36), 8 arms, and label 0 (legs) takes the free ratio; otherwise label 0 (torso,
arms, legs: the body skin) takes the free ratio of the ladder.
Usage: m286_sets.py <name> -> work/keep_<name>.npy, work/groups_<name>.npy"""
import os
import sys
import numpy as np
E = lambda k, x: float(os.environ.get(k, x))
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
p = np.load('work/pieces.npy'); g_ = np.load('work/garments.npy'); soles = np.load('work/soles.npy')
headset = np.load('work/headset.npy'); horns = np.load('work/horns.npy'); seen = np.load('work/visible_all.npy')
g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
hand = W[:, [i for i, n in enumerate(names) if n.endswith('_Hand') or 'Finger' in n]].sum(1)
rhand = W[:, [i for i, n in enumerate(names) if n.startswith('B_R_') and (n.endswith('_Hand') or 'Finger' in n)]].sum(1)
lhand = W[:, [i for i, n in enumerate(names) if n.startswith('B_L_') and (n.endswith('_Hand') or 'Finger' in n)]].sum(1)
counts = {q: int((p == q).sum()) for q in set(p.tolist())}
small = np.array([counts[q] <= E('M286_SMALL', '80') for q in p])
face = headset & ~horns & (np.linalg.norm(c - np.array([0.0, -0.27, 1.60]), axis=1) < E('M286_FACE_R', '0.11')) & (c[:, 1] < -0.12)
tips = horns & (v[f][..., 2].max(1) > E('M286_TIP_Z', '2.06'))
facegroup = os.environ.get('M286_FACE_GROUP') == '1'   # face front skin (piece 0) decimated on its own as group 9
keep = (np.isin(p, (3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 19, 20)) | np.isin(g_, (4, 8)) | (rhand[f] > 0.3).any(1) | small
        | soles | (face & ~(facegroup & (p == 0))) | tips)
extra = os.environ.get('M286_EXTRA_KEEP')
if extra:
    for e in extra.split(','):
        keep |= np.load(e)
groups = np.zeros(len(f), int)
groups[headset & ~horns & (p == 0)] = 1
groups[horns] = 2
groups[np.isin(p, (1, 12))] = 3
groups[p == 2] = 4
groups[(seen == 0) & (groups != 2)] = 5
groups[(lhand[f] > 0.3).any(1)] = 6                       # the free left hand (no grip)
if facegroup:
    groups[face & (p == 0)] = 9
groups[keep] = 0
if os.environ.get('M286_SPLIT_BODY') == '1':          # the body skin split: 7 torso, 8 arms, legs stay 0 (free)
    body = (groups == 0) & ~keep
    torso = body & (c[:, 2] > 0.98) & (c[:, 2] < 1.5) & (np.abs(c[:, 0]) < 0.36)
    legs = body & (c[:, 2] < 0.98)
    groups[torso] = 7; groups[body & ~torso & ~legs] = 8
name = sys.argv[1]; np.save(f'work/keep_{name}.npy', keep); np.save(f'work/groups_{name}.npy', groups)
print('KEEP', int(keep.sum()), '(right hand', int(((rhand[f] > 0.3).any(1)).sum()), 'small', int(small.sum()), 'face', int(face.sum()),
      'tips', int(tips.sum()), 'soles', int(soles.sum()), ')', {k: int(((groups == k) & ~keep).sum()) for k in range(10)})
