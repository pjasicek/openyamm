"""Bind the inspected diagonal corrections to source art and exact-pose capture evidence."""
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
manifest = json.loads((P / 'complete_runtime_x2/manifest.json').read_text())
changed = [n for n, r in old['files'].items() if manifest['files'][n]['sha256'] != r['sha256']]
assert set(changed) == {n + '.png' for n in build['changed']} and len(changed) == 4
stage_difference = [n for n, r in manifest['files'].items() if stage['files'][n] != r['sha256']]
assert stage_difference == ['gdrdne2.png']
grid = json.loads((P / 'effective_grids.json').read_text())['out01']
assert 'gdrdne2' not in {n for row in grid for n in row}
for name in {n for row in grid for n in row}:
    assert stage['files'][name + '.png'] == manifest['files'][name + '.png']['sha256']
frames = sorted((HERE / 'captures').glob('mm8_diagonal_v5_final_walk_*.png'))
assert len(frames) == 13 and len({sha(f) for f in frames}) == 13
files = [HERE / n for n in ('build.json', 'validation.json', 'review_stage.json', 'exact_comparison.png',
                            'tile_comparison.png', 'movement_review.png', 'compose.py', 'generation_receipts.json')]
for name in ('mm8_diagonal_v4_exact', 'mm8_diagonal_native_exact', 'mm8_diagonal_v5_final'):
    files.extend(HERE / 'captures' / (name + suffix) for suffix in ('.json', '.png'))
files += frames
files += list((HERE / 'raw').glob('*.png')) + list((HERE / 'prompts').glob('*.txt')) + list((HERE / 'inputs').glob('*.png'))
report = dict(status='visually_reviewed_for_road_edge_update', changed=changed, unchanged_files=235,
              exact_pose=stage['pose'],
              observations=[
                  'Matched original/v4/final comparison at the supplied Dagger Wound pose: the large left teardrop protrusion is shortened and the opposite hooked end is filled into substantial edge stones.',
                  'Natural polygonal edge variation, stone scale, palette and dark contact shading remain. No claim of a ruler-straight road outline.',
                  '13 sequential walking samples along the reported diagonal inspected; repaired shape repeats without the original long pointed tip. Actor movement partly occludes some later samples.',
                  'Four original/previous/final tile comparisons inspected, including final grey mask cleanup; no new clipped stone or grey-earth tint fringe observed.'],
              limitations=['Sampled exact-pose and movement review is not an exhaustive inspection of every map cell or mip.',
                           'Xvfb captures do not establish GPU performance.',
                           'The walk stage predates final one-pixel coverage-hole cleanup in gdrdne2 only. That texture is absent from out01; every texture used on out01 matches the final export. Final grey artwork was checked offline.'],
              evidence={str(f.relative_to(P)): sha(f) for f in files},
              generation=dict(tool='built-in imagegen', calls=6, prompts='roads/v5/prompts', raw='roads/v5/raw',
                              rejected='drsrne2_rejected_wrong_stone: removed a neighbouring stone; never used',
                              successful_tip_input='roads/v5/inputs/drsrne2_tip_crop.png'),
              stage_differences_unused_in_captured_map=stage_difference)
(HERE / 'visual_review.json').write_text(json.dumps(report, indent=2) + '\n')
print('Bound exact-pose comparison,13 movement samples and final four-tile review;235 textures unchanged')
