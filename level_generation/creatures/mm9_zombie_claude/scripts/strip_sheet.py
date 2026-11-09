import sys, glob
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]
clips = sys.argv[3].split(',')
n = int(sys.argv[4]) if len(sys.argv) > 4 else 8
sz = int(sys.argv[5]) if len(sys.argv) > 5 else 200
s = Image.new('RGB', (n * sz, len(clips) * sz), (40, 40, 40)); dr = ImageDraw.Draw(s)
for r, c in enumerate(clips):
    for k in range(n):
        s.paste(Image.open(f'{d}/{c}_{k:02d}.png').convert('RGB').resize((sz, sz)), (k * sz, r * sz))
    dr.text((4, r * sz + 4), c, fill=(255, 255, 0))
s.save(out)
