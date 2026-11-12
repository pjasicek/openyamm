"""Re-lays UV triangles that uv_atlas left collapsed (zero UV area: a chart Blender failed to solve and the packer
dropped onto one point). Each connected group of collapsed triangles is projected onto its best-fit plane (PCA),
split further while a projection flips triangles, scaled to the layout's median texel density and placed in a free
rectangle of the atlas (2 px margin + 1 px safety); where no rectangle is free, at a lower density (x0.85 .. x0.4). Writes a new layout npz (the input stays as it was).
Usage: tp_fix_collapsed.py <in layout npz> <out layout npz>"""
import sys

import numpy as np
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

import tp_common as C
import texture_quality as TQ

src, dst = sys.argv[1:3]
L = dict(np.load(src))
uv, xyz = L['uv'].astype(np.float64), L['xyz'].astype(np.float64)
cfg = C.config()
S = cfg.get('size', 2048)
a2, a3 = C.tri_area2(uv), C.tri_area3(xyz)
bad = np.nonzero(a2 < 1e-12)[0]
print('collapsed triangles', len(bad))
if not len(bad):
    np.savez(dst, **L)
    raise SystemExit
ok = a2 >= 1e-12
density = float(np.median(np.sqrt(a2[ok] / np.maximum(a3[ok], 1e-12))))
# group collapsed triangles by shared 3D corners
pts = np.round(xyz[bad].reshape(-1, 3), 6)
_, vid = np.unique(pts, axis=0, return_inverse=True)
vid = vid.reshape(-1, 3)
n = vid.max() + 1
rows = np.repeat(np.arange(len(bad)), 3)
graph = coo_matrix((np.ones(rows.size), (rows, vid.ravel() + len(bad))), shape=(len(bad) + n, len(bad) + n))
_, comp = connected_components(graph, directed=False)
comp = comp[:len(bad)]
occupied = ndimage.binary_dilation(TQ.raster_union(uv[ok], S), iterations=3)


def project(group):
    p = xyz[group].reshape(-1, 3)
    c = p.mean(0)
    _, _, vt = np.linalg.svd(p - c)
    e1, e2, nrm = vt
    q = np.stack([(xyz[group] - c) @ e1, (xyz[group] - c) @ e2], -1)
    tn = np.cross(xyz[group][:, 1] - xyz[group][:, 0], xyz[group][:, 2] - xyz[group][:, 0])
    flip = (tn @ nrm) < 0
    signed = C.tri_area2(q) * np.where(flip, -1, 1)
    return q, flip


def place(w, h):
    integral = occupied.astype(np.int64).cumsum(0).cumsum(1)
    integral = np.pad(integral, ((1, 0), (1, 0)))
    W, H = int(np.ceil(w)) + 2, int(np.ceil(h)) + 2
    sums = integral[H:, W:] - integral[:-H, W:] - integral[H:, :-W] + integral[:-H, :-W]
    free = np.argwhere(sums == 0)
    if not len(free):
        return None
    y, x = free[0]
    occupied[y:y + H, x:x + W] = True
    return x + 1, y + 1


for c in np.unique(comp):
    group = bad[comp == c]
    q, flip = project(group)
    parts = [group] if (not flip.any() or flip.all()) else [group[~flip], group[flip]]
    for part in parts:
        q, flip = project(part)
        if flip.all():
            q[..., 0] *= -1
        q = q - q.reshape(-1, 2).min(0)
        for scale in (1.0, 0.85, 0.7, 0.6, 0.5, 0.4):
            qq = q * density * S * scale                       # texels
            w, h = qq.reshape(-1, 2).max(0)
            at = place(w, h)
            if at:
                break
        else:
            raise SystemExit('no free rectangle even at 0.4 density')
        uv[part] = (qq + np.array(at)) / S
        print(f'group of {len(part)} triangles -> {w:.0f}x{h:.0f} texels at {at}, density x{scale}')
L['uv'] = uv
np.savez(dst, **L)
print('WROTE', dst, 'zero-area now', int((C.tri_area2(uv) < 1e-12).sum()))
