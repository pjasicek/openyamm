#!/usr/bin/env python3
"""Migrate lighting hashes after a terrain tile table gained rows no baked map uses.

A table change can reach a bake only through the rows its map draws: the direct tiles (rows 0-89) and the four
36-row sets its scene's `tile_set_lookup_indices` name, and through a liquid edge's search for its base tile among
the rows of the same `tileset` id. This command takes the table as the old bakes saw it (--before), refuses unless
every changed row lies outside rows 0-89, outside each consuming map's four sets, and carries a tileset id none of
those sets carries, and unless every other dependency of the map is unchanged; then it rewrites only the recorded
table hash in each consuming sidecar. Baked geometry, probes and pixels are untouched. Sidecars already baked against
the new table are left alone. (Decision D-40 put MM8's lava set into the MM7 table's unused rows 450-485 for Xeen.)

  refresh_tile_table_dependency.py --before <old table> --table engine/data_tables/terrain_tile_data_2.txt \
      --backup-root <dir> --report <file> [--assets-root assets_dev]
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import struct
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bake_assets import dependency_file  # noqa: E402
from convert_lighting_v3 import fnv  # noqa: E402
from refresh_sprite_table_dependency import dependencies  # noqa: E402

SET_ROWS = 36
DIRECT_ROWS = 90


def sha(data):
    return hashlib.sha256(data).hexdigest()


def table_rows(data):
    """{row index: (texture, tile id, bitmap id, tileset, variant, flags)} of a tab-separated tile table."""
    rows = {}
    for row in csv.reader(io.StringIO(data.decode('latin-1')), delimiter='\t'):
        if row and row[0].strip().isdigit():
            rows[int(row[0])] = tuple(cell.strip() for cell in row[1:7])
    return rows


def scene_lookups(scene_path):
    with open(scene_path, encoding='utf-8') as stream:
        scene = yaml.load(stream, Loader=yaml.CSafeLoader)
    lookups = ((scene or {}).get('environment') or {}).get('tile_set_lookup_indices')
    if not isinstance(lookups, list) or len(lookups) != 4:
        raise ValueError(f'{scene_path}: no environment.tile_set_lookup_indices')
    return [int(value) for value in lookups]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--before', required=True, type=Path)
    parser.add_argument('--table', required=True)
    parser.add_argument('--assets-root', default=Path('assets_dev'), type=Path)
    parser.add_argument('--backup-root', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    before = args.before.read_bytes()
    after = (args.assets_root / args.table).read_bytes()
    old_rows, new_rows = table_rows(before), table_rows(after)
    if set(old_rows) != set(new_rows):
        raise ValueError('The tables have different row numbers; rebake required')
    changed = sorted(index for index in old_rows if old_rows[index] != new_rows[index])
    if not changed:
        raise ValueError('The tables do not differ')
    if any(index < DIRECT_ROWS for index in changed):
        raise ValueError('A direct tile row (0-89) changed; rebake required')
    changed_tilesets = {old_rows[index][3] for index in changed} | {new_rows[index][3] for index in changed}

    old_hash, new_hash = fnv(before), fnv(after)
    cached_hashes = {args.table: old_hash}
    pending, skipped = [], []
    for path in sorted((args.assets_root / 'worlds').glob('*/maps/*.lighting')):
        data = path.read_bytes()
        # Indoor bakes (another header) draw no terrain.
        if data[:8] != b'OYMLIT1\0':
            continue
        deps = dependencies(data)
        matching = [(name, value, offset) for name, value, offset in deps if name == args.table]
        if not matching:
            continue
        if len(matching) != 1:
            raise ValueError(f'{path}: the table is listed twice')
        if matching[0][1] == new_hash:
            skipped.append(str(path))
            continue
        if matching[0][1] != old_hash:
            raise ValueError(f'{path}: baked against neither table; rebake required')
        for name, value, _ in deps:
            if name not in cached_hashes:
                cached_hashes[name] = fnv(dependency_file(args.assets_root, name).read_bytes())
            if cached_hashes[name] != value:
                raise ValueError(f'{path}: another dependency changed: {name}; rebake required')
        lookups = scene_lookups(path.with_name(path.stem + '.scene.yml'))
        used = {row for start in lookups for row in range(start, start + SET_ROWS)}
        if used & set(changed):
            raise ValueError(f'{path}: its tile sets {lookups} draw a changed row; rebake required')
        used_tilesets = {old_rows[row][3] for row in used if row in old_rows}
        if used_tilesets & changed_tilesets:
            raise ValueError(f'{path}: a changed row shares a tileset id with its sets; rebake required')
        output = bytearray(data)
        offset = matching[0][2]
        struct.pack_into('<Q', output, offset, new_hash)
        assert data[:offset] == output[:offset] and data[offset + 8:] == output[offset + 8:]
        pending.append((path, data, output, offset, lookups))
    if not pending:
        raise ValueError('No lighting sidecar was baked against the supplied table')
    for path, *_ in pending:
        backup = args.backup_root / path.relative_to(args.assets_root)
        if backup.exists():
            raise ValueError(f'Backup already exists: {backup}')
    records = []
    # Every check is done before any map file is written.
    for path, data, output, offset, lookups in pending:
        backup = args.backup_root / path.relative_to(args.assets_root)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        # A new file, then a rename: assets_dev files may be hard links shared with review mirrors.
        temporary = path.with_suffix('.lighting.pending')
        temporary.write_bytes(output)
        temporary.replace(path)
        records.append(dict(path=str(path), backup=str(backup), lookups=lookups, before_sha256=sha(data),
                            after_sha256=sha(output), dependency_hash_offset=offset))
    report = dict(table=args.table, before_table_sha256=sha(before), after_table_sha256=sha(after),
                  before_dependency_fnv64=old_hash, after_dependency_fnv64=new_hash, changed_rows=changed,
                  changed_tilesets=sorted(changed_tilesets), other_dependencies_verified=len(cached_hashes) - 1,
                  baked_geometry_probes_pixels_unchanged=True, already_new=skipped, sidecars=records)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(f'Updated {len(records)} lighting dependency hashes ({len(skipped)} already on the new table); '
          'baked geometry, probes and pixels unchanged.')


if __name__ == '__main__':
    main()
