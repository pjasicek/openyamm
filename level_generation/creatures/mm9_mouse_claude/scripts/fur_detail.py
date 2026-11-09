"""Fur detail for the mouse (imported by compose_mouse.py).

The 4K Meshy paint has the right colours (grey-brown back, cream belly, pink ears) but turned the fur into a coarse,
high-contrast ripple (viewer shots: zebra or fingerprint lines, wavelength about 2 mm). So the colour is split: the low
frequencies stay Meshy's (blurred inside each UV island, then again in 3D, so chart borders cannot show), and the
ripple is replaced by short
hair strokes: line integral convolution of noise along a hair flow field (snout to tail, sweeping down the flanks),
evaluated per texel through each triangle's UV map, so strokes keep their length in millimetres on every chart. The
normal map gets the same split. Tail and paws keep the Meshy paint (rings, toes); inner ears take a faint version.
"""
import numpy as np
from scipy import ndimage

HAIR_MM = 3.2         # stroke length on the model
LOW_SIGMA = 14.0      # px at 2K: above the ripple's wavelength (12-20 px)
AMP = {'fur': 0.20, 'ear': 0.05}
LUM = np.array([0.2126, 0.7152, 0.0722])
GRID_MM, LOW3D_MM = 0.5, 1.8   # the 3D colour grid and its blur


def normalized_blur(img, mask, sigma):
    """Gaussian blur over the masked texels only (normalized convolution), so island borders keep their own colour."""
    w = ndimage.gaussian_filter(mask.astype(np.float32), sigma)
    out = np.stack([ndimage.gaussian_filter(img[..., c] * mask, sigma) for c in range(img.shape[-1])], -1)
    return out / np.maximum(w, 1e-4)[..., None]


def texel_positions(mask, tri, d):
    """3D position of the masked texels (barycentric in their triangle): (ys, xs, xyz)."""
    size = mask.shape[0]
    ys, xs = np.nonzero(mask)
    ti = tri[ys, xs]
    p = d['uv'][ti] * size
    gx, gy = xs + 0.5, size - 1 - ys + 0.5
    a, b, c = p[:, 0], p[:, 1], p[:, 2]
    den = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
    den = np.where(np.abs(den) < 1e-9, 1e-9, den)
    l1 = ((b[:, 1] - c[:, 1]) * (gx - c[:, 0]) + (c[:, 0] - b[:, 0]) * (gy - c[:, 1])) / den
    l2 = ((c[:, 1] - a[:, 1]) * (gx - c[:, 0]) + (a[:, 0] - c[:, 0]) * (gy - c[:, 1])) / den
    return ys, xs, (d['xyz'][ti] * np.stack([l1, l2, 1 - l1 - l2], 1)[..., None]).sum(1)


def seamless_low(low, mask, tri, d):
    """Low-frequency colour by position instead of by chart: the blurred texels are splatted into a 3D grid, blurred
    there and read back per texel, so neither chart borders nor the long body triangles can show."""
    ys, xs, pos = texel_positions(mask, tri, d)
    lo = pos.min(0) - GRID_MM * 1e-3 * 6
    idx = ((pos - lo) / (GRID_MM * 1e-3)).astype(int)
    shape = tuple(idx.max(0) + 7)
    num = np.zeros(shape, np.float32)
    np.add.at(num, tuple(idx.T), 1)
    sigma = LOW3D_MM / GRID_MM
    weight = ndimage.gaussian_filter(num, sigma)
    out = low.copy()
    colors = low[ys, xs]
    for c in range(3):
        acc = np.zeros(shape, np.float32)
        np.add.at(acc, tuple(idx.T), colors[:, c])
        vol = ndimage.gaussian_filter(acc, sigma) / np.maximum(weight, 1e-5)
        out[ys, xs, c] = ndimage.map_coordinates(vol, ((pos - lo) / (GRID_MM * 1e-3)).T, order=1)
    # ear backs and rims: Meshy's white flecks (texels no master saw) capped at the ear's own brightness
    ears = (np.abs(pos[:, 0]) > 0.014) & (pos[:, 2] > 0.028) & (pos[:, 1] > -0.095) & (pos[:, 1] < -0.05)
    vals = out[ys, xs]
    lum = vals @ LUM
    cap = 1.06 * np.median(lum[ears])
    over = ears & (lum > cap)
    vals[over] *= (cap / lum[over])[:, None]
    out[ys, xs] = vals
    return out


