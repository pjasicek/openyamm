"""Before/after sheet from review-viewer shots (identical cameras): rows skin x (installed, texture pass), columns head
front, head 3/4, head left, head back, shoulders front, whole body 3/4; head shots cropped to the face.
Usage: texpass_sheet.py <outfit a|b|c> <out png>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
S = HERE / 'review' / 'shots'
outfit, out = sys.argv[1], sys.argv[2]
COLS = [('hf', (0.30, 0.22, 0.70, 0.92)), ('hq', (0.30, 0.22, 0.70, 0.92)), ('hl', (0.25, 0.10, 0.75, 0.95)),
        ('hb', (0.20, 0.10, 0.80, 0.98)), ('sf', (0.25, 0.0, 0.75, 1.0)), ('bq', (0.25, 0.0, 0.75, 1.0))]
CELL = 340
rows = [(f'{outfit}{t}', tag) for t in 'abc' for tag in ('before', 'tp')]
sheet = Image.new('RGB', (len(COLS) * CELL + 130, len(rows) * CELL), (24, 26, 30))
d = ImageDraw.Draw(sheet)
for r, (skin, tag) in enumerate(rows):
    d.text((6, r * CELL + CELL // 2 - 8), f'm342_{skin}\n{"installed" if tag == "before" else "texture pass"}',
           fill=(235, 235, 235))
    for c, (name, box) in enumerate(COLS):
        im = Image.open(S / f'{skin}_{tag}_{name}.png').convert('RGB')
        w, h = im.size
        crop = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
        crop.thumbnail((CELL - 4, CELL - 4), Image.Resampling.LANCZOS)
        sheet.paste(crop, (130 + c * CELL + (CELL - crop.width) // 2, r * CELL + (CELL - crop.height) // 2))
sheet.save(out)
print('SHEET', out, sheet.size)
