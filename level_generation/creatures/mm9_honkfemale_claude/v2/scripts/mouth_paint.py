#!/usr/bin/env python3
"""Closed mouth in a head base colour (Meshy's lips are two separate cups over the shell; the reference's teeth land as a
pale jagged strip on the shell and the lips' inner rims): pale texels on the lip plates take the lips' median colour, the
shell strip behind them and the inner rim go dark.
Usage: mouth_paint.py <in png> <out png> <uv json> [r g b]"""
import json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
src, dst, js = sys.argv[1:4]
rgb = [int(x) for x in sys.argv[4:7]] if len(sys.argv) > 6 else [70, 34, 30]
im = Image.open(src).convert('RGB'); W, H = im.size
J = json.load(open(js))


def foot(tris):
    m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m)
    for t in tris:
        d.polygon([(u * W, (1 - v) * H) for u, v in t], fill=255)
    return m


px = np.asarray(im, np.float32)
plate = np.asarray(foot(J['plate'])) > 0
lum = px @ np.array([.299, .587, .114]) / 255
pale = plate & (lum > .55) & (px[..., 0] - px[..., 2] < 90)
lip = plate & ~pale & (px[..., 0] > px[..., 1] * 1.2) & (lum > .28)
lipc = np.median(px[lip], 0)
soft = np.asarray(Image.fromarray(np.uint8(pale) * 255).filter(ImageFilter.GaussianBlur(1.5)), np.float32)[..., None] / 255
out = px * (1 - soft) + lipc * soft
dark = np.maximum(np.asarray(foot(J['shell']).filter(ImageFilter.GaussianBlur(1.2)), np.float32),
                  np.asarray(foot(J['rim']).filter(ImageFilter.GaussianBlur(1.2)), np.float32))[..., None] / 255
out = out * (1 - dark) + np.array(rgb, np.float32) * dark
Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(dst)
print('MOUTHPAINT pale', int(pale.sum()), 'lip', lipc.round(0).tolist(), 'dark', int((dark > .5).sum()))
