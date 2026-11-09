"""Compose the clump preview renders (preview_clump.py) into review/clump_review.png: one row per atlas and scene
(old plants_v3 grass mats, new plants_v4 clump cards; single clump, patch), columns eye level, 45 degrees, top.
Usage: python3 review_sheet.py <render dir> <out.png>"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

renders, out = Path(sys.argv[1]), Path(sys.argv[2])
VIEWS = [('eye', 'eye level, 10 deg down'), ('mid', '45 deg down'), ('top', 'straight down')]
ROWS = [('v3', 'single'), ('v4', 'single'), ('v3', 'patch'), ('v4', 'patch')]
first = Image.open(renders / 'v3_single_eye.png')
width, height = first.size
sheet = Image.new('RGB', (width * 3, (height + 20) * len(ROWS)), '#1c1c20')
draw = ImageDraw.Draw(sheet)
for row, (label, scene) in enumerate(ROWS):
    for column, (view, caption) in enumerate(VIEWS):
        y = row * (height + 20)
        sheet.paste(Image.open(renders / f'{label}_{scene}_{view}.png').convert('RGB'), (column * width, y + 20))
        name = 'old mats (plants_v3)' if label == 'v3' else 'new clump cards (plants_v4)'
        draw.text((column * width + 6, y + 4), f'{name}, {scene}, {caption}', fill='white')
sheet.save(out)
print('wrote', out)
