"""Eye sheet from review-viewer shots (identical cameras): rows skin x (r2, r3), columns eyes front, eyes 3/4 and eyes
side in Standing, eyes front and 3/4 in Fidget (0 s), cropped to the eyes.
Usage: eye_sheet.py <out png> <skin>..."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
S = HERE / 'review' / 'shots'
out, skins = sys.argv[1], sys.argv[2:]
COLS = [('eyes', (250, 250, 1000, 560)), ('eyesq', (250, 250, 1000, 560)), ('eyesl', (250, 250, 1000, 560)),
        ('feyes', (250, 250, 1000, 560)), ('feyesq', (250, 250, 1000, 560))]
W, H = 340, 160
rows = [(k, t) for k in skins for t in ('r2', 'r3')]
sheet = Image.new('RGB', (len(COLS) * W + 90, len(rows) * H), (24, 26, 30))
d = ImageDraw.Draw(sheet)
for r, (k, t) in enumerate(rows):
    d.text((6, r * H + H // 2 - 8), f'{k}\n{t}', fill=(235, 235, 235))
    for c, (name, box) in enumerate(COLS):
        crop = Image.open(S / f'ey_{k}_{t}_{name}.png').convert('RGB').crop(box)
        crop.thumbnail((W - 4, H - 4), Image.Resampling.LANCZOS)
        sheet.paste(crop, (90 + c * W + (W - crop.width) // 2, r * H + (H - crop.height) // 2))
sheet.save(out)
print('SHEET', out, sheet.size)
