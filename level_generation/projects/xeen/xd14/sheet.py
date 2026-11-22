import sys, os
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; names = sorted(os.listdir(d))[int(sys.argv[3]):int(sys.argv[4])]
cells = []
for n in names:
    im = Image.open(os.path.join(d, n)).convert('RGB'); im.thumbnail((560, 400))
    c = Image.new('RGB', (564, im.size[1] + 22), (30, 30, 30)); c.paste(im, (2, 2))
    ImageDraw.Draw(c).text((4, im.size[1] + 6), n, fill=(255, 255, 0)); cells.append(c)
cols = 3; rows = (len(cells) + cols - 1) // cols; h = max(c.size[1] for c in cells)
S = Image.new('RGB', (cols * 564, rows * h), (0, 0, 0))
for i, c in enumerate(cells): S.paste(c, ((i % cols) * 564, (i // cols) * h))
S.save(out, quality=85)
