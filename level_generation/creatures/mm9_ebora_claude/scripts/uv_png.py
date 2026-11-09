"""Draw a UV npz layout (all materials) to a PNG. Args: <uv npz> <out png> [size]"""
import sys, numpy as np
from PIL import Image, ImageDraw
D = np.load(sys.argv[1]); S = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
uv, tri, mat = D['uv'], D['tri'], D['mat']
im = Image.new('RGB', (S, S), (20, 20, 20)); d = ImageDraw.Draw(im)
cols = [(200, 120, 90), (120, 180, 220), (140, 210, 120), (220, 200, 90)]
for t, m in zip(tri, mat):
    p = [(uv[i, 0] * S, (1 - uv[i, 1]) * S) for i in t]; d.polygon(p, fill=cols[m % 4], outline=(0, 0, 0))
im.save(sys.argv[2])
