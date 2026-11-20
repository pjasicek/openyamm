#!/usr/bin/env python3
"""Nearest-texel gutter re-fill (TEXTURE_QUALITY_PASS.md, post step, last on every map): every texel outside the UV
islands takes the value of the nearest island texel, so mip levels and bilinear lookups at island borders read the
island's own colour instead of darkened, graded or black gutters (uv_research_20261111/layout/RESULTS.md, verdict A:
-16 % colour leak at mip 4 on the Magreeb, -48 % on the BHydra; black gutters are 3-4x worse). Reference:
mm6_bh_texpass_claude/scripts/texlib.py `pad`.

    gutter_fill.py <uv source: .glb | .npz> <map.png> [<map.png> ...] [--material <substring>] [--out-dir <dir> |
        --suffix _filled | --in-place]

UV source: a GLB (the triangles of its first mesh, or of the primitives whose material name contains --material; glTF
UVs, image row = v x height) or an npz with `uv` (M x 3 x 2, glTF v-down, e.g. sparrow output converted). Each map is
filled at its own size (2K colour, 1K normal and masks); every channel, alpha included, is copied from the same nearest
island texel. Island coverage is conservative: a texel counts as island when any triangle touches it (centre test at
4x supersampling), the texels a bilinear lookup inside the islands can read.

As a function (numpy arrays):
    from gutter_fill import coverage, pad
    covered = coverage(tri_uv, height, width); filled = pad(image, covered)
"""
import argparse
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from texture_quality import accessor, read_glb  # noqa: E402

Image.MAX_IMAGE_PIXELS = None


def pad(img, covered):
    """Fills every texel outside `covered` (H x W bool) with the nearest covered texel's value (all channels)."""
    if covered.all() or not covered.any():
        return img.copy()
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]


def coverage(tri_uv, height, width, supersample=4):
    """H x W bool: texels any triangle touches (glTF UVs: x = u * width, row = v * height)."""
    sh, sw = height * supersample, width * supersample
    fine = np.zeros((sh, sw), bool)
    p = np.asarray(tri_uv, np.float64) * [sw, sh]
    for a, b, c in p:
        lo = np.maximum(np.floor(np.minimum(np.minimum(a, b), c)).astype(int), 0)
        hi = np.minimum(np.ceil(np.maximum(np.maximum(a, b), c)).astype(int) + 1, [sw, sh])
        if hi[0] <= lo[0] or hi[1] <= lo[1]:
            continue
        gy, gx = np.mgrid[lo[1]:hi[1], lo[0]:hi[0]] + 0.5
        w0 = (b[0] - a[0]) * (gy - a[1]) - (b[1] - a[1]) * (gx - a[0])
        w1 = (c[0] - b[0]) * (gy - b[1]) - (c[1] - b[1]) * (gx - b[0])
        w2 = (a[0] - c[0]) * (gy - c[1]) - (a[1] - c[1]) * (gx - c[0])
        inside = ((w0 >= 0) & (w1 >= 0) & (w2 >= 0)) | ((w0 <= 0) & (w1 <= 0) & (w2 <= 0))
        fine[lo[1]:hi[1], lo[0]:hi[0]] |= inside
        # needle triangles thinner than a sub-texel: mark their corners too
        for q in (a, b, c):
            x, y = int(min(max(q[0], 0), sw - 1)), int(min(max(q[1], 0), sh - 1))
            fine[y, x] = True
    return fine.reshape(height, supersample, width, supersample).any(axis=(1, 3))


def uv_triangles(source, material=None):
    """Per-corner UVs (M x 3 x 2, glTF) from a GLB's first mesh (optionally only primitives whose material name
    contains `material`) or from an npz with `uv`."""
    if str(source).endswith('.npz'):
        return np.load(source)['uv'].astype(np.float64)
    doc, binary = read_glb(source)
    out = []
    for prim in doc['meshes'][0]['primitives']:
        if 'TEXCOORD_0' not in prim['attributes']:
            continue
        if material is not None:
            name = doc['materials'][prim['material']].get('name', '') if 'material' in prim else ''
            if material not in name:
                continue
        uv = accessor(doc, binary, prim['attributes']['TEXCOORD_0'])
        idx = accessor(doc, binary, prim['indices']).astype(np.int64).reshape(-1, 3)
        out.append(uv[idx])
    if not out:
        raise ValueError(f'no UV triangles in {source} (material {material!r})')
    return np.concatenate(out).astype(np.float64)


def fill_file(tri_uv, src, dst):
    im = Image.open(src)
    mode = im.mode
    a = np.asarray(im)
    covered = coverage(tri_uv, a.shape[0], a.shape[1])
    Image.fromarray(pad(a, covered), mode).save(dst)
    return float(covered.mean())


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('uv_source')
    parser.add_argument('maps', nargs='+')
    parser.add_argument('--material')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--out-dir')
    group.add_argument('--suffix')
    group.add_argument('--in-place', action='store_true')
    args = parser.parse_args()
    tri_uv = uv_triangles(args.uv_source, args.material)
    for path in map(Path, args.maps):
        if args.out_dir:
            os.makedirs(args.out_dir, exist_ok=True)
            dst = Path(args.out_dir) / path.name
        elif args.suffix:
            dst = path.with_name(path.stem + args.suffix + path.suffix)
        else:
            dst = path.with_name(path.stem + '.gutter_tmp' + path.suffix)    # temp + rename: never write in place
        share = fill_file(tri_uv, path, dst)
        if args.in_place:
            os.replace(dst, path)
            dst = path
        print(f'GUTTER {path} -> {dst}: islands cover {100 * share:.1f} %')


if __name__ == '__main__':
    main()
