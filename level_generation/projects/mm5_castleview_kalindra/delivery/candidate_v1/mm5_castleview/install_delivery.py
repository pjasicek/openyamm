"""Install an extracted Castleview delivery into a new isolated Linux playtest directory."""
import argparse
import configparser
import hashlib
import json
from pathlib import Path
import shlex
import shutil


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install(bundle, base, destination):
    bundle = bundle.resolve(strict=True)
    base = base.resolve(strict=True)
    destination = destination.resolve()
    manifest = json.loads((bundle/'manifest.json').read_text())
    assert manifest['project'] == 'mm5_castleview_kalindra'
    assert not destination.exists(), 'Choose a new destination; existing settings and saves are never replaced.'
    for name, expected in manifest['files'].items():
        assert digest(bundle/name) == expected, ('Delivery file changed', name)
    for name, expected in manifest['baseDependencies'].items():
        assert digest(base/name) == expected, ('Different base dependency; rebuild the delivery for this base', name)
    for world in ['mm7', 'mm8']:
        assert (base/'worlds'/world/'world.yml').is_file(), ('Missing donor world', world)
    assert not (base/'worlds/mm5').exists(), 'The supplied base already owns MM5; choose the unmodified donor base.'

    assets = destination/'assets_dev'
    assets.mkdir(parents=True)
    # The composed base owns the three explicit registries. Other base assets and worlds remain read-only mounts.
    for source in base.iterdir():
        target = assets/source.name
        if source.name not in ['engine', 'worlds']:
            target.symlink_to(source, target_is_directory=source.is_dir())
            continue
        target.mkdir()
        for child in source.iterdir():
            if source.name == 'engine' and child.name == 'data_tables':
                tables = target/child.name
                tables.mkdir()
                for table in child.iterdir():
                    replacement = bundle/'registries'/table.name
                    if replacement.is_file():
                        shutil.copy2(replacement, tables/table.name)
                    else:
                        (tables/table.name).symlink_to(table, target_is_directory=table.is_dir())
            else:
                (target/child.name).symlink_to(child, target_is_directory=child.is_dir())
    shutil.copytree(bundle/'worlds/mm5', assets/'worlds/mm5')
    shutil.copytree(bundle/'bin', destination/'bin')
    binary = destination/'bin/openyamm'
    binary.chmod(0o755)
    work = destination/'playtest'
    (work/'saves').mkdir(parents=True)
    shutil.copy2(bundle/'castleview_start.oysav', work/'saves/castleview_start.oysav')
    settings = configparser.ConfigParser()
    settings['assets'] = {'root': str(assets)}
    settings['startup'] = {'start_in_main_menu': 'true'}
    settings['controls'] = {'control_scheme': 'classic'}
    settings['debug'] = {'immortal': 'false', 'unlimited_mana': 'false', 'new_game_god_lich': 'false',
                         'movement_speed_multiplier': '1'}
    with (work/'settings.ini').open('w') as stream:
        settings.write(stream, space_around_delimiters=False)
    launcher = destination/'play-mm5.sh'
    launcher.write_text('#!/bin/sh\nset -eu\ncd '+shlex.quote(str(work))+'\nexec '+
                        shlex.quote(str(binary))+' --world mm5 "$@"\n')
    launcher.chmod(0o755)
    report = {'project': manifest['project'], 'bundle': str(bundle), 'base': str(base),
              'nativeSha256': manifest['nativeSha256'], 'binarySha256': digest(binary),
              'manifestSha256': digest(bundle/'manifest.json'), 'launcher': str(launcher),
              'baseModified': False, 'world': 'mm5', 'map': 'mm5_sw.odm'}
    (destination/'installation.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--base-assets', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    install(args.bundle, args.base_assets, args.destination)
