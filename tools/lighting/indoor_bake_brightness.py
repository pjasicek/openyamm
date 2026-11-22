#!/usr/bin/env python3
"""How bright an indoor bake renders: per map, the face texture's mean colour times its lightmap, as the indoor shader
draws them (sRGB texel x lighting, clamped at 1), sampled over every lightmapped face by area.

    python3 tools/lighting/indoor_bake_brightness.py [--assets assets_dev] [--world xeen] [stem ...]
        [--textures N] [--check]

Columns: rendered mean luma (0-255, Rec. 709 on the sRGB result), its 90th percentile, the clipped share (a channel at
1, before any torch), the mean lighting value and the mean texture luma. `--textures N` lists each map's N brightest
textures by area. `--check` fails on a map whose mean is over MEAN_LIMIT (devdocs/INDOOR_BAKED_LIGHTING.md, "Brightness
check"; decision D-100 of the Xeen world): the Torch Light adds up to about 0.76 x the texture on the walls nearest
the party, so a bake that already draws near white leaves the torch nothing but clipping (F23, The Sphinx).

Without a torch the brightest MM6-MM8 interiors render at about 110 in screenshots (MM7's Grand Temple of the Sun,
t03), their dungeons at 30-45; room views run about 20 over this area mean. The clipped share is a hint (per channel
on the texture's mean colour, it counts more than screenshots show under warm lamps), not a limit. Maps without a
sidecar are skipped.
"""
import argparse
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(Path(__file__).resolve().parent)]
from util.map_export import parse_blv_file  # noqa: E402
from bake_assets import bake_texture_paths, liquid_face_colours  # noqa: E402

MEAN_LIMIT = 95.0       # rendered mean luma, 0-255: the profiles' rendered_limit (90) and this tool's sampling margin
LUMA = np.array([0.2126, 0.7152, 0.0722])
SAMPLE_AREA = 32.0 * 32.0


def read_lighting(path):
    data = path.read_bytes()
    magic, _version, _header, _hash, face_count, _sectors, page_count, _deps, page_off, face_off = \
        struct.unpack_from('<8sIIQ6I', data, 0)[:10]
    if magic != b'OYILIT1\0':
        raise ValueError(f'{path}: not an indoor lighting file')
    pages = []
    for index in range(page_count):
        width, height, offset, size = struct.unpack_from('<4I', data, page_off + 16 * index)
        payload = np.frombuffer(data, np.uint8, size, offset)
        texels = np.empty((width * height, 4), np.uint8)
        pos = filled = 0
        while pos < size:
            tag = int(payload[pos])
            count = (tag & 127) + 1
            if tag & 128:
                texels[filled:filled + count] = payload[pos + 1:pos + 5]
                pos += 5
            else:
                texels[filled:filled + count] = payload[pos + 1:pos + 1 + 4 * count].reshape(count, 4)
                pos += 1 + 4 * count
            filled += count
        rgb = texels[:, [2, 1, 0]].astype(np.float32) / 255 * (texels[:, 3:4].astype(np.float32) / 255) * 4
        pages.append(rgb.reshape(height, width, 3))
    faces = []
    for index in range(face_count):
        page, _flags, *axes = struct.unpack_from('<HH8f', data, face_off + 36 * index)
        faces.append(None if page == 0xFFFF else (page, np.array(axes[:4]), np.array(axes[4:])))
    return pages, faces


_TEXTURE_CACHE = {}


def texture_colour(path):
    """Mean sRGB colour (0-1) of a bitmap's opaque texels (magenta key excluded)."""
    if path not in _TEXTURE_CACHE:
        pixels = np.asarray(Image.open(path).convert('RGB'), np.float32).reshape(-1, 3) / 255
        key = (pixels[:, 0] >= 248 / 255) & (pixels[:, 1] <= 8 / 255) & (pixels[:, 2] >= 248 / 255)
        kept = pixels[~key]
        _TEXTURE_CACHE[path] = kept.mean(axis=0) if len(kept) else np.zeros(3)
    return _TEXTURE_CACHE[path]


def face_samples(points, rng):
    """Uniform points over a planar polygon (fan triangles) and the area each stands for."""
    tris = [(points[0], points[i], points[i + 1]) for i in range(1, len(points) - 1)]
    out, weights = [], []
    for a, b, c in tris:
        area = np.linalg.norm(np.cross(b - a, c - a)) / 2
        if area <= 0:
            continue
        n = int(min(max(area / SAMPLE_AREA, 2), 400))
        r1, r2 = rng.random(n), rng.random(n)
        s = np.sqrt(r1)
        out.append((1 - s)[:, None] * a + (s * (1 - r2))[:, None] * b + (s * r2)[:, None] * c)
        weights.append(np.full(n, area / n))
    if not out:
        return np.zeros((0, 3)), np.zeros(0)
    return np.vstack(out), np.concatenate(weights)


