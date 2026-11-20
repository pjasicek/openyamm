"""Grid montage: montage.py out.png cols label1=img1 label2=img2 ... (labels drawn top-left; '-' skips a cell)"""
import sys
from PIL import Image, ImageDraw
out, cols = sys.argv[1], int(sys.argv[2])
items = [a.split('=', 1) if '=' in a else ('', a) for a in sys.argv[3:]]
ims = [Image.open(p).convert('RGB') if p != '-' else None for _, p in items]
w = max(i.width for i in ims if i); h = max(i.height for i in ims if i)
rows = (len(ims) + cols - 1) // cols
S = Image.new('RGB', (cols * w, rows * h), (40, 40, 40)); d = ImageDraw.Draw(S)
for k, (im, (lab, _)) in enumerate(zip(ims, items)):
    x, y = (k % cols) * w, (k // cols) * h
    if im: S.paste(im, (x, y))
    d.rectangle([x, y, x + 8 * len(lab) + 6, y + 14], fill=(0, 0, 0)); d.text((x + 3, y + 2), lab, fill=(255, 255, 0))
S.save(out); print('MONTAGE', out, S.size)
