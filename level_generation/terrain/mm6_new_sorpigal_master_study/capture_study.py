"""Run under xvfb-run to capture the saved terrain reference cameras through the real game."""

import argparse
import json
from pathlib import Path
import subprocess

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('variant')
parser.add_argument('--only', nargs='+')
args = parser.parse_args()
poses = json.loads((PROJECT / 'poses.json').read_text())['poses']
for name in args.only or poses:
    assert name in poses
    print('Capturing', args.variant, name, flush=True)
    target = PROJECT / 'review' / args.variant
    target.mkdir(parents=True, exist_ok=True)
    with (target / (name + '_capture.log')).open('w') as log:
        subprocess.run([
            'python3', str(ROOT / 'level_generation/projects/brackenford_greywatch/capture_gameplay.py'),
            f'terrain_{args.variant}_fixed_{name}', '--world', 'mm6', '--map', 'oute3.odm',
            '--stage', '/tmp/openyamm-sorpigal-terrain-master-study/' + args.variant,
            '--review-directory', str(target),
            '--start-save', str(PROJECT / 'references/poses' / (name + '.oysav')),
            '--actions', str(PROJECT / 'references/capture_actions.json'),
            '--warmup', '1', '--seconds', '0',
        ], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    print('Captured', args.variant, name, flush=True)
