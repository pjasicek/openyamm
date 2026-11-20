"""Mount compiled bank fixtures and prepare empty-world camera saves without touching production."""
import configparser
import argparse
import json
import shutil
import subprocess

from common import P, ROOT, STAGE, sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--restore-snapshot', action='store_true',
                        help='Recreate temporary mounts using the retained manifest, without changing evidence')
    parser.add_argument('--roads', action='store_true', help='Mount road fixtures with grounded route cameras')
    parser.add_argument('--land', action='store_true', help='Mount flat land-family fixtures')
    parser.add_argument('--extra-banks', action='store_true', help='Mount remaining bank-family native patches')
    args = parser.parse_args()
    assert sum((args.roads, args.land, args.extra_banks)) <= 1
    category = 'road' if args.roads else 'land' if args.land else 'bank_extra' if args.extra_banks else 'bank'
    fixture_path = P / ('reports/' + category + '_fixtures.json')
    manifest_path = P / ('reports/' + category + '_fixture_stage.json')
    fixtures = json.loads(fixture_path.read_text())
    candidates = json.loads((P / 'reports/candidate_stage.json').read_text())
    source_terrain = STAGE / 'enhanced/assets_dev/worlds/mm8/terrain_x2'
    assert {f.name: sha(f) for f in source_terrain.glob('*.png')} == candidates['files']
    seed = P / 'liquids/v1/water_flying.oysav'
    report = dict(fixtures_sha256=sha(fixture_path),
                  candidate_manifest_sha256=sha(P / 'reports/candidate_stage.json'),
                  files=candidates['files'], seed_sha256=sha(seed),
                  binary_sha256=sha(STAGE / 'openyamm'), poses={})
    sources = {f.name: f for f in source_terrain.glob('*.png')}
    if args.restore_snapshot:
        report = json.loads(manifest_path.read_text())
        assert report['binary_sha256'] == sha(STAGE / 'openyamm')
        by_hash = {}
        wanted = set(report['files'].values())
        for path in P.rglob('*.png'):
            if 'runtime' not in path.parts and 'terrain_x2' not in path.parts:
                continue
            digest = sha(path)
            if digest in wanted:
                by_hash[digest] = path
        assert wanted <= set(by_hash), 'Retained runtime source missing from snapshot'
        sources = {name: by_hash[digest] for name, digest in report['files'].items()}
    for family, fixture in fixtures['fixtures'].items():
        folder = P / fixture['folder']
        assert sha(folder / 'out01.odm') == fixture['odm_sha256']
        for quality in ('x1', 'x2'):
            stage = STAGE / ('flat_' + family + '_' + quality)
            assets = stage / 'assets_dev'
            assets.mkdir(parents=True, exist_ok=True)
            for source in (ROOT / 'assets_dev').iterdir():
                target = assets / source.name
                if source.name != 'worlds' and not target.exists():
                    target.symlink_to(source, target_is_directory=source.is_dir())
            worlds = assets / 'worlds'
            worlds.mkdir(exist_ok=True)
            for world in (ROOT / 'assets_dev/worlds').iterdir():
                target = worlds / world.name
                if world.name != 'mm8':
                    if not target.exists():
                        target.symlink_to(world, target_is_directory=world.is_dir())
                    continue
                target.mkdir(exist_ok=True)
                for source in world.iterdir():
                    dest = target / source.name
                    if source.name in ('maps', 'events'):
                        dest.mkdir(exist_ok=True)
                        for item in source.iterdir():
                            if item.name.startswith(('out01.', 'out01_')):
                                continue
                            if not (dest / item.name).exists():
                                (dest / item.name).symlink_to(item, target_is_directory=item.is_dir())
                    elif source.name != 'terrain_x2' and not dest.exists():
                        dest.symlink_to(source, target_is_directory=source.is_dir())
                for ext in ('odm', 'scene.yml'):
                    shutil.copy2(folder / ('out01.' + ext), target / 'maps' / ('out01.' + ext))
                terrain = target / 'terrain_x2'
                terrain.mkdir(exist_ok=True)
                for name, source in sources.items():
                    shutil.copy2(source, terrain / name)
            config = configparser.ConfigParser(interpolation=None)
            config.read(STAGE / 'original/settings.ini')
            config['assets']['root'] = str(assets)
            config['video_quality']['terrain'] = quality
            with (stage / 'settings.ini').open('w') as stream:
                config.write(stream)
            placements = {k: dict(pose=v) for k, v in fixture['poses'].items()} if args.roads or args.land else fixture['placements']
            for kind, placement in placements.items():
                name = 'flat_' + family + '_' + kind + '_' + quality
                save = folder / (kind + '.oysav')
                grounded = args.roads and kind in ('west', 'east', 'south', 'north')
                if quality == 'x1' and not args.restore_snapshot:
                    subprocess.run(['/tmp/mm8-terrain-capture-save', str(seed), str(save),
                                    *map(str, placement['pose']), 'empty-world',
                                    '--grounded' if grounded else '--fly-buff'], check=True)
                if args.restore_snapshot:
                    assert sha(save) == report['poses'][name]['save_sha256']
                    continue
                report['poses'][name] = dict(stage=str(stage), save=str(save.relative_to(P)),
                                            save_sha256=sha(save), pose=placement['pose'],
                                            quality=quality, family=family, kind=kind,
                                            grounded=grounded,
                                            map_sha256=fixture['odm_sha256'])
    if not args.restore_snapshot:
        manifest_path.write_text(json.dumps(report, indent=2) + '\n')
    print('Staged', len(report['poses']), 'fixture views')


if __name__ == '__main__':
    main()
