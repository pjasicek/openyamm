#!/usr/bin/env python3
"""Sheet: the sprite's x2 frame, then candidate renders cropped and stretched to the sprite's aspect (as a vertical
scale of the model would). Usage: compare_sheet.py <sprite> <out.png> <render.png>..."""
import os, sys
from PIL import Image, ImageDraw
import scans

sprite, out, *renders = sys.argv[1:]


def crop(im):
    im = im.convert('RGBA'); return im.crop(im.getchannel('A').point(lambda a: 255 if a > 8 else 0).getbbox())


s = crop(Image.open(os.path.join(scans.X2, sprite + '_p2.png')))
H = 260; W = int(H * s.width / s.height)
items = [(sprite, s)] + [(os.path.basename(r)[:-4], crop(Image.open(r))) for r in renders]
cols = min(len(items), 6); rows = (len(items) + cols - 1) // cols
sheet = Image.new('RGB', (cols * (W + 10), rows * (H + 30)), (90, 110, 90)); d = ImageDraw.Draw(sheet)
for i, (label, im) in enumerate(items):
    im = im.resize((W, H), Image.LANCZOS)
    x, y = (i % cols) * (W + 10) + 5, (i // cols) * (H + 30) + 25
    sheet.paste(im, (x, y), im); d.text((x, y - 20), label, fill=(255, 255, 255))
sheet.save(out); print('SHEET', out)
