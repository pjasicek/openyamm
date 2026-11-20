import sys
from PIL import Image, ImageDraw
l = [x.split('\t') for x in open(sys.argv[1] + '.list').read().splitlines()]
w = Image.open(l[0][1]).size[0]
n = len(l[0]) - 1
s = Image.new('RGB', (w * n, w * len(l)))
for r, row in enumerate(l):
    for c, f in enumerate(row[1:]):
        s.paste(Image.open(f).convert('RGB'), (c * w, r * w))
    ImageDraw.Draw(s).text((4, r * w + 4), row[0], fill=(255, 255, 0))
s.save(sys.argv[1])
