"""Number the parts on part_views renders. Args: <stats txt> <prefix> <out prefix>"""
import re, sys
from PIL import Image, ImageDraw, ImageFont
st, pre, out = sys.argv[1:4]
P = {}
for l in open(st):
    m = re.match(r'P(\d+) tris (\d+) .*cen \[\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\]', l)
    P[int(m[1])] = (int(m[2]), float(m[3]), float(m[4]), float(m[5]))
CR = dict(torso=((0, .02, .22), .42), pelvis=((0, .02, .03), .3), hand=((-.32, .02, .07), .16), elbow=((-.27, .03, .12), .12), foot=((-.19, -.03, -.47), .2), knee=((-.17, .02, -.3), .3))
f = ImageFont.load_default(size=18)
for n, (c, s) in CR.items():
    for v, (u, w) in dict(front=((1, 0, 0), (0, 0, 1)), back=((-1, 0, 0), (0, 0, 1)), right=((0, -1, 0), (0, 0, 1)), left=((0, 1, 0), (0, 0, 1)), top=((1, 0, 0), (0, 1, 0)), bottom=((1, 0, 0), (0, -1, 0))).items():
        if n in ('elbow', 'knee') and v in ('top', 'bottom'): continue
        im = Image.open(f'{pre}_{n}_{v}.png').convert('RGB'); d = ImageDraw.Draw(im); S = im.width
        for k, (t, x, y, z) in P.items():
            du = sum((a - b) * q for a, b, q in zip((x, y, z), c, u)); dw = sum((a - b) * q for a, b, q in zip((x, y, z), c, w))
            px, py = S / 2 + du / s * S, S / 2 - dw / s * S
            if 0 < px < S and 0 < py < S:
                d.text((px - 8, py - 9), str(k), fill=(255, 255, 255), font=f, stroke_width=2, stroke_fill=(0, 0, 0))
        im.resize((1000, 1000)).save(f'{out}_{n}_{v}.png')
