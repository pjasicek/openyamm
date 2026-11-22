import sys, glob
from PIL import Image, ImageDraw
src, out = sys.argv[1], sys.argv[2]
fs = sorted(glob.glob(src + '/*.png'))
w, h = 640, 360
for k in range(0, len(fs), 4):
    s = Image.new('RGB', (w * 2, h * 2))
    for i, f in enumerate(fs[k:k + 4]):
        im = Image.open(f).convert('RGB').resize((w, h))
        ImageDraw.Draw(im).text((6, 6), f.split('/')[-1], fill=(255, 255, 0))
        s.paste(im, ((i % 2) * w, (i // 2) * h))
    s.save(f'{out}_{k // 4 + 1}.jpg', quality=85)
print((len(fs) + 3) // 4)
