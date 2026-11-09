"""Remove Codex's soft halo: keep the opaque figure (largest component above a threshold), feather 1 px. Args: in out [thr]"""
import sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi
src, dst = sys.argv[1:3]
thr = int(sys.argv[3]) if len(sys.argv) > 3 else 200
im = np.array(Image.open(src).convert('RGBA'))
a = im[..., 3]
m = a >= thr
lab, n = ndi.label(m)
sz = ndi.sum(m, lab, range(1, n + 1))
print('hist', np.percentile(a[a > 0], [5, 25, 50, 75, 95]), 'components', n, 'largest', int(sz.max()), 'next', sorted(sz)[-3:])
m = lab == (1 + int(np.argmax(sz)))
m = ndi.binary_fill_holes(m) & (a > thr * 0.6) | m
b = Image.fromarray((m * 255).astype('u1')).filter(ImageFilter.GaussianBlur(0.7))
out = im.copy(); out[..., 3] = np.array(b)
# colour bleed: extend figure colours into the transparent border
idx = ndi.distance_transform_edt(~m, return_distances=False, return_indices=True)
out[..., :3] = im[..., :3][idx[0], idx[1]]
Image.fromarray(out).save(dst)
