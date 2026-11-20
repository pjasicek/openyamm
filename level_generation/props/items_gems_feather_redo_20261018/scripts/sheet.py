"""Icon beside the three review views, one row per item: python3 sheet.py <tag>."""
import sys
from pathlib import Path
from PIL import Image
PROJECT = Path(__file__).resolve().parents[1]
tag = sys.argv[1]
icons = ['7item146', '7item154', '7item264', 'quill']
sheet = Image.new('RGB', (4 * 300, len(icons) * 300), (36, 38, 44))
for row, icon in enumerate(icons):
    image = Image.open(PROJECT / f'references/icon_{icon}.png').convert('RGBA')
    scale = min(280 / image.width, 280 / image.height)
    image = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    sheet.paste(image, (10, row * 300 + 10), image)
    for col, view in enumerate(['above', 'three_quarter', 'low']):
        path = PROJECT / f'review/{tag}/{icon}_{view}.png'
        if path.exists():
            render = Image.open(path).convert('RGBA').resize((290, 290))
            sheet.paste(render, ((col + 1) * 300, row * 300 + 5), render)
sheet.save(PROJECT / f'review/{tag}_sheet.png')
