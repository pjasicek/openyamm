"""Contact sheet from clay_frames.py rows.json: one row per clip and view. Args: <rows.json> <out.jpg>"""
import json, sys
from PIL import Image, ImageDraw
rows = json.load(open(sys.argv[1])); ims = []
for c, row in rows:
    nv = len(row[0])
    for v in range(nv):
        ims.append((c, [Image.open(fr[v]).convert('RGB') for fr in row]))
w, h = ims[0][1][0].size; ncol = max(len(r) for _, r in ims)
S = Image.new('RGB', (w * ncol, h * len(ims)), (255, 255, 255)); d = ImageDraw.Draw(S)
for r, (c, frs) in enumerate(ims):
    for k, im in enumerate(frs):
        S.paste(im, (k * w, r * h))
    d.text((4, r * h + 4), c, fill=(0, 0, 0))
S.save(sys.argv[2], quality=85)
