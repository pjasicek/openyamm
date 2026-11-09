#!/usr/bin/env python3
"""Head + hands texture set (after claude_shared/compose_head_set.py; user review 2026-10-14, new hands).

The head maps (1K, head-set UV 0..1) are resampled to HEAD_SCALE into the lower-left corner (export_runtime.py scales
the head faces' UVs by the same factor, so this is exact); the hands' squares in the freed top-right corner
(fit_hands.py) take the baked MakeHuman skin (bake_hands.py), graded so its median and spread per channel match the
face skin of the head set, times a soft baked AO normalised to keep that median.
Normal: flat on the hands. ORM: R 1, G the old hands' median roughness (old hand faces of the body map), B 0. Every map is edge-padded around the hand
islands. Writes textures/cle_headhand_basecolor.png, cle_headhand_normal_1k.png, cle_headhand_metal_rough_1k.png."""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

P = Path(__file__).resolve().parents[1]
T, H = P / 'textures', P / 'work' / 'hands'
FIT = json.load(open(H / 'fit.json'))
S = FIT['head_scale']
N = 1024
AO_STRENGTH = 0.45


def scaled(img, fill):
    """head map scaled into the lower-left corner (UV origin bottom-left = image bottom-left)"""
    out = Image.new(img.mode, (N, N), fill)
    k = int(round(N * S))
    out.paste(img.resize((k, k), Image.LANCZOS), (0, N - k))
    return np.asarray(out).astype(np.float32)


def pad(arr, mask, iters=24):
    """repeat each covered texel outward (nearest), so filtering and mips never pull in the background"""
    idx = ndimage.distance_transform_edt(~mask, return_distances=False, return_indices=True)
    grown = ndimage.binary_dilation(mask, iterations=iters)
    out = arr.copy()
    out[grown & ~mask] = arr[idx[0], idx[1]][grown & ~mask]
    return out


base = scaled(Image.open(T / 'cle_head_basecolor_graded.png').convert('RGB'), (0, 0, 0))
normal = scaled(Image.open(T / 'cle_head_normal_1k.png').convert('RGB'), (128, 128, 255))
orm = scaled(Image.open(T / 'cle_head_metal_rough_1k.png').convert('RGB'), (255, 200, 0))

# roughness of the installed hands: the old hand faces' centroids (fit_hands.py) sampled in the body ORM map
bodyc = np.asarray(Image.open(T / 'cle_a_basecolor_1k.png').convert('RGB')).astype(np.float32)
bodym = np.asarray(Image.open(T / 'cle_metal_rough_1k.png').convert('RGB')).astype(np.float32)
uvs = np.array(json.load(open(H / 'old_hand_uvs.json')))
bh, bw = bodyc.shape[:2]
yy = np.clip(((1 - uvs[:, 1]) * bh).astype(int), 0, bh - 1); xx = np.clip((uvs[:, 0] * bw).astype(int), 0, bw - 1)
ref_rough = float(np.median(bodym[yy, xx, 1]))
# colour reference: the face's skin in the head set (the old Meshy hands were a brighter peach than the face)
head = np.asarray(Image.open(T / 'cle_head_basecolor_graded.png').convert('RGB')).astype(np.float32)
f = head.reshape(-1, 3)[::3] / 255
mx, mn = f.max(1), f.min(1); sat = (mx - mn) / np.maximum(mx, 1e-6)
hue = np.where(mx == f[:, 0], ((f[:, 1] - f[:, 2]) / np.maximum(mx - mn, 1e-6) / 6.0) % 1.0, 0.5)
ref = f[(hue < 0.07) & (sat > 0.3) & (sat < 0.55) & (mx > 0.7)] * 255

skin = np.asarray(Image.open(H / 'hand_skin.png').convert('RGB')).astype(np.float32)
mask = np.asarray(Image.open(H / 'hand_mask.png').convert('L')) > 127
ao = np.asarray(Image.open(H / 'hand_ao.png').convert('L').filter(ImageFilter.GaussianBlur(1.6))).astype(np.float32) / 255
src = skin[mask]
graded = (skin - np.median(src, 0)) * (np.std(ref, 0) / np.maximum(np.std(src, 0), 1e-3)) * 0.6 + np.median(ref, 0)
aof = 1 - AO_STRENGTH + AO_STRENGTH * np.clip(ao / np.percentile(ao[mask], 90), 0, 1)
graded *= (aof / np.median(aof[mask]))[..., None]
graded = np.clip(graded, 0, 255)

region = np.zeros((N, N), bool)
for u0, v0, side in FIT['squares'].values():
    x0, x1 = int(u0 * N), int(round((u0 + side) * N)); y0, y1 = N - int(round((v0 + side) * N)), N - int(v0 * N)
    region[y0:y1, x0:x1] = True
hand = mask & region
base[region] = 0
base[hand] = graded[hand]
normal[region] = (128, 128, 255)
orm[region] = (255, ref_rough, 0)
base = pad(base, hand | ~region)
Image.fromarray(np.uint8(np.round(base))).save(T / 'cle_headhand_basecolor.png')
Image.fromarray(np.uint8(np.round(normal))).save(T / 'cle_headhand_normal_1k.png')
Image.fromarray(np.uint8(np.round(orm))).save(T / 'cle_headhand_metal_rough_1k.png')
print('HANDSET head scale', S, 'hand texels', int(hand.sum()), 'skin ref median', np.median(ref, 0).round(1),
      'graded median', np.median(base[hand], 0).round(1), 'roughness', round(ref_rough, 1))
