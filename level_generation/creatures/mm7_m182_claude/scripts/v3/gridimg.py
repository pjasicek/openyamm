"""Draw a labelled metric grid on an orthographic render made by render.py.
Usage: gridimg.py <png> <view: side|front|top> <target x,y,z> <ortho scale> <step m> [out]
side: camera from +X (image x = -Y, image y = -Z); front: from -Y (image x = +X... mirrored: x = X); top: from +Z."""
import sys
from PIL import Image, ImageDraw
png, view, t, S, step = sys.argv[1], sys.argv[2], [float(v) for v in sys.argv[3].split(',')], float(sys.argv[4]), float(sys.argv[5])
out = sys.argv[6] if len(sys.argv) > 6 else png.replace('.png', '_grid.png')
im = Image.open(png).convert('RGB'); W, H = im.size; ppm = max(W, H) / S; d = ImageDraw.Draw(im)
# axis mapping: horizontal axis (world index, sign), vertical axis (world index, sign)
ax = {'side': ((1, -1), (2, 1)), 'front': ((0, 1), (2, 1)), 'top': ((0, 1), (1, 1))}[view]
(hi, hs), (vi, vs) = ax
import math
def to_px(hw, vw):
    return W / 2 + (hw - t[hi]) * hs * ppm, H / 2 - (vw - t[vi]) * vs * ppm
lo_h = t[hi] - S; hi_h = t[hi] + S
k = math.floor(lo_h / step)
while k * step <= hi_h:
    x, _ = to_px(k * step, t[vi]); col = (255, 70, 70) if abs(round(k * step / (5 * step)) * 5 * step - k * step) < 1e-9 else (110, 110, 110)
    d.line([(x, 0), (x, H)], fill=col, width=1); d.text((x + 2, 2), f'{k*step:.2f}', fill=(255, 255, 0)); k += 1
k = math.floor((t[vi] - S) / step)
while k * step <= t[vi] + S:
    _, y = to_px(t[hi], k * step); col = (255, 70, 70) if abs(round(k * step / (5 * step)) * 5 * step - k * step) < 1e-9 else (110, 110, 110)
    d.line([(0, y), (W, y)], fill=col, width=1); d.text((2, y + 2), f'{k*step:.2f}', fill=(255, 255, 0)); k += 1
im.save(out)
