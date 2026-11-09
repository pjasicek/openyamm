"""Bind the inspected connected bands to their exact capture and generation inputs."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from common import *
import json

stage = json.loads((HERE / 'review_stage.json').read_text())
manifest = json.loads((P / 'complete_runtime_x2/manifest.json').read_text())
expected = {n: r['sha256'] for n, r in manifest['files'].items()}
assert stage['files'] == expected
assert {f.name: sha(f) for f in (Path(stage['stage']) / 'assets_dev/worlds/mm8/terrain_x2').glob('*.png')} == expected
old = json.loads((HERE / 'previous_delivery/complete_runtime_x2/manifest.json').read_text())
changed = [n for n in expected if expected[n] != old['files'][n]['sha256']]
assert set(changed) == {'drsrne1.png', 'drsrne2.png', 'gdrdne1.png', 'gdrdne2.png'}
validation = json.loads((HERE / 'validation.json').read_text())
assert validation['build_sha256'] == sha(HERE / 'build.json')
assert not validation['failures'] and all(r['passed'] for r in validation['masks'])
frames = sorted((HERE / 'captures').glob('mm8_diagonal_v6_walk_walk_*.png'))
assert len(frames) == 13 and len({sha(f) for f in frames}) == 13
receipts = []
for name, prompt, inputs, disposition in [
    ('drsrne1_attempt1', 'diagonal', ['roads/v4/authoring/drsrne1.png', 'roads/v6/inputs/drsrne1_coverage.png'], 'rejected_opening_drift'),
    ('drsrne2', 'drsrne2', ['roads/v4/authoring/drsrne2.png', 'roads/v6/inputs/drsrne2_coverage.png'], 'registered_and_composited'),
    ('drsrne1', 'drsrne1', ['roads/v6/inputs/drsrne1_coverage.png', 'roads/v4/authoring/drsrne1.png'], 'registered_and_composited')]:
    receipts.append(dict(raw='raw/' + name + '.png', raw_sha256=sha(HERE / 'raw' / (name + '.png')),
                         prompt='prompts/' + prompt + '.txt', prompt_sha256=sha(HERE / 'prompts' / (prompt + '.txt')),
                         input_order=inputs, inputs={n: sha(P / n) for n in inputs}, disposition=disposition))
(HERE / 'generation_receipts.json').write_text(json.dumps(dict(tool='built-in imagegen', calls=receipts), indent=2) + '\n')
files = [HERE / n for n in ['build.json', 'validation.json', 'review_stage.json', 'generation_receipts.json',
                           'compose.py', 'prepare_guides.py', 'exact_comparison.png', 'tile_comparison.png',
                           'connected_width.json', 'v5_connected.png', 'v6_connected.png']]
files += list((HERE / 'raw').glob('*.png')) + list((HERE / 'prompts').glob('*.txt'))
files += list((HERE / 'inputs').glob('*')) + list(HERE.glob('movement_*.png')) + frames
for name in ['mm8_diagonal_v6_pose_a', 'mm8_diagonal_v6_pose_b', 'mm8_diagonal_v6_walk']:
    files += [HERE / 'captures' / (name + suffix) for suffix in ['.png', '.json']]
report = dict(status='visually_reviewed_for_road_edge_update', changed=changed, unchanged_files=235,
              poses=stage['poses'], movement_samples=13,
              observations=['Both supplied poses compared with v5; repeated deep dirt bites removed.',
                            'Connected native patch and all four tiles inspected; consistent band with small stone-edge irregularity.',
                            '13 walking samples inspected; no return of the deep bay while approaching tile joins.',
                            'Grey companions share the contour, with grey substrate contact shading.'],
              limitations=['Fixed openings constrain the band: former bulges are narrower; native width is not identical.',
                           'Small polygonal edge protrusions remain; this is not a perfectly smooth outline.',
                           'Actors partially occlude later walking samples; views are sampled, not exhaustive.',
                           'Xvfb captures do not establish hardware GPU performance.'],
              evidence={str(f.relative_to(P)): sha(f) for f in files})
(HERE / 'visual_review.json').write_text(json.dumps(report, indent=2) + '\n')
print('Bound two supplied poses,13 walking samples and four tiles to exact239-file capture stage')
