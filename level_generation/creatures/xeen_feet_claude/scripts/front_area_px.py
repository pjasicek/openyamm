#!/usr/bin/env python3
"""Binding scale from silhouette area: native idle body area (1530 px at 1.34 units/px, the Xeen witch calibration)
against the model's front silhouette over Standing (work/front_area.npz)."""
import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path
d = np.load(Path(__file__).resolve().parents[1] / 'work/front_area.npz')['tris']
R = 2000                                       # px per metre
areas, heights, widths = [], [], []
for fr in d:
    im = Image.new('L', (2000, 1000), 0); dr = ImageDraw.Draw(im)
    for t in fr:
        dr.polygon([(float(x) * R + 1000, 900 - float(z) * R) for x, z in t], fill=255)
    a = np.asarray(im) > 0; areas.append(a.sum() / R / R)
    ys, xs = np.nonzero(a); heights.append((ys.max() - ys.min()) / R); widths.append((xs.max() - xs.min()) / R)
A = float(np.mean(areas)); native = 1530 * 1.34 ** 2
print('model area m2', round(A, 4), 'height m', round(float(np.mean(heights)), 3), 'width m', round(float(np.mean(widths)), 3))
print('SCALE by area', round((native / A) ** 0.5, 1), '| by width', round(137 * 1.34 / np.mean(widths), 1),
      '| by height', round(45 * 1.34 / np.mean(heights), 1))
