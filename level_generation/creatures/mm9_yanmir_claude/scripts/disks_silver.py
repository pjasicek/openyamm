#!/usr/bin/env python3
"""The necklace disks on the fur mantle (the coordinator: Meshy painted them black with white dots; MM9's are dark silver knotwork):
texels inside the collar band (3D: front, z 0.72-0.93, |x| 0.04-0.34) whose 9 px neighbourhood is mostly near-black are the disks;
they take a dark-silver ramp by their own luminance (the dots become bright silver studs), and in the ORM metal 0.85, roughness 0.38.
In place on textures/yan_body_final.png and textures/yan_body_orm.png (the pre-disk copies kept as *_predisk.png)."""
import shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
for n in ('final', 'orm'):
    p = Path(f'textures/yan_body_{n}.png'); q = Path(f'textures/yan_body_{n}_predisk.png')
    if not q.exists(): shutil.copyfile(p, q)
A = np.asarray(Image.open('textures/yan_body_final_predisk.png').convert('RGB'), np.float32) / 255
O = np.asarray(Image.open('textures/yan_body_orm_predisk.png').convert('RGB'), np.float32) / 255
Z = np.load('work/body_pos.npz'); pos, cov = Z['pos'], Z['cov']
L = A @ np.array([0.3, 0.55, 0.15])
reg = cov & (pos[..., 1] < -0.05) & (pos[..., 2] > 0.72) & (pos[..., 2] < 0.93) & (np.abs(pos[..., 0]) > 0.04) & (np.abs(pos[..., 0]) < 0.34)
dark = ndimage.uniform_filter((L < 0.16).astype(np.float32), 9)
m = reg & (ndimage.binary_closing(dark > 0.45, iterations=2))
m = ndimage.binary_dilation(m, iterations=2) & reg
lab, n = ndimage.label(m); sz = ndimage.sum(m, lab, range(1, n + 1))
keep = np.isin(lab, 1 + np.nonzero(sz > 150)[0])
w = ndimage.gaussian_filter(keep.astype(np.float32), 1.2)[..., None]
lo, hi = np.array([0.20, 0.23, 0.27]), np.array([0.80, 0.83, 0.86])
t = np.clip((L - 0.05) / 0.75, 0, 1)[..., None]
silver = lo + (hi - lo) * t
out = A * (1 - w) + silver * w
wo = np.asarray(Image.fromarray((w[..., 0] * 255).astype('u1')).resize(O.shape[1::-1], Image.BILINEAR), np.float32) / 255      # the ORM is 1K
O2 = O.copy(); O2[..., 1] = O[..., 1] * (1 - wo) + 0.38 * wo; O2[..., 2] = O[..., 2] * (1 - wo) + 0.85 * wo
Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save('textures/yan_body_final.png')
Image.fromarray((np.clip(O2, 0, 1) * 255 + .5).astype('u1')).save('textures/yan_body_orm.png')
print('DISKS blobs', int((sz > 150).sum()), 'texels', int(keep.sum()))
