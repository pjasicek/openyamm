#!/usr/bin/env python3
"""Keep set and region groups for the Chain Fighter ladder (work/regions.npy, work/soles.npy, work/groups.npz,
work/basecolor.png). Kept exactly: both hands and fingers (every face touching a vertex with hand + finger weight
> 0.3: the solved scimitar fist and the open left hand, with the gauntlet cuffs), small pieces (belt links, eyes),
the boot soles (faces below 6 cm), the front of the face (M222_KEEP_FACE=1, default) and its painted features
(head-set faces whose base colour is far from the median skin, one ring dilated: lips, brows, eye lines), with
M222_KEEP_PAINT=1 the painted chest strap and green bands (work/trims.npy), and M222_KEEP_EXTRA=<npy,...> lock sets.
Groups (their own ratio in decimate_tex.py): 2 face front when not kept, 3 sleeves (rest of the arm shells), 4 helmet,
5 shoulder guard, 6 gold panels, 7 neck trims, 10 boots (M222_BOOT_Z), 11 torso (M222_TORSO_Z), 9 rest of the head set (hair, neck, ears, scalp); label 0 (body:
torso, skirt, legs, boots) takes the ladder budget.
Usage: m222_sets.py <name> -> work/keep_<name>.npy, work/groups_<name>.npy"""
import os, sys
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']
reg = np.load('work/regions.npy'); soles = np.load('work/soles.npy'); c = v[f].mean(1)
g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
hand = W[:, [i for i, n in enumerate(names) if n.endswith('_Hand') or 'Finger' in n]].sum(1)
hands = (hand[f] > 0.3).any(1)
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32) / 255; H, Wd = img.shape[:2]
B = np.random.default_rng(1).dirichlet((1, 1, 1), 9); uv = d['wuv'].reshape(-1, 3, 2)
u = np.einsum('sk,fkc->fsc', B, uv)
col = img[np.clip(((1 - u[..., 1] % 1) * H).astype(int), 0, H - 1), np.clip(((u[..., 0] % 1) * Wd).astype(int), 0, Wd - 1)]
head = reg == 2
YF = float(os.environ.get('M222_FACE_Y', '-0.075'))
front = head & (c[:, 1] < YF) & (c[:, 2] > 1.42) & (np.abs(c[:, 0]) < 0.075)
skin = np.median(col[front].reshape(-1, 3), 0)
dev = np.linalg.norm(col - skin, axis=-1).max(1)
feat = front & (dev > 0.16)
vf = np.zeros(len(v), bool); vf[f[feat].ravel()] = True
feat |= head & vf[f].any(1)
keep = hands | (reg == 8) | soles | feat
if os.environ.get('M222_KEEP_FACE', '1') == '1':
    keep |= front
if os.environ.get('M222_KEEP_TRIMS') == '1':
    keep |= reg == 7
if os.environ.get('M222_KEEP_PAINT') == '1':  # painted chest strap and green cloth bands (trim_faces.py)
    keep |= np.load('work/trims.npy')
for extra in filter(None, os.environ.get('M222_KEEP_EXTRA', '').split(',')):  # drift / error locks
    keep |= np.load(extra)
groups = np.zeros(len(f), int)
for r in (3, 4, 5, 6, 7):
    groups[(reg == r) & ~keep] = r
groups[front & ~keep] = 2; groups[head & ~front & ~keep] = 9
ZB = float(os.environ.get('M222_BOOT_Z', '0'))  # boots (body below this height) as their own group 10
groups[(reg == 1) & (c[:, 2] < ZB) & ~keep] = 10
ZT = float(os.environ.get('M222_TORSO_Z', '9'))  # torso, upper arms and hair slab (body above this height) as group 11
groups[(reg == 1) & (c[:, 2] > ZT) & ~keep] = 11
name = sys.argv[1]; np.save(f'work/keep_{name}.npy', keep); np.save(f'work/groups_{name}.npy', groups)
lab = np.where(keep, 1, groups + 2); lab[keep & hands] = 20; lab[keep & feat] = 21; lab[keep & soles] = 22
np.save(f'work/labels_{name}.npy', lab)
print('skin', skin.round(2), 'KEEP', int(keep.sum()), '(hands', int(hands.sum()), 'features', int(feat.sum()),
      'front', int(front.sum()), 'small', int((reg == 8).sum()), 'soles', int(soles.sum()), ')',
      {k: int((groups == k).sum()) for k in (0, 2, 3, 4, 5, 6, 7, 9, 10, 11)})
