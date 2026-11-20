#!/usr/bin/env python3
"""Read-only audit of staged BLV/ODM decoration IDs against the names their projects authored.

Print every Hesper placement and per-map counts. Hold the shared stage lock while reading; exit 1 on any
mismatch or missing/ambiguous source data. Registry IDs are table rows; native map IDs are one less.
"""
import fcntl
import json
from pathlib import Path
import sys

import yaml

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
STAGE = ROOT / 'output/hesper_stage'
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_blv_file, parse_odm_file


def compare_entities(native, source, ids, indoor):
    """Match indoor marker names or outdoor placement indices, never the possibly stale source IDs."""
    by_id = {value: name for name, value in ids.items()}
    if len(by_id) != len(ids):
        raise ValueError('the decoration registry contains duplicate IDs')
    if len(native) != len(source):
        raise ValueError(f'placement counts differ: staged {len(native)}, source {len(source)}')
    expected = {}
    for entity in source:
        key = entity['id'][:32] if indoor else entity['entity_index']
        if key in expected:
            raise ValueError(f'ambiguous source placement {key!r}')
        if indoor:
            name, separator, index = entity['id'].rpartition('_')
            if not separator or not index.isdigit():
                raise ValueError(f'indoor marker lacks its placement suffix: {entity["id"]}')
        else:
            name = entity['name']
        expected[key] = (name, entity)

    results = []
    for entity in native:
        key = entity['name'] if indoor else entity['index']
        name, authored = expected.get(key, (None, None))
        actual = entity['decoration_list_id'] + 1
        if actual not in by_id and name not in ids:
            continue
        problem = ''
        if authored is None:
            problem = 'no matching source placement'
        elif name not in ids:
            problem = f'expected name {name!r} is not in the Hesper registry'
        elif not indoor and (entity['name'] != name[:32] or entity['position'] != authored['position']):
            problem = 'outdoor placement name/position differs from source'
        elif actual != ids[name]:
            problem = 'wrong decoration ID'
        results.append(dict(index=entity['index'], expected=name, expected_id=ids.get(name),
                            actual=by_id.get(actual, '<non-Hesper>'), actual_id=actual, problem=problem))
    return results


def audit():
    ids = yaml.safe_load((PROJECT / 'decoration_ids.yml').read_text())['ids']
    projects = {row['file']: ROOT / 'level_generation/projects' / row['project']
                for row in yaml.safe_load((PROJECT / 'maps.yml').read_text())['maps']}
    maps = sorted(p for p in (STAGE / 'assets_editor_dev/worlds/hesper/maps').iterdir()
                  if p.suffix in ('.blv', '.odm'))
    if not maps:
        raise ValueError('no built Hesper maps in the stage')
    failed = False
    total_placed = total_mismatches = 0
    for path in maps:
        try:
            indoor = path.suffix == '.blv'
            native = (parse_blv_file if indoor else parse_odm_file)(path)['payload']['entities']
            kind = 'geometry' if indoor else 'scene'
            source = json.loads((projects[path.name] / 'source' / f'{path.stem}.{kind}.yml').read_text())['entities']
            rows = compare_entities(native, source, ids, indoor)
        except (OSError, ValueError, KeyError) as error:
            print(f'{path.name}: ERROR: {error}')
            failed = True
            continue
        placed = sum(row['actual_id'] in ids.values() for row in rows)
        mismatches = sum(bool(row['problem']) for row in rows)
        total_placed += placed
        total_mismatches += mismatches
        failed |= mismatches > 0
        print(f'{path.name}: Hesper decorations={placed}, mismatches={mismatches}')
        for row in rows:
            status = 'MISMATCH' if row['problem'] else 'OK'
            print(f'  {status} #{row["index"]}: expected {row["expected"]} ({row["expected_id"]}), '
                  f'placed {row["actual"]} ({row["actual_id"]})'
                  + (f' — {row["problem"]}' if row['problem'] else ''))
    print(f'TOTAL: maps={len(maps)}, Hesper decorations={total_placed}, mismatches={total_mismatches}')
    return int(failed)


def main():
    with (STAGE / 'locks/stage.lock').open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_SH)
        return audit()


if __name__ == '__main__':
    raise SystemExit(main())
