#!/usr/bin/env python3
"""Installed | reduced pairs of close shots per row. Usage: pair_sheet.py <dir> <tierA> <tierB> <out> <shot,...>"""
import sys
from PIL import Image, ImageDraw
D, A, B, out, shots = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5].split(',')
W = 640; H = int(W * 1060 / 1440)
sh = Image.new('RGB', (2 * W, len(shots) * (H + 18)), (25, 25, 25)); d = ImageDraw.Draw(sh)
for r, s in enumerate(shots):
    for j, m in enumerate((A, B)):
        sh.paste(Image.open(f'{D}/{m}/{s}.png').convert('RGB').resize((W, H)), (j * W, r * (H + 18) + 18))
        d.text((j * W + 4, r * (H + 18) + 3), f'{m} {s}', fill=(255, 220, 120))
sh.save(out)
