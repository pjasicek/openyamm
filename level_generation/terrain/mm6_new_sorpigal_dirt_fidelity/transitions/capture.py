"""Capture isolated map/fixture views, each on its own X display."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import json
from pathlib import Path
import subprocess

P = Path(__file__).resolve().parent
ROOT = P.parents[3]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--only', nargs='*')
parser.add_argument('--version', choices=['v1', 'v2'], default='v2')
args = parser.parse_args()
review = P / 'captures' / args.version
review.mkdir(exist_ok=True)
poses = json.loads((P / 'captures/poses.json').read_text())


def capture(pose):
    name = pose['stage'] + '_' + pose['name']
    if args.only and name not in args.only:
        return
    if (review / ('dirt_' + args.version + '_' + name + '.json')).exists():
        return
    with (review / (name + '_capture.log')).open('w') as log:
        command = ['xvfb-run', '-a', '-s', '-screen 0 1600x1200x24', 'python3',
                   str(ROOT / 'level_generation/projects/brackenford_greywatch/capture_gameplay.py'),
                   'dirt_' + args.version + '_' + name, '--world', 'mm6', '--map', 'oute3.odm',
                   '--stage', pose['stage_path'], '--review-directory', str(review),
                   '--start-save', pose['save'], '--diagnostic-flying',
                   '--actions', pose.get('actions', str(P.parents[1] / 'mm6_new_sorpigal_master_study/references/capture_actions.json')),
                   '--binary', '/tmp/openyamm-sorpigal-dirt-fidelity/transitions/openyamm', '--warmup', '1', '--seconds', '0']
        subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    print('Captured', name, flush=True)


with ThreadPoolExecutor(max_workers=2) as pool:
    list(pool.map(capture, poses))
