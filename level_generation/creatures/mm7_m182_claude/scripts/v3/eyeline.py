"""Eye-line angle from side images (system Python): eye = centroid of the iris pixels (tier A: red, R > 2.2 G), snout
= the foremost opaque pixel within 0.6 head lengths of the eye's height band; angle of eye -> snout below the
horizontal (degrees). Head faces image right. Usage: eyeline.py <png> [iris rule: red|yellow]"""
import sys, math
import numpy as np
from PIL import Image
im = np.asarray(Image.open(sys.argv[1]).convert('RGBA')).astype(float); rule = sys.argv[2] if len(sys.argv) > 2 else 'red'
R, G, B, A = im[..., 0], im[..., 1], im[..., 2], im[..., 3]
if rule == "red": iris = (A > 128) & (R > 110) & (R > 2.0 * G) & (R > 1.5 * B)
else: iris = (A > 128) & (R > 150) & (G > 100) & (B < 70) & (R > G)
ys, xs = np.nonzero(iris)
if rule != 'red':   # native: the eye is the iris blob nearest the head front at mid height; take the largest blob near x max
    keep = xs > np.percentile(xs, 0)
ey, ex = ys.mean(), xs.mean()
op = A > 128; band = np.abs(np.arange(op.shape[0]) - ey) < 0.12 * op.shape[0]
cols = np.where(op[band].any(0))[0]; sx = cols.max(); rows = np.nonzero(op[band][:, sx])[0] + np.nonzero(band)[0][0]; sy = rows.mean()
print('EYELINE', round(math.degrees(math.atan2(sy - ey, sx - ex)), 2), 'eye', (round(ex), round(ey)), 'snout', (int(sx), round(sy)))
