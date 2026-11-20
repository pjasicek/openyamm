"""Compose render_frames.py tiles: python3 compose_frames.py tag [cols]"""
import json, os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tag = sys.argv[1]; cols0 = int(sys.argv[2]) if len(sys.argv) > 2 else 6
j = os.path.join(HERE, 'review', 'tmpf_%s.json' % tag)
tiles = json.load(open(j))['tiles']
ims = [Image.open(p) for _, p in tiles]; W, H = ims[0].size
n = len(tiles); cols = min(n, cols0); rows = (n + cols - 1) // cols
img = Image.new('RGB', (W * cols, H * rows), 'white'); d = ImageDraw.Draw(img)
for i, ((label, p), im) in enumerate(zip(tiles, ims)):
    img.paste(im, ((i % cols) * W, (i // cols) * H)); d.text(((i % cols) * W + 4, (i // cols) * H + 4), label, fill=(0, 0, 0))
    os.remove(p)
os.remove(j)
img.save(os.path.join(HERE, 'review', tag + '.png'))
