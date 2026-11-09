"""Rebuild accepted terrain with quilted periodic borders, without new AI artwork.

Opposite border pixels are consecutive texture samples, not identical averages.
Only coverage/shading fields are edge-extended during minification; materials wrap.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, map_coordinates

P = Path(__file__).resolve().parent
T = P.parent
L = T / 'mm6_new_sorpigal_transitions'
W = T / 'mm6_new_sorpigal_water'
S = T / 'mm6_new_sorpigal_master_study'
sys.path.insert(0, str(L))
from compose_tiles import linear, srgb


def read(path):
    return np.asarray(Image.open(path), dtype=float)


def byte(a):
    return np.uint8(np.clip(np.rint(a), 0, 255))


def pad(a, mode):
    return np.pad(a, [(8, 8), (8, 8)] + [(0, 0)] * (a.ndim - 2), mode=mode)


def reduce(a):
    # 528 authoring pixels -> 264 runtime pixels, then remove the four-pixel gutter.
    return np.asarray(Image.fromarray(byte(a)).resize((264, 264), Image.Resampling.LANCZOS))[4:-4, 4:-4]


def closed_cut(cost):
    """Minimum-error cyclic cut, with adjacent rows moving at most one pixel."""
    n, width = cost.shape
    scores = np.full((width, width), np.inf)
    scores[np.arange(width), np.arange(width)] = cost[0]
    parents = np.empty((n, width, width), dtype=np.int8)
    for y in range(1, n):
        choices = np.stack([np.pad(scores[:, :-1], ((0, 0), (1, 0)), constant_values=np.inf),
                            scores, np.pad(scores[:, 1:], ((0, 0), (0, 1)), constant_values=np.inf)])
        choice = choices.argmin(axis=0)
        parents[y] = choice.astype(np.int8) - 1
        scores = choices.min(axis=0) + cost[y][None, :]
    start = int(np.diag(scores).argmin())
    path = np.empty(n, dtype=int)
    path[-1] = start
    for y in range(n - 1, 0, -1):
        path[y - 1] = path[y] + parents[y, start, path[y]]
    assert path[0] == path[-1]
    return path


def periodic(a):
    """Borrow existing interior detail for both sides of each wrap, join with narrow cuts."""
    original = a.copy()
    for axis in (1, 0):
        b = a if axis == 1 else a.transpose(1, 0, 2)
        donor = np.roll(b, 256, axis=1)
        for reverse in (False, True):
            target = b[:, ::-1] if reverse else b
            source = donor[:, ::-1] if reverse else donor
            cost = np.mean((target[:, 16:64] - source[:, 16:64]) ** 2, axis=2)
            path = closed_cut(cost) + 16
            x = np.arange(512)[None, :]
            # At most a one-pixel blend along an irregular minimum-error cut.
            weight = np.clip(path[:, None] + 0.5 - x, 0, 1)[:, :, None]
            target[:] = target * (1 - weight) + source * weight
        a = b if axis == 1 else b.transpose(1, 0, 2)
    assert np.array_equal(a[64:-64, 64:-64], original[64:-64, 64:-64])
    return a


def detail(a):
    a = a.astype(float)
    high = a - gaussian_filter(a, sigma=(1, 1, 0), mode='wrap')
    border = np.zeros(a.shape[:2], bool)
    border[:4] = border[-4:] = True
    border[:, :4] = border[:, -4:] = True
    return float(np.sqrt(np.mean(high[border] ** 2)) / np.sqrt(np.mean(high[16:-16, 16:-16] ** 2)))


def main():
    out = P / 'runtime_x2/worlds/mm6/terrain_x2'
    author = P / 'authoring'
    materials_dir = P / 'materials'
    for directory in (out, author, materials_dir):
        directory.mkdir(parents=True, exist_ok=True)
    decisions = json.loads((S / 'material_decisions.json').read_text())
    materials = {}
    sources = {}
    for name in ('water', 'grass', 'dirt', 'volcano', 'cobbles'):
        source = W / 'raw/water_v1.png' if name == 'water' else S / decisions[name]['master_png']
        a = np.asarray(Image.open(source).convert('RGB').resize((512, 512), Image.Resampling.LANCZOS), dtype=float)
        sources[name] = {'path': str(source.relative_to(T)), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
        materials[name] = periodic(a)
        Image.fromarray(byte(materials[name])).save(materials_dir / (name + '.png'))
    runtime = {}
    def save(name, a):
        Image.fromarray(byte(a[8:-8, 8:-8])).save(author / (name + '.png'))
        runtime[name] = reduce(a)
        Image.fromarray(runtime[name]).save(out / (name + '.png'))
    mat = {name: linear(pad(a, 'wrap')) for name, a in materials.items()}
    for tile, name in [('6dirttyl', 'dirt'), ('6grastyl', 'grass'), ('6voltyl', 'volcano')]:
        save(tile, srgb(mat[name]))
    for record in json.loads((L / 'mask_inventory.json').read_text())['masks']:
        name = record['tile']
        alpha = pad(read(L / 'masks/connected_v4' / (name + '.png')) / 255, 'edge')[:, :, None]
        delta = pad(np.load(L / 'edge_treatment/layers/v5' / (name + '.npz'))['linear_rgb_delta'], 'edge')
        save(name, srgb(mat['dirt'] * (1 - alpha) + mat[record['white']] * alpha + delta))
    yy, xx = np.mgrid[:512, :512]
    u, v = xx / 512, yy / 512
    frames = []
    for f in range(14):
        phase = 2 * np.pi * f / 14
        dx = 5 * np.sin(2 * np.pi * v + phase) + 2 * np.sin(4 * np.pi * (u + v) - phase)
        dy = 4 * np.sin(2 * np.pi * u - phase) + 2 * np.sin(4 * np.pi * (u - v) + phase)
        a = np.stack([map_coordinates(materials['water'][:, :, c], [yy + dy, xx + dx],
                                      order=1, mode='grid-wrap') for c in range(3)], axis=2)
        name = f'6hdwtr{f:03}'
        save(name, pad(a, 'wrap'))
        frames.append(runtime[name])
    save('6wtrtyl', pad(read(author / '6hdwtr000.png'), 'wrap'))
    old_dirt = read(L / 'material_seams/connected_v2/dirt.png')
    for path in sorted((W / 'authoring/v1').glob('6wtrdr*.png')):
        old = read(path)
        # Recover the already reviewed contact shading; keep its alpha and exact dirt phase.
        shade = np.clip(np.mean(old[:, :, :3] / np.maximum(old_dirt, 1), axis=2), 0.8, 1)
        rgb = pad(materials['dirt'], 'wrap') * pad(shade, 'edge')[:, :, None]
        save(path.stem, np.dstack([rgb, pad(old[:, :, 3], 'edge')]))
    checks = {}
    sheet = Image.new('RGB', (1024, 5 * 288), '#202933')
    draw = ImageDraw.Draw(sheet)
    for i, (name, tile) in enumerate([('water', '6wtrtyl'), ('grass', '6grastyl'), ('dirt', '6dirttyl'),
                                    ('volcano', '6voltyl'), ('cobbles', '6drsrew')]):
        old_dir = W if name == 'water' else L
        before = read(old_dir / 'runtime_x2/worlds/mm6/terrain_x2' / (tile + '.png'))
        after = runtime[tile]
        checks[name] = {'before_border_detail_ratio': detail(before), 'after_border_detail_ratio': detail(after)}
        for j, a in enumerate((before, after)):
            repeated = np.tile(byte(a), (2, 2, 1))
            sheet.paste(Image.fromarray(repeated).resize((512, 256)), (j * 512, i * 288 + 24))
        draw.text((8, i * 288 + 5), name + ' — before / after', fill='white')
    sheet.save(P / 'comparison.png')
    animation = [Image.fromarray(np.tile(f, (2, 2, 1))) for f in frames]
    animation[0].save(P / 'water_loop.webp', save_all=True, append_images=animation[1:], duration=117, loop=0, lossless=True)
    steps = [float(np.abs(frames[(i + 1) % 14].astype(float) - frames[i]).mean()) for i in range(14)]
    report = {'sources': sources, 'runtime_size': 256, 'files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.png')},
              'detail': checks, 'animation_steps': steps, 'loop_step_ratio': steps[-1] / np.mean(steps),
              'central_384_square_master_pixels_unchanged': True,
              'method': 'Periodic donor strips with cyclic minimum-error cuts; wrapped material gutters; existing coverage and edge deltas reused.'}
    (P / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    manifest = {'iteration': 'periodic_borders_v1', 'size': [256, 256], 'dirt_master': 'v6',
                'coverage_masks': 'connected_v4 unchanged', 'edge_treatment': 'Existing v5 linear RGB deltas',
                'water': '14 frames and 12 shore overlays, existing alpha and contact shade',
                'files': {'worlds/mm6/terrain_x2/' + n: h for n, h in report['files'].items()}}
    (P / 'runtime_x2/manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'files': len(report['files']), 'detail': checks, 'loop_step_ratio': report['loop_step_ratio']}, indent=2))


if __name__ == '__main__':
    main()
