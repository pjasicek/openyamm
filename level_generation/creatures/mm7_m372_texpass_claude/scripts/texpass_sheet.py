"""Before/after sheets from review-viewer shots (identical cameras): rows skin x (installed, texture pass), columns
face close-up front and 3/4, head front, head 3/4, upper body front, hands, whole body 3/4, back; close shots cropped to the subject.
Usage: texpass_sheet.py <out png> <skin>... (shots review/shots/<skin>_<before|pass>_<col>.png)"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
S = HERE / 'review' / 'shots'
out, skins = sys.argv[1], sys.argv[2:]
COLS = [('cf', (0.15, 0.0, 0.85, 0.75)), ('cq', (0.15, 0.0, 0.85, 0.75)),
        ('hf', (0.30, 0.15, 0.70, 0.75)), ('hq', (0.30, 0.15, 0.70, 0.75)), ('ub', (0.25, 0.0, 0.75, 1.0)),
        ('hands', (0.55, 0.25, 1.0, 1.0)), ('bq', (0.30, 0.05, 0.70, 0.98)), ('back', (0.30, 0.05, 0.70, 0.98))]
CELL = 320
rows = [(k, t) for k in skins for t in ('before', 'pass')]
sheet = Image.new('RGB', (len(COLS) * CELL + 130, len(rows) * CELL), (24, 26, 30))
d = ImageDraw.Draw(sheet)
for r, (k, t) in enumerate(rows):
    d.text((6, r * CELL + CELL // 2), f'm372_{k}\n{"installed" if t == "before" else "texture pass"}', fill=(235, 235, 235))
    for c, (name, box) in enumerate(COLS):
        im = Image.open(S / f'{k}_{t}_{name}.png').convert('RGB')
        w, h = im.size
        crop = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
        crop.thumbnail((CELL - 4, CELL - 4), Image.Resampling.LANCZOS)
        sheet.paste(crop, (130 + c * CELL + (CELL - crop.width) // 2, r * CELL + (CELL - crop.height) // 2))
sheet.save(out)
print('SHEET', out, sheet.size)
