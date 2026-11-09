#!/usr/bin/env python3
"""Keep set and region groups for the MM7 Archer (m154) ladder, from the connected pieces of the rest mesh
(work/piece.npy, scratch pieces listing in the README) and the base colour sampled per face (work/basecolor.png).
Kept exactly: both gloves with fingers (bow grip and draw pinch are fitted), the bowstring tube (Bow/StringNock),
pieces of up to 80 faces (seven quiver arrows, eyes, helmet spike, quiver cap) and the belt buckle, boot soles (faces
below 6 cm), the face's painted features (eyes, brows, lips: colour far from the median skin, one ring dilated) and
the white tunic emblem (one ring). Groups (ratios from REA_GROUP_RATIOS): 1 front of the face, 2 rest of the head
skin (neck, scalp under coif and helmet), 3 mail coif, 4 helmet, 5 horns, 6 fur quiver, 7 diagonal strap, 8 mail
arms, 9 gold trims of the tunic (gorget, pauldron edges); label 0 (tunic and legs) takes the ladder budget.
Env: M154_FACE_KEEP=1 keeps the whole front of the face; M154_EMBLEM_RING=0 keeps only the white emblem faces;
M154_HEM_Z keeps the tunic below that height; M154_MAIL_KEEP=1 keeps the mail arms; M154_HELMET_RIM_Z keeps the helmet below that height;
M154_HORNS_KEEP=1 keeps the horns; M154_LOCK_POINTS='x,y,z;...'
(rest positions, radius M154_LOCK_R) keeps faces around error spots; M154_TRIM_GROUP=1 makes the gold
trims group 9 (decimated alone with fixed borders they stall at 218 faces with 10 mm error: off by default). Usage: m154_sets.py <name> -> work/keep_<name>.npy, work/groups_<name>.npy"""
import os, sys
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
pc = np.load('work/piece.npy'); sizes = np.bincount(pc)
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32) / 255; H, W = img.shape[:2]
B = np.random.default_rng(1).dirichlet((1, 1, 1), 9); uv = d['wuv'].reshape(-1, 3, 2)
u = np.einsum('sk,fkc->fsc', B, uv)
col = img[np.clip(((1 - u[..., 1] % 1) * H).astype(int), 0, H - 1), np.clip(((u[..., 0] % 1) * W).astype(int), 0, W - 1)]
mx = col.max(-1); mn = col.min(-1); s = (mx - mn) / (mx + 1e-6); r, g, b = col[..., 0], col[..., 1], col[..., 2]
hue = np.where(mx == r, ((g - b) / (mx - mn + 1e-6)) % 6, np.where(mx == g, (b - r) / (mx - mn + 1e-6) + 2, (r - g) / (mx - mn + 1e-6) + 4)) / 6
gold = ((hue > 0.08) & (hue < 0.17) & (s > 0.45) & (mx > 0.45)).any(1)
white = ((s < 0.2) & (mx > 0.7)).any(1)
P = dict(head=4, tunic=2, legs=3, glove_r=5, glove_l=7, quiver=11, quiver2=10, coif=19, helmet=20, strap=0, string=18,
         mail_r=6, mail_l=8, buckle=1, horn_l=24, horn_r=25)
isp = lambda *ns: np.isin(pc, [P[n] for n in ns])
vring = lambda m: m | np.isin(f, np.unique(f[m])).any(1)


def ring(m, within):
    return m | (within & np.isin(f, np.unique(f[m])).any(1))


head = isp('head'); front = head & (c[:, 1] < -0.07) & (c[:, 2] > 1.33)
skin = np.median(col[front].reshape(-1, 3), 0)
feat = front & (np.linalg.norm(col - skin, axis=-1).max(1) > 0.16)
feat = ring(feat, head)
E = os.environ.get
emblem = isp('tunic') & white
if E('M154_EMBLEM_RING', '1') == '1':
    emblem = ring(emblem, isp('tunic'))
hem = isp('tunic') & (c[:, 2] < float(E('M154_HEM_Z', '0')))  # tunic hem band (the front hem point tore in poses)
small = sizes[pc] <= 80
soles = c[:, 2] < 0.06
keep = isp('glove_r', 'glove_l', 'string', 'buckle') | small | soles | feat | emblem | hem
for pt in [x for x in E('M154_LOCK_POINTS', '').split(';') if x]:  # error lock: worst points of a ladder step (probe)
    keep |= np.linalg.norm(c - np.array([float(t) for t in pt.split(',')]), axis=1) < float(E('M154_LOCK_R', '0.03'))
keep |= isp('helmet') & (c[:, 2] < float(E('M154_HELMET_RIM_Z', '0')))  # helmet rim band (70 %: a notch under the back rim)
if E('M154_HORNS_KEEP') == '1':
    keep |= isp('horn_l', 'horn_r')
if E('M154_MAIL_KEEP') == '1':  # mail arms (75 %: p99 8 mm in poses)
    keep |= isp('mail_r', 'mail_l')
if os.environ.get('M154_FACE_KEEP') == '1':
    keep |= front
groups = np.zeros(len(f), int)
for lab, m in [(1, front), (2, head & ~front), (3, isp('coif')), (4, isp('helmet')), (5, isp('horn_l', 'horn_r')),
               (6, isp('quiver', 'quiver2')), (7, isp('strap')), (8, isp('mail_r', 'mail_l'))] + ([(9, isp('tunic') & gold)] if E('M154_TRIM_GROUP') == '1' else []):
    groups[m & ~keep] = lab
name = sys.argv[1]; np.save(f'work/keep_{name}.npy', keep); np.save(f'work/groups_{name}.npy', groups)
print('skin', skin.round(2), 'KEEP', int(keep.sum()), '(face features', int(feat.sum()), 'emblem', int(emblem.sum()),
      'soles', int(soles.sum()), 'hem', int(hem.sum()), 'small', int(small.sum()), ')', {k: int((groups == k).sum()) for k in range(10)})
