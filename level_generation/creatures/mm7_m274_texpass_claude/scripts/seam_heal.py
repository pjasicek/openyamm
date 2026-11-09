"""Seam healing on a texture-pass layout: along every UV seam (welded edge whose two triangles have different UVs)
each side is pulled halfway towards the other side's colour, and the correction fades with the distance from the seam
inside its own island (Gaussian falloff, FALLOFF texels at the layout's median density, scaled by each island's
density so the surface distance is the same on the denser head). Pairs whose sides differ in class (gold next to
cloth) or by more than CAP levels are left alone. Used by compose.py on the composed base colour."""
import numpy as np
from scipy import ndimage

import texlib


def heal(img, classes, tri_id, uv, tri, weld, faces, island_map, island_scale, falloff=6.0, cap=45.0, sel=None):
    """img (S,S,3) float sRGB; classes (S,S) labels; uv (T,3,2) glTF; faces: bool (T,) triangles taking part.
    Returns the healed image and the number of seam samples used."""
    S = img.shape[0]
    wt = weld[tri]
    edges = {}
    for f in np.nonzero(faces)[0]:
        for k in range(3):
            a, b = wt[f, k], wt[f, (k + 1) % 3]
            edges.setdefault((min(a, b), max(a, b)), []).append((f, k))
    smooth = np.stack([ndimage.uniform_filter(img[..., c], 3) for c in range(3)], -1)
    marks_y, marks_x, deltas = [], [], []
    for key, v in edges.items():
        if len(v) != 2:
            continue
        (f1, k1), (f2, k2) = v
        # corner UVs of the shared edge, oriented from welded vertex key[0]
        def ends(f, k):
            p, q = uv[f, k], uv[f, (k + 1) % 3]
            return (p, q) if wt[f, k] == key[0] else (q, p)
        a1, b1 = ends(f1, k1)
        a2, b2 = ends(f2, k2)
        if np.allclose(a1, a2) and np.allclose(b1, b2):
            continue                                                  # not a seam
        n = int(max(2, np.ceil(max(np.linalg.norm(b1 - a1), np.linalg.norm(b2 - a2)) * S)))
        t = (np.arange(n) + 0.5)[:, None] / n
        pts = []
        for f, k, a, b in ((f1, k1, a1, b1), (f2, k2, a2, b2)):
            third = uv[f, (k + 2) % 3]
            p = a + (b - a) * t
            d = third - p
            d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-12)
            pts.append(p + d * (1.2 / S))
        c1 = texlib.bilinear(smooth, pts[0])
        c2 = texlib.bilinear(smooth, pts[1])
        k1c = texlib.nearest(classes[..., None], pts[0])[:, 0]
        k2c = texlib.nearest(classes[..., None], pts[1])[:, 0]
        ok = (k1c == k2c) & (np.abs(c1 - c2).max(1) < cap)
        if sel is not None:
            ok &= texlib.nearest(sel[..., None].astype(np.uint8), pts[0])[:, 0].astype(bool)
        for p, dlt in ((pts[0], (c2 - c1) / 2), (pts[1], (c1 - c2) / 2)):
            x = np.clip((p[:, 0] * S).astype(int), 0, S - 1)
            y = np.clip((p[:, 1] * S).astype(int), 0, S - 1)
            marks_y.append(y[ok]); marks_x.append(x[ok]); deltas.append(dlt[ok])
    if not deltas:
        return img, 0
    my, mx, dl = np.concatenate(marks_y), np.concatenate(marks_x), np.concatenate(deltas)
    num = np.zeros_like(img)
    den = np.zeros(img.shape[:2], np.float32)
    np.add.at(num, (my, mx), dl)
    np.add.at(den, (my, mx), 1)
    out = img.copy()
    for i, sl in enumerate(ndimage.find_objects(island_map + 1)):
        if sl is None:
            continue
        sigma = falloff * island_scale[i]
        pad = int(3 * sigma) + 2
        y0, y1 = max(sl[0].start - pad, 0), min(sl[0].stop + pad, S)
        x0, x1 = max(sl[1].start - pad, 0), min(sl[1].stop + pad, S)
        own = island_map[y0:y1, x0:x1] == i
        d = den[y0:y1, x0:x1] * own
        if d.sum() == 0:
            continue
        gd = ndimage.gaussian_filter(d, sigma, mode='constant')
        corr = np.stack([ndimage.gaussian_filter(num[y0:y1, x0:x1, c] * own, sigma, mode='constant')
                         for c in range(3)], -1) / np.maximum(gd, 1e-6)[..., None]
        dist = ndimage.distance_transform_edt(d == 0)
        fade = np.exp(-0.5 * (dist / sigma) ** 2)
        inside = own & (gd > 1e-6)
        out[y0:y1, x0:x1][inside] += (corr * fade[..., None])[inside]
    return out, len(dl)
