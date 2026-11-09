"""Check that invalid explicit party fixtures and invalid runtime assertions actually fail."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

import yaml

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
STAGE = Path('/tmp/openyamm-brackenford-greywatch')
GAME = ROOT / 'build/game/openyamm'
SOURCE = PROJECT / 'source/baseline_party.json'
party = json.loads(SOURCE.read_text())
cases = []


def fixture_case(name, edit, message):
    fixture = copy.deepcopy(party)
    edit(fixture)
    cases.append((name, [{'new_game_flow': {'start_map': 'lg02.blv', 'party': fixture}}], message))


fixture_case('unknown_class', lambda p: p['members'][0].update({'class': 'NotAnMM8Class'}),
             'party fixture requires a valid class')
fixture_case('ineligible_skill', lambda p: p['members'][4]['skills'].append(
    {'name': 'Plate', 'level': 4, 'mastery': 2}), 'class-ineligible skill')
fixture_case('duplicate_skill', lambda p: p['members'][0]['skills'].append(p['members'][0]['skills'][0]),
             'duplicate or class-ineligible skill')
fixture_case('invalid_equipment', lambda p: p['members'][0]['equipment'].update(main_hand=999999),
             'party fixture cannot equip')
fixture_case('zero_level', lambda p: p['members'][0].update(level=0), 'positive level')
fixture_case('experience_overflow', lambda p: p['members'][0].update(level=100000), 'supported experience range')
fixture_case('experience_below_level', lambda p: p['members'][0].update(experience=1), 'experience is below its level')
cases.append(('failing_health_bound',
    [{'new_game_flow': {'start_map': 'lg02.blv', 'party': party}},
     {'assert': {'runtime_event_variable': {'id': 3, 'member_index': 0, 'max': -1}}}],
    'expected runtime_event_variable[3].member[0]<=-1'))
cases.append(('invalid_action_duration',
    [{'new_game_flow': {'start_map': 'lg02.blv', 'party': party}},
     {'press_action': {'action': 'attack', 'seconds': -1}}], 'positive finite duration'))
results = []
with tempfile.TemporaryDirectory(prefix='levelgen-party-validation-') as temporary:
    for name, steps, message in cases:
        scenario = {'id': 'levelgen.invalid.' + name, 'title': name,
                    'world': 'mm8', 'mode': 'faithful', 'steps': steps}
        path = Path(temporary) / (name + '.yml')
        path.write_text(yaml.safe_dump(scenario, sort_keys=False))
        process = subprocess.run([str(GAME), '--world', 'mm8', '--headless-run-scenario', str(path),
                                  '--scenario-no-color'], cwd=STAGE, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, universal_newlines=True)
        passed = process.returncode != 0 and message in process.stdout
        # Retain the exact error and expectation, without duplicating asset-loader diagnostics.
        errors = [line for line in process.stdout.splitlines() if line.startswith('Scenario failure:')]
        results.append({'case': name, 'passed': passed, 'expected_error': message,
                        'exit_code': process.returncode, 'errors': errors})
        print(name + ': ' + ('PASS (rejected as expected)' if passed else 'FAIL'), flush=True)
report = {'scope': 'Negative scenario coverage; no combat difficulty claim', 'results': results,
          'all_passed': all(case['passed'] for case in results),
          'fixture_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          'game_binary_sha256': hashlib.sha256(GAME.read_bytes()).hexdigest()}
(PROJECT / 'review/baseline_party_validation.json').write_text(json.dumps(report, indent=2) + '\n')
raise SystemExit(0 if report['all_passed'] else 1)
