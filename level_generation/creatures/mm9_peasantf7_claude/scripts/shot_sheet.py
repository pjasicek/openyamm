"""Sheet of viewer shots: args <out png> <tile px> <crop: full|face> <png> [png...] (labels = file stems)"""
import sys
from PIL import Image, ImageDraw
out, px, mode = sys.argv[1], int(sys.argv[2]), sys.argv[3]; fs = sys.argv[4:]
S = Image.new('RGB', (px * len(fs), px + 18), (28, 28, 28)); d = ImageDraw.Draw(S)
for k, f in enumerate(fs):
    im = Image.open(f).convert('RGB'); w, h = im.size; c = min(w, h)
    im = im.crop(((w - c) // 2, (h - c) // 2, (w - c) // 2 + c, (h - c) // 2 + c)) if mode == 'face' else im
    im.thumbnail((px, px)); S.paste(im, (k * px + (px - im.width) // 2, 18)); d.text((k * px + 4, 3), f.split('/')[-1][:-4], fill=(255, 255, 0))
S.save(out); print('SHEET', out)
