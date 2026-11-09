#!/usr/bin/env python3
"""Njam, one tier (after mm9_nobleman_claude/scripts/tone_nb.py): Meshy's fur comes back with hard flecks, so the fur regions (yoke,
coat edges, skirt panel, boot cuffs: warm low-saturation tan texels) get local contrast x 0.5 (detail blurred 0.7 px) with the means kept; normals of torso and
limbs scaled to 0.65, fur to 0.4; head normal from the head paint's fine luminance, gentle. Project folder.
Writes textures/nj_torso_tone.png, nj_limbs_tone.png, nj_torso_normal2.png, nj_limbs_normal2.png, nj_head_normal2.png."""
import numpy as np
from pathlib import Path
from PIL import Image
from scipy import ndimage as ni
T = Path('textures')
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)
def hsv(a):
    mx, mn = a.max(2), a.min(2); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360, (mx - mn) / np.maximum(mx, 1e-6), mx
def local(a, mask, k, r=7.0, blur=0.0):
    L = a @ LUMA; low = ni.gaussian_filter(L, r); det = L - low
    if blur: det = ni.gaussian_filter(det, blur)
    L2 = low + det * k
    g = np.clip((L2 + 0.01) / (L + 0.01), 0.2, 3.0)
    return a + (a * g[..., None] - a) * mask[..., None]
for part in ('torso', 'limbs'):
    a = np.asarray(Image.open(T / f'nj_{part}_a_raw_graded.png').convert('RGB'), np.float32) / 255
    h, s, v = hsv(a)
    fur = ((h > 25) & (h < 55) & (s > 0.25) & (s < 0.65) & (v > 0.35)).astype(np.float32)
    fur = ni.gaussian_filter(ni.uniform_filter(fur, 15), 2.0)
    fur = np.clip((fur - 0.35) / 0.3, 0, 1)
    a = local(a, fur, 0.5, blur=0.7)
    if part == 'limbs':
        # Meshy dropped gold and pale flecks on the green hose (a button-like spot on the left thigh, pale dots by the knees): inside
        # the hose charts, texels far from the hose's green go to the local median green
        from PIL import ImageDraw
        Z = np.load('work/faces.npz'); S_ = a.shape[0]
        im = Image.new('L', (S_, S_)); dr = ImageDraw.Draw(im)
        for t, mt, pt in zip(Z['uv'], Z['mat'], Z['part']):
            if mt == 0 and pt == 5: dr.polygon([(x * S_, (1 - y) * S_) for x, y in t], fill=255)
        hose = ni.binary_erosion(np.asarray(im) > 0, iterations=3)
        med = np.stack([ni.median_filter(a[..., c], size=25) for c in range(3)], -1)
        off = np.linalg.norm(a - med, axis=2) > 0.12
        bad = ni.binary_dilation(off & hose, iterations=2) & hose
        a[bad] = med[bad]
        # gold dots on the visible hose above the knee (a button-like spot on the left thigh, r10 viewer): yellow texels on hose faces
        # between the hem and the boot cuff take the non-yellow median around them
        im2 = Image.new('L', (S_, S_)); dr2 = ImageDraw.Draw(im2)
        for t, mt, pt, co in zip(Z['uv'], Z['mat'], Z['part'], Z['co']):
            if mt == 0 and pt == 5 and -0.375 < co.mean(0)[2] < -0.05: dr2.polygon([(x * S_, (1 - y) * S_) for x, y in t], fill=255)
        band = np.asarray(im2) > 0
        mx_ = a.max(2); sat_ = (mx_ - a.min(2)) / np.maximum(mx_, 1e-4)
        hue_ = np.degrees(np.arctan2(np.sqrt(3) * (a[..., 1] - a[..., 2]), 2 * a[..., 0] - a[..., 1] - a[..., 2])) % 360
        yel = ni.binary_dilation((hue_ > 20) & (hue_ < 70) & (mx_ > 0.3) & (sat_ > 0.3) & band, iterations=3) & band
        green = np.median(a[band & ~yel], 0)
        fill = np.stack([ni.median_filter(np.where(yel, green[c], a[..., c]), size=31) for c in range(3)], -1)
        a[yel] = fill[yel]
        print('TONE hose gold dots texels', int(yel.sum()))          # r2: 0.7 still read as white flecks up close (viewer, yoke)
    Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype('u1')).save(T / f'nj_{part}_tone.png')
    n = np.asarray(Image.open(T / f'nj_{part}_a_normal.png').convert('RGB'), np.float32) / 127.5 - 1
    fs = np.asarray(Image.fromarray((fur * 255).astype('u1')).resize((n.shape[1], n.shape[0]), Image.BILINEAR), np.float32) / 255
    k = 0.65 - 0.25 * fs
    n[..., :2] *= k[..., None]; n /= np.linalg.norm(n, axis=2, keepdims=True)
    Image.fromarray(((n + 1) * 127.5 + .5).astype('u1')).save(T / f'nj_{part}_normal2.png')
    print('TONE', part, 'fur share', round(float((fur > 0.5).mean()), 3))
p = T / 'nj_head_a_raw.png'
if p.exists():
    col = np.asarray(Image.open(p).convert('RGB'), np.float32) / 255
    lum = col @ LUMA
    im1k = np.asarray(Image.fromarray((lum * 255).astype('u1')).resize((1024, 1024), Image.LANCZOS), np.float32) / 255
    hp = im1k - ni.gaussian_filter(im1k, 6)
    gx = ni.sobel(hp, axis=1) * 0.55; gy = ni.sobel(hp, axis=0) * 0.55
    nn = np.dstack([-gx, gy, np.ones_like(gx)]); nn /= np.linalg.norm(nn, axis=2, keepdims=True)
    Image.fromarray(((nn * 0.5 + 0.5) * 255 + .5).astype('u1')).save(T / 'nj_head_normal2.png')
print('TONE done')
