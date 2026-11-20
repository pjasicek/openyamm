"""Concept | original | run, one row per concept view of a map:  python3 source/sheet.py <map> <run> <out.jpg> [width]"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import maps  # noqa: E402

stem, run, out = sys.argv[1:4]
w = int(sys.argv[4]) if len(sys.argv) > 4 else 360
h = w * 9 // 16
concepts = sorted(maps.concepts(stem).glob('*_A.png'))
sheet = Image.new('RGB', (w * 3, h * len(concepts)))
draw = ImageDraw.Draw(sheet)
for i, concept in enumerate(concepts):
    shot = concept.name[:-6]
    for k, path in enumerate((concept, maps.original(stem) / f'{shot}.png', maps.run(stem, run) / f'{shot}.png')):
        if path.exists():
            sheet.paste(Image.open(path).convert('RGB').resize((w, h)), (k * w, i * h))
    draw.rectangle([0, i * h, 200, i * h + 13], fill=(0, 0, 0))
    draw.text((2, i * h + 1), shot, fill=(255, 255, 0))
sheet.save(out, quality=80)
