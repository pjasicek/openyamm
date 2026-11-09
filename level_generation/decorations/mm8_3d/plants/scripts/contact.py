"""Contact sheet of the native x2 plant sprites (review/sprites_all.png)."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[5]
INV = json.load(open(ROOT / 'level_generation/decorations/mm8_3d/inventory.json'))
OUT = Path(__file__).resolve().parents[1] / 'review'
ents = sorted([e for e in INV if e['name'].startswith('plant')], key=lambda e: e['name'])
if len(sys.argv) > 1:
    ents = [e for e in ents if e['name'] in sys.argv[1:]]
cell = int(__import__("os").environ.get("CELL", 300))
cols = int(__import__("os").environ.get("COLS", 6))
rows = (len(ents) + cols - 1) // cols
sheet = Image.new('RGB', (cols * cell, rows * (cell + 20)), (96, 110, 120))
d = ImageDraw.Draw(sheet)
for i, e in enumerate(ents):
    im = Image.open(ROOT / 'assets_dev/engine/decorations_x2' / e['files'][0]).convert('RGBA')
    bb = im.getbbox()
    im = im.crop(bb)
    s = min((cell - 10) / im.width, (cell - 10) / im.height)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    x, y = (i % cols) * cell, (i // cols) * (cell + 20)
    sheet.paste(im, (x + (cell - im.width) // 2, y + 20 + cell - im.height - 5), im)
    d.text((x + 4, y + 3), f"{e['name']} {e['hint']} n{e['outdoor']} h{e['height']} w{e['width']}", fill=(255, 255, 255))
sheet.save(OUT / ('sprites_all.png' if len(sys.argv) == 1 else 'sprites_sel.png'))
