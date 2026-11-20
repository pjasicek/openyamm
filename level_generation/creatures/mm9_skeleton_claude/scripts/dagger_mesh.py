#!/usr/bin/env python3
"""Dagger mesh from the HD master's alpha (references_prop/dagger_flat.png): rings along the blade axis, each a diamond section between the column's top and bottom alpha edge, thin for the blade, round for the grip, flat for guard and pommel.
Both faces sample the same image, planar. Writes work/dagger_mesh.npz (verts in px with z in px, faces, uv, side) and textures/skel_dagger_basecolor.png (padded). Args: none (project folder)."""
import numpy as np
from PIL import Image
from scipy import ndimage
im = Image.open('references_prop/dagger_flat.png').convert('RGBA')
W, H = im.size
a = np.asarray(im, np.float32)
mask = a[..., 3] > 128
mask = ndimage.binary_opening(mask, iterations=1)
lab, n = ndimage.label(mask); sizes = ndimage.sum(mask, lab, range(1, n + 1)); mask = ndimage.binary_fill_holes(lab == (1 + int(np.argmax(sizes))))
px_m = 0.336 / (1487 - 49)
xs = list(range(51, 150, 25)) + list(range(150, 500, 70)) + list(range(500, 650, 12)) + list(range(650, 890, 60)) + list(range(890, 1260, 90)) + [1262] + list(range(1290, 1486, 40)) + [1483]
Z = lambda x: (0.0075 if x < 150 else 1.0 if x < 500 else 0.0065 if x < 645 else 0.0042)
V, F, S = [], [], []
rings = []
for x in xs:
    c = np.where(mask[:, x])[0]
    top, bot = float(c.min()), float(c.max()); mid = (top + bot) / 2
    hz = (bot - top) / 2 if Z(x) == 1.0 else min(Z(x) / px_m, (bot - top) * 0.45)
    r = len(V); V += [(x, top, 0.0), (x, mid, hz), (x, bot, 0.0), (x, mid, -hz)]; rings.append(r)
for r0, r1 in zip(rings[:-1], rings[1:]):
    for i in range(4):
        a0, a1, b0, b1 = r0 + i, r0 + (i + 1) % 4, r1 + i, r1 + (i + 1) % 4
        sd = 1 if i in (0, 1) else -1
        F += [(a0, b0, b1), (a0, b1, a1)]; S += [sd, sd]
# end caps
for r, flip in ((rings[0], 0), (rings[-1], 1)):
    for tri in ((r, r + 1, r + 2), (r, r + 2, r + 3)):
        F.append(tri[::-1] if flip else tri); S.append(1)
V = np.array(V, float); F = np.array(F, int); S = np.array(S, float)
uv = np.c_[V[:, 0] / W, 1 - V[:, 1] / H]
np.savez('work/dagger_mesh.npz', v=V, f=F, uv=uv, side=S, px_m=px_m, w=W, h=H)
print('dagger verts', len(V), 'tris', len(F))
rgb = a[..., :3].astype(np.uint8)
_, (iy, ix) = ndimage.distance_transform_edt(~ndimage.binary_erosion(mask, iterations=1), return_indices=True)
Image.fromarray(rgb[iy, ix]).save('textures/skel_dagger_basecolor.png')
