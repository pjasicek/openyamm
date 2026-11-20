"""Bake AI-painted boundary edits, keeping reviewed interiors and shared tile-edge profiles.

The AI supplies appearance. This script only limits edits to a coverage-derived band,
reconciles equivalent border strips, and resamples the opaque runtime exports.
"""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt

E = Path(__file__).resolve().parent
P = E.parent
sys.path.insert(0, str(P))
from compose_tiles import linear, srgb


def read(path):
    with Image.open(path) as im:
        return np.asarray(im.convert('RGB').resize((512, 512), Image.Resampling.LANCZOS), dtype=float)


def strip(a, side, depth):
    return {'N': a[depth], 'S': a[-1-depth], 'W': a[:, depth], 'E': a[:, -1-depth]}[side]


def smooth(t):
    t = np.clip(t, 0, 1)
    return t*t*(3-2*t)


def main():
    global P, E
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-directory', type=Path,
                        help='Independent catalogue with the same masks/composites/edge_treatment layout')
    parser.add_argument('--version', default='v5')
    parser.add_argument('--pilot', action='store_true')
    parser.add_argument('--publish-runtime', action='store_true')
    args = parser.parse_args()
    if args.project_directory:
        P = args.project_directory.resolve(strict=True)
        E = P / 'edge_treatment'
    inventory = json.loads((P/'mask_inventory.json').read_text())['masks']
    source_paths = {r['tile']: P/r['source'] for r in inventory}
    originals = {f.stem: read(f) for f in (P/'composites/v4').glob('*.png')}
    bases = {n: linear(a) for n, a in originals.items()}
    deltas = {}
    bands = {}
    generated = []
    for r in inventory:
        name = r['tile']
        raw = E/'raw/v1'/f'{name}.png'
        if not raw.exists():
            assert args.pilot, f'Missing AI boundary edit: {name}'
            continue
        mask = np.asarray(Image.open(P/'masks/connected_v4'/f'{name}.png')) >= 128
        distance = np.where(mask, distance_transform_edt(mask), distance_transform_edt(~mask))
        # Full AI boundary detail through 10px, smoothly back to accepted pixels by 24px.
        # Rock has a narrower, weaker blend because original art has no heavy stone rim.
        inner, outer, strength = (6, 16, .65) if r['white'] == 'volcano' else (10, 24, 1.)
        band = (1-smooth((distance-inner)/(outer-inner))) * strength
        bands[name] = band
        deltas[name] = (linear(read(raw))-bases[name]) * band[:, :, None]
        generated.append(name)

    # The same axis/topology gets the same signed RGB edit at every boundary.
    # Pure-material borders get no edit, including their corners. Mirror-locked first
    # eight pixels cover the Lanczos support of the 512 -> 256 export.
    samples = {}
    for r in inventory:
        if r['tile'] not in deltas:
            continue
        for side, topology in r['edge_topology'].items():
            key = ('horizontal' if side in 'NS' else 'vertical') + ':' + topology
            samples.setdefault(key, []).append(np.mean([
                strip(deltas[r['tile']], side, depth) for depth in range(8)], axis=0))
    profiles = {}
    for key, values in samples.items():
        topology = key.split(':')[1]
        profiles[key] = np.zeros((512, 3)) if topology in (
            'dirt/dirt', 'grass/grass', 'volcano/volcano') else np.mean(values, axis=0)
        profiles[key][:32] = 0
        profiles[key][-32:] = 0

    out = P/'composites'/args.version
    runtime = E/'runtime'/args.version
    out.mkdir(parents=True, exist_ok=True)
    runtime.mkdir(parents=True, exist_ok=True)
    layers = E/'layers'/args.version
    layers.mkdir(parents=True, exist_ok=True)
    report = []
    for r in inventory:
        name = r['tile']
        delta = deltas.get(name, np.zeros((512, 512, 3))).copy()
        if name in deltas:
            for side, topology in r['edge_topology'].items():
                key = ('horizontal' if side in 'NS' else 'vertical') + ':' + topology
                for depth in range(32):
                    weight = 1-smooth((depth-8)/24)
                    row = strip(delta, side, depth)
                    row[:] = row*(1-weight)+profiles[key]*weight
        composite = srgb(bases[name]+delta)
        im = Image.fromarray(composite)
        im.save(out/f'{name}.png')
        im.resize((256, 256), Image.Resampling.LANCZOS).save(runtime/f'{name}.png')
        np.savez_compressed(layers/f'{name}.npz', linear_rgb_delta=delta.astype('float32'))
        if name in bands:
            Image.fromarray(np.rint(bands[name]*255).astype('uint8')).save(layers/f'{name}_band.png')
            interior = bands[name][32:-32, 32:-32] == 0
            unchanged = np.array_equal(composite[32:-32, 32:-32][interior],
                                       originals[name][32:-32, 32:-32][interior])
            assert unchanged, name
            report.append({'tile': name, 'raw_sha256': hashlib.sha256((E/'raw/v1'/f'{name}.png').read_bytes()).hexdigest(),
                           'protected_interior_unchanged': unchanged,
                           'changed_fraction': float(np.mean(np.any(composite != originals[name], axis=2)))})
    for name in ['6dirttyl', '6grastyl', '6voltyl']:
        shutil.copy2(P/'composites/v4'/f'{name}.png', out/f'{name}.png')
        Image.open(out/f'{name}.png').resize((256, 256), Image.Resampling.LANCZOS).save(runtime/f'{name}.png')
    np.savez_compressed(layers/'shared_profiles.npz', **profiles)
    (E/f'bake_{args.version}.json').write_text(json.dumps({
        'version': args.version, 'pilot': args.pilot, 'generated_count': len(generated),
        'authoring_size': 512, 'runtime_size': 256, 'base_composites': 'v4',
        'coverage_masks': 'connected_v4 unchanged', 'water': 'excluded',
        'boundary_band': 'AI RGB edit: full through10px, fade to0 by24px; rock6..16px at65% strength',
        'seams': 'Axis/topology mean AI RGB delta;8px mirrored lock;24px smooth approach',
        'tiles': report}, indent=2)+'\n')
    for family in ['roads', 'grass_dirt', 'rock_dirt']:
        names = [r['tile'] for r in inventory if r['family'] == family and r['tile'] in generated]
        if not names:
            continue
        sheet = Image.new('RGB', (3*256, len(names)*280), '#202933')
        draw = ImageDraw.Draw(sheet)
        for i, name in enumerate(names):
            for j, (label, path) in enumerate([
                ('Original', source_paths[name]),
                ('Before', P/'composites/v4'/f'{name}.png'), ('Edge treatment', runtime/f'{name}.png')]):
                draw.text((j*256+4, i*280+4), name+' '+label, fill='white')
                sheet.paste(Image.open(path).resize((256, 256), Image.Resampling.BILINEAR), (j*256, i*280+24))
        sheet.save(E/f'{family}_{args.version}.png')
    if args.publish_runtime:
        target = P/'runtime_x2/worlds/mm6/terrain_x2'
        for f in runtime.glob('*.png'):
            shutil.copy2(f, target/f.name)
    print(f'Baked {len(generated)} AI boundary edits; exported36 tiles to {runtime}')


if __name__ == '__main__':
    main()
