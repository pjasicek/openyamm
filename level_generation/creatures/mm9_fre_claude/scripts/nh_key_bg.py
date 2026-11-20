"""Pass 7: transparent background for a Codex bust on a flat grey background. Background = pixels within TOL of the median border colour
that are connected to the image border; the figure keeps every enclosed pixel; edge feathered 1 px. Args: <in png> <out png> [tol]"""
import sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi
src, dst = sys.argv[1:3]; tol = float(sys.argv[3]) if len(sys.argv) > 3 else 14
im = np.asarray(Image.open(src).convert('RGB')).astype(float)
b = np.r_[im[0], im[-1], im[:, 0], im[:, -1]]; bg = np.median(b, 0)
close = np.abs(im - bg).max(2) < tol
lab, n = ndi.label(close)
edge = np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]]); edge = edge[edge > 0]
bgm = np.isin(lab, edge)
fig = ~bgm
lab2, n2 = ndi.label(fig); sz = ndi.sum(fig, lab2, range(1, n2 + 1)); fig = lab2 == 1 + int(np.argmax(sz))
fig = ndi.binary_fill_holes(fig)
a = Image.fromarray((fig * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))
out = np.dstack([im.astype(np.uint8), np.asarray(a)])
Image.fromarray(out, 'RGBA').save(dst)
print('KEYED', dst, 'bg', bg.round(0), 'figure px', int(fig.sum()))
