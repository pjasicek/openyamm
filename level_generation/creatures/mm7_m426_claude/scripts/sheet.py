"""Contact sheet from a frames.json written by a preview/render script: one labelled row per entry.
Args: <frames.json> <out.png> [scale]"""
import json, sys
from PIL import Image, ImageDraw

rows = json.load(open(sys.argv[1]))
scale = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
ims = [[Image.open(p).convert('RGB') for p in r['frames']] for r in rows]
w = max(sum(i.width for i in r) for r in ims); h = sum(max(i.height for i in r) + 18 for r in ims)
sheet = Image.new('RGB', (w, h), (40, 40, 40)); d = ImageDraw.Draw(sheet); y = 0
for r, row in zip(rows, ims):
    d.text((4, y + 3), r['label'], fill=(255, 255, 255)); y += 18; x = 0
    for i in row:
        sheet.paste(i, (x, y)); x += i.width
    y += max(i.height for i in row)
if scale != 1.0:
    sheet = sheet.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
sheet.save(sys.argv[2])
print('SHEET', sys.argv[2], sheet.size)
