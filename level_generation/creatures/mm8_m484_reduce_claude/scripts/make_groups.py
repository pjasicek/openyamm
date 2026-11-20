#!/usr/bin/env python3
"""Minotaur per-region budgets for decimate_tex.py (REA_GROUPS / REA_KEEP_FACES).
Keep exactly: small pieces (<= REA_SMALL faces, default 80: eyes, nose ring, harness buckles, mane locks), soles
(faces below REA_SOLE m, default 0.03), the edge of the mail region mask (faces straddling it; plus one ring) and
REA_EXTRA_KEEP. The fingers are kept (REA_FINGERS=keep, default) or form group 6: both hands grip the axe handle.
Groups: 1 head (B_Head faces of the main piece, without the horns), 2 palms (B_*_Hand), 3 feet and hooves, 4 horns
(ivory B_Head faces of the main piece), 5 the mail kilt piece, 6 fingers, 7 the face (head faces in front of
REA_FACE_Y m between 1.40 and 1.75 m: eyes, brow, muzzle; only when REA_FACE_Y is set), 8 the nose pad (head faces
in front of REA_NOSE_Y m between 1.44 and 1.56 m: black nose and nostrils, where the black / fur border flecked),
0 the rest. REA_SILVER=1 also keeps the silver bracer faces of the hands and forearm twists (plus one ring): their
fur border flecked at the wrists.
-> work/groups.npy, work/keep.npy"""
import os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from PIL import Image
d = np.load('work/mesh_in.npz'); f = d['faces']; v = d['verts']
fb = np.load('work/face_bones.npz'); names = [str(n) for n in fb['names']]; dom = fb['dom']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl); main = int(np.argmax(sizes))
bone = np.array([names[i] for i in dom])
small = sizes[fl] <= int(os.environ.get('REA_SMALL', '80'))
fingers = np.char.find(bone, '_Finger') >= 0
palm = np.isin(bone, ['B_R_Hand', 'B_L_Hand'])
feet = np.isin(bone, ['B_L_Foot', 'B_R_Foot', 'B_L_Toe0', 'B_R_Toe0'])
cen = v[f].mean(1); sole = v[f][:, :, 2].max(1) < float(os.environ.get('REA_SOLE', '0.03'))
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32); H, W = img.shape[:2]
msk = np.asarray(Image.open('work/region_mask.png').convert('RGBA'), np.float32)[..., 0] / 255
uv = d['wuv'].reshape(-1, 3, 2); B = np.random.default_rng(1).dirichlet((1, 1, 1), 12)
su = np.einsum('sk,fkc->fsc', B, uv)
x = np.clip((su[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - su[..., 1] % 1) * H, 0, H - 1).astype(int)
c = np.median(img[y, x], 1); mx = c.max(1); mn = c.min(1); sat = (mx - mn) / np.maximum(mx, 1)
ivory = (mx > 150) & (sat < 0.35) & (c[:, 0] >= c[:, 2])
mr = msk[y, x]; mail_edge = (mr.max(1) > 0.5) & (mr.min(1) < 0.5)


def ring(m, k=1):
    for _ in range(k):
        vk = np.zeros(n, bool); vk[f[m].ravel()] = True; m = m | vk[f].any(1)
    return m


head = (bone == 'B_Head') & (fl == main)
horns = head & ivory
mail_edge = ring(mail_edge)
keep = small | sole | mail_edge
silver = (sat < 0.15) & (mx > 120) & (np.char.find(bone, '_Hand') >= 0) | (sat < 0.15) & (mx > 120) & \
    (np.char.find(bone, 'ForearmTwist') >= 0)
if os.environ.get('REA_SILVER') == '1':
    keep |= ring(silver)
if os.environ.get('REA_FINGERS', 'keep') == 'keep':
    keep |= fingers
if os.environ.get('REA_EXTRA_KEEP'):
    keep |= np.load(os.environ['REA_EXTRA_KEEP'])
kilt = fl == max(np.unique(fl), key=lambda p: np.char.startswith(bone[fl == p], 'Skirt').sum())
groups = np.zeros(len(f), int)
groups[head] = 1; groups[palm] = 2; groups[feet] = 3; groups[horns] = 4; groups[kilt] = 5; groups[fingers] = 6
if os.environ.get('REA_FACE_Y'):
    groups[(groups == 1) & (cen[:, 1] < float(os.environ['REA_FACE_Y'])) & (cen[:, 2] > 1.40) & (cen[:, 2] < 1.75)] = 7
if os.environ.get('REA_NOSE_Y'):
    groups[np.isin(groups, (1, 7)) & (cen[:, 1] < float(os.environ['REA_NOSE_Y'])) & (cen[:, 2] > 1.44) &
           (cen[:, 2] < 1.56)] = 8
groups[keep] = 0
np.save('work/keep.npy', keep); np.save('work/groups.npy', groups)
print('ivory', int(ivory.sum()), 'horns', int(horns.sum()), 'mail edge', int(mail_edge.sum()), 'fingers', int(fingers.sum()),
      'sole', int(sole.sum()), 'small', int(small.sum()))
print('KEEP', int(keep.sum()), 'head', int((groups == 1).sum()), 'palm', int((groups == 2).sum()),
      'feet', int((groups == 3).sum()), 'horns', int((groups == 4).sum()), 'kilt', int((groups == 5).sum()),
      'fingers', int((groups == 6).sum()), 'face', int((groups == 7).sum()), 'nose', int((groups == 8).sum()),
      'silver', int(silver.sum()), 'rest', int(((groups == 0) & ~keep).sum()), 'of', len(f))
