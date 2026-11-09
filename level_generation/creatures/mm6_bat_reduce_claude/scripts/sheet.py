"""Contact sheet of render_regions.py views with labels. Usage: sheet.py <tag> [label ids: yes/no]"""
import json, sys
from PIL import Image, ImageDraw
tag = sys.argv[1]; L = json.load(open(f'review/horns/{tag}_labels.json')); tiles = []
for v in ['side', 'top', 'back', 'front', 'q34']:
    im = Image.open(f'review/horns/{tag}_{v}.png').convert('RGB'); dr = ImageDraw.Draw(im)
    if len(sys.argv) < 3 or sys.argv[2] != 'no':
        for r, (x, y) in L[v].items():
            if 0 < x < 1 and 0 < y < 1:
                dr.text((x * 900, (1 - y) * 900), r, fill=(0, 0, 0))
    dr.text((10, 10), v, fill=(255, 255, 255)); tiles.append(im.resize((600, 600)))
s = Image.new('RGB', (1800, 1200))
for i, t in enumerate(tiles):
    s.paste(t, ((i % 3) * 600, (i // 3) * 600))
s.save(f'review/horns/{tag}_sheet.png')
