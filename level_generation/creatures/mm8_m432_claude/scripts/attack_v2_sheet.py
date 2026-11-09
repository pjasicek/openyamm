"""Contact sheet of attack_v2_render.py output: attack_v2_sheet.py <dir> <out.png> <view,...> [scale]."""
import sys, glob, os
from PIL import Image, ImageDraw
d, out, views = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
s = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
files = sorted(glob.glob(os.path.join(d, '*.png')))
keys = sorted({os.path.basename(f).rsplit('_', 1)[0] for f in files})
im0 = Image.open(files[0]); w, h = int(im0.width * s), int(im0.height * s)
sheet = Image.new('RGB', (w * len(keys), h * len(views)), 'white')
for c, k in enumerate(keys):
    for r, v in enumerate(views):
        p = os.path.join(d, f'{k}_{v}.png')
        if os.path.exists(p):
            sheet.paste(Image.open(p).convert('RGB').resize((w, h)), (c * w, r * h))
        ImageDraw.Draw(sheet).text((c * w + 4, r * h + 4), f'{k} {v}', fill=(255, 255, 0))
sheet.save(out); print(out, sheet.size)
