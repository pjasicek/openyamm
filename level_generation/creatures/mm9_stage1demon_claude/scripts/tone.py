"""Hide tone toward MM9's LESSERDEMON skin (dark maroon with orange, not bright orange-red): red-orange texels lose value and
some saturation, steel, horn, teeth and eyes are untouched. Args: in.png out.png [value] [sat]"""
import sys, numpy as np
from PIL import Image
src, dst = sys.argv[1:3]; kv = float(sys.argv[3]) if len(sys.argv) > 3 else 0.72; ks = float(sys.argv[4]) if len(sys.argv) > 4 else 0.9
a = np.asarray(Image.open(src).convert('RGB'), np.float32) / 255
mx, mn = a.max(2), a.min(2); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
w = np.clip((sat - 0.35) / 0.2, 0, 1) * np.clip(1 - np.minimum(np.abs(((hue + 180) % 360) - 180) - 25, 999) / 15, 0, 1)
w = np.where((hue < 40) | (hue > 330), w, 0)[..., None]
gray = a.mean(2, keepdims=True)
t = (gray + (a - gray) * ks) * kv
out = a * (1 - w) + t * w
# steel: MM9's plates are mid gunmetal, the paint came back near white: grey texels above mid value lose up to 25 %
ws = (np.clip((0.22 - sat) / 0.1, 0, 1) * np.clip((mx - 0.35) / 0.3, 0, 1))[..., None]
out = out * (1 - ws * float(sys.argv[5] if len(sys.argv) > 5 else 0.25))
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(dst)
print('TONE', dst, 'weighted share %.2f' % float((w > 0.5).mean()))
