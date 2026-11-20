"""Contact sheet of prop_compare.py renders: review/props/<name>_compare.png. Usage: prop_sheet.py <name>"""
import os, sys
from PIL import Image
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'review', 'props')
name = sys.argv[1]
rows = [r.split() for r in open(os.path.join(OUT, f'_{name}_rows.txt')).read().splitlines()]
sheet = Image.new('RGB', (400 * len(rows[0]), 400 * len(rows)))
for j, shots in enumerate(rows):
    for i, f in enumerate(shots):
        sheet.paste(Image.open(f).convert('RGB'), (i * 400, j * 400)); os.remove(f)
os.remove(os.path.join(OUT, f'_{name}_rows.txt')); sheet.save(os.path.join(OUT, f'{name}_compare.png'))
