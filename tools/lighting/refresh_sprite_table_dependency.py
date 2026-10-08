#!/usr/bin/env python3
"""Migrate lighting hashes after proven unrelated creature texture-binding edits.

This command rejects changes to decoration groups or script-selected bake states.
It preserves baked geometry, probes and texture bytes; it never suppresses runtime
dependency checks. Supply the exact sprite-table snapshot used by the old bake.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import struct

import yaml

from bake_decorations import sprite_states
from convert_lighting_v3 import fnv


TABLE = 'engine/rendering/sprite_frame_data_common.yml'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dependencies(data):
    if len(data) < 96 or data[:8] != b'OYMLIT1\0':
        raise ValueError('Expected an outdoor lighting sidecar')
    version, header = struct.unpack_from('<II', data, 8)
    if version not in (3, 4, 5) or header != 96:
        raise ValueError('Expected a version-3, version-4 or version-5 lighting sidecar')
    if struct.unpack_from('<I', data, 68)[0] != len(data):
        raise ValueError('Invalid lighting file size')
    if not struct.unpack_from('<I', data, 76)[0] & 1:
        return []
    page_count = struct.unpack_from('<I', data, 32)[0]
    page_offset = struct.unpack_from('<I', data, 48)[0]
    end = struct.unpack_from('<I', data, 64)[0]
    for i in range(page_count):
        _, _, offset, size = struct.unpack_from('<4I', data, page_offset+i*16)
        if offset != end or size > len(data)-end:
            raise ValueError('Invalid lighting page bounds')
        end += size
    if version >= 4:
        end += 24
    probes, count = struct.unpack_from('<II', data, end)
    cursor = end+8+probes*(52 if version >= 4 else 36)
    result = []
    for _ in range(count):
        length, value = struct.unpack_from('<IQ', data, cursor)
        name = data[cursor+12:cursor+12+length].decode('utf-8')
        if not length or cursor+12+length > len(data) or '..' in Path(name).parts or Path(name).is_absolute():
            raise ValueError('Invalid lighting dependency path')
        result.append((name, value, cursor+4))
        cursor += 12+length
    if version >= 5:
        direct_count = struct.unpack_from('<I', data, cursor)[0]
        cursor += 4
        if direct_count * 2 != page_count:
            raise ValueError('Invalid direct-sun page count')
        for index in range(direct_count):
            width, height, size = struct.unpack_from('<3I', data, cursor)
            cursor += 12
            if (width, height) != struct.unpack_from('<2I', data, page_offset+index*2*16) or size > len(data)-cursor:
                raise ValueError('Invalid direct-sun page bounds')
            cursor += size
    if cursor != len(data):
        raise ValueError('Invalid lighting dependency section')
    return result


def changed_groups(before, after):
    old = yaml.load(before, Loader=yaml.CSafeLoader)
    new = yaml.load(after, Loader=yaml.CSafeLoader)
    changed = set()
    for a, b in zip(old['sprites'], new['sprites'], strict=True):
        if a != b:
            changed.add((b['sprite_id'], b['sprite_name'].lower()))
        for x, y in zip(a['frames'], b['frames'], strict=True):
            x.pop('texture_name')
            y.pop('texture_name')
    if old != new:
        raise ValueError('Only texture-name changes can be migrated without rebaking')
    return changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', required=True, type=Path)
    parser.add_argument('--assets-root', default=Path('assets_dev'), type=Path)
    parser.add_argument('--backup-root', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    before = args.before.read_bytes()
    after = (args.assets_root/TABLE).read_bytes()
    changed = changed_groups(before, after)
    changed_ids = {i for i, _ in changed}
    changed_names = {n for _, n in changed}
    with (args.assets_root/'engine/data_tables/decoration_data.txt').open() as stream:
        rows = csv.reader(stream, delimiter='\t')
        decoration_ids = {int(r[12]) for r in rows if r and r[0].isdigit()}
    if changed_ids & decoration_ids:
        raise ValueError('A changed sprite group is referenced by decoration data; rebake required')

    cached_hashes = {TABLE: fnv(before)}
    old_hash, new_hash = cached_hashes[TABLE], fnv(after)
    pending, scripts, state_names = [], set(), set()
    for path in sorted((args.assets_root/'worlds').glob('*/maps/*.lighting')):
        data = path.read_bytes()
        deps = dependencies(data)
        matching = [(name, value, offset) for name, value, offset in deps if name == TABLE]
        if not matching:
            continue
        if len(matching) != 1 or matching[0][1] != old_hash:
            raise ValueError(f'{path}: dependency does not match the supplied original snapshot')
        for name, value, _ in deps:
            if name not in cached_hashes:
                cached_hashes[name] = fnv((args.assets_root/name).read_bytes())
            if cached_hashes[name] != value:
                raise ValueError(f'{path}: another dependency changed: {name}; rebake required')
        script_directory = path.parent.parent / 'events/maps'
        scripts.add(script_directory / (path.stem + '.lua'))
        scripts.update(script_directory.glob(path.stem + '_*.lua'))
        output = bytearray(data)
        offset = matching[0][2]
        struct.pack_into('<Q', output, offset, new_hash)
        assert data[:offset] == output[:offset] and data[offset+8:] == output[offset+8:]
        pending.append((path, data, output, offset))
    for path in sorted(scripts):
        if not path.is_file():
            continue
        for states in sprite_states(path.read_bytes().decode('latin-1'), path).values():
            state_names.update(n for _, n in states if n)
    if changed_names & state_names:
        raise ValueError('A changed sprite is selected by a baked map script; rebake required')
    if not pending:
        raise ValueError('No lighting sidecar consumes the supplied sprite-table snapshot')
    records = []
    # Finish every dependency/consumer check before writing any map file.
    for path, data, output, offset in pending:
        backup = args.backup_root/path.relative_to(args.assets_root)
        if backup.exists():
            raise ValueError(f'Backup already exists: {backup}')
    for path, data, output, offset in pending:
        backup = args.backup_root/path.relative_to(args.assets_root)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        temporary = path.with_suffix('.lighting.pending')
        temporary.write_bytes(output)
        temporary.replace(path)
        records.append(dict(path=str(path), backup=str(backup), before_sha256=sha(data),
                            after_sha256=sha(output), dependency_hash_offset=offset))
    report = dict(before_table_sha256=sha(before), after_table_sha256=sha(after),
                  before_dependency_fnv64=old_hash, after_dependency_fnv64=new_hash,
                  changed_groups=[dict(id=i, name=n) for i, n in sorted(changed)],
                  decoration_group_overlap=[], script_state_overlap=[],
                  consumed_bake_scripts=len(scripts), other_dependencies_verified=len(cached_hashes)-1,
                  baked_geometry_probes_pixels_unchanged=True, sidecars=records)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2)+'\n')
    print(f'Updated {len(records)} lighting dependency hashes; baked geometry, probes and pixels unchanged.')


if __name__ == '__main__':
    main()
