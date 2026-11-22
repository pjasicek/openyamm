import sys, glob
from PIL import Image, ImageDraw
fs = sorted(glob.glob(sys.argv[1] + '/*.png'))
lo = int(sys.argv[3]) if len(sys.argv) > 3 else 0
hi = int(sys.argv[4]) if len(sys.argv) > 4 else len(fs)
fs = fs[lo:hi]
ims = []
for f in fs:
    im = Image.open(f).convert('RGB').resize((640, 360))
    ImageDraw.Draw(im).text((8, 340), f.split('/')[-1], fill=(255, 255, 0))
    ims.append(im)
W = 2; H = (len(ims) + 1) // 2
sheet = Image.new('RGB', (W * 640, H * 360))
for i, im in enumerate(ims):
    sheet.paste(im, ((i % W) * 640, (i // W) * 360))
sheet.save(sys.argv[2], quality=88)
