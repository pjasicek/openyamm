"""Shared helpers of the Dragon King texture pass: UV triangle rasters, gutter padding, resampling a texture of the old
layout onto the new one at the same surface points, and the broad tone pin (as mm9_annud_claude/v2/scripts/match_skin.py)."""
import numpy as np
from PIL import Image
from scipy import ndimage


def raster(uv, size):
    """Triangle index per texel (row 0 = v 1), -1 outside. uv: M x 3 x 2."""
    tri = np.full((size, size), -1, np.int32)
    P = uv * size
    for t in range(len(P)):
        p = P[t]
        x0, x1 = max(int(np.floor(p[:, 0].min())), 0), min(int(np.ceil(p[:, 0].max())), size - 1)
        y0, y1 = max(int(np.floor(p[:, 1].min())), 0), min(int(np.ceil(p[:, 1].max())), size - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = p
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        inside = (l1 >= -1e-3) & (l2 >= -1e-3) & (1 - l1 - l2 >= -1e-3)
        iy, ix = np.nonzero(inside)
        tri[size - 1 - (iy + y0), ix + x0] = t
    return tri


def pad(img, covered):
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]


def load(path, mode='RGB'):
    return np.asarray(Image.open(path).convert(mode), np.float32)


def down(arr, size):
    """Lanczos downsample of a float image (0..255), once."""
    if arr.shape[0] == size:
        return arr
    if arr.ndim == 2:
        return np.asarray(Image.fromarray(arr.astype(np.float32), 'F').resize((size, size), Image.LANCZOS), np.float32)
    return np.stack([down(arr[..., k], size) for k in range(arr.shape[2])], -1)


def save(arr, path):
    Image.fromarray(np.clip(np.round(arr), 0, 255).astype(np.uint8)).save(path)


def bilinear(img, u, v):
    H, W = img.shape[:2]
    x, y = u * W - 0.5, (1 - v) * H - 0.5
    x0, y0 = np.clip(np.floor(x).astype(int), 0, W - 2), np.clip(np.floor(y).astype(int), 0, H - 2)
    fx, fy = np.clip(x - x0, 0, 1), np.clip(y - y0, 0, 1)
    if img.ndim == 3:
        fx, fy = fx[:, None], fy[:, None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
            + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


def resample(old_img, pairs, size, nearest=False):
    """The old-layout image on the new layout: per new texel, the old texel of the same surface point."""
    out = np.zeros((size, size) + old_img.shape[2:], np.float32)
    cover = np.zeros((size, size), bool)
    H = old_img.shape[0]
    for to, tn in zip(pairs['old'], pairs['new']):
        p = np.stack([tn[:, 0] * size, (1 - tn[:, 1]) * size], 1)
        lo, hi = np.floor(p.min(0)).astype(int), np.ceil(p.max(0)).astype(int) + 1
        xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], size)), np.arange(max(lo[1], 0), min(hi[1], size)))
        if not xs.size:
            continue
        q = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
        T = np.array([p[1] - p[0], p[2] - p[0]]).T
        if abs(np.linalg.det(T)) < 1e-9:
            continue
        st = (q - p[0]) @ np.linalg.inv(T).T
        w = np.stack([1 - st.sum(1), st[:, 0], st[:, 1]], 1)
        inside = (w >= -0.01).all(1)
        if not inside.any():
            continue
        uv = w[inside] @ to
        yy, xx = ys.ravel()[inside], xs.ravel()[inside]
        if nearest:
            out[yy, xx] = old_img[np.clip(((1 - uv[:, 1]) * H).astype(int), 0, H - 1),
                                  np.clip((uv[:, 0] * H).astype(int), 0, H - 1)]
        else:
            out[yy, xx] = bilinear(old_img, uv[:, 0], uv[:, 1])
        cover[yy, xx] = True
    return out, cover


def broad_shift(new, approved, mask, sigma):
    """blur(approved - new), mask-normalised: the tone difference at the scale of sigma texels."""
    m = mask.astype(np.float32)
    den = ndimage.gaussian_filter(m, sigma)
    diff = (approved - new) * m[..., None]
    return np.stack([ndimage.gaussian_filter(diff[..., k], sigma) for k in range(3)], -1) / np.maximum(den, 1e-4)[..., None]


def lum(a):
    return a[..., :3] @ np.array([0.2126, 0.7152, 0.0722], np.float32)
