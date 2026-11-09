"""Join render_pose.py tiles into <out> (system python with PIL). Args: <out.png>"""
import json, os, sys
from PIL import Image
out = sys.argv[1]; d = json.load(open(out + '.json'))
r = d['res']; sheet = Image.new('RGB', (d['cols'] * r, d['rows'] * r))
for si, vi, f in d['tiles']:
    sheet.paste(Image.open(f).convert('RGB'), (vi * r, si * r)); os.remove(f)
if os.environ.get('GRID') and os.environ.get('FIXED'):
    from PIL import ImageDraw
    cx, cy, cz, size = [float(x) for x in os.environ['FIXED'].split(',')]
    dr = ImageDraw.Draw(sheet)
    for row in range(d['rows']):
        for col in range(d['cols']):
            x0, y0 = col * r, row * r
            for k in range(-30, 31):
                z = round(round(cz, 1) + k * 0.1, 3); py = y0 + r / 2 - (z - cz) / size * r
                if y0 <= py < y0 + r:
                    dr.line([(x0, py), (x0 + r, py)], fill=(90, 160, 90) if abs(z * 10 % 5) < 1e-6 else (70, 110, 70))
                    dr.text((x0 + 2, py - 10), f'{z:.1f}', fill=(150, 255, 150))
                px = x0 + r / 2 + k * 0.1 / size * r  # lines at multiples of 0.1 from the frame centre
                if x0 <= px < x0 + r:
                    dr.line([(px, y0), (px, y0 + r)], fill=(70, 110, 70))
sheet.save(out); os.remove(out + '.json'); print('SHEET', out)
