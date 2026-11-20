#!/usr/bin/env python3
"""Keep sets and region groups for the Salamander ladder (work/mesh_in.npz, work/groups.npz, work/keep_small.npy,
work/basecolor.png). Kept exactly: both hands with their fingers (grips fitted around the polearm), small pieces
(claws, crest ribs, the 140-face snout piece) and the painted eyes with two rings of neighbours.
Group 1: head and neck skin, group 2: the crest membrane (the 1,832-face piece), group 0: tail, torso and arms.
Writes work/keep_s.npy, work/groups_s.npy."""
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); g = np.load('work/groups.npz'); small = np.load('work/keep_small.npy')
f, v = d['faces'], d['verts']; W = g['W']; names = list(g['names'])
uv = d['wuv'].reshape(-1, 3, 2)
idx = lambda pred: [i for i, n in enumerate(names) if pred(n)]
fm = lambda a: a[f].mean(1)
hand = fm(W[:, idx(lambda n: n.endswith('_Hand') or 'Finger' in n)].sum(1)) > .5
head = fm(W[:, idx(lambda n: n in ('B_Head', 'B_Neck'))].sum(1)) > .5
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl)
crest = (sizes[fl] > 1000) & (sizes[fl] < 3000)
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32) / 255; H, Wd = img.shape[:2]
B = np.random.default_rng(1).dirichlet((1, 1, 1), 9)
u = np.einsum('sk,fkc->fsc', B, uv)
col = img[np.clip((1 - u[..., 1] % 1) * H, 0, H - 1).astype(int), np.clip((u[..., 0] % 1) * Wd, 0, Wd - 1).astype(int)]
r, gg, b = col[..., 0], col[..., 1], col[..., 2]
yellow = ((r > .6) & (gg > .55) & (b < .3) & (gg > r * .8)).mean(1) > .3
eye = head & ~crest & yellow
for _ in range(2):
    vf = np.zeros(n, bool); vf[f[eye].ravel()] = True
    eye |= head & ~crest & vf[f].any(1)
keep = small | hand | eye
groups = np.zeros(len(f), int); groups[head & ~crest & ~keep] = 1; groups[crest & ~keep] = 2
np.save('work/keep_s.npy', keep); np.save('work/groups_s.npy', groups)
print('KEEP', int(keep.sum()), '(hand', int(hand.sum()), 'small', int(small.sum()), 'eye', int(eye.sum()),
      'eye centres', np.round(v[f[eye & ~small]].reshape(-1, 3).mean(0), 3) if (eye & ~small).any() else None,
      ') G1 head', int((groups == 1).sum()), 'G2 crest', int((groups == 2).sum()), 'FREE', int(((groups == 0) & ~keep).sum()))
