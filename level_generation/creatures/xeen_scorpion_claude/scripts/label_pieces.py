"""Draw piece numbers onto the coloured piece renders (work/pieces_labels.json from prep.py)."""
import json, os
from PIL import Image, ImageDraw
here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path, lst in json.load(open(os.path.join(here, 'work', 'pieces_labels.json'))).items():
    im = Image.open(path).convert('RGB'); d = ImageDraw.Draw(im); W, H = im.size
    for r, x, y, z in lst:
        d.text((x * W - 6, y * H - 6), str(r), fill=(0, 0, 0)); d.text((x * W - 7, y * H - 7), str(r), fill=(255, 255, 255))
    im.save(path)
