"""Icon beside its three review views, one row per icon -> review/<name>.png"""
import sys
from pathlib import Path
from PIL import Image
P = Path(__file__).resolve().parents[1]
name, icons = sys.argv[1], sys.argv[2:]
W = 300
sheet = Image.new('RGB', (4 * W, W * len(icons)), (40, 42, 46))
for row, icon in enumerate(icons):
    image = Image.open(P / f'references/icon_{icon}.png').convert('RGBA')
    image.thumbnail((W - 20, W - 20))
    sheet.paste(image, (10, row * W + 10), image)
    for col, view in enumerate(['above', 'three_quarter', 'low']):
        render = Image.open(P / f'review/{icon}_{view}.png').convert('RGBA').resize((W, W))
        sheet.paste(render, ((col + 1) * W, row * W), render)
sheet.save(P / f'review/{name}.png')
