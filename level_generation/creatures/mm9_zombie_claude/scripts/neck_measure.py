#!/usr/bin/env python3
"""Colour on both sides of the neck join in the viewer's light (front shots, same boxes): neck skin above the join, chest skin below, cheek. Args: <dir>"""
import sys
import numpy as np
from PIL import Image
d = sys.argv[1]
for t in 'abc':
    a = np.asarray(Image.open(f'{d}/{t}_f.png').convert('RGB'), np.float32)
    box = lambda x0, y0, x1, y1: a[y0:y1, x0:x1].reshape(-1, 3).mean(0)
    n, c, f = box(385, 510, 470, 570), box(395, 610, 480, 650), box(150, 200, 230, 260)
    print(t, 'neck', n.round(0), 'chest', c.round(0), 'cheek', f.round(0), 'neck/chest', (n / c).round(2))
