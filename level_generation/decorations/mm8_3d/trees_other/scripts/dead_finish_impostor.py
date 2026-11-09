#!/usr/bin/env python3
"""work/dead_<id>/impostor_*_raw.png -> impostor_basecolor.png (RGBA, colour dilated into transparent texels, cutout
grown by `impostor_dilate` px of 1024 (default 0), albedo times `impostor_tone` in linear) and impostor_normal.png, both reduced to
512² keeping the cutout coverage at the 0.5 alpha test (as the living trees' finish_impostor.py + shrink_far_maps.py).
A dilated cutout merges the fine twig network into dark blobs, so bare trees keep the plain 0.5 cutout.
Usage: dead_finish_impostor.py <id>"""
import os
import numpy as np
from PIL import Image
from scipy import ndimage
import dead_common as dc

spec = dc.load(); W = spec['work']
albedo = np.asarray(Image.open(os.path.join(W, 'impostor_albedo_raw.png')).convert('RGBA')).copy()
normal = np.asarray(Image.open(os.path.join(W, 'impostor_normal_raw.png')).convert('RGBA')).copy()
inside = albedo[..., 3] >= 128
if spec.get('impostor_dilate', 0):
    inside = ndimage.binary_dilation(inside, iterations=spec['impostor_dilate'])
albedo[..., 3] = np.where(inside, 255, 0)
idx = ndimage.distance_transform_edt(~inside, return_distances=False, return_indices=True)
albedo[..., :3] = albedo[..., :3][idx[0], idx[1]]
normal[..., :3] = normal[..., :3][idx[0], idx[1]]
tone = np.array(spec.get('impostor_tone', [1.0, 1.0, 1.0]))
albedo[..., :3] = (np.clip(dc.srgb(dc.lin(albedo[..., :3] / 255.0) * tone), 0, 1) * 255 + 0.5).astype(np.uint8)

SIZE = 512


def resize(channel):
    return np.asarray(Image.fromarray(channel.astype(np.float32), 'F').resize((SIZE, SIZE), Image.LANCZOS))


px = albedo.astype(np.float32) / 255.0
coverage = float((px[..., 3] >= 0.5).mean())
out = np.stack([resize(px[..., c]) for c in range(4)], 2).clip(0.0, 1.0)
low, high = 0.5, 8.0
for _ in range(40):
    scale = 0.5 * (low + high)
    if float((out[..., 3] * scale >= 0.5).mean()) < coverage:
        low = scale
    else:
        high = scale
out[..., 3] = (out[..., 3] * high).clip(0.0, 1.0)
Image.fromarray((out * 255 + 0.5).astype(np.uint8), 'RGBA').save(os.path.join(W, 'impostor_basecolor.png'))
n = normal[..., :3].astype(np.float32) / 255.0 * 2 - 1
n = np.stack([resize(n[..., c]) for c in range(3)], 2)
n /= np.maximum(np.linalg.norm(n, axis=2, keepdims=True), 1e-6)
Image.fromarray(((n * 0.5 + 0.5) * 255 + 0.5).clip(0, 255).astype(np.uint8), 'RGB').save(
    os.path.join(W, 'impostor_normal.png'))
print('IMPOSTOR coverage 1024', round(coverage, 4), '512', round(float((out[..., 3] >= 0.5).mean()), 4))
