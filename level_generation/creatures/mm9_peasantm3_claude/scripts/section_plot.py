"""Plot section_probe.py's json: one panel per plane, segments coloured by kind, a tick along each segment's normal.
Args: <json> <out png> [half width m 0.2]"""
import sys, json
from PIL import Image, ImageDraw
d = json.load(open(sys.argv[1]))
HW = float(sys.argv[3]) if len(sys.argv) > 3 else 0.2
S = 420
COL = {'R': (150, 110, 60), 'G': (200, 60, 120), 'B': (60, 140, 255), 'A': (230, 230, 230), 'hand': (255, 190, 150),
       'head': (255, 255, 0), 'none': (120, 120, 120)}
panels = []
for name, segs in d.items():
    im = Image.new('RGB', (S, S), (20, 20, 20)); dr = ImageDraw.Draw(im)
    tr = lambda p: ((p[0] / HW * 0.5 + 0.5) * S, (0.5 - p[1] / HW * 0.5) * S)
    for s in segs:
        a, b = tr(s['p'][0]), tr(s['p'][1])
        c = COL.get(s['k'], (255, 0, 0))
        dr.line([a, b], fill=c, width=2)
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        dr.line([m, (m[0] + s['n'][0] * 6, m[1] - s['n'][1] * 6)], fill=(90, 90, 90), width=1)
    dr.text((4, 4), name, fill=(255, 255, 255))
    dr.line([(S / 2 - 4, S / 2), (S / 2 + 4, S / 2)], fill=(0, 255, 0)); dr.line([(S / 2, S / 2 - 4), (S / 2, S / 2 + 4)], fill=(0, 255, 0))
    panels.append(im)
cols = 4
rows = (len(panels) + cols - 1) // cols
sheet = Image.new('RGB', (cols * S, rows * S), (0, 0, 0))
for i, p in enumerate(panels):
    sheet.paste(p, ((i % cols) * S, (i // cols) * S))
sheet.save(sys.argv[2])