def uv_flow(uv, xyz, normal, size):
    """Per triangle: the hair direction in image pixels (x right, y down) and pixels per model unit along it."""
    e1, e2 = xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]
    d1 = (uv[:, 1] - uv[:, 0]) * [size, -size]    # image axes: v up becomes row down
    d2 = (uv[:, 2] - uv[:, 0]) * [size, -size]
    c = xyz.mean(1)
    # hair runs snout to tail (+Y) and sweeps from the dorsal line down the flanks
    side = np.stack([np.sign(c[:, 0]) * 0.25, np.zeros(len(c)), -0.45 * np.clip(np.abs(c[:, 0]) / 0.028, 0, 1)], 1)
    f = np.array([0.0, 1.0, 0.0]) + side
    f = f - (f * normal).sum(1, keepdims=True) * normal
    f /= np.maximum(np.linalg.norm(f, axis=1, keepdims=True), 1e-9)
    # solve f = a e1 + b e2 in the triangle plane
    g11, g12, g22 = (e1 * e1).sum(1), (e1 * e2).sum(1), (e2 * e2).sum(1)
    b1, b2 = (f * e1).sum(1), (f * e2).sum(1)
    det = g11 * g22 - g12 * g12
    det = np.where(np.abs(det) < 1e-20, 1e-20, det)
    a = (g22 * b1 - g12 * b2) / det
    b = (g11 * b2 - g12 * b1) / det
    v = a[:, None] * d1 + b[:, None] * d2
    rate = np.linalg.norm(v, axis=1)
    return v / np.maximum(rate, 1e-9)[:, None], rate


def lic(noise, dirx, diry, length, mask, steps=28):
    """Line integral convolution of noise along the per-texel unit directions, length in px (Hann weight)."""
    ys, xs = np.nonzero(mask)
    h, w = noise.shape
    total = noise[ys, xs].astype(np.float32).copy()
    weight = np.ones(len(ys), np.float32)
    for sign in (1, -1):
        px, py = xs.astype(np.float32), ys.astype(np.float32)
        step = (length[ys, xs] / (2 * steps)).astype(np.float32)
        for k in range(1, steps + 1):
            ix, iy = np.clip(px.round().astype(int), 0, w - 1), np.clip(py.round().astype(int), 0, h - 1)
            px = px + sign * dirx[iy, ix] * step
            py = py + sign * diry[iy, ix] * step
            ix, iy = np.clip(px.round().astype(int), 0, w - 1), np.clip(py.round().astype(int), 0, h - 1)
            wk = 0.5 + 0.5 * np.cos(np.pi * k / (steps + 1))
            inside = mask[iy, ix]
            total += np.where(inside, noise[iy, ix] * wk, 0)
            weight += np.where(inside, wk, 0)
    out = np.zeros_like(noise, dtype=np.float32)
    out[ys, xs] = total / weight
    return out


def hair_field(tri, d, size, seed=9):
    """Unit-variance hair detail over the covered texels (fine strokes + longer, sparser dark guard hairs)."""
    dirs, rate = uv_flow(d['uv'], d['xyz'], d['normal'], size)
    cov = tri >= 0
    ti = np.maximum(tri, 0)
    dirx, diry = np.where(cov, dirs[ti, 0], 0).astype(np.float32), np.where(cov, dirs[ti, 1], 0).astype(np.float32)
    length = np.where(cov, rate[ti] * HAIR_MM * 1e-3, 1.0).astype(np.float32)
    rng = np.random.default_rng(seed)
    fine = lic(rng.standard_normal((size, size)).astype(np.float32), dirx, diry, length, cov)
    coarse_n = ndimage.gaussian_filter(rng.standard_normal((size, size)).astype(np.float32), 1.2)
    coarse = lic(coarse_n, dirx, diry, length * 1.6, cov)
    fine = (fine - fine[cov].mean()) / fine[cov].std()
    coarse = (coarse - coarse[cov].mean()) / coarse[cov].std()
    detail = 0.7 * fine + 0.3 * coarse - 0.35 * np.clip(-coarse - 1.2, 0, None)
    return detail / detail[cov].std(), length


def apply(base2k, nrm2k, tri, d, fur, ear, rest):
    """base2k, nrm2k: 2K float images; fur, ear: 2K masks of the regions to rebuild; rest stays Meshy's."""
    size = base2k.shape[0]
    detail, _ = hair_field(tri, d, size)
    lowc = seamless_low(normalized_blur(base2k, fur, LOW_SIGMA), fur, tri, d)
    lowe = normalized_blur(base2k, ear, LOW_SIGMA / 2)
    # Meshy left white flecks on the ear rims (texels no master view saw): clamp to the ear's own brightness
    lum = lowe @ np.array([0.2126, 0.7152, 0.0722])
    med = np.median(lowe[ear], axis=0)
    k = np.clip((lum / max(float(med @ np.array([0.2126, 0.7152, 0.0722])), 1e-3) - 1.15) / 0.2, 0, 1)
    lowe = lowe + (med - lowe) * k[..., None]
    out = base2k.copy()
    out[fur] = np.clip(lowc[fur] * (1 + AMP['fur'] * detail[fur])[:, None], 0, 1)
    out[ear] = np.clip(lowe[ear] * (1 + AMP['ear'] * detail[ear])[:, None], 0, 1)
    # normals: Meshy's low frequencies plus a whisper of hair relief (y down, Meshy's convention)
    n = nrm2k * 2 - 1
    both = fur | ear
    low = normalized_blur(n, both, LOW_SIGMA)
    h = ndimage.gaussian_filter(detail, 0.7) * 0.5
    gy, gx = np.gradient(h)
    rel = low.copy()
    rel[..., 0] -= gx
    rel[..., 1] -= gy
    rel /= np.maximum(np.linalg.norm(rel, axis=-1, keepdims=True), 1e-6)
    nout = n.copy()
    nout[both] = rel[both]
    return out, nout * 0.5 + 0.5
