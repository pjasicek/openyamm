"""Icon / above / three-quarter / low rows for the given icons -> review/<name>.png"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parents[1]
name, icons = sys.argv[1], sys.argv[2:]
cell = 240
sheet = Image.new('RGB', (4 * cell, len(icons) * cell), (34, 37, 44))
draw = ImageDraw.Draw(sheet)
for row, icon in enumerate(icons):
    image = Image.open(HERE / 'references' / f'icon_{icon}.png').convert('RGBA')
    image.thumbnail((cell - 20, cell - 20))
    sheet.paste(image, (10, row * cell + 10), image)
    for col, view in enumerate(['above', 'three_quarter', 'low']):
        render = Image.open(HERE / 'review' / f'{icon}_{view}.png').convert('RGBA').resize((cell, cell))
        sheet.paste(render, ((col + 1) * cell, row * cell), render)
    draw.text((4, row * cell + 2), icon, fill=(230, 230, 230))
sheet.save(HERE / 'review' / f'{name}.png')
