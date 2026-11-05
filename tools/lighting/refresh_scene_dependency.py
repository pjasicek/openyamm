#!/usr/bin/env python3
"""Migrate outdoor lighting hashes after proven unrelated scene edits (actor fields, movement limits).

For each outdoor sidecar whose only changed dependency is its map's .scene.yml, the scene the bake was made from is
found in git history by its recorded hash. The sidecar is migrated only when every scene section the producer reads
(bake_outdoor.py and bake_decorations.py) is identical between that snapshot and the current scene; otherwise it must
be re-baked. Baked geometry, probes and pixels are preserved: only the 8-byte dependency hash is rewritten.
Usage: refresh_scene_dependency.py --backup-root DIR --report FILE [--assets-root assets_dev]
"""
import argparse
import json
from pathlib import Path
import shutil
import struct
import subprocess

import yaml

from bake_assets import dependency_file
from convert_lighting_v3 import fnv
from refresh_sprite_table_dependency import dependencies, sha


ROOT = Path(__file__).resolve().parents[2]


def bake_inputs(scene):
    """The parts of a scene the outdoor producer reads."""
    return dict(mechanisms=scene.get('mechanisms'),
                scene_profile=scene.get('scene_profile', 'classic_odm'),
                terrain_attribute_overrides=(scene.get('terrain') or {}).get('attribute_overrides'),
                tile_set_lookup_indices=scene['environment']['tile_set_lookup_indices'],
                interactive_faces=(scene.get('bmodel_faces') or {}).get('interactive_faces'),
                entities=scene.get('entities'))


def baked_snapshot(path, expected):
    """The committed version of path whose hash the bake recorded, or None."""
    relative = path.resolve().relative_to(ROOT)
    revisions = subprocess.run(['git', 'log', '--format=%H', '--', str(relative)], cwd=ROOT, check=True,
                               capture_output=True, text=True).stdout.split()
    for revision in revisions:
        blob = subprocess.run(['git', 'show', f'{revision}:{relative}'], cwd=ROOT, capture_output=True).stdout
        if fnv(blob) == expected:
            return revision, blob
    return None, None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--assets-root', default=ROOT / 'assets_dev', type=Path)
    parser.add_argument('--backup-root', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    pending, refused = [], []
    for path in sorted((args.assets_root / 'worlds').glob('*/maps/*.lighting')):
        data = path.read_bytes()
        try:
            deps = dependencies(data)
        except ValueError:
            continue  # indoor sidecars have their own format
        changed = [(name, value, offset) for name, value, offset in deps
                   if fnv(dependency_file(args.assets_root, name).read_bytes()) != value]
        if not changed:
            continue
        scene_name = str(path.with_suffix('.scene.yml').relative_to(args.assets_root))
        if [name for name, _, _ in changed] != [scene_name]:
            refused.append(dict(path=str(path), reason='other dependencies changed',
                                changed=[name for name, _, _ in changed]))
            continue
        _, expected, offset = changed[0]
        current = dependency_file(args.assets_root, scene_name).read_bytes()
        revision, before = baked_snapshot(dependency_file(args.assets_root, scene_name), expected)
        if before is None:
            refused.append(dict(path=str(path), reason='baked scene not found in git history'))
            continue
        old = yaml.load(before, Loader=yaml.CSafeLoader)
        new = yaml.load(current, Loader=yaml.CSafeLoader)
        if bake_inputs(old) != bake_inputs(new):
            refused.append(dict(path=str(path), reason='a scene section the bake reads changed', revision=revision))
            continue
        output = bytearray(data)
        struct.pack_into('<Q', output, offset, fnv(current))
        assert data[:offset] == output[:offset] and data[offset + 8:] == output[offset + 8:]
        pending.append((path, data, output, offset, revision))
    # Finish every check before writing any map file.
    for path, *_ in pending:
        backup = args.backup_root / path.relative_to(args.assets_root)
        if backup.exists():
            raise ValueError(f'Backup already exists: {backup}')
    records = []
    for path, data, output, offset, revision in pending:
        backup = args.backup_root / path.relative_to(args.assets_root)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        # A new file, then a rename: assets_dev files may be hard links shared with review mirrors.
        temporary = path.with_suffix('.lighting.pending')
        temporary.write_bytes(output)
        temporary.replace(path)
        records.append(dict(path=str(path), backup=str(backup), baked_scene_revision=revision,
                            before_sha256=sha(data), after_sha256=sha(output), dependency_hash_offset=offset))
    report = dict(baked_geometry_probes_pixels_unchanged=True, sidecars=records, refused=refused)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(f'Updated {len(records)} lighting scene hashes; {len(refused)} sidecar(s) need a re-bake.')
    for entry in refused:
        print(f"  REBAKE {entry['path']}: {entry['reason']}")


if __name__ == '__main__':
    main()
