"""Run the existing Cycles producer for native MM6/MM7/MM8 outdoor maps.

This is a sequential batch driver, not an indoor or MM9 lighting producer.
Each successful output retains its recipe, report and intermediate files.
"""

import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
PROFILES = ROOT / 'level_generation/lighting/baked_outdoors/profiles'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path, help='Directory for per-world/map bake output and logs')
    parser.add_argument('--world', nargs='+', choices=['mm6', 'mm7', 'mm8'], default=['mm6', 'mm7', 'mm8'])
    parser.add_argument('--samples', type=int, help='Override profile samples; 16 for drafts, normally 64')
    parser.add_argument('--azimuth', type=float, help='Override sun azimuth in every selected map profile (degrees)')
    parser.add_argument('--blender', default='blender', help='Blender executable with Cycles support')
    parser.add_argument('--install', action='store_true', help='Copy successful lighting/recipe pairs into assets_dev')
    parser.add_argument('--dry-run', action='store_true', help='List candidates without baking or writing files')
    parser.add_argument('--retry-failed', type=Path, help='Retry only failed entries from this batch report')
    args = parser.parse_args()
    if args.samples is not None and args.samples < 1:
        parser.error('--samples must be positive')
    if args.azimuth is not None and not math.isfinite(args.azimuth):
        parser.error('--azimuth must be finite')

    sources = sorted(source for world in set(args.world)
                     for source in (ROOT / 'assets_dev/worlds' / world / 'maps').glob('*.odm'))
    if args.retry_failed:
        try:
            previous = json.loads(args.retry_failed.read_text())['results']
            failed = {result['map'] for result in previous if result['status'] == 'failed'}
        except (OSError, ValueError, KeyError, TypeError) as error:
            parser.error(f'Unable to read retry report: {error}')
        sources = [source for source in sources if f'{source.parent.parent.name}/{source.name}' in failed]
        if not sources:
            print('No failed maps to retry in the selected worlds.')
            return 0
    if not sources:
        parser.error('No native outdoor maps found in the selected worlds')
    output = args.output.resolve()
    # The producer writes the recipe before baking. Never let a failed job overwrite an installed recipe.
    assets = (ROOT / 'assets_dev').resolve()
    if output == assets or assets in output.parents:
        parser.error('--output must be outside assets_dev; use --install to copy successful pairs')

    print(f'{len(sources)} outdoor candidates; indoor BLV and other worlds are outside this producer.', flush=True)
    print('The producer rejects unsupported scene profiles, moving mechanisms and terrain overrides.', flush=True)
    if args.dry_run:
        for source in sources:
            print(source.relative_to(ROOT))
        print('Enumeration only: no scene validation, bakes or installation performed.')
        return 0

    blender = shutil.which(args.blender)
    if blender is None:
        parser.error(f'Blender executable not found: {args.blender}')
    output.mkdir(parents=True, exist_ok=True)
    template = json.loads((PROFILES / 'mm6_oute3.yml').read_text())
    results = []
    report_path = output / ('retry-report.json' if args.retry_failed else 'batch-report.json')
    if args.retry_failed and report_path.resolve() == args.retry_failed.resolve():
        parser.error('Use a different --output directory so the input retry report is preserved')
    for index, source in enumerate(sources, 1):
        world = source.parent.parent.name
        label = f'{world}/{source.name}'
        map_output = output / world / source.stem
        map_output.mkdir(parents=True, exist_ok=True)
        authored_profile = PROFILES / f'{world}_{source.stem}.yml'
        profile = json.loads(authored_profile.read_text()) if authored_profile.is_file() else dict(template)
        profile.update(world=world, map=source.name)
        if args.samples is not None:
            profile['samples'] = args.samples
        if args.azimuth is not None:
            profile['azimuth'] = args.azimuth % 360
        profile_path = map_output / 'profile.json'
        profile_path.write_text(json.dumps(profile, indent=2) + '\n')
        log_path = map_output / 'blender.log'
        result = dict(map=label, status='failed', output=str(map_output), log=str(log_path))
        print(f'[{index}/{len(sources)}] Baking {label} ({profile["samples"]} samples)', flush=True)
        try:
            command = [blender, '--background', '--factory-startup', '--python-exit-code', '1',
                       '--python', str(ROOT / 'tools/lighting/bake_outdoor.py'), '--',
                       '--profile', str(profile_path), '--output', str(map_output)]
            with log_path.open('w') as log:
                completed = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=False)
            if completed.returncode != 0:
                raise RuntimeError(f'Blender exited with code {completed.returncode}; see {log_path}')
            pair = [map_output / f'{source.stem}.lighting', map_output / f'{source.stem}.bake.json']
            if not all(path.is_file() for path in pair):
                raise RuntimeError('Producer did not emit both lighting and recipe files')
            if args.install:
                for path in pair:
                    shutil.copy2(path, source.parent / path.name)
            result['status'] = 'installed' if args.install else 'generated'
            print(f'  {result["status"]}: {label}', flush=True)
        except (OSError, RuntimeError) as error:
            result['error'] = str(error)
            print(f'  FAILED: {label}: {error}', flush=True)
        results.append(result)
        report_path.write_text(json.dumps(dict(results=results), indent=2) + '\n')

    failures = sum(result['status'] == 'failed' for result in results)
    print(f'Finished: {len(results) - failures} succeeded, {failures} failed. Report: {report_path}', flush=True)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
