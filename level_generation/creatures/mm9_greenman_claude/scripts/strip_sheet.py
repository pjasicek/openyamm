"""Assemble _strip_tmp/list.json renders into one labelled sheet. Args: <tmp dir> <out png> <cols>"""
import sys, json
from PIL import Image, ImageDraw
d, out, cols = sys.argv[1], sys.argv[2], int(sys.argv[3])
files = json.load(open(d + '/list.json'))
ims = [(l, Image.open(p).convert('RGB')) for l, p in files]
w, h = ims[0][1].size; rows = (len(ims) + cols - 1) // cols
s = Image.new('RGB', (cols * w, rows * h), (90, 90, 90)); dr = ImageDraw.Draw(s)
for k, (l, im) in enumerate(ims):
    x, y = (k % cols) * w, (k // cols) * h; s.paste(im, (x, y)); dr.text((x + 6, y + 6), l, fill=(255, 255, 0))
s.save(out); print('SHEET', out, s.size)
