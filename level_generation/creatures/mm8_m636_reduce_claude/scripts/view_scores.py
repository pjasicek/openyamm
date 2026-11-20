#!/usr/bin/env python3
"""Silhouette IoU and textured SSIM of fish_views.py renders against the source renders (playbook gates: IoU >= 0.98
per view, mean SSIM >= 0.93). The mask is every pixel differing from the background colour by more than 6/255.
Usage: view_scores.py <label>... -> prints per view"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
C = Path(__file__).resolve().parents[1] / 'review' / 'close'
VIEWS = ['side', 'top', 'front', 'rear', 'fins', 'small', 'school']


def ssim(a, b):
    g = lambda x: ndimage.gaussian_filter(x, 1.5)
    ma, mb = g(a), g(b); va = g(a * a) - ma ** 2; vb = g(b * b) - mb ** 2; cov = g(a * b) - ma * mb
    c1, c2 = .01 ** 2, .03 ** 2
    return float((((2 * ma * mb + c1) * (2 * cov + c2)) / ((ma ** 2 + mb ** 2 + c1) * (va + vb + c2))).mean())


for lab in sys.argv[1:]:
    row = []
    for v in VIEWS:
        a = np.asarray(Image.open(C / f'src_{v}_tex.png').convert('RGB'), np.float32) / 255
        b = np.asarray(Image.open(C / f'{lab}_{v}_tex.png').convert('RGB'), np.float32) / 255
        bg = a[0, 0]; ma = np.abs(a - bg).max(-1) > 6 / 255; mb = np.abs(b - bg).max(-1) > 6 / 255
        row.append((v, round(float((ma & mb).sum() / max((ma | mb).sum(), 1)), 4), round(ssim(a.mean(-1), b.mean(-1)), 4)))
    print(lab, 'IoU min', min(r[1] for r in row), 'SSIM mean', round(float(np.mean([r[2] for r in row])), 4), row)
