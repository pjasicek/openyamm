"""Compose review/tmp_sheet.json renders into one image per action: rows = views, columns = frames."""
import json, os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = json.load(open(os.path.join(HERE, 'review/tmp_sheet.json')))
out = sys.argv[1]
acts = []
for n, v, i, f, p in rows:
    if n not in acts:
        acts.append(n)
for n in acts:
    rs = [r for r in rows if r[0] == n]
    views = sorted({r[1] for r in rs}, reverse=True); N = max(r[2] for r in rs) + 1
    W, H = 240, 320
    img = Image.new('RGB', (W * N, H * len(views)), 'white'); d = ImageDraw.Draw(img)
    for _, v, i, f, p in rs:
        img.paste(Image.open(p), (i * W, views.index(v) * H))
        d.text((i * W + 4, views.index(v) * H + 4), '%s f%d' % (n, f), fill=(0, 0, 0))
        os.remove(p)
    img.save(os.path.join(HERE, 'review', '%s_%s.png' % (out, n)))
