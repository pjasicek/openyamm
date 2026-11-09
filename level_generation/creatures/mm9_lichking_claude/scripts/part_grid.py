"""Grid of mesh parts (comp) as front (x,z) and side (y,z) triangle silhouettes, each against the whole figure in grey. Args: <npz> <out png> [parts csv]"""
import sys, numpy as np
from PIL import Image, ImageDraw
D = np.load(sys.argv[1]); co, tri, comp = D['co'], D['tri'], D['comp']
names = [str(x) for x in D['names']] if 'names' in D.files else None
parts = [int(x) for x in sys.argv[3].split(',')] if len(sys.argv) > 3 else sorted(set(comp.tolist()))
S = 220; sc = S / 1.9; tp = comp[tri[:, 0]]
def draw(dr, ox, ax, sel, col):
    for t in tri[sel]:
        p = co[t]; pts = [(ox + S / 2 + q[ax] * sc, S - 10 - q[2] * sc * 0.95) for q in p]
        dr.polygon(pts, fill=col)
cols = 6; rows = (len(parts) + cols - 1) // cols
im = Image.new('RGB', (cols * 2 * S, rows * S), (40, 40, 40)); dr = ImageDraw.Draw(im)
for k, pi in enumerate(parts):
    ox, oy = (k % cols) * 2 * S, (k // cols) * S
    for j, ax in enumerate((0, 1)):
        sub = Image.new('RGB', (S, S), (40, 40, 40)); d2 = ImageDraw.Draw(sub)
        draw(d2, 0, ax, tp != pi, (90, 90, 90)); draw(d2, 0, ax, tp == pi, (240, 160, 60))
        im.paste(sub, (ox + j * S, oy))
    dr.text((ox + 4, oy + 4), f'{pi} {names[pi] if names else ""} {int((comp == pi).sum())}', fill=(255, 255, 255))
im.save(sys.argv[2])
