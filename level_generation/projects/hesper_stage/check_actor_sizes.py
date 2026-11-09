#!/usr/bin/env python3
"""Read-only audit of staged placed-actor sizes against their monster rows.

A built map stores each placed actor's body height and radius from its monster row as it was at build time, and the
game draws the actor's model at binding scale x stored height / the row's height. When a row's height or radius
changes after a map was built, the map's actors are drawn and collide at the old size until the map is rebuilt.
Every built Hesper map's placed actors (`<map>.scene.yml`, initial_state.actors) are compared with their rows in the
staged monster_descriptors.txt (the hesper world's contribution first, then the engine's table). Print per map the
actors checked and the mismatches; exit 1 on any. Hold the shared stage lock while reading.
"""
import fcntl
import json
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
STAGE = ROOT / 'output/hesper_stage'
ASSETS = STAGE / 'assets_editor_dev'
TABLES = [ASSETS / 'worlds/hesper/data_tables/monster_descriptors.txt',
          ASSETS / 'engine/data_tables/monster_descriptors.txt']


def descriptor_sizes():
    """Monster id -> (name, height, radius); the first table that lists an id wins (the hesper world's)."""
    sizes = {}
    for table in TABLES:
        for line in table.read_text(encoding='utf-8', errors='replace').splitlines():
            fields = line.split('\t')
            if len(fields) < 4 or not fields[0].strip().isdigit():
                continue
            sizes.setdefault(int(fields[0]), (fields[1], int(fields[2]), int(fields[3])))
    return sizes


def audit():
    sizes = descriptor_sizes()
    maps = sorted(p for p in (ASSETS / 'worlds/hesper/maps').iterdir() if p.suffix in ('.blv', '.odm'))
    if not maps:
        raise ValueError('no built Hesper maps in the stage')
    failed = False
    total_checked = total_mismatches = 0
    for path in maps:
        name = path.stem
        try:
            actors = json.loads(path.with_suffix('.scene.yml').read_text())['initial_state']['actors']
        except (OSError, ValueError, KeyError) as error:
            print(f'{name}: ERROR: {error}')
            failed = True
            continue
        mismatches = []
        for actor in actors:
            row = sizes.get(actor['monster_info_id'])
            if row is None:
                mismatches.append((actor, None))
            elif (actor['height'], actor['radius']) != row[1:]:
                mismatches.append((actor, row))
        total_checked += len(actors)
        total_mismatches += len(mismatches)
        failed |= bool(mismatches)
        print(f'{name}: actors={len(actors)}, mismatches={len(mismatches)}')
        for actor, row in mismatches:
            label = f'#{actor["actor_index"]} {actor["name"]!r} (monster {actor["monster_info_id"]})'
            if row is None:
                print(f'  MISMATCH {label}: no monster row')
            else:
                print(f'  MISMATCH {label}: stored height {actor["height"]} radius {actor["radius"]}, '
                      f'row {row[0]} height {row[1]} radius {row[2]}')
    print(f'TOTAL: maps={len(maps)}, actors={total_checked}, mismatches={total_mismatches}')
    return int(failed)


def main():
    with (STAGE / 'locks/stage.lock').open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_SH)
        return audit()


if __name__ == '__main__':
    raise SystemExit(main())
