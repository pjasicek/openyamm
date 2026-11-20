"""Before | after sheet from review-viewer shots at identical cameras: rows tier x (before, after), columns the given
shot names, each cropped by a fractional box.
Usage: pair_sheet.py <out png> <after tag[,tag...]> [before=<tag>] <name>:<x0,y0,x1,y1> ... (before tag default 'before')"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
S = HERE / 'review' / 'shots'
out, tag = sys.argv[1], sys.argv[2]
rest = sys.argv[3:]
before = 'before'
if rest and rest[0].startswith('before='):
    before = rest.pop(0).split('=', 1)[1]
cols = [(a.split(':')[0], tuple(float(x) for x in a.split(':')[1].split(','))) for a in rest]
CELL = 400
rows = [(k, tt) for k in 'abc' for tt in (before, *tag.split(','))]
sheet = Image.new('RGB', (len(cols) * CELL + 130, len(rows) * CELL), (24, 26, 30))
d = ImageDraw.Draw(sheet)
names = {'a': 'A Sorcerer', 'b': 'B Wizard', 'c': 'C Archmage'}
for r, (k, tt) in enumerate(rows):
    d.text((6, r * CELL + CELL // 2), f'{names[k]}\n{tt}', fill=(235, 235, 235))
    for c, (name, box) in enumerate(cols):
        im = Image.open(S / f'm274_{k}_{tt}_{name}.png').convert('RGB')
        w, h = im.size
        crop = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
        crop.thumbnail((CELL - 4, CELL - 4), Image.Resampling.LANCZOS)
        sheet.paste(crop, (130 + c * CELL + (CELL - crop.width) // 2, r * CELL + (CELL - crop.height) // 2))
sheet.save(out)
print('SHEET', out, sheet.size)
