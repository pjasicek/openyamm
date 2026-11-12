"""Prototype sheet: concept | now | kit for the concept view, then now | kit for the street views.

  python3 source/kit_sheet.py <map> <out.jpg> <shot>...
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import maps  # noqa: E402

stem, out, shots = sys.argv[1], sys.argv[2], sys.argv[3:]
base = maps.PROJECT / 'review/kit' / stem
w, h = 520, 293
rows = []
for shot in shots:
    name = shot.split('-', 1)[1]
    now = sorted((base / 'now').glob(f'*-{name}_*.png'))
    kit = sorted((base / 'kit').glob(f'*-{name}_*.png'))
    rows.append([maps.concepts(stem) / f'{shot}_A.png', now[0], kit[0]])
    for a, b in zip(now[1:], kit[1:]):
        rows.append([None, a, b])
sheet = Image.new('RGB', (w * 3, h * len(rows)), (30, 30, 30))
draw = ImageDraw.Draw(sheet)
for r, row in enumerate(rows):
    for k, path in enumerate(row):
        if path is not None and Path(path).exists():
            sheet.paste(Image.open(path).convert('RGB').resize((w, h)), (k * w, r * h))
for k, label in enumerate(('concept A', 'now', 'kit')):
    draw.rectangle([k * w, 0, k * w + 80, 14], fill=(0, 0, 0))
    draw.text((k * w + 3, 1), label, fill=(255, 255, 0))
sheet.save(out, quality=85)
