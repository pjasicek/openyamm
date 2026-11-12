#!/usr/bin/env python3
"""xatlas charts and packing for one triangle mesh (TEXTURE_QUALITY_PASS.md). Runs in claude_shared/xatlas_venv
(`python3 -m venv xatlas_venv && xatlas_venv/bin/pip install xatlas==0.0.11 numpy`); uv_atlas.py calls it from
Blender. UVs are per triangle corner (M x 3 x 2, v up as in Blender).

  xatlas_charts.py charts <in.npz> <out.npz> [--max-cost 2] [--roundness 0.5]
      in: positions (N x 3), triangles (M x 3). out: uv (charts flattened at a common scale, packed loosely),
      chart (M). xatlas cuts charts at creases and where flattening would stretch; never overlapping.
  xatlas_charts.py pack <in.npz> <out.npz> [--size 2048] [--padding 3]
      in: uv (M x 3 x 2, islands at their wanted relative scale), vert (M x 3 mesh vertex ids). Islands are the
      UV-connected pieces. out: uv packed into one square size x size atlas with `padding` texels between islands
      (brute-force placement, rotation), the largest uniform scale that still fits (binary search on texels per
      unit), so the texel density stays isotropic and every island keeps its relative scale.
      --height-share S (0 < S < 1) packs into the lower S of the square instead (v 0..S, the rest stays free for a
      strip painted by other means): islands are turned to their smallest bounding box, stretched by 1/S in v and
      packed without rotation, then squeezed back, so they stay isotropic.
"""
import argparse
import time

import numpy as np
import xatlas


def components(index):
    parent = np.arange(index.max() + 1)

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for a, b, c in index:
        for u, v in ((a, b), (b, c)):
            ru, rv = find(u), find(v)
            if ru != rv:
                parent[ru] = rv
    return np.array([find(t[0]) for t in index])


def charts(args):
    data = np.load(args.inp)
    pos, tri = data['positions'].astype(np.float32), data['triangles'].astype(np.uint32)
    atlas = xatlas.Atlas()
    atlas.add_mesh(pos, tri)
    options = xatlas.ChartOptions()
    options.max_cost = args.max_cost
    options.roundness_weight = args.roundness
    pack = xatlas.PackOptions()
    pack.resolution = 2048
    pack.padding = 2
    pack.rotate_charts = True
    atlas.generate(options, pack)
    vmap, idx, uvs = atlas[0]
    assert len(idx) == len(tri) and np.allclose(pos[vmap[idx]], pos[tri])
    corner = (uvs[idx] * [atlas.width, atlas.height]).astype(np.float64)   # isotropic texel units
    corner /= corner.max()
    corner[..., 1] = 1.0 - corner[..., 1]
    chart = np.unique(components(idx), return_inverse=True)[1]
    print('XATLAS charts', atlas.chart_count)
    np.savez(args.out, uv=corner.astype(np.float32), chart=chart.astype(np.int32))


def uv_area(uv):
    d1, d2 = uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]
    return float(np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]).sum() / 2)


def turn_to_box(uv, vertex_island):
    """Each island rotated about its centre to its smallest bounding box (1 degree steps), in place."""
    angles = np.radians(np.arange(0, 90))
    cos, sin = np.cos(angles)[:, None], np.sin(angles)[:, None]
    for i in np.unique(vertex_island):
        m = vertex_island == i
        p = uv[m].astype(np.float64)
        p -= p.mean(0)
        x, y = cos * p[:, 0] - sin * p[:, 1], sin * p[:, 0] + cos * p[:, 1]
        box = np.ptp(x, axis=1) * np.ptp(y, axis=1)
        k = int(np.argmin(box))
        uv[m] = np.stack([x[k], y[k]], 1)


def try_pack(uv, idx, size, padding, tpu, brute, rotate=True):
    atlas = xatlas.Atlas()
    atlas.add_uv_mesh(uv, idx)
    options = xatlas.PackOptions()
    options.resolution = size
    options.padding = padding
    options.bilinear = True
    options.rotate_charts = rotate
    options.rotate_charts_to_axis = rotate
    options.bruteForce = brute
    options.texels_per_unit = tpu
    atlas.generate(xatlas.ChartOptions(), options)
    ok = atlas.atlas_count == 1 and atlas.width <= size and atlas.height <= size
    return ok, atlas


