#!/usr/bin/env python3
"""v2 bark maps from Poly Haven bark_brown_01 (CC0, 2k; deep vertical furrows like the sprite's trunk) into work/:
1024² (2k sources downsampled: at a 0.8 m repeat that is ~1300 px/m) bark2_basecolor.png (diffuse x ambient occlusion^1.5 x a little height, so the furrows read dark even in the crown's
shade; channels scaled so the mean matches the sprite's reddish-brown trunk while keeping the texture's contrast),
bark2_normal.png (OpenGL normal map) and bark2_mr.png (glTF metallic-roughness: G = roughness, R = B = 0)."""
import os
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(HERE, 'work'); S = os.path.join(HERE, 'source', 'bark_brown_01')
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - 0.055)


def load(name, channels):
    # The roughness map is 16-bit greyscale, displacement RGBA, the rest 8-bit.
    raw = np.asarray(Image.open(os.path.join(S, f'bark_brown_01_{name}_2k.png')))
    values = raw.astype(np.float32) / (65535.0 if raw.dtype == np.uint16 else 255.0)
    return values[..., :channels] if values.ndim == 3 else values


diffuse = lin(load('diff', 3))
ao = load('ao', 1)
height = load('disp', 3).mean(2)
height = (height - height.min()) / max(float(height.max() - height.min()), 1e-6)
cavity = ao ** 1.5 * (0.7 + 0.3 * height)
bark = diffuse * cavity[..., None]
target = lin(np.array([104, 66, 46]) / 255.0)          # sprite trunk mean (sRGB), as in v1
bark = bark / bark.reshape(-1, 3).mean(0) * target
SIZE = (1024, 1024)
Image.fromarray((np.clip(srgb(bark), 0, 1) * 255).astype(np.uint8)).resize(SIZE, Image.LANCZOS).save(
    os.path.join(W, 'bark2_basecolor.png'))
Image.open(os.path.join(S, 'bark_brown_01_nor_gl_2k.png')).convert('RGB').resize(SIZE, Image.LANCZOS).save(
    os.path.join(W, 'bark2_normal.png'))
rough = (load('rough', 1) * 255).astype(np.uint8)
zero = np.zeros_like(rough)
Image.fromarray(np.stack([zero, rough, zero], 2)).resize(SIZE, Image.LANCZOS).save(os.path.join(W, 'bark2_mr.png'))
luma = srgb(bark).mean(2) * 255
print('BARK2 mean sRGB', (srgb(bark.reshape(-1, 3).mean(0)) * 255).round(1), 'luma p5/p50/p95',
      np.percentile(luma, [5, 50, 95]).round(1), 'rough mean', round(float(rough.mean()) / 255, 2))
