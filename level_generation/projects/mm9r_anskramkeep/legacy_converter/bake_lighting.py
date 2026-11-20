#!/usr/bin/env python3
"""Bake Anskram Keep's lighting with the indoor producer (tools/lighting/bake_indoor.py, devdocs/
INDOOR_BAKED_LIGHTING.md) and install the sidecar pair in the review root through review_root.install().

    python3 level_generation/projects/mm9r_anskramkeep/bake_lighting.py              # full bake (about 3 min)
    python3 level_generation/projects/mm9r_anskramkeep/bake_lighting.py --samples 16 # draft
    python3 level_generation/projects/mm9r_anskramkeep/bake_lighting.py --recompose  # new scales, same passes
    python3 level_generation/projects/mm9r_anskramkeep/bake_lighting.py --remove     # back to unbaked

The bake belongs to the BLV it was made from: after convert.py rebuilds the map, bake again (the game ignores a
stale bake and logs it; tools/lighting/stale_bakes.py --assets output/mm9_rework/assets_dev lists it).
"""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'level_generation/projects/mm9r_common'))
import review_root  # noqa: E402

PROFILE = ROOT / 'tools/lighting/baked_indoors/profiles/mm9_anskramkeep.yml'
OUTPUT = ROOT / 'output/mm9_rework/bakes/anskramkeep'
MAPS = 'worlds/mm9/maps'
FILES = ['anskramkeep.lighting', 'anskramkeep.bake.json']


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--samples', type=int)
    parser.add_argument('--recompose', action='store_true')
    parser.add_argument('--no-install', action='store_true')
    parser.add_argument('--remove', action='store_true', help='remove the installed bake from the review root')
    args = parser.parse_args()
    if args.remove:
        for name in FILES:
            review_root.remove(f'{MAPS}/{name}')
        print('removed', ', '.join(FILES))
        return 0
    command = ['blender', '--background', '--factory-startup', '--python-exit-code', '1',
               '--python', str(ROOT / 'tools/lighting/bake_indoor.py'), '--',
               '--profile', str(PROFILE), '--output', str(OUTPUT), '--assets', str(review_root.ASSETS)]
    if args.samples:
        command += ['--samples', str(args.samples)]
    if args.recompose:
        command.append('--recompose')
    subprocess.run(command, check=True, cwd=ROOT)
    if not args.no_install:
        for name in FILES:
            print('installed', review_root.install_file(f'{MAPS}/{name}', OUTPUT / name))
    return 0


if __name__ == '__main__':
    sys.exit(main())
