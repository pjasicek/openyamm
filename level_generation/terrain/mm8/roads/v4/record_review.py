"""Bind the manually inspected road-edge comparison and movement captures to their inputs."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from common import *
import json

stage = json.loads((HERE / 'review_stage.json').read_text())
assert {f.name: sha(f) for f in (Path(stage['stage']) / 'assets_dev/worlds/mm8/terrain_x2').glob('*.png')} == stage['files']
build = json.loads((HERE / 'build.json').read_text())
validation = json.loads((HERE / 'validation.json').read_text())
assert validation['build_sha256'] == sha(HERE / 'build.json')
assert not validation['failures'] and all(r['passed'] for r in validation['masks'])
old = json.loads((HERE / 'previous_delivery/complete_runtime_x2/manifest.json').read_text())
changed = [n for n, r in old['files'].items() if stage['files'][n] != r['sha256']]
assert set(changed) == {n + '.png' for n in build['changed']}
assert len(changed) == 30
frames = sorted((HERE / 'captures').glob('mm8_v4_flat_walk_walk_*.png'))
assert len(frames) == 13 and len({sha(f) for f in frames}) == 13
files = [HERE / n for n in ('build.json', 'validation.json', 'review_stage.json', 'repeat_comparison.png', 'connected_review.png', 'movement_review.png', 'native_comparison.png', 'compose.py', 'raw/drsrns.png', 'prompts/drsrns.txt')]
for name in ('mm8_v3_dagger', 'mm8_v4_dagger', 'mm8_v3_alvar', 'mm8_v4_alvar', 'mm8_v4_flat_walk'):
    files.extend(HERE / 'captures' / (name + suffix) for suffix in ('.json', '.png'))
files += frames
report = dict(status='visually_reviewed_for_road_edge_update', changed=changed, unchanged_files=209,
              observations=[
                  'Original/previous/repaired NS repeat comparison: narrow pointed stone fingers and deep bites replaced by fuller edge stones. Broad irregularity, palette and dark mortar retained.',
                  'Matched out01 and out03 native captures: same shared NS defect visible in both at this angle; repaired silhouettes restrained in both. These are representative native poses, not an exact reconstruction of user screenshot1293.',
                  'All19 dirt-road shapes inspected in connected_review.png: junction interiors and diagonal character retained; no new clipped edge stones observed.',
                  '13 sequential grounded flat approach samples inspected: repaired repeated edges and approach to crossroads remain coherent; no discontinuous tile border observed.'],
              limitations=['Native actor/UI states differ slightly between runs.', 'Sampled movement inspection does not establish absence of all temporal artifacts.', 'Xvfb captures do not measure real-GPU performance.', 'Prior v3 road visual acceptance missed the exaggerated teeth; this revision supersedes that edge judgment.'],
              evidence={str(f.relative_to(P)): sha(f) for f in files},
              generation=dict(tool='built-in imagegen', calls=1, prompt='roads/v4/prompts/drsrns.txt',
                              prompt_sha256=sha(HERE / 'prompts/drsrns.txt'), raw_sha256=sha(HERE / 'raw/drsrns.png')))
(HERE / 'visual_review.json').write_text(json.dumps(report, indent=2) + '\n')
print('Bound native comparisons, connected tiles and13 movement samples;209 runtime textures unchanged')
