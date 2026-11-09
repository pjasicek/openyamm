#!/usr/bin/env python3
"""Even out the trousers' large-scale brightness in the base colour (user review 5: "what are the streaks on his
trousers?").

The engine recolours the trousers per tier (fs_model.sc): the luminance of each base-colour texel, normalised to the
region's narrow range (0.028-0.068 linear, a 2.4x window), picks one of 16 native palette stops from near black to
bright green. The shared texture's UV islands differ in brightness and carry baked fold/occlusion blotches, so the
ramp turns them into near-black triangles and streaks next to bright green ones, in the installed model too.

Per UV island of the trouser mask (texture space), the luminance is split into a low-frequency part (Gaussian of
SIGMA texels, normalised to the island so neighbouring islands do not bleed in) and the fine detail around it; the
low part is replaced by the mean trouser luminance and the detail is kept at DETAIL strength (clamped). RGB is scaled
by the luminance change, blended by the soft mask, so the cloth grain and the mask edges stay and only the blotches
go. Other regions, the ramps, the mask and the other maps are untouched. Usage: level_trousers.py <in.glb> <out.glb>"""
import io
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, append_accessor  # noqa: E402,F401

SIGMA = float(os.environ.get('LEVEL_SIGMA', '12'))
DETAIL = float(os.environ.get('LEVEL_DETAIL', '0.6'))
W = np.array([0.2126, 0.7152, 0.0722])
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = read_glb(src); binary = bytearray(binary)


def load(name):
    i = next(k for k, im in enumerate(doc['images']) if name in im['name']); v = doc['bufferViews'][doc['images'][i]['bufferView']]
    o = v.get('byteOffset', 0)
    return i, Image.open(io.BytesIO(bytes(binary[o:o + v['byteLength']])))


bi, base = load('basecolor'); _, maskim = load('region_mask')
rgba = np.asarray(base.convert('RGBA'), np.float64) / 255
mask = np.asarray(maskim.convert('RGBA').resize(base.size, Image.BILINEAR), np.float64)[..., 0] / 255
rgb = lin(rgba[..., :3]); lum = np.maximum(rgb @ W, 1e-5)
inside = mask > 0.02
target = np.average(lum[inside], weights=mask[inside])
islands, count = ndimage.label(inside)
new = lum.copy(); pad = int(3 * SIGMA)
for k, sl in enumerate(ndimage.find_objects(islands), 1):
    ys = slice(max(0, sl[0].start - pad), sl[0].stop + pad); xs = slice(max(0, sl[1].start - pad), sl[1].stop + pad)
    m = (islands[ys, xs] == k).astype(np.float64)
    low = ndimage.gaussian_filter(np.log(lum[ys, xs]) * m, SIGMA) / np.maximum(ndimage.gaussian_filter(m, SIGMA), 1e-6)
    detail = np.clip(np.log(lum[ys, xs]) - low, -0.5, 0.5) * DETAIL
    new[ys, xs] = np.where(m > 0, target * np.exp(detail), new[ys, xs])
scale = 1 + mask * (new / lum - 1)
out = rgba.copy(); out[..., :3] = np.clip(srgb(rgb * scale[..., None]), 0, 1)
buf = io.BytesIO(); Image.fromarray((out * 255 + 0.5).astype(np.uint8), 'RGBA').convert(base.mode).save(buf, 'PNG', optimize=True)
binary += b'\0' * (-len(binary) % 4)
doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())})
binary += buf.getvalue(); doc['images'][bi]['bufferView'] = len(doc['bufferViews']) - 1
before, after = lum[mask > 0.5], new[mask > 0.5]
print('LEVEL', count, 'islands; trouser luminance target', round(float(target), 4),
      'p5/p50/p95 before', np.round(np.percentile(before, [5, 50, 95]), 4), 'after', np.round(np.percentile(after, [5, 50, 95]), 4))
write_glb(dst, doc, bytes(binary))
