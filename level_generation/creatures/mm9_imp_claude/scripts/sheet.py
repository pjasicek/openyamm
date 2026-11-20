#!/usr/bin/env python3
"""Contact sheet of viewer shots. Usage: sheet.py <out png> <columns> <scale> name [name ...] (names in review/shots/)"""
import sys
from PIL import Image, ImageDraw
out, cols, sc = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
names = sys.argv[4:]
R = 'level_generation/creatures/mm9_imp_claude/review/shots/'
ims = [Image.open(R + n + '.png').convert('RGB') for n in names]
w, h = int(ims[0].width * sc), int(ims[0].height * sc)
s = Image.new('RGB', (w * cols, h * ((len(ims) + cols - 1) // cols)))
d = ImageDraw.Draw(s)
for i, (n, im) in enumerate(zip(names, ims)):
    s.paste(im.resize((w, h), Image.LANCZOS), (i % cols * w, i // cols * h))
    d.text((i % cols * w + 6, i // cols * h + 6), n, fill=(255, 255, 0))
s.save(out)
