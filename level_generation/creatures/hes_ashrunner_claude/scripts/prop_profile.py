#!/usr/bin/env python3
"""Side-view prop profile for make_slab_prop.py: the reference's alpha mask (minus the config's cut boxes) on a grid of
CELL px, its boundary as closed loops (outer outline and holes: cell edges between opaque and transparent cells,
chained, then Douglas-Peucker simplified to TOL cells), the same for the glow mask (bright blue or orange texels), the
texture (alpha box crop, transparent texels filled with the nearest opaque colour) and the runtime maps.
Writes work/<name>_profile.json and textures/props/<name>.png, textures/har_<name>_{basecolor,normal,metal_rough}.png.
Args: <name>  (config scripts/props.json)"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
name = sys.argv[1]
CF = json.load(open(HERE / 'scripts' / 'props.json'))[name]
im = np.asarray(Image.open(HERE / 'references_hd' / CF['image']).convert('RGBA')).astype(np.float64)
al = im[..., 3] > 140
for x0, y0, x1, y1 in CF.get('cut', []):
    al[y0:y1, x0:x1] = False
al = ndimage.binary_opening(al, iterations=2)
lab, n = ndimage.label(al)
al = lab == (np.argmax(np.bincount(lab.ravel())[1:]) + 1)       # the largest piece only (no stray specks)
rgb = im[..., :3]
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
if CF['glow'] == 'blue':
    glow = (b > 170) & (b > r + 50) & (b > g + 10)
else:
    glow = (r > 215) & (g > 70) & (g < 215) & (b < 120) & (r > g + 40)
glow &= al
glow = ndimage.binary_opening(glow, iterations=3)
C = int(CF.get('cell', 6)); TOL = float(CF.get('tol', 1.2))


def loops_of(mask):
    """Closed boundary loops (corner points in px) of a binary mask on CELL px cells."""
    H, W = mask.shape[0] // C, mask.shape[1] // C
    m = mask[:H * C, :W * C].reshape(H, C, W, C).mean((1, 3)) > 0.5
    m = np.pad(m, 1)
    nxt = {}
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        if not m[y - 1, x]:
            nxt.setdefault((x + 1, y), []).append((x, y))
        if not m[y + 1, x]:
            nxt.setdefault((x, y + 1), []).append((x + 1, y + 1))
        if not m[y, x - 1]:
            nxt.setdefault((x, y), []).append((x, y + 1))
        if not m[y, x + 1]:
            nxt.setdefault((x + 1, y + 1), []).append((x + 1, y))
    loops = []
    while nxt:
        s = next(iter(nxt)); lp, p = [], s
        while True:
            lp.append(p); q = nxt[p].pop()
            if not nxt[p]:
                del nxt[p]
            p = q
            if p == s:
                break
        if len(lp) >= 8:
            loops.append(simplify(np.array(lp, float)))
    return [[[float((x - 1) * C), float((y - 1) * C)] for x, y in lp] for lp in loops if len(lp) >= 3]


def simplify(pts):
    """Douglas-Peucker on a closed loop (split at the two farthest points)."""
    def dp(p):
        if len(p) < 3:
            return p
        a, b = p[0], p[-1]; ab = b - a; L = np.hypot(*ab)
        d = np.abs(np.cross(ab, p - a)) / L if L > 1e-9 else np.hypot(*(p - a).T)
        i = int(np.argmax(d))
        if d[i] > TOL:
            return np.vstack([dp(p[:i + 1])[:-1], dp(p[i:])])
        return np.array([a, b])
    k = int(np.argmax(np.hypot(*(pts - pts[0]).T)))
    a = dp(np.vstack([pts[:k + 1]])); b = dp(np.vstack([pts[k:], pts[:1]]))
    return np.vstack([a[:-1], b[:-1]])


ys, xs = np.nonzero(ndimage.binary_opening(im[..., 3] > 140, iterations=2))   # the texture box keeps cut parts (grip)
box = [int(xs.min()), int(xs.max()) + 1, int(ys.min()), int(ys.max()) + 1]
out = {'box': box, 'loops': loops_of(al), 'glow_loops': loops_of(glow), 'size': [im.shape[1], im.shape[0]]}
json.dump(out, open(HERE / 'work' / f'{name}_profile.json', 'w'))
full = np.asarray(Image.open(HERE / 'references_hd' / CF['image']).convert('RGBA')).astype(np.float64)
op = full[..., 3] > 140
_, (iy, ix) = ndimage.distance_transform_edt(~op, return_indices=True)
fill = full[..., :3][iy, ix][box[2]:box[3], box[0]:box[1]]
T = HERE / 'textures'; (T / 'props').mkdir(parents=True, exist_ok=True)
tw = int(CF.get('tex_w', 1024)); th = 2 ** int(round(np.log2(tw * (box[3] - box[2]) / (box[1] - box[0]))))   # power of two (split_attachment.py crops on a grid)
tex = Image.fromarray(fill.astype(np.uint8)).resize((tw, max(th, 64)), Image.LANCZOS)
tex.save(T / 'props' / f'{name}.png'); tex.save(T / f'har_{name}_basecolor.png')
Image.new('RGB', tex.size, (128, 128, 255)).save(T / f'har_{name}_normal.png')
h, s, v = [np.asarray(c, np.float64) / 255 for c in tex.convert('HSV').split()]
gold = (h * 360 > 28) & (h * 360 < 60) & (s > 0.35) & (v > 0.45)
ceramic = (s < 0.18) & (v > 0.62)
orm = np.zeros(tex.size[::-1] + (3,))
orm[..., 0] = np.where(gold, 0.8, np.where(ceramic, 0.6, 0.3)); orm[..., 1] = np.where(gold, 0.3, np.where(ceramic, 0.45, 0.6))
Image.fromarray((orm * 255).astype(np.uint8)).save(T / f'har_{name}_metal_rough.png')
print('PROFILE', name, 'box', box, 'loops', [len(l) for l in out['loops']], 'glow loops', [len(l) for l in out['glow_loops']],
      'tex', tex.size)
