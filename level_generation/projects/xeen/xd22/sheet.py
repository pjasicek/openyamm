import sys, glob
from PIL import Image, ImageDraw
files = sorted(glob.glob(sys.argv[1] + '/*.png'))
start, count = int(sys.argv[3]), int(sys.argv[4])
files = files[start:start + count]
w, h = 480, 270
cols = 3
rows = (len(files) + cols - 1) // cols
sheet = Image.new('RGB', (cols * w, rows * (h + 18)), (0, 0, 0))
for i, f in enumerate(files):
    im = Image.open(f).convert('RGB').resize((w, h))
    x, y = (i % cols) * w, (i // cols) * (h + 18)
    sheet.paste(im, (x, y + 18))
    ImageDraw.Draw(sheet).text((x + 4, y + 2), f.split('/')[-1], fill=(255, 255, 0))
sheet.save(sys.argv[2], quality=85)
