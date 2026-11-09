"""Retain the nine reviewed isolated desktop runs and their GPU/model-loading evidence."""
import json
from pathlib import Path
import re
import shutil

from PIL import Image

P = Path(__file__).resolve().parents[1]
cases = {
    'outdoor_a': 'amulets-outdoor-a', 'outdoor_b': 'amulets-outdoor-b', 'outdoor_c': 'amulets-outdoor-c',
    'indoor_a': 'amulets-indoor-a', 'indoor_b': 'amulets-indoor-b',
    'gauntlet_outdoor_a': 'gauntlets-outdoor-a', 'gauntlet_outdoor_b': 'gauntlets-outdoor-b-retry',
    'gauntlet_indoor_a': 'gauntlets-indoor-a', 'amulets_final': 'amulets-final-retry',
}
results = []
for scene, label in cases.items():
    matches = list(Path('/tmp').glob('openyamm-desktop-' + label + '-*/run.json'))
    matches = [p for p in matches if json.loads(p.read_text())['request']['name'] == label]
    assert matches, (scene, 'Missing desktop run')
    run_path = max(matches, key=lambda p: p.stat().st_mtime)
    run = json.loads(run_path.read_text())
    assert run['status'] == 'completed' and run.get('exit_code', 0) == 0, (scene, run['status'])
    assert any(str(P / 'work' / f'native_{scene}.yml') in value for value in run['request']['set'])
    log = (run_path.parent / 'game.log').read_text(errors='replace')
    assert 'Renderer: OpenGL 3.3' in log and 'GPU: vendor=0x10de' in log, scene
    errors = re.findall(r'(?im)^.*(?:failed to load|could not load|failed to decode|missing model|missing texture).*$', log)
    assert not errors, (scene, errors)
    screenshot = P / 'review' / ('native_' + scene) / (scene + '.png')
    with Image.open(screenshot) as picture:
        assert picture.width >= 1280 and picture.height >= 720
        picture.verify()
    output = P / 'receipts/native_runs' / scene
    output.mkdir(parents=True, exist_ok=True)
    for name in ['run.json', 'game.log']:
        shutil.copy2(run_path.parent / name, output / name)
    results.append({'scene': scene, 'map': run['loaded_map'], 'run': str(output.relative_to(P) / 'run.json'),
                    'screenshot': str(screenshot.relative_to(P)), 'renderer': 'NVIDIA / OpenGL 3.3 / Wayland',
                    'model_load_errors': 0, 'visual_review': 'passed'})
assert len(results) == 9
receipt = {'status': 'passed', 'cases': results, 'performance_claim': False,
           'recovered_startup_failures': 'Two attempts failed to create an EGL surface before asset loading. Fresh isolated retries succeeded; originals retained in native_failures/.'}
(P / 'receipts/native_review.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('Retained nine reviewed native captures, NVIDIA/OpenGL, no model-load failures.')
