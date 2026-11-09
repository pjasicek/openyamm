#!/usr/bin/env python3
"""Compare a rock's current review renders with an earlier set (default ../work/<rock>/review_1200): per view, the
alpha-mask IoU (silhouette), the mean absolute luma difference inside the shared mask (texture/shading, 0-255), and
the lit-mean colour shift. Writes ../work/<rock>/compare_<old>.png (old row above new row).
Usage: compare_lods.py <rock> [old_dir_name]"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
import scans

rock = sys.argv[1]; old = sys.argv[2] if len(sys.argv) > 2 else 'review_1200'
W = os.path.join(scans.HERE, 'work', rock)
views = ['render_lod0', 'render_yaw090', 'render_yaw180', 'render_yaw270', 'render_lod1', 'render_lod2', 'render_lod3']
rows = []
for v in views:
    a = np.asarray(Image.open(os.path.join(W, old, v + '.png')).convert('RGBA'), np.float32)
    b = np.asarray(Image.open(os.path.join(W, 'review', v + '.png')).convert('RGBA'), np.float32)
    ma, mb = a[..., 3] > 127, b[..., 3] > 127
    iou = (ma & mb).sum() / max((ma | mb).sum(), 1)
    la, lb = a[..., :3] @ [0.2126, 0.7152, 0.0722], b[..., :3] @ [0.2126, 0.7152, 0.0722]
    both = ma & mb
    rows.append((v, iou, np.abs(la - lb)[both].mean(), a[..., :3][ma].mean(0) - b[..., :3][mb].mean(0)))
    print(f'{rock} {v:14s} IoU {iou:.3f} luma diff {rows[-1][2]:5.1f} mean shift {np.round(rows[-1][3], 1)}')
sheet = Image.new('RGB', (len(views) * 256, 2 * 256 + 20), (88, 104, 88)); d = ImageDraw.Draw(sheet)
for i, v in enumerate(views):
    for j, folder in enumerate((old, 'review')):
        im = Image.open(os.path.join(W, folder, v + '.png')).convert('RGBA').resize((256, 256))
        sheet.paste(im, (i * 256, 20 + j * 256), im)
    d.text((i * 256 + 4, 4), f'{v[7:]} IoU {rows[i][1]:.3f}', fill=(255, 255, 255))
sheet.save(os.path.join(W, f'compare_{old}.png'))
