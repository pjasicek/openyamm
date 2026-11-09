#!/usr/bin/env python3
"""Wing outlines and wing texture from the HD top view (references_hd/05_wings_top.png).

Writes work/wing_profiles.json (per wing: image root, tip, perpendicular, lateral extents per station, in source
image pixels) and textures/dfly_wing_basecolor_src.png (the crop, colour dilated past the outline so filtering never
pulls in the background) with the crop box, so UV = (pixel - crop origin) / crop size.

Wing ids follow the MM9 pieces: d_winga (creature's right front, -X), d_wingb (right rear), d_wingc (left front,
+X), d_wingd (left rear). In the top view the head is at the image top and image right is the creature's right (-X).
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
SRC = HERE / 'references_hd' / '05_wings_top.png'
STATIONS = 17
ROOT_CLEAN = 0.25
CROP = (24, 80, 1512, 944)  # x0, y0, x1, y1
TEX = 1024

im = np.array(Image.open(SRC).convert('RGBA')).astype(np.float32)
alpha = im[..., 3] > 128
H, W = alpha.shape
ys, xs = np.nonzero(alpha)
# body column: the narrow run in the rows below the wings
lower = alpha[700:880]
cols = np.nonzero(lower.any(0))[0]
cx = (cols.min() + cols.max()) / 2.0
body_half = 0.5 * (cols.max() - cols.min()) + 14
exclude_half = body_half + 20
wing = alpha.copy()
wing[:, int(cx - body_half):int(cx + body_half) + 1] = False
wing_far = wing.copy()
wing_far[:, int(cx - exclude_half):int(cx + exclude_half) + 1] = False
lab, n = ndimage.label(wing)
sizes = ndimage.sum(wing, lab, range(1, n + 1))
# rows where wings meet the body: mean y of wing pixels touching the body gap
touch = wing[:, int(cx - body_half) - 3:int(cx - body_half)] | wing[:, int(cx + body_half) + 1:int(cx + body_half) + 4]
root_y = float(np.nonzero(touch.any(1))[0].mean())
profiles = {}
for side, sign in (('right', 1), ('left', -1)):  # image right = creature right (-X)
    sel = wing_far & ((np.arange(W)[None, :] > cx) if sign > 0 else (np.arange(W)[None, :] < cx))
    py, px = np.nonzero(sel)
    root = np.array([cx + sign * body_half, root_y])
    ang = np.arctan2(py - root[1], (px - root[0]) * sign)  # 0 = straight out, negative = up (toward head)
    # two wings: split angles at the largest gap of the angle histogram between the two modes
    hist, edges = np.histogram(ang, bins=90)
    peaks = np.argsort(hist)[::-1]
    p1 = peaks[0]
    p2 = next(p for p in peaks if abs(p - p1) > 12)
    lo, hi = sorted((p1, p2))
    cut = edges[lo + int(np.argmin(hist[lo:hi + 1]))]
    for name, mask in ((('front'), ang < cut), ('rear', ang >= cut)):
        qx, qy = px[mask], py[mask]
        d = np.hypot(qx - root[0], qy - root[1])
        tip = np.array([qx[d.argmax()], qy[d.argmax()]], float)
        root0 = np.array([cx, root_y])
        axis = tip - root0
        L = np.linalg.norm(axis)
        axis /= L
        perp = np.array([-axis[1], axis[0]])
        s = ((qx - root0[0]) * axis[0] + (qy - root0[1]) * axis[1]) / L
        t = (qx - root0[0]) * perp[0] + (qy - root0[1]) * perp[1]
        st = []
        for k in range(STATIONS):
            f = k / (STATIONS - 1)
            m = np.abs(s - f) < 0.6 / (STATIONS - 1)
            if m.sum() < 3 or f <= 0.0 or f >= 1.0:
                st.append([f, 0.0, 0.0])
            else:
                st.append([f, float(np.percentile(t[m], 1)), float(np.percentile(t[m], 99))])
        # the root third overlaps the body and eyes in the top view: taper linearly from the first clean station
        k0 = next(k for k, v in enumerate(st) if v[0] >= ROOT_CLEAN)
        for k in range(k0):
            a = st[k][0] / st[k0][0]
            st[k] = [st[k][0], st[k0][1] * a, st[k0][2] * a]
        piece = {('right', 'front'): 'd_winga', ('right', 'rear'): 'd_wingb', ('left', 'front'): 'd_wingc',
                 ('left', 'rear'): 'd_wingd'}[(side, name)]
        profiles[piece] = {'root': root0.tolist(), 'tip': tip.tolist(), 'length': float(L), 'axis': axis.tolist(),
                           'perp': perp.tolist(), 'stations': st, 'pixels': int(mask.sum())}
out = {'image': str(SRC.relative_to(HERE)), 'size': [W, H], 'centre_x': cx, 'root_y': root_y, 'crop': CROP,
       'texture_size': TEX, 'wings': profiles}
(HERE / 'work' / 'wing_profiles.json').write_text(json.dumps(out, indent=1))

# texture: crop, dilate colour of the wings into the background (nearest wing pixel), resize
rgb = im[..., :3]
fill = ~wing
_, (iy, ix) = ndimage.distance_transform_edt(fill, return_indices=True)
dil = rgb[iy, ix]
x0, y0, x1, y1 = CROP
crop = Image.fromarray(dil[y0:y1, x0:x1].clip(0, 255).astype(np.uint8)).resize((TEX, TEX), Image.LANCZOS)
(HERE / 'textures').mkdir(exist_ok=True)
crop.save(HERE / 'textures' / 'dfly_wing_basecolor_src.png')
mask = Image.fromarray((wing[y0:y1, x0:x1] * 255).astype(np.uint8)).resize((TEX, TEX), Image.BILINEAR)
mask.save(HERE / 'work' / 'wing_alpha_crop.png')
print(json.dumps({k: {'root': v['root'], 'tip': v['tip'], 'px': v['pixels']} for k, v in profiles.items()}),
      'cx', cx, 'root_y', root_y, 'body_half', body_half)
