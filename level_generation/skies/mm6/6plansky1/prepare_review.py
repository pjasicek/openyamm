#!/usr/bin/env python3
"""Prepare an isolated, repeatable x1/x2 sky pilot without altering main assets/settings."""
import argparse
import configparser
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[3]
STAGE = Path('/tmp/openyamm-mm6-6plansky1-pilot')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def link(source, target):
    if not target.exists() and not target.is_symlink():
        target.symlink_to(source, target_is_directory=source.is_dir())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--play', action='store_true',
                        help='Load the pilot save directly; keep historical capture metadata intact')
    args = parser.parse_args()
    manifest = json.loads((PROJECT / 'manifest.json').read_text())
    assets = STAGE / 'assets_dev'
    mm6 = assets / 'worlds/mm6'
    mm6.mkdir(parents=True, exist_ok=True)
    native_root = ROOT / 'assets_dev'
    for child in native_root.iterdir():
        if child.name != 'worlds':
            link(child, assets / child.name)
    for world in (native_root / 'worlds').iterdir():
        if world.name != 'mm6':
            link(world, assets / 'worlds' / world.name)
    for child in (native_root / 'worlds/mm6').iterdir():
        if child.name != 'textures_x2':
            link(child, mm6 / child.name)
    target = mm6 / 'textures_x2'
    assert not target.is_symlink()
    target.mkdir(exist_ok=True)
    sources = ['6plansky1', '6sky06', '6sky12', '6sky03', '6sky04', '6sky19']
    entries = []
    for name in sources:
        destination = target / (name + '.png')
        assert not destination.is_symlink()
        native = native_root / 'worlds/mm6/textures' / (name + '.bmp')
        if name == '6plansky1':
            shutil.copy2(PROJECT / 'runtime_x2/6plansky1.png', destination)
            method = 'imagegen ' + manifest['selected_version'] + ' pilot'
        else:
            subprocess.run(['convert', str(native), '-sample', '200%', '-alpha', 'off',
                            'PNG24:' + str(destination)], check=True)
            method = 'native nearest x2 placeholder, not restored'
        entries.append({'name': name, 'source': str(native), 'method': method, 'sha256': sha(destination)})
    duplicate = target / '6sky01.png'
    assert not duplicate.is_symlink()
    shutil.copy2(PROJECT / 'runtime_x2/6plansky1.png', duplicate)
    native = native_root / 'worlds/mm6/textures/6plansky1.bmp'
    assert native.read_bytes() == (PROJECT / 'source/6plansky1.bmp').read_bytes()
    binary = STAGE / 'openyamm'
    pending_binary = STAGE / 'openyamm.next'
    shutil.copy2(ROOT / 'build/game/openyamm', pending_binary)
    pending_binary.replace(binary)
    report_directory = STAGE if args.play else PROJECT / 'review'
    if args.play:
        save = STAGE / 'saves/Sky_pilot.oysav'
        save.parent.mkdir(exist_ok=True)
        shutil.copy2(PROJECT / 'source/overhead.oysav', save)
    for tier in ('x1', 'x2'):
        run = STAGE / tier
        run.mkdir(exist_ok=True)
        config = configparser.ConfigParser(interpolation=None)
        config.read(ROOT / 'settings.ini')
        config['assets']['root'] = str(assets)
        for name in ('texture', 'terrain', 'sky', 'sprites', 'decorations', 'icons', 'ui', 'effects', 'fonts'):
            config['video_quality'][name] = 'x1'
        config['video_quality']['sky'] = tier
        config['video_quality']['texture'] = 'x1'
        if args.play:
            config['startup'] = {'start_in_main_menu': 'false', 'save_file': str(save)}
        with (run / 'settings.ini').open('w') as f:
            config.write(f, space_around_delimiters=False)
        shutil.copy2(run / 'settings.ini', report_directory / ('settings_' + tier + '.ini'))
    report = {'stage': str(STAGE), 'binary_sha256': sha(binary), 'main_settings_sha256': sha(ROOT / 'settings.ini'),
              'continent_table_sha256': sha(native_root / 'engine/data_tables/continent_settings.txt'),
              'entries': entries, 'duplicate_alias': '6sky01',
              'main_assets_modified': False, 'main_settings_modified': False}
    (report_directory / 'stage.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
