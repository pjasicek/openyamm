"""Repeat fixed native views against the preserved release or the simplified candidate."""
import argparse
import configparser
import json
from pathlib import Path
import subprocess

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
REVIEW = PROJECT/'review/geometry_simplification_v1'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['before', 'after', 'runtime'])
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--ids', nargs='+')
    args = parser.parse_args()
    output = REVIEW/args.phase/'gameplay'
    output.mkdir(parents=True, exist_ok=True)
    # Compare with the user's preserved playtest preferences, changing only the candidate asset composition.
    preferences = configparser.ConfigParser()
    preferences.read(PROJECT/'local_playtest/playtest/settings.ini')
    staged = configparser.ConfigParser()
    staged.read(args.stage/'settings.ini')
    preferences['assets']['root'] = staged['assets']['root']
    settings_dir = REVIEW/args.phase/'capture_settings'
    settings_dir.mkdir(parents=True, exist_ok=True)
    with (settings_dir/'settings.ini').open('w') as stream:
        preferences.write(stream, space_around_delimiters=False)
    views = json.loads((REVIEW/('runtime_plan.json' if args.phase == 'runtime' else 'capture_plan.json')).read_text())
    for view in views:
        if args.ids and view['id'] not in args.ids:
            continue
        name = 'mm5_simplify_'+args.phase+'_'+view['id']
        command = [str(ROOT/'tools/capture_gameplay.sh'), name,
                   '--map', 'mm5_sw.odm', '--world', 'mm5', '--control-scheme', 'classic',
                   '--binary', str(PROJECT/'local_playtest/bin/openyamm'), '--stage', str(settings_dir),
                   '--review-directory', str(output), '--warmup', '2', '--seconds', '0',
                   '--pose']+list(map(str, view['pose']))
        if view.get('actions'):
            command += ['--actions', view['actions']]
        with (output/(name+'_capture.log')).open('w') as stream:
            subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)
        print('Captured '+name, flush=True)


if __name__ == '__main__':
    main()
