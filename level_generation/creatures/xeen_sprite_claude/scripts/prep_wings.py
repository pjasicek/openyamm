"""Wing cards from the HD wing master (references_hd/05_wings.png: the four wings seen from behind, opaque paint on a
transparent background). Writes
- textures/sprite_wing_basecolor.png (1024 RGBA): the LEFT pair (image left = the sprite's left seen from behind),
  colour dilated past the outline, alpha = membrane translucency (pale membrane ALPHA_LO, the dark eye spot and veins up
  to ALPHA_HI, a crisp opaque rim) times the master's own antialiased outline;
- textures/sprite_wing_region_mask.png (1024 RGBA, R = the membrane, padded into the gutter);
- work/wings.json: per wing (UL upper left, LL lower left) the card quads in image pixels (CELL px cells covering the
  outline dilated by PAD px), the root point (where the four wings meet), the texture mapping and the wing axis.
The right wings are the mirror images (same UVs). Args: none"""
import json, os
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *p: os.path.join(HERE, *p)
CELL, PAD = int(os.environ.get('CELL', 48)), int(os.environ.get('PAD', 10))
ALPHA_LO, ALPHA_HI = float(os.environ.get('ALPHA_LO', 0.42)), float(os.environ.get('ALPHA_HI', 0.92))
im = np.asarray(Image.open(P('references_hd', '05_wings.png'))).astype(np.float32)
H, W = im.shape[:2]
a = im[..., 3] / 255
mask = a > 0.5
lab, n = ndimage.label(mask)
sizes = ndimage.sum(mask, lab, range(1, n + 1))
comps = [i + 1 for i in np.argsort(-sizes)[:4]]
cen = {c: np.array(ndimage.center_of_mass(mask, lab, c))[::-1] for c in comps}    # (x, y)
cx = np.mean([cen[c][0] for c in comps]); cy = np.mean([cen[c][1] for c in comps])
# root: mean of each wing's pixel nearest the centre
pts = []
for c in comps:
    ys, xs = np.where(lab == c)
    d = (xs - cx) ** 2 + (ys - cy) ** 2; k = np.argmin(d); pts.append((xs[k], ys[k]))
root = np.mean(pts, axis=0)
print('WINGS components', len(comps), 'sizes', [int(sizes[c - 1]) for c in comps], 'root px', np.round(root, 1).tolist())
left = [c for c in comps if cen[c][0] < root[0]]
UL = min(left, key=lambda c: cen[c][1]); LL = max(left, key=lambda c: cen[c][1])
# texture: the left half, x0..x1, y0..y1 -> 1024 square (uniform scale, left aligned)
x0, x1 = 0, int(np.ceil(root[0])) + 4
ys = np.where(mask[:, :x1].any(1))[0]; y0, y1 = max(0, ys.min() - 16), min(H, ys.max() + 16)
sc = 1024 / max(x1 - x0, y1 - y0)
tw, th = int(round((x1 - x0) * sc)), int(round((y1 - y0) * sc))
crop = im[y0:y1, x0:x1].copy()
cm = crop[..., 3] / 255
lum = (0.2126 * crop[..., 0] + 0.7152 * crop[..., 1] + 0.0722 * crop[..., 2]) / 255
inside = cm > 0.5
lmax = np.percentile(lum[inside], 98)
dark = np.clip(1 - lum / lmax, 0, 1)
alpha = ALPHA_LO + (ALPHA_HI - ALPHA_LO) * np.clip(dark * 1.6, 0, 1) ** 1.2
dist = ndimage.distance_transform_edt(inside)
alpha = np.where(dist < 3.5, np.maximum(alpha, 0.9), alpha)                         # crisp rim
alpha = alpha * np.clip(cm, 0, 1)
# colour dilated into the transparent area (nearest inside pixel)
idx = ndimage.distance_transform_edt(~inside, return_distances=False, return_indices=True)
rgb = crop[..., :3][idx[0], idx[1]]
tex = np.zeros((1024, 1024, 4), np.float32)
big = np.dstack([rgb, alpha * 255]).clip(0, 255).astype(np.uint8)
big = np.asarray(Image.fromarray(big, 'RGBA').resize((tw, th), Image.LANCZOS)).astype(np.float32)
tex[:th, :tw] = big
# fill the rest of the square with the nearest colour (alpha 0) so mips do not bleed black
filled = tex[..., 3] > 0
ii = ndimage.distance_transform_edt(~filled, return_distances=False, return_indices=True)
tex[..., :3] = tex[..., :3][ii[0], ii[1]]
os.makedirs(P('textures'), exist_ok=True)
Image.fromarray(tex.clip(0, 255).astype(np.uint8), 'RGBA').save(P('textures', 'sprite_wing_basecolor.png'))
mk = np.zeros((1024, 1024, 4), np.uint8)
rm = (tex[..., 3] > 4).astype(np.uint8)
rm = ndimage.binary_dilation(rm, iterations=6)
mk[..., 0] = rm * 255
Image.fromarray(mk, 'RGBA').save(P('textures', 'sprite_wing_region_mask.png'))
dil = ndimage.binary_dilation(mask, iterations=PAD)
out = {'image': [W, H], 'root': root.tolist(), 'tex': {'x0': int(x0), 'y0': int(y0), 'scale': float(sc)}, 'wings': {}}
for name, c in (('UL', UL), ('LL', LL)):
    m = dil & ndimage.binary_dilation(lab == c, iterations=PAD)
    ys, xs = np.where(m)
    quads = []
    for gy in range(ys.min() - ys.min() % CELL, ys.max() + 1, CELL):
        for gx in range(xs.min() - xs.min() % CELL, xs.max() + 1, CELL):
            if m[gy:gy + CELL, gx:gx + CELL].any():
                quads.append([int(gx), int(gy)])
    far = np.argmax((xs - root[0]) ** 2 + (ys - root[1]) ** 2)
    out['wings'][name] = {'cells': quads, 'cell': CELL, 'tip': [int(xs[far]), int(ys[far])],
                          'centroid': np.array(ndimage.center_of_mass(lab == c))[::-1].tolist()}
    print('WING', name, 'cells', len(quads), 'tip px', out['wings'][name]['tip'])
json.dump(out, open(P('work', 'wings.json'), 'w'), indent=1)
print('WINGTEX', tw, 'x', th, 'scale', round(sc, 4), 'alpha range', round(float(alpha[inside].min()), 2), round(float(alpha[inside].max()), 2))