def pack(args):
    data = np.load(args.inp)
    corner, vert = data['uv'].astype(np.float64), data['vert']
    # one packing vertex per (mesh vertex, uv) pair, so islands are the UV-connected pieces
    keys = np.concatenate([vert.reshape(-1, 1), np.round(corner.reshape(-1, 2), 7)], 1)
    unique, inverse = np.unique(keys, axis=0, return_inverse=True)
    uv = unique[:, 1:].astype(np.float32)
    idx = inverse.reshape(-1, 3).astype(np.uint32)
    # xatlas merges islands that overlap in the input, so spread them on shelves first (scale is kept)
    island = components(idx)
    vertex_island = np.zeros(len(uv), np.int64)
    vertex_island[idx.ravel()] = np.repeat(island, 3)
    share = args.height_share
    rotate = share >= 1.0
    if not rotate:
        turn_to_box(uv, vertex_island)
        uv[:, 1] /= share
    gap = float(np.ptp(uv, 0).max()) * 0.01
    area = uv_area(corner) / share
    padding = args.padding if rotate else int(np.ceil(args.padding / share))   # the margin survives the squeeze
    row_width = np.sqrt(area) * 3
    x = y = row_height = 0.0
    for i in np.unique(island):
        m = vertex_island == i
        lo, hi = uv[m].min(0), uv[m].max(0)
        if x > 0 and x + hi[0] - lo[0] > row_width:
            x, y, row_height = 0.0, y + row_height + gap, 0.0
        uv[m] += np.array([x, y], np.float32) - lo
        x += hi[0] - lo[0] + gap
        row_height = max(row_height, hi[1] - lo[1])
    hi = size_tpu = args.size / np.sqrt(area)                 # 100 % use: an upper bound
    lo = hi * 0.3
    best = None
    start = time.time()
    for _ in range(8):                                       # fast packer brackets the scale
        mid = (lo + hi) / 2
        ok, atlas = try_pack(uv, idx, args.size, padding, mid, False, rotate)
        if ok:
            lo, best = mid, (mid, atlas)
        else:
            hi = mid
    # the fast packer is not monotonic either: a fine sweep above the bracket costs seconds (Dragon King 2026-10-30:
    # 53.6 % where ten brute-force steps found nothing in 27 minutes)
    base = lo
    for step in range(1, args.fine + 1):
        tpu = base * (1 + 0.001 * step)
        ok, atlas = try_pack(uv, idx, args.size, padding, tpu, False, rotate)
        if ok:
            best = (tpu, atlas)
            print(f'XATLAS fine x{1 + 0.001 * step:.3f} fits', flush=True)
    base = best[0]
    # brute force fits more, and success is not monotonic in the scale: try every step, keep the largest that fits
    for step in range(1, args.steps + 1):
        tpu = base * (1 + 0.02 * step)
        ok, atlas = try_pack(uv, idx, args.size, padding, tpu, True, rotate)
        print(f'XATLAS brute x{1 + 0.02 * step:.2f} {"fits" if ok else "-"}', flush=True)
        if ok:
            best = (tpu, atlas)
    tpu, atlas = best
    vmap, out_idx, out_uv = atlas[0]
    packed = out_uv[out_idx] * [atlas.width, atlas.height] / args.size
    packed[..., 1] = (1.0 - packed[..., 1]) * share
    # xatlas keeps the triangle order; check the corners still belong to the same vertices
    assert np.array_equal(vmap[out_idx], idx)
    used = uv_area(packed)
    print(f'XATLAS packed islands {len(np.unique(island))} (xatlas charts {atlas.chart_count}) use {used:.3f} '
          f'texels/unit {tpu:.0f} '
          f'(upper bound {size_tpu:.0f}) {time.time() - start:.0f}s')
    np.savez(args.out, uv=packed.astype(np.float32))


parser = argparse.ArgumentParser()
sub = parser.add_subparsers(dest='mode', required=True)
c = sub.add_parser('charts')
c.add_argument('inp')
c.add_argument('out')
c.add_argument('--max-cost', type=float, default=2.0)
c.add_argument('--roundness', type=float, default=0.5)
p = sub.add_parser('pack')
p.add_argument('inp')
p.add_argument('out')
p.add_argument('--size', type=int, default=2048)
p.add_argument('--padding', type=int, default=2)
p.add_argument('--steps', type=int, default=10, help='brute-force tries above the fast packer, 2 %% apart')
p.add_argument('--fine', type=int, default=0, help='fast-packer tries above the bracket, 0.1 %% apart')
p.add_argument('--height-share', type=float, default=1.0, help='pack into the lower share of the square')
args = parser.parse_args()
charts(args) if args.mode == 'charts' else pack(args)
