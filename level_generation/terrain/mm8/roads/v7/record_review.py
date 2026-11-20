"""Bind the inspected final join reconstruction and border correction to its evidence."""
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
assert len(changed) == 36
painted = {'drsrne1.png', 'drsrne2.png', 'gdrdne1.png', 'gdrdne2.png'}
for name in set(changed) - painted:
    assert np.array_equal(read(HERE / 'runtime' / name)[8:-8, 8:-8],
                          read(HERE.parent / 'v6/runtime' / name)[8:-8, 8:-8]), name
validation = json.loads((HERE / 'validation.json').read_text())
assert validation['build_sha256'] == sha(HERE / 'build.json')
assert not validation['failures'] and all(r['passed'] for r in validation['masks'])
frames = sorted((HERE / 'captures').glob('mm8_diagonal_v7_ports_a_walk_*.png'))
assert len(frames) == 13 and len({sha(f) for f in frames}) == 13
receipts = []
for side in ('east', 'south'):
    receipts.append(dict(name=side, raw_sha256=sha(HERE / 'raw' / (side + '.png')),
                         prompt_sha256=sha(HERE / 'prompts' / (side + '.txt')),
                         input_sha256=sha(HERE / 'inputs' / (side + '.png'))))
(HERE / 'generation_receipts.json').write_text(json.dumps(dict(tool='built-in imagegen', calls=receipts), indent=2) + '\n')
files = [HERE / n for n in ['build.json', 'validation.json', 'review_stage.json', 'generation_receipts.json',
                           'compose.py', 'match_ports.py', 'build_review.py', 'border_colour_comparison.png']]
files += list((HERE / 'raw').glob('*.png')) + list((HERE / 'prompts').glob('*.txt'))
files += list((HERE / 'inputs').glob('*.png')) + list(HERE.glob('movement_*.png')) + frames
files += list(HERE.glob('v?_path.png')) + list(HERE.glob('v?_*_join.png'))
for name in ['mm8_diagonal_v7_ports_a', 'mm8_diagonal_v7_ports_b', 'mm8_diagonal_v7_ports_alvar']:
    files += [HERE / 'captures' / (name + suffix) for suffix in ['.png', '.json']]
files += [HERE / 'diagnostic' / 'mm8_diagonal_v7_uv_b.png',
          HERE / 'diagnostic' / 'mm8_diagonal_v7_original_b.png']
report = dict(status='visually_reviewed_for_road_edge_update', changed=changed, unchanged_files=203,
              interior_repainted=sorted(painted), border_only_count=32, preserved_other_road_interior=[240, 240],
              poses=stage['poses'], movement_samples=13,
              pose_a_image='captures/mm8_diagonal_v7_ports_a_walk_start.png',
              observations=['East and south join enlargements show coherent stone surfaces instead of v6 rectangular graft cuts.',
                            'The exact-pose faint border line was identified using UVs, then removed by common border colours.',
                            'Native assembled path, straight entry/exit and13 walking samples inspected after final border correction.',
                            'Alvar matched-camera comparison retains existing straight-road shapes and stone artwork.',
                            'Grey diagonal companions inspected for shared stone shapes and grey-earth contact shading.'],
              limitations=['V6 road width is retained; this is not an exact native-width restoration.',
                           'Small polygonal stone-edge irregularities remain.',
                           'Later walking samples are partially occluded by actors; inspection is sampled, not exhaustive.',
                           'Xvfb captures do not establish hardware GPU performance.',
                           'Earlier final_pose captures precede the final shared-colour correction and are not acceptance evidence.'],
              evidence={str(f.relative_to(P)): sha(f) for f in files})
(HERE / 'visual_review.json').write_text(json.dumps(report, indent=2) + '\n')
print('Bound36 road corrections,203 unchanged terrain files, both supplied poses,13 walk samples and Alvar')
