#!/usr/bin/env python3
"""Thin painted detail on the clothes (MM8 Vampire female peasant): the white lace panels and trims of the jacket and
the trouser side stripes (bright, unsaturated texels) and the gold boot studs (yellow texels), on region-0 faces
(torso, trousers, boots), plus their one-ring neighbours. Thin painted lines and dots bend or smear under any
collapse, so they are kept exactly. TRIM_GROUPS=6 (with TRIM_GROUPS_FILE) picks other regions (MM8 Cleric: the
collar and robe-top gold edges). Usage: trim_faces.py <base keep .npy> <out .npy> [ring 0|1]"""
import os, sys
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32); H, W = img.shape[:2]
uv = d['wuv'].reshape(-1, 3, 2); B = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1 / 3, 1 / 3, 1 / 3], [.6, .2, .2], [.2, .6, .2], [.2, .2, .6]])
p = np.einsum('sk,fkc->fsc', B, uv)
x = np.clip((p[..., 0] % 1 * W).astype(int), 0, W - 1); y = np.clip(((1 - p[..., 1] % 1) * H).astype(int), 0, H - 1)
col = img[y, x]
white = (col.min(-1) > 150) & (col.max(-1) - col.min(-1) < 45)
gold = (col[..., 0] > 140) & (col[..., 1] > 100) & (col[..., 0] - col[..., 2] > 70) & (col[..., 1] - col[..., 2] > 40) & (col[..., 0] - col[..., 1] < 70)
g = np.load(os.environ.get('TRIM_GROUPS_FILE', 'work/groups.npy')); rest = np.isin(g, [int(x) for x in os.environ.get('TRIM_GROUPS', '0').split(',')])
trim = rest & ((white.any(1) & (os.environ.get("TRIM_WHITE", "1") == "1")) | gold.any(1))
n = len(v); rows = np.repeat(np.arange(len(f)), 3); A = coo_matrix((np.ones(len(rows)), (rows, f.ravel())), shape=(len(f), n)).tocsr()
ring = ((A @ (A.T @ trim.astype(float))) > 0) & rest if (len(sys.argv) < 4 or sys.argv[3] == '1') else trim
keep = np.load(sys.argv[1]) | ring
np.save(sys.argv[2], keep)
print('TRIM white', int((rest & white.any(1)).sum()), 'gold', int((rest & gold.any(1)).sum()), 'with ring', int(ring.sum()),
      'legs', int((ring & (c[:, 2] < .9)).sum()), 'torso', int((ring & (c[:, 2] >= .9)).sum()), 'keep total', int(keep.sum()))
