"""Add the painted trouser/boot boundary to a keep set: main-body leg faces (below REA_EDGE_ZMAX m) whose texture
samples hold both trouser blue and boot brown, plus their one-ring. The zigzag boot tops drift under the collapse.
Usage: keep_boot_edge.py <base keep .npy> <out .npy>"""
import os, sys
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz'); v, f, uv = d['verts'], d['faces'], d['wuv'].reshape(-1, 3, 2)
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32); H, W = img.shape[:2]
B = np.random.default_rng(1).dirichlet((1, 1, 1), 24)
u = np.einsum('sk,fkc->fsc', B, uv)
x = np.clip((u[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - u[..., 1] % 1) * H, 0, H - 1).astype(int)
c = img[y, x]
blue = (c[..., 2] > c[..., 0] + 25).any(1); brown = (c[..., 0] > c[..., 2] + 25).any(1)
comp = np.load('work/components.npy'); cz = v[f].mean(1)[:, 2]
edge = blue & brown & (comp == 0) & (cz < float(os.environ.get('REA_EDGE_ZMAX', '0.95')))
ring = np.zeros(len(f), bool); verts = np.unique(f[edge])
ring[np.isin(f, verts).any(1)] = True; ring &= (comp == 0) & (cz < 0.95)
keep = np.load(sys.argv[1]).copy(); n0 = int(keep.sum()); keep |= ring
np.save(sys.argv[2], keep); print('EDGE', int(edge.sum()), 'RING', int(ring.sum()), 'z', np.round(np.percentile(cz[edge], [5, 95]), 2) if edge.any() else '-', 'KEEP', n0, '->', int(keep.sum()))
