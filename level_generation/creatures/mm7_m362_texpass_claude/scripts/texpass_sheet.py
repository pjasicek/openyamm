"""Before/after sheet from review-viewer shots (identical cameras): rows skin x (installed, texture pass), columns
face front, 3/4 and right (close-up), head front and 3/4, shoulders 3/4, whole body 3/4 and back; cropped to the
subject.
Usage: texpass_sheet.py <pass tag> <out png> <skin>[,<skin>...]"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
S = HERE / 'review' / 'shots'
tag, out, skins = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
COLS = [('ff', (0.24, 0.08, 0.78, 0.92)), ('fq', (0.20, 0.08, 0.74, 0.92)), ('fr', (0.24, 0.08, 0.78, 0.92)),
        ('hf', (0.32, 0.22, 0.68, 0.84)), ('hq', (0.32, 0.22, 0.68, 0.84)), ('sq', (0.22, 0.10, 0.78, 0.98)),
        ('bq', (0.28, 0.0, 0.72, 1.0)),
        ('bk', (0.28, 0.0, 0.72, 1.0))]
CELL = 330
rows = [(k, t) for k in skins for t in ('before', tag)]
sheet = Image.new('RGB', (len(COLS) * CELL + 130, len(rows) * CELL), (24, 26, 30))
d = ImageDraw.Draw(sheet)
for r, (k, t) in enumerate(rows):
    d.text((6, r * CELL + CELL // 2), f'm362_{k}\n{"installed" if t == "before" else "texture pass"}',
           fill=(235, 235, 235))
    for c, (name, box) in enumerate(COLS):
        im = Image.open(S / f'{t}_{k}_{name}.png').convert('RGB')
        w, h = im.size
        crop = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
        crop.thumbnail((CELL - 4, CELL - 4), Image.Resampling.LANCZOS)
        sheet.paste(crop, (130 + c * CELL + (CELL - crop.width) // 2, r * CELL + (CELL - crop.height) // 2))
sheet.save(out)
print('SHEET', out, sheet.size)
