"""Run focused content checks against the isolated installation and retain reproducible evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import yaml

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--directory', type=Path, default=Path('/tmp/openyamm-brackenford-greywatch'))
parser.add_argument('--report', default='content_checks.json', help='Report basename inside the project review directory')
parser.add_argument('scenarios', nargs='*')
args = parser.parse_args()
assert Path(args.report).name == args.report
stage = args.directory.resolve()
assert json.loads((stage/'levelgen-stage.json').read_text())['project'] == 'brackenford_greywatch'
names = args.scenarios or ['town_doors', 'town_topics', 'town_population_smoke', 'wilderness_ai_control',
    'outdoor_interactions_smoke', 'loose_item_pickup', 'original_exit_mm6', 'original_exit_mm7', 'original_exit_mm8']
results = []
for name in names:
    source = PROJECT/(name+'.yml')
    scenario = yaml.safe_load(source.read_text())
    assert scenario['mode'] == 'faithful'
    log = PROJECT/'review'/(name+'.log')
    start = time.monotonic()
    with log.open('w') as stream:
        process = subprocess.run([str(ROOT/'build/game/openyamm'), '--world', scenario['world'],
            '--headless-run-scenario', str(source), '--scenario-no-color'], cwd=stage,
            stdout=stream, stderr=subprocess.STDOUT)
    passed = process.returncode == 0 and ('Scenario passed: '+scenario['id']) in log.read_text(errors='replace')
    results.append({'scenario': name, 'id': scenario['id'], 'passed': passed,
        'exit_code': process.returncode, 'steps': len(scenario['steps']),
        'elapsed_seconds': round(time.monotonic()-start,3), 'log': str(log.relative_to(PROJECT)),
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
    print(name+': '+('PASS' if passed else 'FAIL'), flush=True)
tracked = ['runtime/worlds/mm8/maps/lg01.odm', 'runtime/worlds/mm8/maps/lg01.scene.yml',
    'runtime/worlds/mm8/events/maps/lg01.lua', 'source/town_registry.json', 'source/lg01.content.json',
    'runtime/worlds/mm8/maps/lg02.blv', 'runtime/worlds/mm8/maps/lg02.scene.yml',
    'runtime/worlds/mm8/events/maps/lg02.lua']
for name in tracked:
    if name.startswith('runtime/'):
        staged = stage/'assets_editor_dev'/name[len('runtime/'):]
        assert staged.read_bytes() == (PROJECT/name).read_bytes(), ('stale staged artifact',str(staged))
report = {'scope': 'Focused content and original-map regression checks; complete goal acceptance remains pending',
    'results': results, 'all_selected_passed': all(r['passed'] for r in results),
    'artifact_sha256': {name: hashlib.sha256((PROJECT/name).read_bytes()).hexdigest() for name in tracked},
    'settings_sha256': hashlib.sha256((stage/'settings.ini').read_bytes()).hexdigest(),
    'game_binary_sha256': hashlib.sha256((ROOT/'build/game/openyamm').read_bytes()).hexdigest()}
(PROJECT/'review'/args.report).write_text(json.dumps(report,indent=2)+'\n')
sys.exit(0 if report['all_selected_passed'] else 1)
