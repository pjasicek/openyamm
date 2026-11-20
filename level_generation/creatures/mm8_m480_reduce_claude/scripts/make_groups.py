#!/usr/bin/env python3
"""Per-face regions for the Troll Peasant ladder (copied from the Troll m476, whose club is in the left hand; the
peasant holds its club in the right hand) (work/mesh_in.npz order):
keep = small separate pieces of up to REA_SMALL faces (eyes, mouth, teeth, hair locks) + right-hand finger faces (the
fitted club grip) + soles (faces below 6 cm); groups: 1 face/head skin (head texture set of the main piece),
2 left hand and right palm (hand/finger bones not kept), 0 the rest. -> work/keep.npy, work/groups.npy"""
import os
import numpy as np
d = np.load('work/mesh_in.npz'); f = d['faces']; v = d['verts']
piece = np.load('work/piece.npy'); bone = np.load('work/face_bone.npy')
sizes = np.bincount(piece); u = d['wuv'].reshape(-1, 3, 2)[:, :, 0].mean(1); c = v[f].mean(1)
small = sizes[piece] <= int(os.environ.get('REA_SMALL', '160'))
grip = np.array([b.startswith('B_R_Finger') for b in bone])
hand = np.array([('Finger' in b or b.endswith('_Hand')) for b in bone])
sole = v[f][..., 2].max(1) < .06
keep = small | grip | sole
groups = np.zeros(len(f), int)
groups[(u > .5) & ~keep] = 1
groups[hand & ~keep] = 2
np.save('work/keep.npy', keep); np.save('work/groups.npy', groups)
print('KEEP', int(keep.sum()), '(small', int(small.sum()), 'right fingers', int(grip.sum()), 'soles', int(sole.sum()), ')',
      'face', int((groups == 1).sum()), 'hands', int((groups == 2).sum()), 'rest', int((groups == 0).sum()))
