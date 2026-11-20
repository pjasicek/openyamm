"""Build an isolated, reproducible Brackenford terrain comparison using existing runtime tiers.

ImageMagick only performs deterministic export/resampling and adapts the saved imagegen
grass master. This does not generate artwork or regenerate any geometry.
"""
import configparser
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import shutil
import subprocess
import sys

import yaml

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
ORIGINAL = PROJECT.parent / 'brackenford_greywatch'
PLAYTEST = PROJECT / 'playtest'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args):
    subprocess.run([str(arg) for arg in args], check=True)


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def prepare():
    source = PROJECT / 'source'
    source.mkdir(exist_ok=True)
    package = source / 'brackenford_greywatch_content.zip'
    # Freeze the package and terrain metadata once; never refresh a running experiment.
    if not package.exists():
        shutil.copy2(ORIGINAL / 'dist' / package.name, package)
        for name in ['lg01.terrain.yml', 'lg01.scene.yml']:
            shutil.copy2(ORIGINAL / 'source' / name, source / name)
    if not (PLAYTEST / 'playtest_snapshot.json').exists():
        run(sys.executable, ORIGINAL / 'prepare_playtest.py', '--no-project-state',
            '--directory', PLAYTEST, '--package', package)

    assets = PLAYTEST / 'assets_editor_dev'
    environment = yaml.safe_load((source / 'lg01.scene.yml').read_text())['environment']
    terrain = yaml.safe_load((source / 'lg01.terrain.yml').read_text())
    counts = Counter(bytes.fromhex(terrain['tile_map_hex']))
    with (assets / 'engine/data_tables/terrain_tile_data.txt').open() as stream:
        descriptors = list(csv.DictReader(stream, delimiter='\t'))
    tile_names = {}
    # Cover all valid atlas entries as well as all actually painted cells.
    for tile_id in range(234):
        if tile_id < 90:
            index = tile_id if tile_id == 0 else [0, 450, 630][environment['master_tile']] + tile_id
        else:
            index = environment['tile_set_lookup_indices'][(tile_id - 90) // 36] + (tile_id - 90) % 36
        tile_names[tile_id] = descriptors[index]['texture_name'].strip().lower() or 'pending'
    names = set(tile_names.values())
    materials = yaml.safe_load((assets / 'engine/rendering/surface_materials.yml').read_text())['materials']
    for material in materials:
        match = material.get('match', {})
        if any(name in match.get('texture_names', []) or
               any(name.startswith(prefix) for prefix in match.get('texture_prefixes', [])) for name in names):
            names.update(frame['texture'].lower() for frame in material.get('animation', {}).get('frames', []))

    # Match terrain-first runtime lookup; original-world bitmaps are the final fallback.
    available = {}
    for directory in [assets / 'worlds/mm8/terrain', assets / 'engine/terrain',
                      assets / 'worlds/mm8/textures', assets / 'engine/textures']:
        if directory.exists():
            for path in sorted(directory.iterdir()):
                if path.suffix.lower() in {'.png', '.bmp'}:
                    available.setdefault(path.stem.lower(), path)
    missing = sorted(names - available.keys())
    if missing:
        raise ValueError('Missing terrain sources: ' + ', '.join(missing))

    native = PROJECT / 'tiles/native'
    smooth = PROJECT / 'tiles/smooth2x'
    ai = PROJECT / 'tiles/ai2x'
    work = PROJECT / 'work'
    for directory in [native, smooth, ai, work]:
        directory.mkdir(parents=True, exist_ok=True)
    records = []
    for name in sorted(names):
        original = available[name]
        # Decode the legacy magenta key before filtering: no pink halo at shore edges.
        run('convert', original, '-alpha', 'set', '-transparent', 'rgb(252,0,252)',
            '-transparent', 'rgb(255,0,255)', 'PNG32:' + str(native / (name + '.png')))
        run('convert', native / (name + '.png'), '-filter', 'Mitchell', '-resize', '256x256!',
            'PNG32:' + str(smooth / (name + '.png')))
        shutil.copy2(smooth / (name + '.png'), ai / (name + '.png'))
        records.append({'name': name, 'source': str(original.relative_to(assets)),
                        'source_sha256': digest(original),
                        'painted_cells': sum(count for tile_id, count in counts.items()
                                             if tile_names[tile_id] == name)})

    # Modest AI contribution, fading to zero at tile boundaries. The native transition
    # family stays untouched. This is a grass-only style pilot, not a finished tileset.
    master = PROJECT / 'reference/grass_ai_master.png'
    run('convert', master, '-filter', 'Lanczos', '-resize', '256x256!', work / 'grass_ai_256.png')
    run('convert', '-size', '256x256', 'xc:black', '-fx',
        '0.4*min(1,max(0,(min(min(i,j),min(w-1-i,h-1-j))-4)/28))', work / 'grass_weight.png')
    run('convert', smooth / 'grastyl.png', work / 'grass_ai_256.png', work / 'grass_weight.png',
        '-compose', 'Over', '-composite', 'PNG32:' + str(ai / 'grastyl.png'))
    for record in records:
        record['smooth2x_sha256'] = digest(smooth / (record['name'] + '.png'))
        record['ai2x_sha256'] = digest(ai / (record['name'] + '.png'))
    manifest = {'map': 'lg01.odm', 'world': 'mm8', 'grid_samples': [128, 128], 'grid_spacing': 512,
                'original_tile_pixels': 128, 'experiment_tile_pixels': 256,
                'package_sha256': digest(package), 'native_map_sha256': digest(assets / 'worlds/mm8/maps/lg01.odm'),
                'terrain_source_sha256': digest(source / 'lg01.terrain.yml'),
                'method': {'smooth2x': 'ImageMagick Mitchell resampling; no invented detail',
                           'ai2x': 'smooth2x plus built-in imagegen grass; 40% interior blend, original edges',
                           'ai_scope': ['grastyl'], 'ai_master_sha256': digest(master),
                           'ai_prompt': 'reference/grass_ai_prompt.txt'},
                'tiles': records}
    write_json(PROJECT / 'manifest.json', manifest)

    for variant in ['native', 'smooth2x', 'ai2x']:
        directory = PROJECT / 'variants' / variant
        directory.mkdir(parents=True, exist_ok=True)
        mounted = assets
        if variant != 'native':
            mounted = directory / 'assets'
            mounted.mkdir(exist_ok=True)
            # Mount directory links, never writable links to individual shared assets.
            for child in assets.iterdir():
                target = mounted / child.name
                if child.name != 'worlds' and not target.exists():
                    target.symlink_to(child, target_is_directory=child.is_dir())
            worlds = mounted / 'worlds'
            worlds.mkdir(exist_ok=True)
            for world in (assets / 'worlds').iterdir():
                target = worlds / world.name
                if world.name != 'mm8':
                    if not target.exists():
                        target.symlink_to(world, target_is_directory=True)
                    continue
                target.mkdir(exist_ok=True)
                for child in world.iterdir():
                    link = target / child.name
                    if child.name != 'terrain_x2' and not link.exists():
                        link.symlink_to(child, target_is_directory=child.is_dir())
                overlay = target / 'terrain_x2'
                if not overlay.exists():
                    overlay.symlink_to(PROJECT / 'tiles' / variant, target_is_directory=True)
        settings = configparser.ConfigParser()
        settings.read(PLAYTEST / 'outdoor/settings.ini')
        settings['assets']['root'] = str(mounted)
        settings['video_quality'] = {key: 'x1' for key in
                                    ['texture', 'terrain', 'sky', 'sprites', 'decorations', 'icons', 'ui', 'effects', 'fonts']}
        settings['video_quality']['terrain'] = 'x1' if variant == 'native' else 'x2'
        settings['video'] = {'terrain_filtering': 'anisotropic', 'terrain_anisotropy': '8x',
                             'resolution': '1600x900', 'window_mode': 'windowed', 'vsync': 'false'}
        with (directory / 'settings.ini').open('w') as stream:
            settings.write(stream, space_around_delimiters=False)
        saves = directory / 'saves'
        saves.mkdir(exist_ok=True)
        for save in (PLAYTEST / 'outdoor/saves').glob('*.oysav'):
            if not (saves / save.name).exists():
                shutil.copy2(save, saves / save.name)
    print(f'Prepared {len(records)} terrain images per variant; {len(counts)} painted tile IDs. Run ./play.sh ai2x')


if __name__ == '__main__':
    prepare()
