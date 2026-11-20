"""Colour leak between UV islands in a mip chain (gutter / margin research).

Definition (per island texel p of island i, mip level k):
  actual_k(p) = bilinear sample of the box mip chain of the whole map (linear light, 2x2 box: the engine's mips) at
                p's UV, as the GPU does at level k;
  pure_k(p)   = the same sample of a chain built from island i alone (its own texels, everything else filled from
                them by push-pull), i.e. what the island would look like with an infinite private gutter;
  leak_k(p)   = mean over RGB of |sRGB(actual) - sRGB(pure)| in 8-bit levels.
Reported per level over all island texels (texel-weighted, so surface-weighted at one density): mean, p95 and the
share of texels with leak > 4 levels (about a just-visible step on a mid-tone).
foreign_k: geometry-only proxy, the share of the bilinear footprint at level k that comes from texels owned by
another island (ownership = nearest island texel, i.e. a perfect nearest-texel fill); independent of the paint.
"""
import numpy as np
from scipy import ndimage

import uvlib


def pad_pow2(a, valid):
    h, w = valid.shape
    n = 1 << int(np.ceil(np.log2(max(h, w))))
    A = np.zeros((n, n) + a.shape[2:], a.dtype)
    V = np.zeros((n, n), bool)
    A[:h, :w], V[:h, :w] = a, valid
    return A, V


def context(tri_uv, tri_pos, size=2048):
    isl = uvlib.island_ids(tri_uv, tri_pos)
    labels = uvlib.raster_labels(tri_uv, isl, size)
    owner = uvlib.voronoi(labels)
    return {'size': size, 'isl': isl, 'labels': labels, 'owner': owner, 'n': int(isl.max() + 1)}


def fill_black(img, ctx):
    out = img.copy()
    out[ctx['labels'] < 0] = 0
    return out


def fill_nearest(img, ctx):
    """Every gutter texel takes the nearest island texel's colour (Meshy's own fill, texlib.pad)."""
    empty = ctx['labels'] < 0
    _, (iy, ix) = ndimage.distance_transform_edt(empty, return_indices=True)
    return img[iy, ix]


def fill_pushpull_global(img, ctx):
    return uvlib.push_pull(img, ctx['labels'] >= 0)


def fill_pushpull_owned(img, ctx, pad=64):
    """Gutter texels owned by island i (nearest-island Voronoi cell) take island i's own push-pull extension: a smooth
    continuation of the island's colours instead of streaks, and never another island's."""
    out = img.astype(np.float64).copy()
    labels, owner = ctx['labels'], ctx['owner']
    size = ctx['size']
    objs = ndimage.find_objects(owner + 1)
    for i, sl in enumerate(objs):
        if sl is None:
            continue
        y0, y1 = max(sl[0].start - pad, 0), min(sl[0].stop + pad, size)
        x0, x1 = max(sl[1].start - pad, 0), min(sl[1].stop + pad, size)
        crop = img[y0:y1, x0:x1].astype(np.float64)
        valid = labels[y0:y1, x0:x1] == i
        if not valid.any():
            continue
        A, V = pad_pow2(crop, valid)
        filled = uvlib.push_pull(A, V)[:y1 - y0, :x1 - x0]
        target = (owner[y0:y1, x0:x1] == i) & (labels[y0:y1, x0:x1] < 0)
        out[y0:y1, x0:x1][target] = filled[target]
    return out


def sharpen_chain(chain, strength):
    """The cook's sharpenMips on levels >= 1: value + strength x (value - 3x3 mean), clamped, in linear light, image
    edges clamped (cook_model_textures_main.cpp)."""
    if not strength:
        return chain
    out = [chain[0]]
    for mip in chain[1:]:
        if min(mip.shape[:2]) < 4:
            out.append(mip)
            continue
        mean = ndimage.uniform_filter(mip, size=(3, 3, 1) if mip.ndim == 3 else 3, mode='nearest')
        out.append(np.clip(mip + strength * (mip - mean), 0, 1))
    return out


