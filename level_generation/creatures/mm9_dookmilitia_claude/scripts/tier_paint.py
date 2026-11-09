#!/usr/bin/env python3
"""Paint fixes after finish_tex.py, on the final images (idempotent). Tier C: MM9's Captain wears dark gloves, the hands of limbs C become dark leather, the skin's relief kept by luminance. Tier A: the cream X lacing on the tunic is Codex's, MM9's tunic has none: inpainted from the tunic round it, colour and normal. Project folder."""
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
Z = np.load('work/faces.npz'); UV, MAT, CO = Z['uv'], Z['mat'], Z['co']
# gloves
p = 'textures/dook_limbs_c_final.png'; a = np.asarray(Image.open(p).convert('RGB'), np.float32); S = a.shape[0]
im = Image.new('L', (S, S)); d = ImageDraw.Draw(im)
for t in UV[(MAT == 0) & (np.abs(CO[:, :, 0]).mean(1) > 0.62)]: d.polygon([(x * S, (1 - y) * S) for x, y in t], fill=255)
m = ndimage.binary_dilation(np.asarray(im) > 0, iterations=4)
L = a @ np.array([.2126, .7152, .0722], np.float32)
hand = m                                                         # part 0, the grafted hands: nothing else of this image lies on them
soft = ndimage.gaussian_filter(hand.astype(np.float32), 1.5)[..., None]
Lm = np.median(L[np.asarray(im) > 0])
gl = 30 + (L - Lm) * 0.42 + ndimage.gaussian_filter(np.random.RandomState(3).randn(S, S), 2) * 14
leather = np.clip(gl, 10, 90)[..., None] * np.array([1.12, 0.94, 0.82], np.float32)
Image.fromarray(np.clip(a * (1 - soft) + leather * soft + .5, 0, 255).astype('u1')).save(p)
print('GLOVES px', int(hand.sum()))
# lacing, tier A: cloned from the quilted tunic beside it, feathered
c = np.asarray(Image.open('textures/dook_torso_a_final.png').convert('RGB'), np.float32)
Sc = c.shape[0]; k = Sc / 1024; lum = c @ np.array([.2126, .7152, .0722], np.float32)
mask = np.zeros((Sc, Sc), bool); Sx = {}
for (x0, y0, x1, y1), dx in (((188, 404, 234, 478), 60), ((30, 452, 90, 498), 62)):
    X0, Y0, X1, Y1 = [int(v * k) for v in (x0, y0, x1, y1)]
    mask[Y0:Y1, X0:X1] = (lum[Y0:Y1, X0:X1] > 100) & (c[Y0:Y1, X0:X1, 0] > c[Y0:Y1, X0:X1, 2] * 1.35)
    Sx[(X0, Y0, X1, Y1)] = int(dx * k)
mask = ndimage.binary_dilation(ndimage.binary_closing(mask, iterations=int(4 * k)), iterations=int(4 * k))
for p in ('textures/dook_torso_a_final.png', 'textures/dook_torso_a_normal.png'):
    b = np.asarray(Image.open(p).convert('RGB'), np.float32).copy(); S = b.shape[0]; r = S / Sc
    mk = np.asarray(Image.fromarray((mask * 255).astype('u1')).resize((S, S)), np.float32) / 255
    soft = ndimage.gaussian_filter(mk, 2.5 * r)
    out = b.copy()
    for (X0, Y0, X1, Y1), dx in Sx.items():
        x0, y0, x1, y1, dd = [int(v * r) for v in (X0, Y0, X1, Y1, dx)]
        pad = int(14 * r); yy0, yy1, xx0, xx1 = y0 - pad, y1 + pad, x0 - pad, x1 + pad
        w = soft[yy0:yy1, xx0:xx1, None]
        out[yy0:yy1, xx0:xx1] = b[yy0:yy1, xx0:xx1] * (1 - w) + b[yy0:yy1, xx0 + dd:xx1 + dd] * w
    Image.fromarray(np.clip(out + .5, 0, 255).astype('u1')).save(p)
    print('LACE', p, int(mask.sum()))
