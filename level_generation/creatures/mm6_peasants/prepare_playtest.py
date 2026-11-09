"""Stage original/enhanced New Sorpigal residents without changing development assets."""

import argparse
import configparser
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import yaml
from PIL import Image

from prepare_decorations import install_decorations


PROJECT = Path(__file__).resolve().parent
REPO = PROJECT.parents[2]
DEFAULT_STAGE = Path('/tmp/openyamm-sorpigal-peasants-playtest')
DEFAULT_SAVE = (REPO / 'level_generation/terrain/mm6_new_sorpigal_master_study'
                / 'references/poses/cobbles.oysav')
SHORE_TERRAIN = REPO / ('level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/'
                  'transitions/shorelines/runtime_x2')
TERRAIN = REPO / 'level_generation/terrain/mm6_remaining/transitions/runtime_x2'
FAMILIES = {
    'pfem': 'mm6_pfem',
    'pman': 'mm6_pman',
    'pmn2': 'mm6_pmn2',
    'gob': 'mm6_goblin/direct_complete',
    'gua': 'mm6_gua',
}
# These directories are mounted separately by AssetFileSystem. Linking individual files inside
# a PhysicsFS mount is not supported. Tables/rendering/sprites_new remain real, private copies.
SHARED_DIRECTORIES = {'textures', 'terrain', 'sprites', 'icons', 'audio', 'music', 'videos',
                      'maps', 'events', '_legacy', 'terrain_x2', 'terrain_x4'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install_terrain(stage):
    """Install the reviewed land/water overlay and its existing corrected map in enhanced mode."""
    marker = stage / 'playtest_snapshot.json'
    report = json.loads(marker.read_text())
    if report['world'] != 'mm6' or report['map'] != 'oute3.odm':
        raise ValueError('Not a New Sorpigal playtest')
    manifest = json.loads((SHORE_TERRAIN / 'manifest.json').read_text())
    prefix = Path('worlds/mm6/terrain_x2')
    if manifest['iteration'] != 'dirt_fidelity_shores_v2' or len(manifest['files']) != 63:
        raise ValueError('Expected the reviewed new-dirt shoreline pack with 63 tiles')
    seams = json.loads((SHORE_TERRAIN.parent / 'local_seams.json').read_text())
    if not seams['pass'] or seams['files'] != {Path(n).name: h for n, h in manifest['files'].items()}:
        raise ValueError('Local seam validation failed or belongs to a different export')
    validation = json.loads((SHORE_TERRAIN.parent / 'validation.json').read_text())
    if validation['failures']:
        raise ValueError('Terrain join validation failed')
    if validation['files'] != {Path(n).name: h for n, h in manifest['files'].items()}:
        raise ValueError('Terrain validation belongs to a different export')
    animation = json.loads((SHORE_TERRAIN.parent / 'native_animation.json').read_text())
    if not animation['water_animated'] or not animation['stationary_land']:
        raise ValueError('Native water animation validation failed')
    if animation['asset_hashes'] != validation['files']:
        raise ValueError('Native animation validation belongs to a different export')
    accepted = json.loads((SHORE_TERRAIN.parent.parent / 'HANDOFF_ASSETS.json').read_text())['accepted_files']
    if len(accepted) != 51 or any(validation['files'].get(n) != r['sha256'] for n, r in accepted.items()):
        raise ValueError('Accepted land or water was changed')
    if digest(stage / 'openyamm') != animation['binary_sha256']:
        raise ValueError('Executable differs from the native terrain review; review this build before installation')
    shoreline_iteration = manifest['iteration']
    manifest = json.loads((TERRAIN / 'manifest.json').read_text())
    files = {Path(n).name: h for n, h in manifest['files'].items()}
    if manifest['iteration'] != 'mm6_complete_terrain_v1' or len(files) != 134:
        raise ValueError('Expected the complete reviewed MM6 pack with 134 textures')
    complete = json.loads((TERRAIN.parent / 'reports/validation.json').read_text())
    review = json.loads((TERRAIN.parent / 'reports/review.json').read_text())
    native = json.loads((TERRAIN.parent / 'reports/review_stage.json').read_text())
    if complete['failures'] or complete['files'] != files or native['files'] != files:
        raise ValueError('Complete terrain validation failed or belongs to another export')
    if any(files.get(n) != h for n, h in validation['files'].items()):
        raise ValueError('Complete pack changed accepted New Sorpigal terrain or water')
    if digest(stage / 'openyamm') != native['binary_sha256']:
        raise ValueError('Executable differs from the complete terrain native review')
    if set(review['captures']) != {'sand', 'snow', 'cracked', 'tropical', 'swamp'}:
        raise ValueError('Complete terrain native family review is missing')
    for family, evidence in review['captures'].items():
        capture = TERRAIN.parent / 'captures' / ('mm6_' + family)
        if (digest(capture.with_suffix('.png')) != evidence['image_sha256']
                or digest(capture.with_suffix('.json')) != evidence['metadata_sha256']):
            raise ValueError('Terrain capture changed after review: ' + family)
    for name, expected in manifest['files'].items():
        if Path(name).parent != prefix or digest(TERRAIN / name) != expected:
            raise ValueError('Invalid terrain file or hash: ' + name)
    run = stage / 'enhanced'
    target = run / 'assets_dev' / prefix
    # Never write through shared artwork directory links into the repository.
    for parent in (target, *target.parents):
        if parent == stage:
            break
        if parent.is_symlink():
            raise ValueError('Terrain destination must be private: ' + str(parent))
    target.mkdir(parents=True, exist_ok=True)
    correction = REPO / 'level_generation/terrain/mm6_new_sorpigal_water/map_correction'
    patch = json.loads((correction / 'patch.json').read_text())
    maps = run / 'assets_dev/worlds/mm6/maps'
    if not maps.is_symlink() and (maps / 'oute3.odm').is_symlink():
        raise ValueError('Enhanced map file must be private')
    if digest(correction / 'oute3.odm') != patch['output_sha256']:
        raise ValueError('Invalid reviewed terrain map correction')
    if digest(maps / 'oute3.odm') not in (patch['source_sha256'], patch['output_sha256']):
        raise ValueError('Enhanced map has additional changes; do not overwrite it')
    backup = stage / 'seed/terrain_before_mm6_complete_v1'
    backup.mkdir(parents=True, exist_ok=True)
    for name in manifest['files']:
        destination = target / Path(name).name
        if destination.is_symlink():
            raise ValueError('Terrain file must be private: ' + str(destination))
        if destination.exists() and not (backup / destination.name).exists():
            shutil.copy2(destination, backup / destination.name)
        shutil.copy2(TERRAIN / name, destination)
    if maps.is_symlink():
        source_maps = maps.resolve()
        maps.unlink()
        shutil.copytree(source_maps, maps)
    if not (backup / 'oute3.odm').exists():
        shutil.copy2(maps / 'oute3.odm', backup / 'oute3.odm')
    shutil.copy2(correction / 'oute3.odm', maps / 'oute3.odm')
    settings = configparser.ConfigParser(interpolation=None)
    settings.read(run / 'settings.ini')
    if not settings.has_section('video_quality'):
        settings.add_section('video_quality')
    if settings['video_quality'].get('terrain') != 'x2':
        settings['video_quality']['terrain'] = 'x2'
        with (run / 'settings.ini').open('w') as stream:
            settings.write(stream, space_around_delimiters=False)
    report['terrain'] = {**manifest, 'source': str(TERRAIN), 'mode': 'enhanced',
                         'map_correction_installed': True, 'map_sha256': patch['output_sha256']}
    report['water'] = {**report.get('water', {}), 'version': 'native_water_v3',
                       'shoreline_version': shoreline_iteration, 'source': str(SHORE_TERRAIN),
                       'map_correction_installed': True, 'map_patch': patch,
                       'files': {Path(n).name: h for n, h in manifest['files'].items()
                                 if Path(n).name.startswith(('6wtr', '6hdwtr'))}}
    marker.write_text(json.dumps(report, indent=2) + '\n')
    print('Installed complete MM6 terrain: 134 textures, including sand/snow and all transitions; terrain quality x2.')


def install_sky(stage):
    """Stage native MM6 skies at x2 until authentic MM6 restorations are accepted."""
    marker = stage / 'playtest_snapshot.json'
    report = json.loads(marker.read_text())
    if report['world'] != 'mm6' or report['map'] != 'oute3.odm':
        raise ValueError('Not a New Sorpigal playtest')
    native_sources = {
        '6plansky1': 'mm6/textures/6plansky1.bmp',
        '6sky06': 'mm6/textures/6sky06.bmp',
        '6sky12': 'mm6/textures/6sky12.bmp',
        '6sky03': 'mm6/textures/6sky03.bmp',
        '6sky04': 'mm6/textures/6sky04.bmp',
        '6sky19': 'mm6/textures/6sky19.bmp',
    }
    run = stage / 'enhanced'
    # Validate the staged weather table rather than silently omitting a newly configured sky.
    table = run / 'assets_dev/engine/data_tables/continent_settings.txt'
    enroth = next(line.split('\t') for line in table.read_text().splitlines() if line.startswith('3\t'))
    if {name.strip().lower() for name in enroth[21].split(',')} != set(native_sources):
        raise ValueError('Enroth weather skies changed; update the explicit sky export list')
    target = run / 'assets_dev/worlds/mm6/textures_x2'
    for parent in (target, *target.parents):
        if parent == stage:
            break
        if parent.is_symlink():
            raise ValueError('Sky destination must be private: ' + str(parent))
    for name in native_sources:
        if (target / (name + '.png')).is_symlink():
            raise ValueError('Sky destination must be a private file: ' + name)
    binary = REPO / 'build/game/openyamm'
    if not binary.is_file():
        raise FileNotFoundError('Build openyamm first; the sky needs logical-dimension projection support')
    target.mkdir(parents=True, exist_ok=True)
    records = {}
    for name, relative in native_sources.items():
        native = run / 'assets_dev/worlds' / relative
        with Image.open(native) as image:
            size = [image.width * 2, image.height * 2]
        destination = target / (name + '.png')
        # Preserve the native pixels and palette, without presenting these exports as AI restoration.
        subprocess.run(['convert', str(native), '-sample', '200%', '-alpha', 'off',
                        'PNG24:' + str(destination)], check=True)
        destination.chmod(0o644)
        records[name] = {'source': relative, 'source_sha256': digest(native), 'size': size,
                         'method': 'native nearest x2', 'sha256': digest(destination)}
    pending_binary = stage / 'openyamm.next'
    shutil.copy2(binary, pending_binary)
    pending_binary.replace(stage / 'openyamm')
    settings = configparser.ConfigParser(interpolation=None)
    settings.read(run / 'settings.ini')
    if not settings.has_section('video_quality'):
        settings.add_section('video_quality')
    settings['video_quality']['sky'] = 'x2'
    with (run / 'settings.ini').open('w') as stream:
        settings.write(stream, space_around_delimiters=False)
    report['sky'] = {'mode': 'native_mm6_nearest_x2', 'files': records,
                     'note': 'Native palette placeholders; authentic MM6 AI restoration is pending.'}
    report['binary_sha256'] = digest(stage / 'openyamm')
    marker.write_text(json.dumps(report, indent=2) + '\n')
    print('Installed six native MM6 sky exports for seven weather states; sky quality x2; binary refreshed.')


def mirror_assets(source, target):
    target.mkdir()
    for child in source.iterdir():
        destination = target / child.name
        if child.is_dir():
            if child.name in SHARED_DIRECTORIES:
                destination.symlink_to(child.resolve(), target_is_directory=True)
            else:
                mirror_assets(child, destination)
        else:
            shutil.copy2(child, destination)


def install_family(family, engine, update=False):
    source = PROJECT.parent / FAMILIES[family]
    manifest = json.loads((source / 'manifest.json').read_text())
    # Earlier completed packages store their art schema/recolor operation under different keys.
    # Export both explicitly into the compact runtime schema; never change the accepted art manifest.
    model = manifest['recolor']['model'] if family in ('gob', 'pmn2') else manifest['recolor_model']
    expected_model = {'gob': 'masked_regions_luminance_rgb_v1', 'gua': 'multi_mask_luminance_rgb_v1'}.get(
        family, 'masked_luminance_rgb_v1')
    if model != expected_model:
        raise ValueError('Unexpected recoloring contract: ' + family)
    runtime = {key: manifest[key] for key in ('creature', 'pixels_per_logical_pixel', 'logical_canvas',
                                             'logical_pivot', 'variants')}
    runtime.update(schema_version=1, recolor_model=model)
    runtime['pages'] = [{key: page[key] for key in ('base', 'mask', 'size')}
                        for page in manifest['pages']]
    runtime['frames'] = {name: {key: frame[key] for key in ('page', 'atlas_xywh', 'crop_origin_px')}
                         for name, frame in manifest['frames'].items()}
    source_root = engine.parent.parent / 'assets_source/engine/sprites_new'
    target = source_root / ('mm6_' + family)
    if target.is_symlink():
        raise ValueError('Runtime package must be a private directory: ' + str(target))
    target.mkdir(parents=True, exist_ok=update)
    (target / 'atlas').mkdir(exist_ok=update)
    for page in runtime['pages']:
        for key in ('base', 'mask'):
            relative = Path(page[key])
            if relative.parent != Path('atlas') or relative.suffix != '.png':
                raise ValueError('Unexpected atlas path: ' + str(relative))
            shutil.copy2(source / relative, target / relative)
    (target / 'manifest.json').write_text(json.dumps(runtime, indent=2) + '\n')
    subprocess.run([sys.executable, str(REPO / 'tools/cook_sprite_atlases.py'),
                    '--source', str(source_root), '--output', str(engine / 'sprites_new'),
                    '--profile', 'desktop', '--family', 'mm6_' + family], cwd=REPO, check=True)
    return runtime


def wire_frames(path, manifests, original_path=None):
    original = (original_path or path).read_text()
    groups = yaml.load(original, Loader=yaml.CSafeLoader)['sprites']
    bindings = {family: 0 for family in FAMILIES}
    palette_ids = {family: set() for family in FAMILIES}
    replacements = {}
    for group in groups:
        for frame in group['frames']:
            texture = frame['texture_name'].lower()
            family = next((name for name in FAMILIES if texture.startswith(name)
                           and str(frame.get('palette_id')) in manifests[name]['variants']), None)
            if family is None:
                continue
            manifest = manifests[family]
            names = [texture] if 'Image1' in frame.get('flags', []) else [texture + str(i) for i in range(5)]
            if not all(name in manifest['frames'] for name in names):
                raise ValueError('Missing enhanced frame: ' + texture)
            palette = str(frame['palette_id'])
            if palette not in manifest['variants']:
                raise ValueError('Missing enhanced palette: ' + palette)
            frame['texture_name'] = 'atlas:mm6_' + family + '/' + texture
            replacements[texture] = frame['texture_name']
            bindings[family] += 1
            palette_ids[family].add(int(palette))
    if any(count == 0 for count in bindings.values()):
        raise ValueError('Native peasant animation bindings were not found')
    # Preserve native YAML formatting and every field except these texture references.
    pattern = re.compile(r'(texture_name:\s*")(' + '|'.join(map(re.escape, replacements)) + r')(")', re.IGNORECASE)
    replaced, count = pattern.subn(
        lambda match: match[1] + replacements[match[2].lower()] + match[3],
        original)
    if count != sum(bindings.values()) or yaml.load(replaced, Loader=yaml.CSafeLoader)['sprites'] != groups:
        raise ValueError('Texture-only replacement did not preserve the native animation table')
    path.write_text(replaced)
    return {family: {'frame_bindings': bindings[family], 'palettes': sorted(palette_ids[family])}
            for family in FAMILIES}


def prepare(stage, source_save):
    binary = REPO / 'build/game/openyamm'
    if not binary.is_file():
        raise FileNotFoundError('Build first: cmake --build build --target openyamm -j25')
    source_save = source_save.resolve(strict=True)
    if stage.exists():
        raise FileExistsError('Use a new --directory; existing playtests may contain personal saves: ' + str(stage))
    stage.mkdir(parents=True)
    shutil.copy2(binary, stage / 'openyamm')
    (stage / 'seed').mkdir()
    shutil.copy2(source_save, stage / 'seed/New_Sorpigal_Start.oysav')
    bindings = None
    for mode in ('original', 'enhanced'):
        run = stage / mode
        run.mkdir()
        assets = run / 'assets_dev'
        mirror_assets(REPO / 'assets_dev', assets)
        if mode == 'enhanced':
            manifests = {family: install_family(family, assets / 'engine') for family in FAMILIES}
            bindings = wire_frames(assets / 'engine/rendering/sprite_frame_data_common.yml', manifests)
        settings = configparser.ConfigParser(interpolation=None)
        settings.read(REPO / 'settings.ini')
        for section in ('assets', 'startup', 'debug'):
            if not settings.has_section(section):
                settings.add_section(section)
        settings['assets']['root'] = str(assets)
        settings['startup']['start_in_main_menu'] = 'true'
        settings['debug']['start_world'] = 'mm6'
        settings['debug']['start_map_file'] = 'oute3.odm'
        with (run / 'settings.ini').open('w') as stream:
            settings.write(stream, space_around_delimiters=False)
        (run / 'saves').mkdir()
        shutil.copy2(source_save, run / 'saves/New_Sorpigal_Start.oysav')
    report = {
        'stage': str(stage), 'world': 'mm6', 'map': 'oute3.odm', 'families': bindings,
        'source_save': str(source_save), 'seed_sha256': digest(source_save),
        'binary_sha256': digest(stage / 'openyamm'),
        'original_frame_table_sha256': digest(stage / 'original/assets_dev/engine/rendering/sprite_frame_data_common.yml'),
        'enhanced_frame_table_sha256': digest(stage / 'enhanced/assets_dev/engine/rendering/sprite_frame_data_common.yml'),
        'shared_assets': sorted(SHARED_DIRECTORIES),
        'shader_dependency': str(REPO / 'build/runtime/shaders'),
        'review': 'User performs in-game checks; preparation does not run the game or scenarios.',
    }
    (stage / 'playtest_snapshot.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


def update_playtest(stage):
    marker = stage / 'playtest_snapshot.json'
    report = json.loads(marker.read_text())
    if report['world'] != 'mm6' or report['map'] != 'oute3.odm':
        raise ValueError('Not a New Sorpigal playtest')
    original = stage / 'original/assets_dev/engine/rendering/sprite_frame_data_common.yml'
    if digest(original) != report['original_frame_table_sha256']:
        raise ValueError('Original frame table changed; prepare a separate snapshot')
    # Only update the explicit atlas assets, enhanced references, and executable. Save files,
    # settings, map state and gameplay tables are never rewritten by this operation.
    engine = stage / 'enhanced/assets_dev/engine'
    manifests = {family: install_family(family, engine, update=True) for family in FAMILIES}
    table = engine / 'rendering/sprite_frame_data_common.yml'
    pending = table.with_suffix('.pending')
    report['families'] = wire_frames(pending, manifests, original_path=original)
    pending.replace(table)
    binary = stage / 'openyamm.next'
    shutil.copy2(REPO / 'build/game/openyamm', binary)
    binary.replace(stage / 'openyamm')
    report['binary_sha256'] = digest(stage / 'openyamm')
    report['enhanced_frame_table_sha256'] = digest(table)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=DEFAULT_STAGE)
    parser.add_argument('--source-save', type=Path, default=DEFAULT_SAVE,
                        help='Existing New Sorpigal save used identically in both modes')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--update', action='store_true',
                      help='Update enhanced sprites, binary, terrain and sky; preserve saves')
    mode.add_argument('--terrain-only', action='store_true',
                      help='Add/update terrain in an existing playtest; retain its sprites and binary')
    mode.add_argument('--sky-only', action='store_true',
                      help='Add/update sky and binary in an existing playtest; preserve saves and other art')
    args = parser.parse_args()
    if args.sky_only:
        install_sky(args.directory.resolve())
    elif args.terrain_only:
        install_terrain(args.directory.resolve())
    else:
        if args.update:
            update_playtest(args.directory.resolve())
        else:
            prepare(args.directory.resolve(), args.source_save)
        install_terrain(args.directory.resolve())
        install_sky(args.directory.resolve())
        install_decorations(args.directory.resolve())
