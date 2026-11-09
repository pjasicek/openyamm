"""work/headuv.npz -> review/head/headuv_layout.png (face orange, scalp/neck/ears pale, hair brown, hood green). Usage: draw_headuv.py"""
import numpy as np
from PIL import Image, ImageDraw
d = np.load('work/headuv.npz'); S = 1024
im = Image.new('RGB', (S, S), (30, 30, 30)); dr = ImageDraw.Draw(im)
col = {1: (230, 140, 100), 4: (200, 170, 150), 2: (140, 90, 50), 3: (60, 160, 80), 5: (40, 110, 60)}
for p, t in zip(d['uvpart'], d['huv']):
    dr.polygon([(u * S, (1 - v) * S) for u, v in t], fill=col[int(p)], outline=(0, 0, 0))
im.save('review/head/headuv_layout.png')
