import json, sys, os
from PIL import Image, ImageDraw
here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tiles = json.load(open(os.path.join(here, 'work', '_sheet.json')))
out = sys.argv[1]
W, H = 360, 300
S = Image.new('RGB', (W * len(tiles[0][1]) + 90, H * len(tiles)), (255, 255, 255))
d = ImageDraw.Draw(S)
for r, (name, row) in enumerate(tiles):
    d.text((4, r * H + 140), name, fill=(0, 0, 0))
    for c, p in enumerate(row):
        S.paste(Image.open(p), (90 + c * W, r * H)); os.remove(p)
S.save(os.path.join(here, 'review', out))
