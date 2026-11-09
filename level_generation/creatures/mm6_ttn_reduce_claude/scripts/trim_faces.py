"""Per-face region-mask coverage of the source mesh (work/mesh_in.npz, work/region_mask.png from the installed GLB):
12 barycentric samples per face; channel 1 is the gold trim. -> work/trim_frac.npy (fraction of trim samples)."""
import numpy as np
from PIL import Image
m = np.asarray(Image.open('work/region_mask.png'))[..., 1]; H, W = m.shape
d = np.load('work/mesh_in.npz'); uv = d['wuv'].reshape(-1, 3, 2)
B = np.random.default_rng(1).dirichlet((1, 1, 1), 12)
u = np.einsum('sk,fkc->fsc', B, uv)
x = np.clip((u[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - u[..., 1] % 1) * H, 0, H - 1).astype(int)
frac = (m[y, x] > 128).mean(1); np.save('work/trim_frac.npy', frac)
print('TRIM any', int((frac > 0).sum()), 'mixed', int(((frac > 0) & (frac < 1)).sum()), 'full', int((frac == 1).sum()), 'of', len(frac))
