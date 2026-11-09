"""Run under Xvfb to compare all three terrain versions at an identical saved viewpoint."""
import argparse
from pathlib import Path
import subprocess

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--directory', type=Path, default=Path('/tmp/openyamm-sorpigal-dirt-fidelity'))
parser.add_argument('--only', nargs='+', choices=['original', 'current', 'candidate'])
args = parser.parse_args()
for mode in args.only or ['original', 'current', 'candidate']:
    print('Capturing', mode, flush=True)
    subprocess.run([
        'python3', str(ROOT / 'level_generation/projects/brackenford_greywatch/capture_gameplay.py'),
        'dirt_' + mode, '--world', 'mm6', '--map', 'oute3.odm',
        '--stage', str(args.directory / mode), '--binary', str(args.directory / 'openyamm'),
        '--review-directory', str(PROJECT / 'review'),
        '--start-save', str(PROJECT / 'references/Dirt_View.oysav'),
        '--actions', str(PROJECT.parent / 'mm6_new_sorpigal_master_study/references/capture_actions.json'),
        '--warmup', '1', '--seconds', '0'], cwd=ROOT, check=True)
