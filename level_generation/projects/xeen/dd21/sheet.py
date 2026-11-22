#!/usr/bin/env python3
"""sheet.py <folder> <out prefix>: JPEG contact sheets of a tour's PNGs, 3 by 3, labelled."""
import sys, glob, os
from PIL import Image, ImageDraw
files = sorted(glob.glob(os.path.join(sys.argv[1], '*.png')))
W, H = 640, 360
for k in range(0, len(files), 9):
    sheet = Image.new('RGB', (W * 3, (H + 18) * 3), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(files[k:k + 9]):
        im = Image.open(f).convert('RGB').resize((W, H))
        x, y = (i % 3) * W, (i // 3) * (H + 18)
        sheet.paste(im, (x, y + 18))
        d.text((x + 4, y + 3), os.path.basename(f), fill=(255, 255, 0))
    sheet.save(f'{sys.argv[2]}_{k // 9 + 1}.jpg', quality=82)
