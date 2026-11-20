"""Add the saved ESRGAN x2 surface textures to the enhanced New Sorpigal playtest."""

import argparse
import configparser
import hashlib
import json
from pathlib import Path
import shutil


REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / 'tools/upscaling/out_prod_bmodel_mm6_x2'
DEFAULT_STAGE = Path('/tmp/openyamm-sorpigal-peasants-playtest')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install_model_textures(stage):
    stage = stage.resolve(strict=True)
    marker = stage / 'playtest_snapshot.json'
    report = json.loads(marker.read_text())
    if report['world'] != 'mm6' or report['map'] != 'oute3.odm':
        raise ValueError('Not a New Sorpigal playtest')
    manifest = json.loads((SOURCE / 'manifest.json').read_text())
    if manifest['world'] != 'mm6' or manifest['runtime_directory'] != 'worlds/mm6/textures_x2':
        raise ValueError('Unexpected surface texture package')
    records = manifest['files']
    if len(records) != manifest['count'] or len({r['file'] for r in records}) != len(records):
        raise ValueError('Incorrect texture count or duplicate names')
    run = stage / 'enhanced'
    target = run / 'assets_dev/worlds/mm6/textures_x2'
    for parent in (target, *target.parents):
        if parent == stage:
            break
        if parent.is_symlink():
            raise ValueError('Texture destination must be private: ' + str(parent))
    for record in records:
        name = record['file']
        if Path(name).name != name or Path(name).suffix != '.png':
            raise ValueError('Unexpected texture path: ' + name)
        if digest(SOURCE / name) != record['sha256']:
            raise ValueError('Texture source hash mismatch: ' + name)
        if (target / name).is_symlink():
            raise ValueError('Texture destination must be a private file: ' + name)
    target.mkdir(parents=True, exist_ok=True)
    for record in records:
        shutil.copy2(SOURCE / record['file'], target / record['file'])
    settings = configparser.ConfigParser(interpolation=None)
    settings.read(run / 'settings.ini')
    if not settings.has_section('video_quality'):
        settings.add_section('video_quality')
    settings['video_quality']['texture'] = 'x2'
    with (run / 'settings.ini').open('w') as stream:
        settings.write(stream, space_around_delimiters=False)
    report['model_textures'] = {**manifest, 'source': str(SOURCE), 'mode': 'enhanced'}
    marker.write_text(json.dumps(report, indent=2) + '\n')
    print(f'Installed {len(records)} ESRGAN surface textures; enhanced texture quality x2.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=DEFAULT_STAGE)
    install_model_textures(parser.parse_args().directory)
