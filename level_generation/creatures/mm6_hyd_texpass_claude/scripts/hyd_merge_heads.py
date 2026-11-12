"""One 4K heads paint from the per-head retextures (meshy/head<k>_retexture_v1, each painted on head k's triangles
only, same layout): every texel of head k's charts from head k's job, gutters filled with the nearest chart texel.
A head may instead come from another job on the same layout (e.g. the study's whole-heads job 5b).
Usage: hyd_merge_heads.py <out job name> [k=job ...]   (default: k -> head<k>_retexture_v1)
Writes meshy/<out>/texture_urls_0_{base_color,normal}.png."""
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

import hyd_heads
import texlib

Image.MAX_IMAGE_PIXELS = None
P = hyd_heads.PROJECT
out = sys.argv[1]
source = {k: f'head{k}_retexture_v1' for k in range(1, 6)}
for a in sys.argv[2:]:
    k, job = a.split('=')
    source[int(k)] = job
S = 4096
L = np.load(P / 'work' / 'uv_study_heads.npz')
head_t, _ = hyd_heads.head_of_triangle()
tri_id, _ = texlib.raster(L['uv'], S)
cov = tri_id >= 0
hmap = np.where(cov, head_t[np.maximum(tri_id, 0)], 0)
_, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
hmap = hmap[iy, ix]                                     # gutters: the nearest chart's head
(P / 'meshy' / out).mkdir(parents=True, exist_ok=True)
for kind in ('base_color', 'normal'):
    result = np.zeros((S, S, 3), np.uint8)
    for k in range(1, 6):
        img = Image.open(P / 'meshy' / source[k] / f'texture_urls_0_{kind}.png').convert('RGB')
        if img.size != (S, S):
            img = img.resize((S, S), Image.Resampling.LANCZOS)
        a = np.asarray(img)
        sel = hmap == k
        result[sel] = a[sel]
    Image.fromarray(result).save(P / 'meshy' / out / f'texture_urls_0_{kind}.png')
    print('WROTE', out, kind, {k: source[k] for k in source})
(P / 'meshy' / out / 'SOURCE.txt').write_text(
    'Merged by scripts/hyd_merge_heads.py: ' + ', '.join(f'head {k}: {v}' for k, v in source.items()) + '\n')
