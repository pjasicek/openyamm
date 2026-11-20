"""Head close-up comparison sheet from review-viewer shots (identical cameras): one column per skin, rows per tag and
view, cropped to the head. Usage: head_sheet.py <out png> <tag>[,<tag>...] <view>[,<view>...] [skins]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
S = HERE / 'review' / 'shots'
out, tags, views = sys.argv[1], sys.argv[2].split(','), sys.argv[3].split(',')
skins = sys.argv[4].split(',') if len(sys.argv) > 4 else ['aa', 'ab', 'ac', 'ba', 'bb', 'bc', 'ca', 'cb', 'cc']
BOX = (330, 170, 710, 640)
CW, CH = 300, 371
rows = [(t, v) for v in views for t in tags]
sheet = Image.new('RGB', (110 + len(skins) * CW, 22 + len(rows) * CH), (24, 26, 30))
d = ImageDraw.Draw(sheet)
for c, k in enumerate(skins):
    d.text((110 + c * CW + 6, 5), f'm362_{k}', fill=(235, 235, 235))
for r, (t, v) in enumerate(rows):
    d.text((6, 22 + r * CH + CH // 2), f'{t}\n{v}', fill=(235, 235, 235))
    for c, k in enumerate(skins):
        im = Image.open(S / f'{t}_{k}_{v}.png').convert('RGB').crop(BOX).resize((CW, CH), Image.Resampling.LANCZOS)
        sheet.paste(im, (110 + c * CW, 22 + r * CH))
sheet.save(out)
print('SHEET', out, sheet.size)
