"""Draw work/uv_layout.json as review/uv_layout.png (regions coloured like uv_check.py)."""
import json, os, colorsys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(HERE, 'work/uv_layout.json')))
S = 2048; img = Image.new('RGB', (S, S), (25, 25, 25)); d = ImageDraw.Draw(img)
cols = [tuple(int(255 * c) for c in colorsys.hsv_to_rgb((i * 0.618) % 1, 0.6, 0.95)) for i in range(len(data['regions']))]
for r, pts in data['faces']:
    d.polygon([(u * S, (1 - v) * S) for u, v in pts], fill=cols[r], outline=(0, 0, 0))
img.save(os.path.join(HERE, 'review/uv_layout.png'))
