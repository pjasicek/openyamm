"""Stack the same crop of concept, original and a run:
  python3 source/crops.py [--map <stem>] <run> <shot> x0 y0 x1 y1 <out.png>"""
import sys
from pathlib import Path

from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'source'))
from astra_review import concept_of  # noqa: E402
import maps  # noqa: E402

args = sys.argv[1:]
stem = 'oute3'
if '--map' in args:
    stem = args.pop(args.index('--map') + 1)
    args.remove('--map')
run, shot = args[0], args[1]
box = tuple(int(v) for v in args[2:6])
paths = [concept_of(shot, stem), maps.original(stem) / f'{shot}.png', maps.run(stem, run) / f'{shot}.png']
crops = [Image.open(p).convert('RGB').resize((1600, 900)).crop(box) for p in paths if p and p.exists()]
w, h = crops[0].size
sheet = Image.new('RGB', (w, (h + 4) * len(crops)))
for i, c in enumerate(crops):
    sheet.paste(c, (0, i * (h + 4)))
sheet.save(args[6])
