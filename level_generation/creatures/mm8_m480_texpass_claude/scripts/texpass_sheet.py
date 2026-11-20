"""Before/after sheet from review-viewer shots (identical cameras): rows tier x (installed, texture pass), columns
head front, head 3/4, upper back, belly and hand, whole body 3/4; close shots cropped to the subject.
Usage: texpass_sheet.py <world prefix m480|m461> <out png>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
S = HERE / 'review' / 'shots'
world, out = sys.argv[1], sys.argv[2]
COLS = [('hf', (0.30, 0.28, 0.70, 0.98)), ('hq', (0.30, 0.28, 0.70, 0.98)), ('sb', (0.38, 0.40, 0.62, 0.92)),
        ('hands', (0.35, 0.25, 0.75, 0.90)), ('bq', (0.30, 0.10, 0.70, 0.98))]
CELL = 360
rows = [(k, t) for k in 'abc' for t in ('before', 's4')]
sheet = Image.new('RGB', (len(COLS) * CELL + 150, len(rows) * CELL), (24, 26, 30))
d = ImageDraw.Draw(sheet)
for r, (k, t) in enumerate(rows):
    d.text((6, r * CELL + CELL // 2), f'{world} {k.upper()}\n{"installed" if t == "before" else "texture pass"}',
           fill=(235, 235, 235))
    for c, (name, box) in enumerate(COLS):
        im = Image.open(S / f'{world}_{k}_{t}_{name}.png').convert('RGB')
        w, h = im.size
        crop = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
        crop.thumbnail((CELL - 4, CELL - 4), Image.Resampling.LANCZOS)
        sheet.paste(crop, (150 + c * CELL + (CELL - crop.width) // 2, r * CELL + (CELL - crop.height) // 2))
sheet.save(out)
print('SHEET', out, sheet.size)
