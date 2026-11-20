#!/usr/bin/env python3
"""Stage 2 of the fish body clean (system python, scipy): from the Meshy shell's distance band (fish_volume.py),
inside = everything the outside flood fill cannot reach; a morphological opening with a ball of R metres removes the
thin fin sheets (dorsal, anal, caudal) and keeps the body; the result is made exactly mirror-symmetric about x = 0
(MM9's fish is symmetric) and written as a signed distance (metres, negative inside).
Usage: fish_open.py <in npz> <out npz> [R=0.003] [caudal_keep_y]"""
import sys, json
import numpy as np
from scipy import ndimage

src, dst = sys.argv[1], sys.argv[2]
R = float(sys.argv[3]) if len(sys.argv) > 3 else 0.003
d = np.load(src)
sdf, lo, vox = d['sdf'], d['lo'], float(d['vox'])
shell = np.abs(sdf) <= 0.7 * vox
ball1 = np.sum(np.mgrid[-1:2, -1:2, -1:2] ** 2, 0) <= 1
free = ~ndimage.binary_dilation(shell, ball1)      # seal pin holes in the Meshy shell (1 voxel)
lab, n = ndimage.label(free)
border = set(np.unique(np.concatenate([lab[0].ravel(), lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(),
                                       lab[:, :, 0].ravel(), lab[:, :, -1].ravel()])))
border.discard(0)
outside = ndimage.binary_dilation(np.isin(lab, list(border)), ball1)
inside = ~outside
# the sealing dilation moves the inside/outside border by up to a voxel: near the surface take the side of the nearest
# voxel at least 2.5 voxels from it (the distance band is continuous, only its sign comes from the fill)
near = np.abs(sdf) < 2.5 * vox
_, idx = ndimage.distance_transform_edt(near, return_indices=True)
inside = np.where(near, inside[tuple(idx)], inside)
inside = inside | inside[::-1]          # symmetric: union with the mirror (x is axis 0, box symmetric about 0)
r = R / vox
din = ndimage.distance_transform_edt(inside)
eroded = din > r
dout = ndimage.distance_transform_edt(~eroded)
opened = dout <= r
# signed distance of the opened solid (voxel EDT, metres) and a light smoothing
sd_open = np.where(opened, -ndimage.distance_transform_edt(opened), ndimage.distance_transform_edt(~opened)) * vox
sd_open = ndimage.gaussian_filter(sd_open, 1.2)
# keep the Meshy surface itself wherever the opening did not remove material (the continuous band distance, signed
# by the flood fill), the voxel distance only where fins were cut away (blended over 3 voxels)
band = np.minimum(np.abs(sdf), 4 * vox)
sd_orig = np.where(inside, -band, band)
sd_orig = 0.5 * (sd_orig + sd_orig[::-1])
far = ndimage.distance_transform_edt(~(inside & ~opened))
w = np.clip((far - 2) / 3, 0, 1)                      # 0 at the cut, 1 three voxels away
sd = w * sd_orig + (1 - w) * np.maximum(sd_orig, sd_open)
sd = ndimage.gaussian_filter(sd, 0.6)
sd = 0.5 * (sd + sd[::-1])
np.savez(dst, sdf=sd.astype(np.float32), lo=lo, vox=vox)
print('OPEN', json.dumps({'R': R, 'inside_voxels': int(inside.sum()), 'opened_voxels': int(opened.sum()),
                          'removed_share': round(1 - opened.sum() / inside.sum(), 4), 'components': int(n)}))
