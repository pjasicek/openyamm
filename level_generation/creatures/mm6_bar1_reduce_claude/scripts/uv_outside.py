"""Faces of a decimated mesh whose UVs leave the source's UV islands (thin dark streaks the mean-colour drift check
misses): rasterise the source UV triangles into a coverage mask, sample each candidate face densely and report the
fraction of samples outside the mask. -> work/outside_<tag>.npy. Usage: uv_outside.py <tag, e.g. r64>"""
import sys
import numpy as np
from PIL import Image, ImageDraw
tag = sys.argv[1]; W, H = 2080, 1024
src = np.load('work/mesh_in.npz'); m = Image.new('L', (W, H)); dr = ImageDraw.Draw(m)
for t in src['wuv'].reshape(-1, 3, 2):
    dr.polygon([(u % 1 * W, (1 - v % 1) * H) for u, v in t], fill=255, outline=255)
cov = np.asarray(m) > 0
d = np.load(f'work/mesh_{tag}.npz'); uv = d['wuv'].reshape(-1, 3, 2); tri = d['verts'][d['faces']]
n = 10; b = np.array([(i, j, n - i - j) for i in range(n + 1) for j in range(n + 1 - i)], float) / n
u = np.einsum('sk,fkc->fsc', b, uv)
x = np.clip((u[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - u[..., 1] % 1) * H, 0, H - 1).astype(int)
out = 1 - cov[y, x].mean(1); np.save(f'work/outside_{tag}.npy', out)
area = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1) / 2 * 1e4
print(tag, 'faces with >10 % of samples outside the source islands:', int((out > .1).sum()))
for i in np.argsort(-out)[:12]:
    if out[i] > .05: print(' ', i, f'{out[i]:.2f}', f'{area[i]:.2f} cm2', np.round(tri[i].mean(0), 3))
