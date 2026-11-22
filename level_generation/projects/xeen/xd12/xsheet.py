#!/usr/bin/env python3
"""Contact sheets of a tour folder: xsheet.py <folder> <prefix> [per sheet]: <prefix>_s_N.jpg, 2 columns of 640x360."""
import glob
import sys
from PIL import Image, ImageDraw
folder, prefix = sys.argv[1], sys.argv[2]
per = int(sys.argv[3]) if len(sys.argv) > 3 else 8
fs = sorted(glob.glob(folder + '/*.png'))
w, h = 640, 360
for k in range(0, len(fs), per):
    part = fs[k:k + per]
    s = Image.new('RGB', (w * 2, h * ((len(part) + 1) // 2)))
    for i, f in enumerate(part):
        im = Image.open(f).convert('RGB').resize((w, h))
        ImageDraw.Draw(im).text((6, 6), f.split('/')[-1], fill=(255, 255, 0))
        s.paste(im, ((i % 2) * w, (i // 2) * h))
    s.save(f'{prefix}_s_{k // per + 1}.jpg', quality=85)
    print(f'{prefix}_s_{k // per + 1}.jpg')
