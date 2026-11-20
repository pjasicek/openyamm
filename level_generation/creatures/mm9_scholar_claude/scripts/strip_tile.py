#!/usr/bin/env python3
"""Tile <dir>/<clip>_NN.png rows. Args: out dir frames cell clip,clip,..."""
import sys, os, glob
from PIL import Image, ImageDraw
out, d, N, cell = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
clips = sys.argv[5].split(',')
S = Image.new('RGB', (cell * N, cell * len(clips)), (30, 30, 30))
for r, c in enumerate(clips):
    for i in range(N):
        p = f'{d}/{c}_{i:02d}.png'
        if not os.path.exists(p): continue
        im = Image.open(p).convert('RGB').resize((cell, cell), Image.LANCZOS)
        if i == 0: ImageDraw.Draw(im).text((4, 4), c, fill=(255, 255, 0))
        S.paste(im, (i * cell, r * cell))
S.save(out)
