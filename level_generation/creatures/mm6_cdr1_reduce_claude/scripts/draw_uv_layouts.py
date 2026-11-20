"""Draw work/uv_tris_{body,head}.npy (set id + three UV corners) to work/uv_layouts.png: body red, head blue,
wings green; prints covered fraction per set."""
import numpy as np
from PIL import Image, ImageDraw
N = 1024; cols = {0: (200, 80, 60), 1: (80, 160, 220), 2: (120, 200, 90)}; sheet = Image.new('RGB', (2 * N, N))
for i, label in enumerate(['body', 'head']):
    t = np.load(f'work/uv_tris_{label}.npy'); im = Image.new('RGB', (N, N), (20, 20, 20)); dr = ImageDraw.Draw(im)
    for row in t:
        p = row[1:].reshape(3, 2); dr.polygon([(x * N, (1 - y) * N) for x, y in p], fill=cols[int(row[0])])
    a = np.asarray(im); print(label, {k: round(float((a == np.array(c)).all(-1).mean()), 3) for k, c in cols.items()})
    sheet.paste(im, (i * N, 0))
sheet.save('work/uv_layouts.png')
