#!/usr/bin/env python3
"""Five views side by side. Args: out dir prefix cell"""
import sys
from PIL import Image
out, d, p, c = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
vs = ['q34', 'front', 'left', 'back', 'right']
S = Image.new('RGB', (c * 5, c))
for i, v in enumerate(vs):
    S.paste(Image.open(f'{d}/{p}_{v}.png').convert('RGB').resize((c, c), Image.LANCZOS), (i * c, 0))
S.save(out)
