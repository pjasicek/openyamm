#!/usr/bin/env python3
"""Meshy paints the bandage cloth as pebbles (a hide, not linen). Pattern kept, grain replaced, on the bandage only: inside a mask of the cloth (bright, not the dark gaps, not the flesh) colour and normal are low-passed
within the mask and a linen weave from the Codex strip swatch goes on top. Flesh and the dark gaps keep the paint. Args: none. Reads textures/mummy_<T>_base_raw.png, _normal_1k.png; writes _base_linen.png, _normal_linen_1k.png, _cloth_mask.png."""
import numpy as np
from PIL import Image
from scipy import ndimage as ni
cov = np.load('work/l2_cov.npz')['cov']
cov = np.asarray(Image.fromarray(cov.astype(np.uint8) * 255)) > 0
sw = np.asarray(Image.open('references_hd/strip_swatch.png').convert('L'), np.float32) / 255
hp = sw - ni.gaussian_filter(sw, 8); hp = hp[45:290]; hp = hp / hp.std()   # the middle of one strip, no frayed edges
ht, wt = hp.shape
# tile by mirroring
Y, X = np.mgrid[0:2048, 0:2048]
yy = np.abs((Y % (2 * ht)) - ht).clip(0, ht - 1); xx = np.abs((X % (2 * wt)) - wt).clip(0, wt - 1)
weave = hp[yy, xx]
gx = ni.sobel(ni.gaussian_filter(hp, .8), axis=1) / 8; gy = ni.sobel(ni.gaussian_filter(hp, .8), axis=0) / 8
wnx, wny = gx[yy, xx], gy[yy, xx]
S = 7.0
for t in 'ABC':
    im = np.asarray(Image.open(f'textures/mummy_{t}_base_raw.png').convert('RGB'), np.float32) / 255
    lum = im @ [.2126, .7152, .0722]; sat = (im.max(2) - im.min(2)) / np.maximum(im.max(2), 1e-3)
    # pebble texture averaged by a median, the dark gaps stay out
    med = ni.median_filter(lum[::2, ::2], size=9); med = np.asarray(Image.fromarray(med).resize((2048, 2048), Image.BILINEAR))
    thr = {'A': 0.26, 'B': 0.30, 'C': 0.30}[t]
    # the real gaps: long dark lines; pebble grout is small blobs
    sm = ni.gaussian_filter(lum, 1.6); loc = ni.gaussian_filter(lum, 22)
    dark = sm < 0.70 * loc
    lab, n = ni.label(dark); sz = np.bincount(lab.ravel()); keep = sz >= 140; keep[0] = False
    gaps = keep[lab]
    gaps = ni.binary_dilation(gaps, iterations=1)
    M = (med > thr) & (sat < 0.72) & ~gaps
    M = ni.binary_opening(M, iterations=1)
    Mf = ni.gaussian_filter(M.astype(np.float32), 1.2)
    print(t, 'cloth share', M[cov].mean(), 'mean cloth', im[M].mean(0))
    den = ni.gaussian_filter(M.astype(np.float32), S) + 1e-4
    low = np.stack([ni.gaussian_filter(im[..., c] * M, S) / den for c in range(3)], 2)
    cl = low * (1 + 0.16 * np.clip(weave, -2.5, 2.5))[..., None]
    out = im * (1 - Mf[..., None]) + cl * Mf[..., None]
    Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype(np.uint8)).save(f'textures/mummy_{t}_base_linen.png')
    Image.fromarray((Mf * 255).astype(np.uint8)).save(f'textures/mummy_{t}_cloth_mask.png')
    n = np.asarray(Image.open(f'textures/mummy_{t}_normal_1k.png').convert('RGB').resize((2048, 2048), Image.BILINEAR), np.float32) / 127.5 - 1
    den = ni.gaussian_filter(M.astype(np.float32), S) + 1e-4
    nl = np.stack([ni.gaussian_filter(n[..., c] * M, S) / den for c in range(3)], 2)
    nl[..., 0] += -wnx * 1.4; nl[..., 1] += wny * 1.4
    nl /= np.maximum(np.linalg.norm(nl, axis=2, keepdims=True), 1e-6)
    o = n * (1 - Mf[..., None]) + nl * Mf[..., None]
    o /= np.maximum(np.linalg.norm(o, axis=2, keepdims=True), 1e-6)
    Image.fromarray(((o * .5 + .5) * 255 + .5).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(f'textures/mummy_{t}_normal_linen_1k.png')
