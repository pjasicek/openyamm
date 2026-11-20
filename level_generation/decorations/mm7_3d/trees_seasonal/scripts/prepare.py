#!/usr/bin/env python3
"""Inputs for one species (work/<id>/): profile.json (the crown envelope: the upscaled sprite's half-width per height,
both as fractions of the tree height) and the bark maps from Poly Haven bark_brown_01 (CC0, 2k reduced to 1024²):
bark_basecolor.png (diffuse x ambient occlusion^1.5 x a little height, so the furrows read dark even in the crown's
shade; channels scaled so the mean matches the species' trunk colour bark.target_srgb), bark_normal.png (OpenGL) and
bark_mr.png (glTF metallic-roughness: G = roughness). Usage: prepare.py <id>"""
import json, os
import numpy as np
from PIL import Image
import common
spec = common.load(); W = spec['work']; S = os.path.join(common.SOURCE, 'bark_brown_01')

sprite = np.asarray(Image.open(spec['envelope_path']).convert('RGBA'))
a = sprite[..., 3] > 128
rows = np.where(a.any(1))[0]; top, bottom = rows.min(), rows.max(); H = bottom - top + 1
profile = []
for k in range(51):
    y = int(bottom - k / 50 * (H - 1))
    cols = np.where(a[y])[0]
    profile.append([k / 50, float((cols.max() - cols.min() + 1) / 2 / H) if cols.size else 0.0])
json.dump({'height_px': int(H), 'width_px': int(a.any(0).sum()), 'half_width_by_height': profile},
          open(os.path.join(W, 'profile.json'), 'w'), indent=1)
print('PROFILE', [(p[0], round(p[1], 3)) for p in profile[::5]])


def load(name, channels):
    # The roughness map is 16-bit greyscale, displacement RGBA, the rest 8-bit.
    raw = np.asarray(Image.open(os.path.join(S, f'bark_brown_01_{name}_2k.png')))
    values = raw.astype(np.float32) / (65535.0 if raw.dtype == np.uint16 else 255.0)
    return values[..., :channels] if values.ndim == 3 else values


diffuse = common.lin(load('diff', 3))
ao = load('ao', 1)
height = load('disp', 3).mean(2)
height = (height - height.min()) / max(float(height.max() - height.min()), 1e-6)
bark = diffuse * (ao ** 1.5 * (0.7 + 0.3 * height))[..., None]
if spec['bark'].get('contrast'):        # MM7 change: luminance contrast about the mean (bare trees' rough bark)
    lum = np.maximum(bark @ np.array([0.2126, 0.7152, 0.0722]), 1e-4)
    bark = bark * ((lum / lum.mean()) ** (spec['bark']['contrast'] - 1.0))[..., None]
target = common.lin(np.array(spec['bark']['target_srgb']) / 255.0)
bark = bark / bark.reshape(-1, 3).mean(0) * target
SIZE = (1024, 1024)
Image.fromarray((np.clip(common.srgb(bark), 0, 1) * 255).astype(np.uint8)).resize(SIZE, Image.LANCZOS).save(
    os.path.join(W, 'bark_basecolor.png'))
Image.open(os.path.join(S, 'bark_brown_01_nor_gl_2k.png')).convert('RGB').resize(SIZE, Image.LANCZOS).save(
    os.path.join(W, 'bark_normal.png'))
rough = (load('rough', 1) * 255).astype(np.uint8); zero = np.zeros_like(rough)
Image.fromarray(np.stack([zero, rough, zero], 2)).resize(SIZE, Image.LANCZOS).save(os.path.join(W, 'bark_mr.png'))
print('BARK mean sRGB', (common.srgb(bark.reshape(-1, 3).mean(0)) * 255).round(1))
