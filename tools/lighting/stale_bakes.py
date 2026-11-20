#!/usr/bin/env python3
"""List the lighting bakes (outdoor ODM and indoor BLV) that are older than a file they were baked from, and rewrite
the note of them (<assets>/STALE_LIGHTING_BAKES.txt) to match: every stale bake with its changed sources, no note when
none is stale. The game loads bakes without checking their sources (an indoor bake of other geometry it ignores); run
this before a release or a commit and re-bake what it lists (bake_outdoor.py / bake_all_outdoors.py; indoor maps:
bake_indoor.py).
Exit status 1 while any bake is stale. Usage: stale_bakes.py [--assets assets_dev] [--check]"""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from package_runtime_assets import lighting_dependencies  # noqa: E402
sys.path.insert(0, str(ROOT / 'tools' / 'lighting'))
from bake_assets import dependency_file  # noqa: E402

NOTE = 'STALE_LIGHTING_BAKES.txt'
# Source hashes by size and modification time, so only changed sources are hashed again (FNV-1a in Python is slow).
CACHE = ROOT / 'output' / 'stale_bakes_hash_cache.json'
HEADER = ('# Lighting bakes (outdoor and indoor) older than a file they were baked from (noted by\n'
          '# tools/lighting/stale_bakes.py). Re-bake each map, then run tools/lighting/stale_bakes.py.\n')


def fnv1a64(data):
    value = 14695981039346656037
    for byte in data:
        value = ((value ^ byte) * 1099511628211) & 0xffffffffffffffff
    return value


def source_hash(source, cache):
    if not source.is_file():
        return None
    status = source.stat()
    key = str(source.resolve())
    stamp = [status.st_size, status.st_mtime_ns]
    if key not in cache or cache[key][:2] != stamp:
        cache[key] = stamp + [fnv1a64(source.read_bytes())]
    return cache[key][2]


def stale_bakes(assets):
    """{lighting path relative to assets: [changed or missing sources]} for every stale bake, outdoor or indoor."""
    try:
        cache = json.loads(CACHE.read_text())
    except (OSError, ValueError):
        cache = {}
    stale = {}
    for lighting in sorted((assets / 'worlds').glob('*/maps/*.lighting')):
        changed = [name for name, expected in lighting_dependencies(lighting)
                   if source_hash(dependency_file(assets, name), cache) != expected]
        if changed:
            stale[str(lighting.relative_to(assets))] = changed
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(cache))
    return stale


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--assets', type=Path, default=ROOT / 'assets_dev')
    parser.add_argument('--check', action='store_true', help='report only; leave the note as it is')
    args = parser.parse_args()
    stale = stale_bakes(args.assets)
    for lighting, changed in stale.items():
        print(f'STALE {lighting}: {", ".join(changed)}')
    print(f'{len(stale)} stale lighting bake(s)')
    if not args.check:
        note = args.assets / NOTE
        if stale:
            # A new file, then a rename: assets_dev files may be hard links shared with review mirrors.
            temporary = note.with_name(note.name + '.tmp')
            temporary.write_text(HEADER + ''.join(f'{lighting}: {", ".join(changed)}\n'
                                                  for lighting, changed in sorted(stale.items())))
            os.replace(temporary, note)
        elif note.exists():
            note.unlink()
    return 1 if stale else 0


if __name__ == '__main__':
    sys.exit(main())
