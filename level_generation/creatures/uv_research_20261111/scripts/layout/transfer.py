"""Carry a paint from one layout to another with the same triangles (same order): each target texel is 2x2
supersampled, mapped through its triangle's barycentric coordinates to the source layout and sampled bilinearly
there. Texels whose centre is outside every triangle stay empty (gutter, filled by the caller)."""
import numpy as np
from scipy import ndimage

import uvlib


def transfer(src_img, src_uv, dst_uv, size=2048, ss=2):
    n = size * ss
    tri_index = uvlib.raster_labels(dst_uv, np.arange(len(dst_uv)), n)
    ys, xs = np.nonzero(tri_index >= 0)
    t = tri_index[ys, xs]
    p = np.stack([(xs + 0.5) / n, (ys + 0.5) / n], 1)
    a, b, c = dst_uv[t, 0], dst_uv[t, 1], dst_uv[t, 2]
    v0, v1, v2 = b - a, c - a, p - a
    d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
    d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
    den = d00 * d11 - d01 * d01
    den[np.abs(den) < 1e-30] = 1e-30
    w1 = (d11 * d20 - d01 * d21) / den
    w2 = (d00 * d21 - d01 * d20) / den
    w0 = 1 - w1 - w2
    q = w0[:, None] * src_uv[t, 0] + w1[:, None] * src_uv[t, 1] + w2[:, None] * src_uv[t, 2]
    sh = src_img.shape[0]
    cy, cx = q[:, 1] * sh - 0.5, q[:, 0] * sh - 0.5
    lin = uvlib.srgb_to_linear(src_img.astype(np.float64))
    vals = np.stack([ndimage.map_coordinates(lin[..., ch], [cy, cx], order=1, mode='nearest') for ch in range(3)], 1)
    acc = np.zeros((n, n, 3))
    cnt = np.zeros((n, n))
    acc[ys, xs] = vals
    cnt[ys, xs] = 1
    acc = acc.reshape(size, ss, size, ss, 3).sum((1, 3))
    cnt = cnt.reshape(size, ss, size, ss).sum((1, 3))
    out = uvlib.linear_to_srgb(acc / np.maximum(cnt, 1)[..., None])
    return out
