"""Face close-up sheet (eyes, mouth, nose) from review-viewer shots at identical cameras: per skin a column, rows
installed / texture pass for the front and 3/4 close-up, cropped to eyes-to-chin.
Usage: closeup_sheet.py <pass tag> <out png>"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
S = HERE / 'review' / 'shots'
tag, out = sys.argv[1], sys.argv[2]
SKINS = ['aa', 'ab', 'ac', 'ba', 'bb', 'bc', 'ca', 'cb', 'cc']
ROWS = [('before', 'ff', (300, 250, 760, 690)), (tag, 'ff', (300, 250, 760, 690)),
        ('before', 'fq', (380, 250, 840, 690)), (tag, 'fq', (380, 250, 840, 690))]
CW, CH = 300, 287
sheet = Image.new('RGB', (110 + len(SKINS) * CW, 20 + len(ROWS) * CH), (24, 26, 30))
d = ImageDraw.Draw(sheet)
for c, k in enumerate(SKINS):
    d.text((110 + c * CW + 6, 4), f'm362_{k}', fill=(235, 235, 235))
for r, (t, v, box) in enumerate(ROWS):
    d.text((6, 20 + r * CH + CH // 2), f'{"installed" if t == "before" else "texture pass"}\n{v}', fill=(235, 235, 235))
    for c, k in enumerate(SKINS):
        im = Image.open(S / f'{t}_{k}_{v}.png').convert('RGB').crop(box).resize((CW, CH), Image.Resampling.LANCZOS)
        sheet.paste(im, (110 + c * CW, 20 + r * CH))
sheet.save(out)
print('SHEET', out, sheet.size)
