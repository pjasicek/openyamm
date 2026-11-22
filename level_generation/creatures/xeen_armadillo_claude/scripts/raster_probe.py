"""Rasterise work/uv3d.npz at 2048 (as compose does) and print where the paint's eye-yellow, claw-grey and pale-pink
texels are (by bone and 3D position)."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'mm6_gob_claude' / 'scripts'))
import compose_textures_v2 as C
d = np.load(ROOT / 'work/uv3d.npz'); bones = [str(b) for b in d['bones']]
label, xyz = C.rasterise(d, values=d['bone'] * 8 + d['mpart'])
valid = label >= 0; bone = np.where(valid, label // 8, -1); mp = np.where(valid, label % 8, -1)
rgb = np.asarray(Image.open(ROOT / 'meshy/retexture_v1/texture_urls_0_base_color.png').convert('RGB').resize((2048, 2048), Image.LANCZOS), np.float32) / 255
mx = rgb.max(-1); mn = rgb.min(-1); dd = mx - mn; sat = np.where(mx > 0, dd / np.maximum(mx, 1e-4), 0)
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
h = np.zeros_like(mx); m = dd > 1e-5
hr = m & (mx == r); hg = m & (mx == g) & ~hr; hb = m & ~hr & ~hg
h[hr] = ((g - b)[hr] / dd[hr]) % 6; h[hg] = (b - r)[hg] / dd[hg] + 2; h[hb] = (r - g)[hb] / dd[hb] + 4
hue = h * 60
np.savez_compressed(ROOT / 'work/raster.npz', label=label, xyz=xyz)
def rep(name, sel):
    print(name, int(sel.sum()), 'bones', {bones[k]: int((bone[sel] == k).sum()) for k in np.unique(bone[sel])},
          'xyz p5/50/95', np.round(np.percentile(xyz[sel], [5, 50, 95], axis=0), 3).tolist() if sel.any() else '')
rep('YELLOW', valid & (hue > 28) & (hue < 65) & (sat > 0.45) & (mx > 0.5))
rep('GREY', valid & (sat < 0.18) & (mx > 0.35))
rep('PALE', valid & (hue < 30) & (sat > 0.18) & (sat < 0.45) & (mx > 0.6))
rep('DARK', valid & (mx < 0.15))
print('sat/val percentiles of valid', np.percentile(sat[valid], [5, 25, 50, 75, 95]).round(2), np.percentile(mx[valid], [5, 50, 95]).round(2))
