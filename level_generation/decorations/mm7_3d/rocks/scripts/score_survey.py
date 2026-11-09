#!/usr/bin/env python3
"""Score the survey silhouettes (../work/survey) against each MM7 rock sprite's alpha. Both are cropped to their bounds
and resized to 64x64 (a vertical stretch is free, penalised outside 0.75-1.4). Score = IoU minus the mean difference
of the top and side contours (fractions of the box), so peaks, notches and leaning sides count. Mirrored views are
marked 'M'. Writes ../work/score_<sprite>.png (sprite mask, then the best views). Usage: score_survey.py [top]"""
import glob, os, sys
import numpy as np
from PIL import Image, ImageDraw
import scans

TOP = int(sys.argv[1]) if len(sys.argv) > 1 else 8
N = 64


def norm(mask):
    ys, xs = np.nonzero(mask)
    crop = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    im = Image.fromarray((crop * 255).astype(np.uint8)).resize((N, N), Image.BILINEAR)
    return np.asarray(im) > 127, crop.shape[0] / crop.shape[1]


def contours(m):
    rows = np.arange(N)[:, None]
    top = np.where(m.any(0), np.where(m, rows, N).min(0), N) / N              # per column
    cols = np.arange(N)[None, :]
    left = np.where(m.any(1), np.where(m, cols, N).min(1), N) / N             # per row
    right = np.where(m.any(1), N - 1 - np.where(m, cols, -1).max(1), N) / N
    return top, left, right


renders = {}
for path in sorted(glob.glob(os.path.join(scans.HERE, 'work', 'survey', '*.png'))):
    renders[os.path.basename(path)[:-4]] = norm(np.asarray(Image.open(path).convert('RGBA'))[..., 3] > 127)
for sprite in scans.SPRITES:
    s_mask, s_aspect = norm(np.asarray(Image.open(os.path.join(scans.X2, sprite + '_p2.png')).convert('RGBA'))[..., 3] > 127)
    s_c = contours(s_mask)
    rows = []
    for name, (mask, aspect) in renders.items():
        if name.startswith('nbs01a'):
            continue                                                       # same stone as nbs01b
        stretch = s_aspect / aspect
        pen = max(0.0, abs(np.log(stretch)) - np.log(1.4 if stretch > 1 else 1 / 0.75)) * 0.5
        for mirrored, m in ((False, mask), (True, mask[:, ::-1])):
            iou = (m & s_mask).sum() / (m | s_mask).sum()
            c = contours(m)
            cdiff = np.mean([np.abs(a - b).mean() for a, b in zip(c, s_c)])
            rows.append((iou - 2 * cdiff - pen, iou, cdiff, stretch, name + (' M' if mirrored else ''), m))
    rows.sort(key=lambda r: -r[0])
    best = {}
    for row in rows:
        key = row[4].split('_e')[0]
        if key not in best:
            best[key] = row
    picks = sorted(best.values(), key=lambda r: -r[0])[:TOP]
    print(sprite, 'aspect', round(s_aspect, 2))
    for score, iou, cdiff, stretch, name, _ in picks:
        print(f'   {score:.3f} iou {iou:.3f} contour {cdiff:.3f} stretch {stretch:.2f} {name}')
    sheet = Image.new('RGB', ((TOP + 1) * 100, 120), (40, 40, 40)); d = ImageDraw.Draw(sheet)
    for i, (label, m) in enumerate([(sprite, s_mask)] + [(p[4], p[5]) for p in picks]):
        sheet.paste(Image.fromarray((m * 255).astype(np.uint8)).resize((90, 90)), (i * 100 + 5, 25))
        d.text((i * 100 + 3, 5), label.replace('_e', ' e').replace('_y', ' y'), fill=(255, 255, 0))
    sheet.save(os.path.join(scans.HERE, 'work', f'score_{sprite}.png'))
