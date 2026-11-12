#!/usr/bin/env python3
"""One strip of viewer shots (tools/run_creature_review.py shots), a fixed crop around the body:
shots_strip.py <out.png> <shot.png ...>"""
import sys

from PIL import Image

ims = [Image.open(p).convert('RGB') for p in sys.argv[2:]]
w, h = ims[0].size
box = (int(w * 0.36), int(h * 0.38), int(w * 0.64), int(h * 0.88))
cw = box[2] - box[0]
out = Image.new('RGB', (cw * len(ims), box[3] - box[1]))
for i, im in enumerate(ims):
    out.paste(im.crop(box), (i * cw, 0))
out.save(sys.argv[1])
print(sys.argv[1], out.size)
