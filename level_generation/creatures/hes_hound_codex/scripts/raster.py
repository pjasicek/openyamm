"""Raster helpers copied from the existing creature texture pipeline."""
import numpy as np
from PIL import Image
SIZE=2048

def load(path, mode='RGB'):
    return np.asarray(Image.open(path).convert(mode), dtype=np.float32) / 255.0


def rasterise(data, tol=0.03, values=None):
    uv, xyz, part = data['uv'], data['xyz'], data['part']
    values = part if values is None else values
    part_map = np.full((SIZE, SIZE), -1, dtype=np.int32)
    xyz_map = np.zeros((SIZE, SIZE, 3), dtype=np.float32)
    for t in range(len(uv)):
        p = uv[t] * SIZE
        p[:, 1] = SIZE - p[:, 1]
        x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, SIZE - 1), min(y1, SIZE - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = p
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12:
            continue
        w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / d
        w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / d
        w2 = 1 - w0 - w1
        inside = (w0 >= -tol) & (w1 >= -tol) & (w2 >= -tol)
        ys, xs = np.nonzero(inside)
        part_map[y0 + ys, x0 + xs] = values[t]
        xyz_map[y0 + ys, x0 + xs] = (w0[inside, None] * xyz[t][0] + w1[inside, None] * xyz[t][1]
                                     + w2[inside, None] * xyz[t][2])
    return part_map, xyz_map


def hsv(rgb):
    mx = rgb.max(-1); mn = rgb.min(-1); delta = mx - mn
    sat = np.where(mx > 1e-4, delta / np.maximum(mx, 1e-4), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    safe = np.maximum(delta, 1e-5)
    h = np.where(mx == r, ((g - b) / safe) % 6, np.where(mx == g, (b - r) / safe + 2, (r - g) / safe + 4)) * 60
    return np.where(delta > 1e-5, h, 0), sat, mx


