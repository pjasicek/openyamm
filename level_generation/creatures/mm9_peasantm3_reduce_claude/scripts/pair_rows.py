#!/usr/bin/env python3
"""Installed | reduced full-frame pairs of close viewer shots, a few rows per sheet.
Usage: pair_rows.py <shots dir> <tag> <out prefix> <shot,...> [rows per sheet 3] [width 1600]"""
import sys
from PIL import Image, ImageDraw
d0, tag, pre, shots = sys.argv[1:5]; R = int(sys.argv[5]) if len(sys.argv) > 5 else 3; W = int(sys.argv[6]) if len(sys.argv) > 6 else 1600
shots = shots.split(',')
for k in range(0, len(shots), R):
    rows = shots[k:k + R]; a0 = Image.open(f'{d0}/inst_a/{rows[0]}.png'); w, h = a0.size; s = W / (2 * w); H = int(h * s)
    sh = Image.new('RGB', (W, len(rows) * (H + 16)), (25, 25, 25)); dr = ImageDraw.Draw(sh)
    for r, n in enumerate(rows):
        for c, m in enumerate(('inst_a', 'red_a')):
            im = Image.open(f'{d0}/{m}/{n}.png').convert('RGB').resize((W // 2, H))
            sh.paste(im, (c * W // 2, r * (H + 16) + 16)); dr.text((c * W // 2 + 4, r * (H + 16) + 2), f'{n} {"installed" if c == 0 else tag}', fill=(255, 220, 120))
    sh.save(f'{pre}_{k // R}.png'); print(f'{pre}_{k // R}.png')
