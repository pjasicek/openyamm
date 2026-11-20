"""Install the new boundary pack into a separate dirt trial, preserving existing saves and trials."""
import argparse
import configparser
import hashlib
import json
from pathlib import Path
import shutil

P = Path(__file__).resolve().parent
WATER = P.parents[1] / 'mm6_new_sorpigal_water/restoration_v3'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path('/tmp/openyamm-sorpigal-dirt-fidelity'))
    parser.add_argument('--binary', type=Path, default=P.parents[3] / 'build/game/openyamm',
                        help='Executable containing the native_water_v3 repeat-sampler fix')
    args = parser.parse_args()
    root = args.directory.resolve(strict=True)
    source = root / 'current'
    target = root / 'transitions'
    if not target.exists():
        shutil.copytree(source, target, symlinks=True)
    assets = target / 'assets_dev/worlds/mm6/terrain_x2'
    assert assets.is_dir() and not assets.is_symlink()
    files = sorted((P / 'edge_treatment/runtime/v2').glob('*.png'))
    assert len(files) == 36
    manifest = json.loads((WATER / 'runtime_x2/manifest.json').read_text())
    assert manifest['iteration'] == 'native_water_v3'
    water_files = [WATER / 'runtime_x2/worlds/mm6/terrain_x2' / name
                   for name in [*(f'6hdwtr{i:03}.png' for i in range(14)), '6wtrtyl.png']]
    for path in water_files:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest['files']['worlds/mm6/terrain_x2/' + path.name]
    binary = args.binary.resolve(strict=True)
    hashes = {}
    for path in files:
        destination = assets / path.name
        assert not destination.is_symlink()
        shutil.copy2(path, destination)
        hashes[path.name] = hashlib.sha256(destination.read_bytes()).hexdigest()
    water_hashes = {}
    for path in water_files:
        destination = assets / path.name
        assert not destination.is_symlink()
        shutil.copy2(path, destination)
        water_hashes[path.name] = hashlib.sha256(destination.read_bytes()).hexdigest()
    # This mode owns its newer binary; the original/current/candidate trials retain theirs.
    assert not (target / 'openyamm').is_symlink()
    shutil.copy2(binary, target / 'openyamm')
    settings = configparser.ConfigParser(interpolation=None)
    settings.read(target / 'settings.ini')
    settings['assets']['root'] = str(target / 'assets_dev')
    settings['video_quality']['terrain'] = 'x2'
    settings['startup']['start_in_main_menu'] = 'true'
    with (target / 'settings.ini').open('w') as stream:
        settings.write(stream, space_around_delimiters=False)
    report = {'stage': str(target), 'runtime': 'edge_treatment/runtime/v2', 'files': hashes,
              'water': {'version': manifest['iteration'], 'source': str(WATER), 'files': water_hashes},
              'binary_source': str(binary),
              'binary_sha256': hashlib.sha256((target / 'openyamm').read_bytes()).hexdigest()}
    (P / 'reports/playtest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(target)


if __name__ == '__main__':
    main()