def _sample(mip, ys, xs, k):
    """Bilinear sample of a level-k mip at level-0 texel centres (ys, xs are level-0 integer texel indices)."""
    s = 2.0 ** k
    cy, cx = (ys + 0.5) / s - 0.5, (xs + 0.5) / s - 0.5
    if mip.ndim == 2:
        return ndimage.map_coordinates(mip, [cy, cx], order=1, mode='nearest')
    return np.stack([ndimage.map_coordinates(mip[..., c], [cy, cx], order=1, mode='nearest')
                     for c in range(mip.shape[2])], 1)


def leak(img, ctx, levels=5, limit=4.0, pure_cache=None, chain=None, sharpen=0.0):
    """img: filled sRGB 0-255 map (size x size x 3). Returns per-level stats (see module doc)."""
    size = ctx['size']
    labels, owner = ctx['labels'], ctx['owner']
    lin = uvlib.srgb_to_linear(img.astype(np.float64))
    if chain is None:
        chain = sharpen_chain(uvlib.box_mips(lin, levels), sharpen)
    align = 2 ** levels
    pad = 3 * align
    errs = [[] for _ in range(levels + 1)]
    foreign = [[] for _ in range(levels + 1)]
    own_chain_cache = {}
    objs = ndimage.find_objects(labels + 1)
    for i, sl in enumerate(objs):
        if sl is None:
            continue
        y0 = max((sl[0].start - pad) // align * align, 0)
        x0 = max((sl[1].start - pad) // align * align, 0)
        y1 = min(-(-(sl[0].stop + pad) // align) * align, size)
        x1 = min(-(-(sl[1].stop + pad) // align) * align, size)
        mine = labels[y0:y1, x0:x1] == i
        ys, xs = np.nonzero(mine)
        if pure_cache is not None and i in pure_cache:
            pure_chain = pure_cache[i]
        else:
            A, V = pad_pow2(lin[y0:y1, x0:x1], mine)
            pure = uvlib.push_pull(A, V)
            pure_chain = sharpen_chain(uvlib.box_mips(pure, levels), sharpen)
            if pure_cache is not None:
                pure_cache[i] = pure_chain
        own = (owner[y0:y1, x0:x1] == i).astype(np.float64)
        Ao, _ = pad_pow2(own, mine)
        own_chain = uvlib.box_mips(Ao, levels)
        for k in range(1, levels + 1):
            s = 2 ** k
            local = chain[k][y0 // s:y1 // s, x0 // s:x1 // s]
            a = _sample(local, ys, xs, k)
            p = _sample(pure_chain[k], ys, xs, k)
            e = np.abs(uvlib.linear_to_srgb(a) - uvlib.linear_to_srgb(p)).mean(1)
            errs[k].append(e)
            foreign[k].append(1.0 - _sample(own_chain[k], ys, xs, k))
    out = []
    for k in range(1, levels + 1):
        e, f = np.concatenate(errs[k]), np.concatenate(foreign[k])
        out.append({'mip': k, 'leak_mean': round(float(e.mean()), 2), 'leak_p95': round(float(np.percentile(e, 95)), 1),
                    'over_limit_pct': round(100 * float((e > limit).mean()), 2),
                    'foreign_mean_pct': round(100 * float(f.mean()), 2),
                    'foreign_over10_pct': round(100 * float((f > 0.1).mean()), 2)})
    return out


def gaps(ctx):
    """Per island: distance in texels to the nearest texel of another island (edge to edge), median and p10."""
    labels = ctx['labels']
    size = ctx['size']
    res = []
    objs = ndimage.find_objects(labels + 1)
    for i, sl in enumerate(objs):
        if sl is None:
            continue
        y0, y1 = max(sl[0].start - 40, 0), min(sl[0].stop + 40, size)
        x0, x1 = max(sl[1].start - 40, 0), min(sl[1].stop + 40, size)
        crop = labels[y0:y1, x0:x1]
        other = (crop >= 0) & (crop != i)
        if not other.any():
            continue
        d = ndimage.distance_transform_edt(~other)
        res.append(float(d[crop == i].min()) - 1.0)
    res = np.array(res)
    return {'gap_min_px': float(res.min()), 'gap_p10_px': float(np.percentile(res, 10)),
            'gap_median_px': float(np.median(res))}
