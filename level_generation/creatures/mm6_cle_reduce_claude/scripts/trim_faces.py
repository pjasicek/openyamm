"""Faces that carry thin painted trim (region mask G: mantle/hem piping and the chest ankh) outside the legs and boots
(their whole surface is G). Thin painted lines bend under any collapse (Medusa trims), so they are kept exactly.
Samples each face's UV triangle on a barycentric grid in the installed region mask. -> work/keep_trim.npy (+ tie)."""
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz'); comp = np.load('work/comp.npy'); reg = np.load('work/regions.npy')
m = np.array(Image.open('work/cle_region_mask_head_atlas.png'))[..., 1] > 128
H, W = m.shape
wuv = d['wuv'].reshape(-1, 3, 2)
bc = np.array([(a, b, 1 - a - b) for a in np.linspace(0, 1, 9) for b in np.linspace(0, 1, 9) if a + b <= 1])
pts = np.einsum('kj,fjc->fkc', bc, wuv)
px = np.clip((pts[..., 0] * W).astype(int), 0, W - 1); py = np.clip(((1 - pts[..., 1]) * H).astype(int), 0, H - 1)
frac = m[py, px].mean(1)
sizes = np.bincount(comp); legs = int(np.argmax([np.median(d['verts'][d['faces'][comp == k]][..., 2]) < .6 and sizes[k] > 500 for k in range(len(sizes))]))
trim = (frac > 0) & (comp != legs)  # partial and whole piping faces on the mantle, hem and ankh
for k in range(len(sizes)):
    print('comp', k, sizes[k], 'trim faces', int((trim & (comp == k)).sum()), 'all-G faces', int(((frac == 1) & (comp == k)).sum()))
keep = trim | (reg == 6)
np.save('work/keep_trim.npy', keep); np.save('work/trim_frac.npy', frac)
print('legs comp', legs, 'KEEP', int(keep.sum()))
