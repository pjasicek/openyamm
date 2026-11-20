#!/usr/bin/env python3
"""Pair MM9 pose renders and ours (pose_frames.py outputs) into one sheet: per clip one row of MM9 frames above
one row of ours. Usage: compare_sheet.py out.png mm9_dir ours_dir view n role=mm9clip [...]"""
import sys
from PIL import Image, ImageDraw
out, mdir, odir, view, n = sys.argv[1:6]
pairs = [a.split('=') for a in sys.argv[6:]]
n = int(n)
ims = []
for role, clip in pairs:
    for d, c in ((mdir, clip), (odir, role)):
        ims.append([Image.open(f'{d}/{c}_{view}_{k:02d}.png').convert('RGB') for k in range(n)])
w, h = ims[0][0].size
sheet = Image.new('RGB', (w * n + 110, h * len(ims)), (40, 40, 46))
dr = ImageDraw.Draw(sheet)
for r, row in enumerate(ims):
    for k, im in enumerate(row):
        sheet.paste(im, (110 + k * w, r * h))
    role, clip = pairs[r // 2]
    dr.text((4, r * h + h // 2), ('MM9 ' + clip) if r % 2 == 0 else ('ours ' + role), fill=(255, 255, 255))
sheet.save(out)
