import sys, glob
from PIL import Image, ImageDraw
tag, count = sys.argv[1], int(sys.argv[2]); views = sys.argv[3].split(',') if len(sys.argv) > 3 else ['left', 'front']
rows = []
out = Image.new('RGB', (300 * count, 300 * len(views)), 'white')
for r, v in enumerate(views):
    for i in range(count):
        im = Image.open(f'review/tmp/{tag}_{i:02d}_{v}.png'); out.paste(im, (300 * i, 300 * r))
        ImageDraw.Draw(out).text((300 * i + 4, 300 * r + 4), f'{i}', fill=(0, 0, 0))
out.save(f'review/{tag}_sheet.png')
