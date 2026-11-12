#!/usr/bin/env python3
"""Layer masks of the Codex head views: the face (skin) region of a view by seeded connected skin, the rest of the head is helmet. face_mask(rgba float image, name) -> bool array."""
import numpy as np
from scipy import ndimage


def skinlike(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return (r > g * 1.12) & (g > b * 1.08) & (r > 0.5) & (g > r * 0.56)


# seeds in image pixels (1254 px views): nose, chin, and the eye windows of the steel helmet
SEEDS = {'01_front': [(800, 627), (1000, 627), (640, 500), (640, 750), (1180, 627)], '03_left': [], '04_right': [], '02_back': []}


def face_mask(im, name):
    al = im[..., 3] > 0.5
    sk = ndimage.binary_opening(skinlike(im[..., :3]) & al, iterations=1)
    closed = ndimage.binary_closing(sk, iterations=5)
    lab, n = ndimage.label(closed)
    if name == '01_front':
        keep = {lab[y, x] for y, x in SEEDS[name] if lab[y, x]}
    else:                                              # side views: skin pieces at the image's face end and bottom (no leather or steel highlights)
        sizes = ndimage.sum(closed, lab, range(1, n + 1)); com = ndimage.center_of_mass(closed, lab, range(1, n + 1))
        keep = {i + 1 for i, s in enumerate(sizes) if s > 2500 and com[i][0] > 480}
    m = np.isin(lab, list(keep))
    m = ndimage.binary_fill_holes(m) & al
    if name == '01_front':                             # creases beside the nose are skin too
        return ndimage.binary_closing(m, iterations=14) & al
    # side views: the painted eye window and everything in front of it is never helmet
    return ndimage.binary_dilation(ndimage.binary_closing(m, iterations=30), iterations=12) & al


def view_fit(im, lo, hi, axis):
    """Image column and row of mesh coordinates: helmet silhouette (upper 62 % of the head in the image) against the mesh helmet's extents on that axis."""
    al = im[..., 3] > 0.5
    ys, xs = np.where(al); y0, y1 = ys.min(), ys.max()
    row = al[y0:int(y0 + 0.62 * (y1 - y0))]; cols = np.where(row.any(0))[0]
    c0, c1 = cols.min(), cols.max()
    return dict(c0=c0, c1=c1, y0=y0, y1=y1, pxm=(c1 - c0) / (hi[axis] - lo[axis]))
