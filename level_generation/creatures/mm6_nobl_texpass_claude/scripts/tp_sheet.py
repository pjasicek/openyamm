"""Before/after sheet of review-viewer shots (texpass_viewer_shots.py shots, model ids <tier>_<tag>): rows = shots,
columns = tier x (before tag, after tag), each shot cropped to its central crop box.
Usage: tp_sheet.py <out png> <shots dir> <tier,...> <before tag> <after tag> <name[=x0,y0,x1,y1],...> [cell px]"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

out, folder, tiers, tb, ta, names = sys.argv[1:7]
cell = int(sys.argv[7]) if len(sys.argv) > 7 else 380
folder = Path(folder)
specs = []
for item in names.split(','):
    name, _, box = item.partition('=')
    specs.append((name, tuple(float(v) for v in box.split(';')) if box else (0.0, 0.03, 1.0, 0.93)))
tiers = tiers.split(',')
sheet = Image.new('RGB', (cell * 2 * len(tiers), (cell + 18) * len(specs)), (24, 26, 30))
draw = ImageDraw.Draw(sheet)
for r, (name, box) in enumerate(specs):
    for t, tier in enumerate(tiers):
        for k, tag in enumerate((tb, ta)):
            im = Image.open(folder / f'{tier}_{tag}_{name}.png').convert('RGB')
            w, h = im.size
            crop = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
            crop.thumbnail((cell - 4, cell - 4), Image.Resampling.LANCZOS)
            x, y = (t * 2 + k) * cell, r * (cell + 18)
            sheet.paste(crop, (x + (cell - crop.width) // 2, y + 18))
            draw.text((x + 4, y + 3), f'{tier} {name} {"installed" if k == 0 else "texture pass"}',
                      fill=(235, 235, 235))
sheet.save(out)
print('SHEET', out, sheet.size)
