#!/usr/bin/env python3
"""Keep sets and region groups for the Naga ladder (work/mesh_in.npz + work/face_info.npz + work/keep_small.npy).
Kept exactly: the six hands with their fingers (grips fitted around the separate swords), small pieces up to 130 faces
(12 cuffs/arm bands, eyes, earrings), the face (skin-coloured head faces plus the front of the face, one ring
dilated) and the painted gold trims on the torso (bikini edges, choker). Group 1: rest of the head (hair shell),
group 2: the remaining gold on arms. Writes work/keep_naga.npy, work/groups_naga.npy."""
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz'); fi = np.load('work/face_info.npz'); small = np.load('work/keep_small.npy')
f = d['faces']; uv = d['wuv'].reshape(-1, 3, 2); reg = fi['region']; c = fi['centroid']; gold = fi['gold']
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32) / 255; H, W = img.shape[:2]
m = uv.mean(1); col = img[np.clip(((1 - m[:, 1] % 1) * H).astype(int), 0, H - 1), np.clip(((m[:, 0] % 1) * W).astype(int), 0, W - 1)]
r, g, b = col.T
skin = (r > .55) & (r > g * 1.05) & (g > b * .95) & ((r - b) < .45)
head = reg == 'head'
face = head & (skin | ((c[:, 1] < -.04) & (c[:, 2] < 2.09) & (np.abs(c[:, 0]) < .1)))
# one ring of neighbours by shared vertex
vf = np.zeros(len(d['verts']), bool); vf[f[face].ravel()] = True
face |= head & vf[f].any(1)
keep = small | (reg == 'hand') | face | ((reg == 'torso') & gold)
groups = np.zeros(len(f), int); groups[head & ~keep] = 1; groups[(reg == 'arm') & gold & ~keep] = 2
np.save('work/keep_naga.npy', keep); np.save('work/groups_naga.npy', groups)
print('KEEP', int(keep.sum()), '(hand', int((reg == 'hand').sum()), 'small', int(small.sum()), 'face', int(face.sum()),
      'torso gold', int(((reg == 'torso') & gold).sum()), ') GROUP1 head rest', int((groups == 1).sum()),
      'GROUP2 arm gold', int((groups == 2).sum()), 'FREE', int(((groups == 0) & ~keep).sum()))
