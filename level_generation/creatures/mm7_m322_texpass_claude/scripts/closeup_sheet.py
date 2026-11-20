"""Close-up before/after sheet from review-viewer shots (identical cameras): rows skin x (r1 = first pass, r2 =
close-up fixes), columns eyes front, eyes 3/4, mouth, chest/strap, cropped to the subject.
Usage: closeup_sheet.py <out png> <skin>..."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
S = HERE / 'review' / 'shots'
out, skins = sys.argv[1], sys.argv[2:]
COLS = [('eyes', (300, 300, 980, 600)), ('eyesq', (300, 290, 980, 600)), ('mouth', (420, 330, 840, 530)),
        ('chest', (250, 120, 800, 560))]
W, H = 420, 260
rows = [(k, t) for k in skins for t in ('r1', 'tp')]
sheet = Image.new('RGB', (len(COLS) * W + 110, len(rows) * H), (24, 26, 30))
d = ImageDraw.Draw(sheet)
for r, (k, t) in enumerate(rows):
    d.text((6, r * H + H // 2 - 8), f'{k}\n{"pass r1" if t == "r1" else "fixes r2"}', fill=(235, 235, 235))
    for c, (name, box) in enumerate(COLS):
        crop = Image.open(S / f'cu_{k}_{t}_{name}.png').convert('RGB').crop(box)
        crop.thumbnail((W - 4, H - 4), Image.Resampling.LANCZOS)
        sheet.paste(crop, (110 + c * W + (W - crop.width) // 2, r * H + (H - crop.height) // 2))
sheet.save(out)
print('SHEET', out, sheet.size)
