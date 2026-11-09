"""Before/after sheets from review-viewer shots (identical cameras): rows skin x (installed, texture pass), columns
head front, head 3/4, head left, chest front, body 3/4, upper back 3/4; close shots cropped to the subject.
Usage: texpass_sheet.py <out png> <skin>... (e.g. m322_a1 m322_a2)"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
S = HERE / 'review' / 'shots'
out, skins = sys.argv[1], sys.argv[2:]
COLS = [('hf', (0.18, 0.05, 0.82, 0.98)), ('hq', (0.18, 0.05, 0.82, 0.98)), ('hl', (0.18, 0.05, 0.82, 0.98)),
        ('ch', (0.18, 0.02, 0.82, 0.98)), ('bq', (0.30, 0.02, 0.70, 0.98)), ('bk', (0.18, 0.02, 0.82, 0.98))]
CELL = 330
rows = [(k, t) for k in skins for t in ('before', 'tp')]
sheet = Image.new('RGB', (len(COLS) * CELL + 130, len(rows) * CELL), (24, 26, 30))
d = ImageDraw.Draw(sheet)
for r, (k, t) in enumerate(rows):
    d.text((6, r * CELL + CELL // 2 - 8), f'{k}\n{"installed" if t == "before" else "texture pass"}', fill=(235, 235, 235))
    for c, (name, box) in enumerate(COLS):
        im = Image.open(S / f'{k}_{t}_{name}.png').convert('RGB')
        w, h = im.size
        crop = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h * 0.93)))
        crop.thumbnail((CELL - 4, CELL - 4), Image.Resampling.LANCZOS)
        sheet.paste(crop, (130 + c * CELL + (CELL - crop.width) // 2, r * CELL + (CELL - crop.height) // 2))
sheet.save(out)
print('SHEET', out, sheet.size)
