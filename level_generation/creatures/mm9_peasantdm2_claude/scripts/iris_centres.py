"""Iris centres (left and right half separately) in a face render: blue-ish (b > r + D) or dark (sum < 150) texels in the eye band,
largest component per half, centre of mass. Args: <png> [D]"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
a = np.asarray(Image.open(sys.argv[1]).convert('RGB'), float)
D = float(sys.argv[2]) if len(sys.argv) > 2 else 10
r, g, b = a[..., 0], a[..., 1], a[..., 2]
m = ((b > r + D) & (b > g - 5)) | ((a.sum(-1) < 150) & (b >= r - 5))
m[:440] = 0; m[570:] = 0
out = []
for x0, x1 in ((380, 627), (627, 880)):
    mm = m.copy(); mm[:, :x0] = 0; mm[:, x1:] = 0
    lab, n = ndi.label(ndi.binary_closing(mm, iterations=2))
    if n == 0:
        out.append(None); continue
    sz = ndi.sum(mm, lab, range(1, n + 1)); k = int(np.argmax(sz)) + 1
    cy, cx = ndi.center_of_mass(lab == k)
    out.append((round(cx, 1), round(cy, 1), int(sz[k - 1])))
print('IRIS', sys.argv[1].split('/')[-1], out)
