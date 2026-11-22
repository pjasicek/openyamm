"""Join a clip_sheet.py folder (frames.json) into one labelled PNG. Args: <dir> <out png> [scale]"""
import json, sys
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; sc = float(sys.argv[3]) if len(sys.argv) > 3 else 0.6
rows = json.load(open(f'{d}/frames.json'))
ims = [[Image.open(p) for p, _ in r] for r in rows]
w, h = ims[0][0].size; w2, h2 = int(w * sc), int(h * sc)
S = Image.new('RGB', (w2 * max(len(r) for r in ims), h2 * len(ims)), (200, 200, 200)); D = ImageDraw.Draw(S)
for y, (r, lab) in enumerate(zip(ims, rows)):
    for x, (im, (_, t)) in enumerate(zip(r, lab)):
        S.paste(im.resize((w2, h2)), (x * w2, y * h2)); D.text((x * w2 + 3, y * h2 + 3), t, fill=(0, 0, 0))
S.save(out)
