#!/usr/bin/env python3
"""Tone of the paint, part by part (work/faces.npz), against the HD masters and MM9's dark armour:
- cuirass, bracers, gauntlets and boots are iron, but Meshy projected bone colour onto faces the views barely show (the collar, the inner side of
  the bracer): bone-coloured blobs on these parts take iron colour, the paint's brightness detail stays;
- iron and mail (unsaturated texels of the armour parts): highlights compressed, the mail's white flecks read as stipple up close;
- red lacquer and blue lacing: a little less saturation and value, MM9's are duller than Meshy's;
- bone: slightly darker and more olive, as MM9's.
Reads textures/*_basecolor_graded.png, writes *_basecolor_final.png."""
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
F = np.load('work/faces.npz')
ARM = [8, 9, 17, 35, 36, 59, 117, 135, 136, 159, 14, 16, 25, 30, 32, 33, 38, 41, 42, 47, 49, 50, 56, 57, 58, 60, 61, 65, 10, 7, 12, 110, 107, 112,
       22, 26, 40, 54, 55, 63, 126, 140, 154, 155, 163, 21, 11, 45]
IRON = [8, 10, 7, 12, 110, 107, 112]


def raster(uv, ids, S):
    im = Image.new('L', (S, S), 0); d = ImageDraw.Draw(im)
    keep = np.isin(F['pid'], ids) & (F['lining'] == 0)
    for t in uv[keep]:
        d.polygon([(float(u * S), float((1 - v) * S)) for u, v in t], fill=255)
    return ndimage.binary_dilation(np.asarray(im) > 0, iterations=3)


for name, key in (('skelwar', 'ub'), ('skelwar_head', 'uh')):
    a = np.asarray(Image.open(f'textures/{name}_basecolor_graded.png').convert('RGB'), np.float32) / 255
    S = a.shape[0]
    arm = raster(F[key], ARM, S); iron = raster(F[key], IRON, S)
    mx, mn = a.max(2), a.min(2); sat = (mx - mn) / np.maximum(mx, 1e-5)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    lum = a @ np.array([0.3, 0.59, 0.11])
    # bone blobs on iron parts (gold rivets and trim are small, they survive the opening)
    bone = iron & (hue > 28) & (hue < 70) & (sat > 0.12) & (lum > 0.28)
    bone = ndimage.binary_opening(bone, iterations=5)
    bone = ndimage.binary_dilation(bone, iterations=6) & iron
    bw = np.clip(ndimage.gaussian_filter(bone.astype(np.float32), 3.0) * 1.4, 0, 1)[..., None]
    grey = np.stack([lum] * 3, -1) * np.array([0.33, 0.33, 0.36])
    out = a * (1 - bw) + grey * bw
    print(name, 'bone blobs', round(float(bone.mean() * 100), 2), '%')
    # iron and mail
    plain = arm & (sat < 0.3)
    pw = np.clip(ndimage.gaussian_filter(plain.astype(np.float32), 1.0), 0, 1)[..., None]
    L = out @ np.array([0.3, 0.59, 0.11]); base = ndimage.gaussian_filter(L, 6.0)
    L2 = base * 0.74 + (L - base) * 0.55
    L2 = np.where(L2 > 0.34, 0.34 + (L2 - 0.34) * 0.45, L2)
    ratio = (L2 / np.maximum(L, 1e-3))[..., None]
    out = out * (1 - pw) + np.clip(out * ratio, 0, 1) * pw
    # bone: MM9's is a darker olive than Meshy's ivory
    bone_w = np.clip(ndimage.gaussian_filter((~arm).astype(np.float32), 1.5), 0, 1)[..., None]
    out = out * (1 - bone_w) + out * np.array([0.84, 0.84, 0.74]) * bone_w
    # lacquer and lacing
    red = arm & ((hue < 24) | (hue > 335)) & (sat > 0.38); blue = arm & (hue > 165) & (hue < 255) & (sat > 0.18)
    for m, sg, vg in ((red, 0.88, 0.8), (blue, 0.8, 0.85)):
        w = np.clip(ndimage.gaussian_filter(m.astype(np.float32), 1.0), 0, 1)[..., None]
        L = (out @ np.array([0.3, 0.59, 0.11]))[..., None]
        c = np.clip((L + (out - L) * sg) * vg, 0, 1)
        out = out * (1 - w) + c * w
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(f'textures/{name}_basecolor_final.png')
    print(name, 'mean', (out.reshape(-1, 3).mean(0) * 255).round(1))
