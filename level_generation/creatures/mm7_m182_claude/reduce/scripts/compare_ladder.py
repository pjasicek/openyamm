# Copied from mm8_m492_reduce_claude/scripts (read-only reference) for the m182 v3b reduction.
#!/usr/bin/env python3
"""Score the reduction ladder (silhouette IoU, textured SSIM per view), pick the lowest passing step automatically
and build one contact sheet: review/ladder_sheet.png and work/selection.json.
Pass: two-way surface p99 <= 3 mm and max <= 15 mm (1 m model, all clips), open edges not above the source,
silhouette IoU >= 0.98 in every view, mean textured SSIM >= 0.93."""
import json
import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parents[1]
L = json.loads((HERE / 'work/ladder.json').read_text())
R = HERE / 'review/ladder'
VIEWS = ['front', 'back', 'left', 'right', 'q34', 'top']


def load(name, mode):
    im = Image.open(R / f'{name}_{mode}.png')
    return np.asarray(im.convert('RGBA' if mode == 'sil' else 'L'), np.float32) / 255


def ssim(a, b):
    g = lambda x: ndimage.gaussian_filter(x, 1.5)
    ma, mb = g(a), g(b); va = g(a * a) - ma ** 2; vb = g(b * b) - mb ** 2; cov = g(a * b) - ma * mb
    c1, c2 = .01 ** 2, .03 ** 2
    return float((((2 * ma * mb + c1) * (2 * cov + c2)) / ((ma ** 2 + mb ** 2 + c1) * (va + vb + c2))).mean())


# thresholds are for a 1 m model; REA_HEIGHT_M scales them to the creature's height
H = float(os.environ.get('REA_HEIGHT_M', '1')); P99, MAXMM = 3 * H, 15 * H
src_open = L['source']['open_edges']
rows = []
for r, c in sorted(L['candidates'].items(), key=lambda kv: -float(kv[0])):
    tag = f'r{int(float(r) * 100)}'
    ious, ssims = [], []
    for v in VIEWS:
        a = load(f'source_{v}', 'sil')[..., 3] > .5; b = load(f'{tag}_{v}', 'sil')[..., 3] > .5
        ious.append(float((a & b).sum() / max((a | b).sum(), 1)))
        ssims.append(ssim(load(f'source_{v}', 'tex'), load(f'{tag}_{v}', 'tex')))
    c.update(iou_min=round(min(ious), 4), ssim_mean=round(float(np.mean(ssims)), 4))
    c['pass'] = bool(c['p99_mm'] <= P99 and c['max_mm'] <= MAXMM and c['open_edges'] <= src_open
                     and c['iou_min'] >= .98 and c['ssim_mean'] >= .93)
    rows.append((tag, r, c))
passing = [x for x in rows if x[2]['pass']]
pick = min(passing, key=lambda x: x[2]['tris']) if passing else None
sel = {'thresholds_mm': {'p99': round(P99, 2), 'max': round(MAXMM, 2)}, 'picked': pick[0] if pick else None, 'source_tris': L['source']['tris'], 'ladder': {t: c for t, _, c in rows}}
(HERE / 'work/selection.json').write_text(json.dumps(sel, indent=1) + '\n')
# sheet: source + every step, 4 views textured, label with metrics
cols = ['q34', 'left', 'front', 'top']; W = 384
sheet = Image.new('RGB', (W * len(cols), (W + 28) * (len(rows) + 1)), (24, 24, 24)); d = ImageDraw.Draw(sheet)
for i, (tag, label) in enumerate([('source', f"source  {L['source']['tris']} tris")] +
                                 [(t, f"{t}  {c['tris']} tris  p99 {c['p99_mm']} mm  max {c['max_mm']} mm  "
                                      f"IoU {c['iou_min']}  SSIM {c['ssim_mean']}  {'PASS' if c['pass'] else 'fail'}"
                                      f"{'  <- PICKED' if pick and t == pick[0] else ''}") for t, _, c in rows]):
    y = i * (W + 28)
    d.text((6, y + 7), label, fill=(255, 230, 120) if pick and tag == pick[0] else (230, 230, 230))
    for j, v in enumerate(cols):
        sheet.paste(Image.open(R / f'{tag}_{v}_tex.png').convert('RGB').resize((W, W)), (j * W, y + 28))
sheet.save(HERE / 'review/ladder_sheet.png')
print(json.dumps(sel, indent=1))
