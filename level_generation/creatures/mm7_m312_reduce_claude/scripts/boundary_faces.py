#!/usr/bin/env python3
"""Faces whose painted green/black boundary crosses the face (some samples green, some near black) in a height band of
region 0, plus one ring: the waistband blocks of the MM8 Vampire female peasant chopped under the collapse at 66-68 %.
Usage: boundary_faces.py <base keep .npy> <out .npy> <zmin> <zmax>"""
import sys
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32); H, W = img.shape[:2]
uv = d['wuv'].reshape(-1, 3, 2); B = np.random.default_rng(2).dirichlet((1, 1, 1), 24)
p = np.einsum('sk,fkc->fsc', B, uv)
x = np.clip((p[..., 0] % 1 * W).astype(int), 0, W - 1); y = np.clip(((1 - p[..., 1] % 1) * H).astype(int), 0, H - 1)
col = img[y, x]
green = (col[..., 1] > col[..., 0] + 25) & (col[..., 1] > 70)
black = col.max(-1) < 45
g = np.load('work/groups.npy'); z0, z1 = float(sys.argv[3]), float(sys.argv[4])
edge = (g == 0) & green.any(1) & black.any(1) & (c[:, 2] > z0) & (c[:, 2] < z1)
n = len(v); rows = np.repeat(np.arange(len(f)), 3); A = coo_matrix((np.ones(len(rows)), (rows, f.ravel())), shape=(len(f), n)).tocsr()
ring = ((A @ (A.T @ edge.astype(float))) > 0) & (g == 0)
keep = np.load(sys.argv[1]) | ring; np.save(sys.argv[2], keep)
print('BOUNDARY', int(edge.sum()), 'with ring', int(ring.sum()), 'keep total', int(keep.sum()))
