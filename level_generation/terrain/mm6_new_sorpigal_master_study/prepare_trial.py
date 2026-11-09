"""Build isolated x2 terrain trials or reproduce historical x4 studies; never writes into assets_dev."""

import argparse
import configparser
import json
from pathlib import Path
import shutil

from PIL import Image

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
CATALOGUE = PROJECT.parent / 'mm6_new_sorpigal'


def mirror_assets(source, destination):
    # PhysicsFS accepts links to entire mounted art directories, but refuses links inside a mount.
    if destination.is_symlink():
        destination.unlink()
    destination.mkdir(parents=True, exist_ok=True)
    for child in source.iterdir():
        target = destination / child.name
        if child.name in {'terrain_x2', 'terrain_x4'}:
            continue
        if child.is_dir():
            if child.name in {'textures', 'terrain', 'sprites', 'icons', 'audio', 'music', 'videos',
                              'maps', 'events', '_legacy'}:
                if not target.exists():
                    target.symlink_to(child, target_is_directory=True)
            else:
                mirror_assets(child, target)
        else:
            if target.is_symlink():
                target.unlink()
            if not target.exists():
                shutil.copy2(child, target)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--variant', choices=['runtime_x2', 'v1', 'v2', 'v3'], default='runtime_x2')
    parser.add_argument('--road-swatches', action='store_true',
                        help='Reproduce historical full-tile paving diagnostics; not final road composition')
    args = parser.parse_args()
    runtime_export = args.variant == 'runtime_x2'
    if runtime_export and args.road_swatches:
        parser.error('Runtime exports require masked cobble-over-dirt tiles; full-tile road swatches are historical only.')
    if runtime_export:
        from export_runtime import export_runtime
        runtime_manifest = export_runtime()
    tile_size = 256 if runtime_export else 512
    tier = 'x2' if runtime_export else 'x4'
    stage = Path('/tmp/openyamm-sorpigal-terrain-master-study') / args.variant
    assets = stage / 'assets_dev'
    mirror_assets(ROOT / 'assets_dev', assets)
    terrain = assets / 'engine' / ('terrain_' + tier)
    terrain.mkdir(parents=True, exist_ok=True)
    catalogue = json.loads((CATALOGUE / 'catalogue.json').read_text())
    # Preserve native mixed artwork and exact cyan shoreline keys at the selected tier.
    for tile in catalogue['tiles']:
        Image.open(CATALOGUE / tile['source_rgb']).resize(
            (tile_size, tile_size), Image.Resampling.NEAREST).save(terrain / (tile['name'] + '.png'))
    # Keep water at the original x1 appearance. No generated water in this study.
    for source in (CATALOGUE / 'water_animation/runtime_x1').glob('*.png'):
        Image.open(source).resize((tile_size, tile_size), Image.Resampling.NEAREST).save(terrain / source.name)

    replacements = {'6grastyl': 'grass', '6dirttyl': 'dirt', '6voltyl': 'volcano'}
    # The cobble master needs a road mask over dirt. Full-tile paving is an explicit diagnostic only.
    if args.road_swatches:
        replacements.update({tile['name']: 'cobbles' for tile in catalogue['tiles'] if tile['family'] == 'roads'})
    versions = {'grass': 'v1', 'cobbles': 'v1',
                'dirt': 'v3' if args.variant == 'v3' else 'v1',
                'volcano': 'v1' if args.variant == 'v1' else 'v2'}
    if runtime_export:
        versions = {name: record['version'] for name, record in runtime_manifest['materials'].items()}
    for name, material in replacements.items():
        version = versions[material]
        source = (PROJECT / 'runtime_x2/materials' / (material + '.png') if runtime_export
                  else PROJECT / 'generated' / version / (material + '_512.png'))
        with Image.open(source) as image:
            assert image.size == (tile_size, tile_size), source
        shutil.copy2(source, terrain / (name + '.png'))

    settings = configparser.ConfigParser()
    settings.read(PROJECT / 'references/settings_original.ini')
    settings['assets']['root'] = str(assets)
    settings['video_quality']['terrain'] = tier
    with (stage / 'settings.ini').open('w') as stream:
        settings.write(stream)
    (PROJECT / f'trial_replacements_{args.variant}.json').write_text(json.dumps({
        'terrain_size': tile_size, 'terrain_tier': tier, 'other_asset_tiers': 'x1',
        'stage': str(stage), 'replacements': replacements, 'material_versions': versions,
        'road_status': ('Diagnostic full-tile paving swatches; NOT final road composition.' if args.road_swatches
                        else 'Original road tiles retained until cobble-over-dirt mask composition is ready.'),
        'mixed_tiles': 'Original native artwork, nearest resized; masks deferred.',
        'water': 'Original x1 frame appearance, nearest resized; no generated water.'
    }, indent=2) + '\n')
    print(f'Prepared {len(replacements)} material replacements in {terrain}')


if __name__ == '__main__':
    main()
