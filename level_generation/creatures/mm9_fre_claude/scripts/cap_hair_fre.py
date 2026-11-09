#!/usr/bin/env python3
"""Fre head paint fix (2026-11-04, viewer r2): along the face opening the hair cap's paint carries skin-coloured teeth (Meshy's paint of
the face reached past the hairline of the HD masters onto the cap). Every texel of the hair cap's outer faces whose colour is skin-like
(light, not the gold circlet: luminance > LUM and blue/red > 0.33 and not gold-yellow) takes the colour of the nearest hair texel of the
cap (inpainting by nearest texel in the texture, within the cap's own texels), plus a 1-texel blend at the border. The braid and the
circlet are left as painted. Args: <in png> <out png> [LUM]   (project folder; faces from work/uv.npz)"""
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ni
SRC, DST = sys.argv[1:3]; LUM = float(sys.argv[3]) if len(sys.argv) > 3 else 0.42
D = np.load('work/uv.npz'); tri, uv, mat, comp, inner = D['tri'], D['uv'], D['mat'], D['comp'], D['inner']
names = [str(x) for x in D['names']]; K4 = names.index('hood4')
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32) / 255; S = im.shape[0]
cv = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(cv)
for f in np.where((mat == 1) & (comp[tri[:, 0]] == K4))[0]:
    dr.polygon([(float(uv[v, 0] * S), float((1 - uv[v, 1]) * S)) for v in tri[f]], fill=255)
cap = np.asarray(cv) > 0
# texels any other head face covers (an island border shared in the texture) are not the cap's: recolouring them drew dotted hair-
# coloured lines along the face islands' edges (viewer r6, cheeks)
cv2 = Image.new('L', (S, S), 0); dr2 = ImageDraw.Draw(cv2)
for f in np.where((mat == 1) & (comp[tri[:, 0]] != K4))[0]:
    dr2.polygon([(float(uv[v, 0] * S), float((1 - uv[v, 1]) * S)) for v in tri[f]], fill=255)
cap &= ~ni.binary_dilation(np.asarray(cv2) > 0, iterations=2)
r, g, b = im[..., 0], im[..., 1], im[..., 2]
lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
gold = (g / np.maximum(r, 1e-3) > 0.62) & (b / np.maximum(r, 1e-3) < 0.40)
skin = cap & (lum > LUM) & (b / np.maximum(r, 1e-3) > 0.33) & ~gold
skin = ni.binary_dilation(skin, iterations=1) & cap
hair = cap & ~skin & (lum < 0.35) & ~gold
idx = ni.distance_transform_edt(~hair, return_distances=False, return_indices=True)
out = im.copy(); out[skin] = im[idx[0][skin], idx[1][skin]]
Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype('u1')).save(DST)
print('CAPHAIR skin texels on the cap ->hair', int(skin.sum()), 'of', int(cap.sum()))
