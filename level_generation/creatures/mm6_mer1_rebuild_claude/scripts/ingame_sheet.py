#!/usr/bin/env python3
"""Contact sheet of in-game captures: <out png> <png> ... (each tile labelled with its file name, 3 per row, 640 wide)"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
out, files = sys.argv[1], sys.argv[2:]
ims = [Image.open(f).convert('RGB') for f in files]
W = 640; ims = [i.resize((W, int(i.height * W / i.width))) for i in ims]; H = max(i.height for i in ims)
cols = 3; rows = (len(ims) + cols - 1) // cols
sheet = Image.new('RGB', (W * cols, (H + 20) * rows), (20, 20, 24)); d = ImageDraw.Draw(sheet)
for k, (f, im) in enumerate(zip(files, ims)):
    x, y = (k % cols) * W, (k // cols) * (H + 20)
    sheet.paste(im, (x, y + 20)); d.text((x + 6, y + 4), Path(f).parent.name + '/' + Path(f).stem, fill=(255, 255, 0))
sheet.save(out); print('SHEET', out, sheet.size)
