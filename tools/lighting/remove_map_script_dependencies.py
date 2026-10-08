#!/usr/bin/env python3
"""Remove obsolete map-script hashes from installed lighting without rebaking.

Validate all retained dependencies before changing any sidecar. Preserve baked
geometry, probes and pixel payloads, and retain a backup of each changed file.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct

from convert_lighting_v3 import fnv
from refresh_sprite_table_dependency import dependencies


def remove_script_dependencies(data):
    deps = dependencies(data)
    removed = [(name, digest, offset) for name, digest, offset in deps
               if name.startswith('worlds/') and '/events/maps/' in name and name.endswith('.lua')]
    if not removed:
        return data, []
    retained = [(name, digest) for name, digest, offset in deps if (name, digest, offset) not in removed]
    if not retained:
        raise ValueError('Paired lighting must retain its source-asset dependencies')

    version = struct.unpack_from('<I', data, 8)[0]
    page_count = struct.unpack_from('<I', data, 32)[0]
    page_offset = struct.unpack_from('<I', data, 48)[0]
    counts_offset = struct.unpack_from('<I', data, 64)[0]
    counts_offset += sum(struct.unpack_from('<I', data, page_offset + i * 16 + 12)[0]
                         for i in range(page_count))
    counts_offset += 24 if version >= 4 else 0
    output = bytearray()
    cursor = 0
    for name, _, hash_offset in removed:
        record_offset = hash_offset - 4
        output += data[cursor:record_offset]
        cursor = record_offset + 12 + len(name.encode('utf-8'))
    output += data[cursor:]
    struct.pack_into('<I', output, counts_offset + 4, len(retained))
    struct.pack_into('<I', output, 68, len(output))
    assert [(name, digest) for name, digest, _ in dependencies(output)] == retained
    return bytes(output), [name for name, _, _ in removed]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets-root', default=Path('assets_dev'), type=Path)
    parser.add_argument('--backup-root', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    pending, hashes = [], {}
    for path in sorted((args.assets_root / 'worlds').glob('*/maps/*.lighting')):
        data = path.read_bytes()
        output, removed = remove_script_dependencies(data)
        if not removed:
            continue
        for name, digest, _ in dependencies(output):
            if name not in hashes:
                hashes[name] = fnv((args.assets_root / name).read_bytes())
            if hashes[name] != digest:
                raise ValueError(f'{path}: retained dependency is stale: {name}; rebake required')
        backup = args.backup_root / path.relative_to(args.assets_root)
        if backup.exists():
            raise ValueError(f'Backup already exists: {backup}')
        pending.append((path, backup, hashlib.sha256(data).hexdigest()))

    records = []
    for path, backup, before_hash in pending:
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != before_hash:
            raise ValueError(f'{path}: sidecar changed during migration')
        output, removed = remove_script_dependencies(data)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        temporary = path.with_suffix('.lighting.pending')
        temporary.write_bytes(output)
        temporary.replace(path)
        records.append(dict(path=str(path), backup=str(backup), removed_dependencies=removed,
                            before_sha256=before_hash, after_sha256=hashlib.sha256(output).hexdigest()))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(dict(baked_geometry_probes_pixels_unchanged=True,
                                         retained_sources_verified=len(hashes), sidecars=records), indent=2) + '\n')
    print(f'Removed map-script dependencies from {len(records)} lighting sidecars; baked samples unchanged.')


if __name__ == '__main__':
    main()
