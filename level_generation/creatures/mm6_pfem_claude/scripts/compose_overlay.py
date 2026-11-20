import sys
from PIL import Image, ImageChops, ImageFilter
tag = sys.argv[1]
row = []
for v in ('front', 'left', 'back', 'right'):
    m = Image.open(f'review/fit_{tag}_meshy_{v}.png').convert('RGBA')
    b = Image.open(f'review/fit_{tag}_body_{v}.png').convert('RGBA')
    bg = Image.new('RGBA', m.size, (235, 235, 230, 255))
    base = Image.alpha_composite(bg, m)
    a = b.split()[3].point(lambda x: 255 if x > 128 else 0)
    edge = ImageChops.subtract(a.filter(ImageFilter.MaxFilter(3)), a.filter(ImageFilter.MinFilter(3)))
    tint = Image.new('RGBA', m.size, (40, 90, 255, 70))
    base = Image.composite(Image.alpha_composite(base, tint), base, a)
    red = Image.new('RGBA', m.size, (230, 20, 20, 255))
    base = Image.composite(red, base, edge)
    row.append(base)
out = Image.new('RGB', (sum(i.width for i in row), row[0].height))
x = 0
for i in row:
    out.paste(i, (x, 0)); x += i.width
out.save(f'review/fit_{tag}_overlay.png')
