#!/usr/bin/env python3
"""The sky maps' fall landings (Xeen.SkyFalls in worlds/xeen/events/common/xeen_common.lua) against the ground.

Xeen.skyFall puts the party Xeen.SkyFallHeight (850) over each landing's `groundZ`, so the fall's damage depends on
that number matching the ground the party lands on (the land, or a structure's top). On 2026-11-25 X9's three fall
playtests failed ("Brokk has 178 health, expected 181"): 3.3's X2 has 736 at entrance:x9_fall where the table said
768, so the fall was 882. This check reads each landing's map (installed, or the asset root given) and reports:

- error `fall.ground`: the ground at the point differs from the table's groundZ by more than 16;
- error `fall.none`: nothing under the point (no land, no floor).

Usage: check_sky_falls.py [--assets assets_dev] [--cache <folder>]. Exit 1 on any error.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_props_support import World  # noqa: E402

OYMAP = ROOT / 'openyamm-studio/build-xeen/oymap'
COMMON = 'worlds/xeen/events/common/xeen_common.lua'
TOLERANCE = 16


def landings(assets: Path):
    text = (assets / COMMON).read_text()
    start = text.index('Xeen.SkyFalls = {')
    block = text[start:text.index('\n}', start)]
    for match in re.finditer(r'(\w+) = \{(-?\d+), (-?\d+), (-?\d+), (-?\d+), "([\w.]+)"\}', block):
        yield match.group(1), int(match.group(2)), int(match.group(3)), int(match.group(4)), match.group(6)


def export(stem: str, assets: Path, cache: Path) -> dict:
    source = assets / 'worlds/xeen/maps' / stem
    out = cache / (stem + '.json')
    if not out.exists() or out.stat().st_mtime < source.stat().st_mtime:
        subprocess.run([str(OYMAP), 'export', stem, '--world', 'xeen', '--assets', str(assets), '--out', str(out)],
                       capture_output=True, text=True, timeout=600, check=True)
    return json.loads(out.read_text())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--assets', default=str(ROOT / 'assets_dev'))
    parser.add_argument('--cache', default=str(ROOT / 'output/xeen_checks/sky_falls'))
    args = parser.parse_args()
    assets = Path(args.assets)
    cache = Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)
    errors = 0
    for key, x, y, z, stem in landings(assets):
        world = World(export(stem, assets, cache), stem.endswith('.odm'))
        ground = world.support(x, y, z + 400)
        if ground is None:
            errors += 1
            print('error fall.none %s: nothing under (%d, %d) on %s' % (key, x, y, stem))
        elif abs(ground - z) > TOLERANCE:
            errors += 1
            print('error fall.ground %s: the ground at (%d, %d) on %s is %.0f, the table says %d (the fall is %.0f, '
                  'not 850)' % (key, x, y, stem, ground, z, z + 850 - ground))
        else:
            print('ok    %s: (%d, %d) on %s, ground %.0f, table %d' % (key, x, y, stem, ground, z))
    print('%d error(s)' % errors)
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
