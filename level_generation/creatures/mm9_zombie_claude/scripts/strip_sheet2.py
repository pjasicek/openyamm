import sys
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; clips = sys.argv[3].split(','); n = 8; w, h = 290, 300
s = Image.new('RGB', (n * w, len(clips) * h), (40, 40, 40)); dr = ImageDraw.Draw(s)
for r, c in enumerate(clips):
    for k in range(n):
        im = Image.open(f'{d}/st_{c}_{k:02d}.png').convert('RGB').crop((270, 0, 800, 548)).resize((w, h))
        s.paste(im, (k * w, r * h))
    dr.text((4, r * h + 4), c, fill=(255, 255, 0))
s.save(out)
