#!/usr/bin/env python3
"""Cut the silver medallion from the head master (references_head/01_front.png: bright, low-saturation pixels above the
cap band, closed and hole-filled, feathered 1.5 px) and place it over the painted blob of our front render
(references_face/our_front.png, render_face.py 0 1.05 0.30 1024: the blob is the least saturated patch above the band),
centre on centre, uniformly scaled to the blob's mean size. Writes references_face/emblem_overlay.png (RGBA) and
references_face/emblem_preview.png. Usage (project folder): emblem_overlay.py [shrink 0.95]"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

shrink = float(sys.argv[1]) if len(sys.argv) > 1 else 0.95
m = np.asarray(Image.open('references_head/01_front.png').convert('RGBA')).astype(float)
rgb = m[..., :3]; mx = rgb.max(2); mn = rgb.min(2); sat = (mx - mn) / np.maximum(mx, 1)
sil = (mx > 150) & (sat < 0.18) & (m[..., 3] > 200); sil[400:] = False
lab, n = ndimage.label(ndimage.binary_closing(sil, iterations=3))
k = np.argmax(ndimage.sum(sil, lab, range(1, n + 1))) + 1
mask = ndimage.binary_fill_holes(ndimage.binary_closing(lab == k, iterations=4))
ys, xs = np.nonzero(mask); mb = (xs.min(), xs.max(), ys.min(), ys.max())
o = np.asarray(Image.open('references_face/our_front.png').convert('RGB')).astype(float)
sub = o[140:330, 360:660]; smx = sub.max(2); smn = sub.min(2)
ssat = ndimage.uniform_filter((smx - smn) / np.maximum(smx, 1), 9)
bm = ssat < np.percentile(ssat, 25)
bl, bn = ndimage.label(bm); kk = np.argmax(ndimage.sum(bm, bl, range(1, bn + 1))) + 1
by, bx = np.nonzero(bl == kk); bx = bx + 360; by = by + 140
s = 0.5 * ((bx.max() - bx.min()) / (mb[1] - mb[0]) + (by.max() - by.min()) / (mb[3] - mb[2])) * shrink
mc = ((mb[0] + mb[1]) / 2, (mb[2] + mb[3]) / 2); oc = ((bx.min() + bx.max()) / 2, (by.min() + by.max()) / 2)
pad = 6
crop = m[mb[2] - pad:mb[3] + pad, mb[0] - pad:mb[1] + pad].copy()
alpha = ndimage.gaussian_filter(mask[mb[2] - pad:mb[3] + pad, mb[0] - pad:mb[1] + pad].astype(float), 1.5)
crop[..., 3] = np.clip(alpha, 0, 1) * 255
ci = Image.fromarray(np.uint8(crop), 'RGBA')
ci = ci.resize((round(ci.width * s), round(ci.height * s)), Image.LANCZOS)
ov = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
ov.paste(ci, (round(oc[0] - ci.width / 2), round(oc[1] - ci.height / 2)))
ov.save('references_face/emblem_overlay.png')
pv = Image.open('references_face/our_front.png').convert('RGBA'); pv.alpha_composite(ov)
pv.crop((300, 100, 720, 380)).resize((840, 560)).save('references_face/emblem_preview.png')
print('EMBLEM_OVERLAY master bbox', mb, 'blob', (bx.min(), bx.max(), by.min(), by.max()), 'scale', round(s, 3))