def measure(assets, world, stem, texture_paths, liquids, lighting_dir=None):
    maps = assets / 'worlds' / world / 'maps'
    pages, lit = read_lighting((lighting_dir or maps) / f'{stem}.lighting')
    blv = parse_blv_file(maps / f'{stem}.blv')['payload']
    vertices = np.array([[v['x'], v['y'], v['z']] for v in blv['vertices']], float)
    rng = np.random.default_rng(1)
    rendered, lighting, albedo, weights, textures = [], [], [], [], []
    for face, entry in zip(blv['faces'], lit):
        if entry is None or face['is_portal']:
            continue
        name = face['texture_name'].lower()
        if name in texture_paths:
            colour = texture_colour(texture_paths[name])
        elif name in liquids:
            colour = np.clip(np.array(liquids[name], float), 0, 1) ** (1 / 2.2)
        else:
            continue
        page, u_axis, v_axis = entry
        points = vertices[face['vertex_indices'][:face['vertex_per_face_count']]]
        samples, w = face_samples(points, rng)
        if not len(w):
            continue
        height, width, _ = pages[page].shape
        u = samples @ u_axis[:3] + u_axis[3]
        v = samples @ v_axis[:3] + v_axis[3]
        x = np.clip((u * width).astype(int), 0, width - 1)
        y = np.clip((v * height).astype(int), 0, height - 1)
        light = pages[page][y, x]
        rendered.append(np.minimum(colour * light, 1.0))
        lighting.append(light)
        albedo.append(np.repeat(colour[None], len(w), axis=0))
        weights.append(w)
        textures.append(np.full(len(w), name, dtype=object))
    rendered, lighting, albedo = np.vstack(rendered), np.vstack(lighting), np.vstack(albedo)
    weights, textures = np.concatenate(weights), np.concatenate(textures)
    luma = rendered @ LUMA * 255
    order = np.argsort(luma)
    cumulative = np.cumsum(weights[order]) / weights.sum()
    clipped = (rendered.max(axis=1) >= 0.995)
    by_texture = {}
    for name in np.unique(textures):
        sel = textures == name
        by_texture[name] = (weights[sel].sum(), np.average(luma[sel], weights=weights[sel]),
                            float(albedo[sel][0] @ LUMA * 255))
    return {'mean': float(np.average(luma, weights=weights)),
            'p90': float(luma[order][np.searchsorted(cumulative, 0.9)]),
            'clip': float(weights[clipped].sum() / weights.sum() * 100),
            'light': float(np.average(lighting @ LUMA, weights=weights)),
            'albedo': float(np.average(albedo @ LUMA, weights=weights) * 255),
            'textures': by_texture}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('stems', nargs='*', help='map stems (default: every map of the world with a sidecar)')
    parser.add_argument('--assets', type=Path, default=ROOT / 'assets_dev')
    parser.add_argument('--world', default='xeen')
    parser.add_argument('--textures', type=int, default=0)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--lighting-dir', type=Path, help='read the sidecars from here (a scratch bake) instead')
    args = parser.parse_args()
    assets = args.assets.resolve()
    maps = assets / 'worlds' / args.world / 'maps'
    stems = args.stems or sorted(p.stem for p in maps.glob('*.lighting') if p.with_suffix('.blv').exists())
    texture_paths, _ = bake_texture_paths(assets, args.world)
    liquids, _ = liquid_face_colours(assets, args.world)
    failures = []
    print('map\tmean\tp90\tclip%\tlight\talbedo')
    for stem in stems:
        if not ((args.lighting_dir or maps) / f'{stem}.lighting').exists():
            continue
        r = measure(assets, args.world, stem, texture_paths, liquids, args.lighting_dir)
        flag = ''
        if r['mean'] > MEAN_LIMIT:
            flag = '\tOVER'
            failures.append(stem)
        print(f"{stem}\t{r['mean']:.0f}\t{r['p90']:.0f}\t{r['clip']:.1f}\t{r['light']:.2f}\t{r['albedo']:.0f}{flag}")
        if args.textures:
            rows = sorted(r['textures'].items(), key=lambda kv: -kv[1][1] * (kv[1][0] > 0))
            total = sum(v[0] for v in r['textures'].values())
            for name, (area, mean, alb) in [row for row in rows if row[1][0] / total > 0.02][:args.textures]:
                print(f'    {name}\t{area / total * 100:.0f}% area\trendered {mean:.0f}\ttexture {alb:.0f}')
    if args.check and failures:
        print(f'{len(failures)} over the mean limit {MEAN_LIMIT:.0f}: ' + ' '.join(failures))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
