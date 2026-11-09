"""Install map-scoped New Sorpigal decoration PNGs into the enhanced playtest only."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image
import yaml


REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / 'level_generation/decorations/mm6_new_sorpigal'
DEFAULT_STAGE = Path('/tmp/openyamm-sorpigal-peasants-playtest')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install_decorations(stage):
    stage = stage.resolve(strict=True)
    marker = stage / 'playtest_snapshot.json'
    report = json.loads(marker.read_text())
    if report['world'] != 'mm6' or report['map'] != 'oute3.odm':
        raise ValueError('Not a New Sorpigal playtest')
    manifest = json.loads((SOURCE / 'manifest.json').read_text())
    if manifest['scope'] != {'world': 'mm6', 'map': 'oute3.odm'}:
        raise ValueError('Unexpected decoration scope')
    target = stage / 'enhanced/assets_dev/worlds/mm6/rendering/decoration_overrides/oute3.odm'
    for parent in (target, *target.parents):
        if parent == stage:
            break
        if parent.is_symlink():
            raise ValueError('Decoration destination must be private: ' + str(parent))
    entries = []
    for name, frame in manifest['frames'].items():
        file = name + '.png'
        if Path(file).name != file or frame['file'] != 'enhanced/' + file:
            raise ValueError('Unexpected decoration path: ' + name)
        source = SOURCE / frame['file']
        if digest(source) != frame['sha256']:
            raise ValueError('Decoration source hash mismatch: ' + name)
        with Image.open(source) as image:
            if image.mode != 'RGBA' or list(image.size) != [v * 2 for v in frame['native_size']]:
                raise ValueError('Decoration must be RGBA at exactly twice native dimensions: ' + name)
        entries.append(dict(name=name, file=file, palette_id=frame['palette_baked'],
                            logical_size=frame['native_size'], pixel_scale=2))
    for file in [e['file'] for e in entries] + ['manifest.yml', 'manifest.pending']:
        if (target / file).is_symlink():
            raise ValueError('Decoration file must be private: ' + file)
    target.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        shutil.copy2(SOURCE / 'enhanced' / entry['file'], target / entry['file'])
    pending = target / 'manifest.pending'
    pending.write_text(yaml.safe_dump(dict(schema_version=1, textures=entries), sort_keys=False))
    pending.replace(target / 'manifest.yml')
    # Atomic executable replacement also works if an earlier playtest is still running.
    binary = stage / 'openyamm.next'
    shutil.copy2(REPO / 'build/game/openyamm', binary)
    binary.replace(stage / 'openyamm')
    report['binary_sha256'] = digest(stage / 'openyamm')
    report['decorations'] = dict(world='mm6', map='oute3.odm', mode='enhanced', images=len(entries),
                                source=str(SOURCE), runtime_manifest=str(target / 'manifest.yml'),
                                manifest_sha256=digest(target / 'manifest.yml'),
                                retained_native_animated_types=6)
    marker.write_text(json.dumps(report, indent=2) + '\n')
    print(f'Installed {len(entries)} map-local decoration images; native animations and saves preserved.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=DEFAULT_STAGE)
    install_decorations(parser.parse_args().directory)
