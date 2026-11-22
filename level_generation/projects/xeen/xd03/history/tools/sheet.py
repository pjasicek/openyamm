import sys, glob
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]
fs = sorted(glob.glob(d + '/*.png'))
sel = sys.argv[3:] 
if sel: fs = [f for f in fs if any(s in f for s in sel)]
W, H = 800, 450
ims = []
for f in fs:
    im = Image.open(f).convert('RGB').resize((W, H))
    ImageDraw.Draw(im).text((8, 8), f.split('/')[-1], fill=(255, 255, 0))
    ims.append(im)
cols = 2; rows = (len(ims) + 1) // 2
sh = Image.new('RGB', (cols * W, rows * H))
for i, im in enumerate(ims): sh.paste(im, ((i % cols) * W, (i // cols) * H))
sh.save(out, quality=85)
