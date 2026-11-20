"""Compose key_shots.py renders: columns = frames, rows = views. Args: <out png>"""
import json, sys
from PIL import Image, ImageDraw
out = sys.argv[1]; cols = json.load(open(out[:-4] + '.json'))
W, H = Image.open(cols[0][0][0]).size
sheet = Image.new('RGB', (W * len(cols), H * len(cols[0])), (200, 200, 200)); d = ImageDraw.Draw(sheet)
for c, col in enumerate(cols):
    for r, (p, label) in enumerate(col):
        sheet.paste(Image.open(p).convert('RGB'), (c * W, r * H)); d.text((c * W + 6, r * H + 6), label, fill=(0, 0, 0))
sheet.save(out)
