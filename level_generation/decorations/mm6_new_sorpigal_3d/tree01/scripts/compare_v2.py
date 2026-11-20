#!/usr/bin/env python3
"""Sprite vs render: mean colour and luminance 5/50/95 percentiles, and a side-by-side crop. compare_v2.py render out"""
import sys
import numpy as np
from PIL import Image
sprite = Image.open('../../../mm6_new_sorpigal/enhanced/6tree01.png').convert('RGBA')
ours = Image.open(sys.argv[1]).convert('RGBA')


def stats(im):
    x = np.asarray(im).astype(float); m = x[..., 3] > 128; l = x[..., :3] @ [0.3, 0.59, 0.11]
    return x[m][:, :3].mean(0).round(1).tolist(), np.percentile(l[m], [5, 50, 95]).round(1).tolist()


print('sprite', stats(sprite)); print('ours  ', stats(ours))
crops = []
for im in (sprite, ours):
    bb = im.getbbox(); im = im.crop(bb); crops.append(im.resize((400, int(400 * im.height / im.width))))
sheet = Image.new('RGBA', (820, max(c.height for c in crops)), (150, 160, 175, 255))
sheet.alpha_composite(crops[0], (0, 0)); sheet.alpha_composite(crops[1], (420, 0)); sheet.convert('RGB').save(sys.argv[2])
