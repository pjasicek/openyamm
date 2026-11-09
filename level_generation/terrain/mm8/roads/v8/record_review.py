"""Record inspected v8 views and bind them to the exact candidate export."""
import sys,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from common import *
manifest=json.loads((P/'complete_runtime_x2/manifest.json').read_text())
old=json.loads((HERE/'previous_delivery/complete_runtime_x2/manifest.json').read_text())
changed=[n for n,r in manifest['files'].items() if r['sha256']!=old['files'][n]['sha256']]
diagonal=[n for n in changed if n[4:7] in ('ne1','ne2','nw1','nw2')]
for n in set(changed)-set(diagonal):
 assert np.array_equal(read(HERE/'runtime'/n)[12:-12,12:-12],read(HERE.parent/'v7/runtime'/n)[12:-12,12:-12])
stage=Path('/tmp/openyamm-mm8-terrain-review/diagonal_v8_boundaries/assets_dev/worlds/mm8/terrain_x2')
assert {f.name:sha(f) for f in stage.glob('*.png')}=={n:r['sha256'] for n,r in manifest['files'].items()}
evidence=[HERE/n for n in ['prepare_native.py','compose.py','match_boundaries.py','fixtures.py','generation.json','native_inventory.json','assembled_paths.png','native_entry_exit.png','walking_0.png','walking_1.png','build.json','validation.json']]
for pattern in ['mm8_diagonal_v8_boundaries_b.*','mm8_diagonal_v8_walk_a.json','mm8_diagonal_v8_walk_a_walk*.png','mm8_diagonal_v8_alvar.*']:
 evidence.extend((HERE/'captures').glob(pattern))
review=dict(status='visually_reviewed_for_road_edge_update',changed=changed,unchanged_files=239-len(changed),interior_repainted=diagonal,border_only_count=len(changed)-len(diagonal),preserved_other_road_interior=[232,232],evidence={str(f.relative_to(P)):sha(f) for f in evidence},candidate_manifest_sha256=sha(P/'complete_runtime_x2/manifest.json'),findings=['Both diagonal orientations preserve original footprint and stone arrangement; repeated paths inspected against native and v7.','Known poseB colour discontinuity removed after boundary matching; native irregularity remains without v7 hooked projections.','13 walking samples from poseA inspected; no sharp repeating tile boundary observed.','Native Dagger entry and exit montage connects to retained straight-road artwork.','Alvar straight-road view inspected after boundary changes; central artwork unchanged.'],limitations=['Generated detail is deliberately subtle; native structural layer remains softer than heavily redrawn v7.','Endpoint colour averaging is a compromise and does not preserve every original edge pixel.','Xvfb views establish appearance, not GPU performance. User review remains welcome.'])
(HERE/'visual_review.json').write_text(json.dumps(review,indent=2)+'\n')
print('Review bound to',len(changed),'changed textures and',len(evidence),'evidence files')
