"""Versioned, checked content archive for an isolated copy of this repository's MM8 base.

The archive includes scoped registration tables, not original artwork. Never apply those
whole tables to an unrelated installation; installation checks the original base hashes.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile, ZIP_DEFLATED

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
TABLES = ('map_stats.txt', 'house_data.txt', 'house_animations.txt', 'npc.txt',
          'bolster_maps.txt', 'map_navigation.txt', 'transport_locations.txt', 'house_rules.txt')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def export(stage, destination):
    assets = stage / 'assets_editor_dev'
    entries = {}
    for source in sorted((PROJECT / 'runtime').rglob('*')):
        if source.is_file():
            name = source.relative_to(PROJECT / 'runtime').as_posix()
            data = (assets / name).read_bytes()
            if data != source.read_bytes():
                raise ValueError('Stale staged runtime: ' + name)
            entries[name] = data
    base = {}
    for table in TABLES:
        name = 'engine/data_tables/' + table
        entries[name] = (assets / name).read_bytes()
        base[name] = digest((ROOT / 'assets_dev' / name).read_bytes())
    manifest = dict(format_version=1, project='brackenford_greywatch',
        installation='isolated MM8 development mount; original base artwork required',
        map_ids=json.loads((PROJECT / 'source/ids.json').read_text())['maps'],
        tested_binary_sha256=digest((ROOT / 'build/game/openyamm').read_bytes()),
        base_sha256=base, files={name: digest(data) for name, data in entries.items()})
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, 'w', ZIP_DEFLATED) as archive:
        archive.writestr('package_manifest.json', json.dumps(manifest, indent=2) + '\n')
        for name, data in entries.items():
            archive.writestr(name, data)
    destination.with_suffix('.manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


def read_verified(package):
    """Verify every entry before the installer makes any content changes."""
    with ZipFile(package) as archive:
        manifest = json.loads(archive.read('package_manifest.json'))
        if manifest['format_version'] != 1 or manifest['project'] != 'brackenford_greywatch':
            raise ValueError('Unsupported project archive')
        expected_base = {'engine/data_tables/' + name for name in TABLES}
        if set(manifest['base_sha256']) != expected_base:
            raise ValueError('Incomplete base compatibility manifest')
        for name, expected in manifest['base_sha256'].items():
            if digest((ROOT / 'assets_dev' / name).read_bytes()) != expected:
                raise ValueError('Base table changed; rebuild package: ' + name)
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != set(manifest['files']) | {'package_manifest.json'}:
            raise ValueError('Archive entry inventory mismatch')
        entries = {}
        for name, expected in manifest['files'].items():
            path = PurePosixPath(name)
            if (path.is_absolute() or '..' in path.parts or str(path) != name or '\\' in name
                    or not (name in expected_base or name.startswith('worlds/mm8/'))):
                raise ValueError('Unsafe content path: ' + name)
            data = archive.read(name)
            if digest(data) != expected:
                raise ValueError('Content checksum mismatch: ' + name)
            entries[name] = data
    return manifest, entries


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path('/tmp/openyamm-brackenford-greywatch'))
    parser.add_argument('--output', type=Path, default=PROJECT / 'dist/brackenford_greywatch_content.zip')
    args = parser.parse_args()
    result = export(args.directory.resolve(), args.output.resolve())
    read_verified(args.output)
    print(json.dumps(dict(package=str(args.output), files=len(result['files']),
                         sha256=digest(args.output.read_bytes())), indent=2))
