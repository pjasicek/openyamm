#!/usr/bin/env python3
"""Lizardman Warrior per-region budgets for decimate_tex.py (REA_GROUPS / REA_KEEP_FACES).
Keep exactly: small pieces (<= 80 faces: belt buckle), the fingers of both hands (both grip the sword hilt), ivory
claws, leg spurs and teeth (base colour; plus one face ring), gold/yellow painted trims (collar, bracer studs; plus one
ring), soles (faces below REA_SOLE m, default 0.03). Groups: 1 head piece, 2 palms (B_*_Hand), 3 feet and toes,
4 cloth (mantle and loincloth bones), 5 tail, 0 the rest.
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
fl = lab[f[:, 0]]; sizes = np.bincount(fl)
bone = np.array([names[i] for i in dom])
small = sizes[fl] <= 80
fingers = np.char.find(bone, '_Finger') >= 0
palm = np.isin(bone, ['B_R_Hand', 'B_L_Hand'])
feet = np.isin(bone, ['B_L_Foot', 'B_R_Foot', 'B_L_Toe0', 'B_R_Toe0'])
cloth = np.isin(bone, ['B_MantleBack', 'B_Loincloth'])
tail = np.char.startswith(bone, 'Tail')
cen = v[f].mean(1); sole = v[f][:, :, 2].max(1) < float(os.environ.get('REA_SOLE', '0.03'))
head_piece = max(np.unique(fl), key=lambda p: (cen[fl == p][:, 2].mean() > 1.6) * sizes[p])
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32); H, W = img.shape[:2]
uv = d['wuv'].reshape(-1, 3, 2); B = np.random.default_rng(1).dirichlet((1, 1, 1), 12)
su = np.einsum('sk,fkc->fsc', B, uv)
x = np.clip((su[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - su[..., 1] % 1) * H, 0, H - 1).astype(int)
c = np.median(img[y, x], 1); mx = c.max(1); mn = c.min(1); sat = (mx - mn) / np.maximum(mx, 1)
ivory = (mx > 150) & (sat < 0.35) & (c[:, 0] >= c[:, 2])
gold = (c[:, 0] > 140) & (c[:, 1] > 100) & (c[:, 0] - c[:, 2] > 60) & ~ivory


def ring(m, k=1):
    for _ in range(k):
        vk = np.zeros(n, bool); vk[f[m].ravel()] = True; m = m | vk[f].any(1)
    return m


ivory_r = ring(ivory); gold_r = ring(gold)
# head spikes: teeth and the small neck spines shrank at a 45 % head cut. Sharp cone tips of the head piece = vertices
# with an angle deficit over 0.6 rad (border vertices excluded); keep every head face within REA_TIP_R (1.2 cm)
from scipy.spatial import cKDTree
Pf = v[f]; ang = np.zeros(n)
for k in range(3):
    a = Pf[:, (k + 1) % 3] - Pf[:, k]; b = Pf[:, (k + 2) % 3] - Pf[:, k]
    cs = (a * b).sum(1) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1) + 1e-12)
    np.add.at(ang, f[:, k], np.arccos(np.clip(cs, -1, 1)))
e2 = np.sort(e, 1); ue, cnt = np.unique(e2, axis=0, return_counts=True); border = np.zeros(n, bool)
border[ue[cnt == 1].ravel()] = True
hv = np.zeros(n, bool); hv[f[fl == head_piece].ravel()] = True
# the long crest spines above 1.76 m keep their shape at 45 % (review/close/sheet_head_g.png); only teeth and neck spines
tips = np.where(hv & ~border & (2 * np.pi - ang > 0.6) & (v[:, 2] < 1.76))[0]
near = np.zeros(n, bool)
dist, _ = cKDTree(v[tips]).query(v); near = dist < float(os.environ.get('REA_TIP_R', '0.012'))
spikes = near[f].any(1) & (fl == head_piece)
keep = small | fingers | sole | ivory_r | gold_r | spikes
if os.environ.get('REA_EXTRA_KEEP'):
    keep |= np.load(os.environ['REA_EXTRA_KEEP'])
groups = np.zeros(len(f), int)
groups[fl == head_piece] = 1; groups[palm] = 2; groups[feet] = 3; groups[cloth] = 4; groups[tail] = 5
groups[keep] = 0
np.save('work/keep.npy', keep); np.save('work/groups.npy', groups)
print('head spike tips', len(tips), 'faces', int(spikes.sum()))
print('ivory', int(ivory.sum()), '->', int(ivory_r.sum()), 'gold', int(gold.sum()), '->', int(gold_r.sum()),
      'fingers', int(fingers.sum()), 'sole', int(sole.sum()), 'small', int(small.sum()))
print('KEEP', int(keep.sum()), 'head', int((groups == 1).sum()), 'palm', int((groups == 2).sum()),
      'feet', int((groups == 3).sum()), 'cloth', int((groups == 4).sum()), 'tail', int((groups == 5).sum()),
      'rest', int(((groups == 0) & ~keep).sum()), 'of', len(f))
