"""Job 7: 1 cm grid over side_ortho.py renders (labels: y and z in metres, export frame). Args: <png> <side R|L> <size> <cy> <cz> <out>"""
import sys
from PIL import Image, ImageDraw
png, side, S, CY, CZ, out = sys.argv[1], sys.argv[2], *map(float, sys.argv[3:6]), sys.argv[6]
im = Image.open(png).convert('RGB'); PX = im.size[0]; d = ImageDraw.Draw(im)
sg = 1 if side == 'R' else -1
for k in range(-20, 21):
    y = round(CY + k * 0.01, 3); px = (sg * (y - CY)) / S * PX + PX / 2
    z = round(CZ + k * 0.01, 3); py = PX / 2 - (z - CZ) / S * PX
    c = (255, 255, 0) if k % 5 == 0 else (90, 90, 90)
    d.line([(px, 0), (px, PX)], fill=c, width=1); d.line([(0, py), (PX, py)], fill=c, width=1)
    if k % 2 == 0:
        d.text((px + 2, 2), f'{y:.2f}', fill=(255, 255, 255)); d.text((2, py + 2), f'{z:.2f}', fill=(255, 255, 255))
im.save(out)
