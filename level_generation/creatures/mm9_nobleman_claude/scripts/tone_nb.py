#!/usr/bin/env python3
"""Look matching against MM9, after the gentle grade (TEXTURE_QUALITY_PASS.md, lesson of the Eye and Basilisk: compare the hide's character). Meshy's fur came back as hard black-and-white flecks (the Viscount's coat read as fish scales) and the Baron's brocade as glowing cells; MM9's are soft.
Local contrast only, the means stay: L = low + k (L - low), on regions rastered from the frozen UVs. Normals: fur and brocade relief scaled down, head normal rebuilt gentler (the luminance normal read as orange peel). Project folder.
Writes textures/nb_torso_{t}_tone.png, nb_torso_{t}_normal2.png, nb_limbs_normal2.png, nb_head_{t}_normal2.png."""
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
from scipy import ndimage as ni
T = Path('textures'); S = 2048
Z = np.load('work/faces.npz'); UV, MAT, PART = Z['uv'], Z['mat'], Z['part']
def raster(mask, S=S):
    im = Image.new('L', (S, S)); d = ImageDraw.Draw(im)
    for t in UV[mask]: d.polygon([(x * S, (1 - y) * S) for x, y in t], fill=255)
    return np.asarray(im, np.float32) / 255
torso = MAT == 1
RM = raster(torso & (PART == 8)); RB = raster(torso & np.isin(PART, (1, 7, 9))); RS = raster(torso & (PART == 5))
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)
def local(a, mask, k, blur=0.0, r=7.0):
    """mask HxW 0..1: local contrast x k inside it"""
    L = a @ LUMA; low = ni.gaussian_filter(L, r); det = L - low
    if blur: det = ni.gaussian_filter(det, blur)
    L2 = low + det * k
    g = (L2 + 0.01) / (L + 0.01); g = np.clip(g, 0.2, 3.0)
    out = a * g[..., None]
    return a + (out - a) * mask[..., None]
def hsv(a):
    mx, mn = a.max(2), a.min(2); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360, (mx - mn) / np.maximum(mx, 1e-6), mx
for t in 'abc':
    a = np.asarray(Image.open(T / f'nb_torso_{t}_raw_graded.png').convert('RGB'), np.float32) / 255
    h, s, v = hsv(a)
    if t == 'a':
        red = ((h < 25) | (h > 335)) & (s > 0.55); redm = ni.gaussian_filter((red & (RB > 0.5)).astype(np.float32), 1.5)
        a = local(a, ni.gaussian_filter(RM, 1.5), 0.62, 0.6)
        a = local(a, redm, 0.68)
        L = a @ LUMA; d = 0.82; a = a + ((L[..., None] + (a - L[..., None]) * d) - a) * redm[..., None]        # MM9's burgundy is browner
        fur = RM
    elif t == 'b':
        blue = (((h > 170) & (h < 260)) | (s < 0.22)) & (a.max(2) < 0.92)
        cover = ni.gaussian_filter(((RB + RM) > 0.5).astype(np.float32), 1.0)
        cream = (s < 0.3) & (a.mean(2) > 0.62) & (ni.uniform_filter(a.mean(2), 25) > 0.55)
        teal = (h > 150) & (h < 200) & (ni.gaussian_filter(s, 6) > 0.16) & (ni.uniform_filter(a.mean(2), 21) > 0.27)
        furm = ni.gaussian_filter((blue & ~cream & ~teal & ((RB + RM) > 0.5)).astype(np.float32), 2.0)
        a = local(a, furm, 0.42, 1.0)
        L = a @ LUMA; lift = 1 + 0.04 * furm                                            # the darks stay fur, not holes
        a = a * lift[..., None]
        fur = furm
    else:
        a = local(a, ni.gaussian_filter(RM, 1.5), 0.62, 0.6)
        a = local(a, ni.gaussian_filter(RB, 1.5), 0.85)
        fur = RM
    Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype('u1')).save(T / f'nb_torso_{t}_tone.png')
    n = np.asarray(Image.open(T / f'nb_torso_{t}_normal.png').convert('RGB'), np.float32) / 127.5 - 1
    fs = np.asarray(Image.fromarray((fur * 255).astype('u1')).resize((n.shape[1], n.shape[0]), Image.BILINEAR), np.float32) / 255
    k = 0.65 - 0.35 * fs
    n[..., :2] *= k[..., None]; n /= np.linalg.norm(n, axis=2, keepdims=True)
    Image.fromarray(((n + 1) * 127.5 + .5).astype('u1')).save(T / f'nb_torso_{t}_normal2.png')
    print('TONE', t, 'fur share', round(float((fur > 0.5).mean()), 3))
n = np.asarray(Image.open(T / 'nb_limbs_a_normal.png').convert('RGB'), np.float32) / 127.5 - 1
n[..., :2] *= 0.7; n /= np.linalg.norm(n, axis=2, keepdims=True)
Image.fromarray(((n + 1) * 127.5 + .5).astype('u1')).save(T / 'nb_limbs_normal2.png')
for t in 'abc':
    col = np.asarray(Image.open(T / f'nb_head_{t}_raw.png').convert('RGB'), np.float32) / 255
    lum = col @ LUMA
    im1k = np.asarray(Image.fromarray((lum * 255).astype('u1')).resize((1024, 1024), Image.LANCZOS), np.float32) / 255
    hp = im1k - ni.gaussian_filter(im1k, 6)
    k = 0.55
    gx = ni.sobel(hp, axis=1) * k; gy = ni.sobel(hp, axis=0) * k
    nn = np.dstack([-gx, gy, np.ones_like(gx)]); nn /= np.linalg.norm(nn, axis=2, keepdims=True)
    Image.fromarray(((nn * 0.5 + 0.5) * 255 + .5).astype('u1')).save(T / f'nb_head_{t}_normal2.png')
print('TONE done')
