"""Rows of mouth_views.py renders: mouth_sheet.py <out.png> <prefix> ... (one row per prefix, labelled)."""
import sys
from PIL import Image, ImageDraw
out, prefixes = sys.argv[1], sys.argv[2:]; V = ['front', 'q34', 'below', 'left']; S = 450
s = Image.new('RGB', (S * len(V), S * len(prefixes))); d = ImageDraw.Draw(s)
for j, p in enumerate(prefixes):
    for i, v in enumerate(V):
        s.paste(Image.open(f'{p}_{v}.png').convert('RGB').resize((S, S)), (i * S, j * S))
    d.text((8, j * S + 8), p.split('/')[-1], fill=(255, 255, 120))
s.save(out)
