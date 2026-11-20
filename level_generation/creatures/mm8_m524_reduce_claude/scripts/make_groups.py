#!/usr/bin/env python3
"""Serpentman per-region budgets for decimate_tex.py (REA_GROUPS / REA_KEEP_FACES). The face material class comes
from the creature's class maps (mm8_m524_claude/textures/*_material_classes.png) placed like the runtime atlas
(body at x 0, head at x 1056 of 2080), median of 12 samples per face.
keep exactly: separate pieces up to 140 faces (teeth and the front fang), eye faces (class 6) and teeth on the head
surface (class 5) with one ring of neighbours; group 1 head and jaw, group 2 hands and digits (claws are class 4),
group 3 tail, 0 the rest (spine, neck, arms). -> work/groups.npy, work/keep.npy, work/face_class.npy"""
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
C = '../mm8_m524_claude/textures/m524_{}_material_classes.png'
atlas = np.zeros((1024, 2080), np.uint8)
atlas[:, :1024] = np.asarray(Image.open(C.format('body'))); atlas[:, 1056:] = np.asarray(Image.open(C.format('head')))
d = np.load('work/mesh_in.npz'); f = d['faces']; v = d['verts']
fb = np.load('work/face_bones.npz'); names = [str(n) for n in fb['names']]; bone = np.array([names[i] for i in fb['dom']])
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl)
uv = d['wuv'].reshape(-1, 3, 2); B = np.random.default_rng(1).dirichlet((1, 1, 1), 12)
su = np.einsum('sk,fkc->fsc', B, uv)
x = np.clip((su[..., 0] % 1) * 2080, 0, 2079).astype(int); y = np.clip((1 - su[..., 1] % 1) * 1024, 0, 1023).astype(int)
cls = np.array([np.bincount(r, minlength=8).argmax() for r in atlas[y, x]])
np.save('work/face_class.npy', cls)
small = sizes[fl] <= 140
feat = np.isin(cls, (5, 6)) & ~small
vk = np.zeros(n, bool); vk[f[feat].ravel()] = True; feat |= vk[f].any(1)
keep = small | feat
head = np.isin(bone, ('Head', 'Jaw'))
hand = np.char.find(bone, 'Hand') >= 0
hand |= np.char.find(bone, 'Digit') >= 0
tail = np.char.startswith(bone, 'Tail')
groups = np.zeros(len(f), int); groups[head] = 1; groups[hand] = 2; groups[tail] = 3; groups[keep] = 0
np.save('work/keep.npy', keep); np.save('work/groups.npy', groups)
print('CLASSES', {int(k): int((cls == k).sum()) for k in np.unique(cls)})
print('KEEP', int(keep.sum()), '(small', int(small.sum()), 'eyes/teeth', int(feat.sum()), ')', 'head', int((groups == 1).sum()),
      'hands', int((groups == 2).sum()), 'tail', int((groups == 3).sum()), 'rest', int(((groups == 0) & ~keep).sum()), 'of', len(f))
