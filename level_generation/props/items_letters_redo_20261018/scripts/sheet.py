"""Icon | above | three-quarter | low per icon -> review/<name>.png. Usage: python3 sheet.py <name> <icon ...>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
P = Path(__file__).resolve().parents[1]
name, icons = sys.argv[1], sys.argv[2:]
S = 256
sheet = Image.new('RGB', (4 * S, len(icons) * S), (34, 36, 42))
draw = ImageDraw.Draw(sheet)
for row, icon in enumerate(icons):
    path = P / 'references/icons' / f'{icon}.png'
    if not path.exists():
        path = P.parents[2] / 'assets_dev/engine/icons_x2' / f'{icon}.png'
    image = Image.open(path).convert('RGBA')
    image.thumbnail((S - 20, S - 30))
    sheet.paste(image, (10, row * S + 20), image)
    draw.text((4, row * S + 2), icon, fill=(230, 230, 230))
    for column, view in enumerate(('above', 'three_quarter', 'low'), 1):
        render = Image.open(P / 'review/renders' / f'{icon}_{view}.png').convert('RGBA').resize((S, S))
        sheet.paste(render, (column * S, row * S), render)
sheet.save(P / 'review' / f'{name}.png')
