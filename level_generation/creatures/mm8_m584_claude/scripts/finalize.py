"""Archive reviewed Raven Man delivery and assert its installed provenance."""
import datetime
import hashlib
import json
import shutil
import sys
from pathlib import Path

P = Path(__file__).resolve().parents[1]
ROOT = P.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from merge_head_material import read_glb


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


review = P / 'review'
validation = review / 'validation'
validation.mkdir(exist_ok=True)
revision = 'raven_textured_60hz_native_hover_v2'
package = read(P / 'work/package_check.json')
for tier in 'abc':
    src = Path(f'/tmp/raven-playback-final-{tier}')
    report = read(src / 'playback.json')
    assert not report['errors'] and len(report['clips']) == 12
    assert {(r['clip'], r['rate']) for r in report['clips']} == {
        (clip, rate) for clip in package['clips'] for rate in (1, .25)}
    digest = sha(review / f'viewer/raven_{tier}.glb')
    for row in report['clips']:
        assert len(row['frames']) == 5
        for frame in row['frames']:
            assert frame['model_sha256'] == digest and frame['revision'] == revision
    shutil.copytree(src, review / f'playback/{tier}', dirs_exist_ok=True)
shutil.copyfile('/tmp/gog-playback.mjs', P / 'scripts/check_playback.mjs')
shutil.copyfile('/tmp/raven-regression-final.log', validation / 'actor_regression.log')
assert 'passed=1 failed=0' in (validation / 'actor_regression.log').read_text()
viewer = read(Path('/tmp/raven-viewer-final-check.log'))
assert viewer['ready'] == 'true' and viewer['switched'] == 18
assert not viewer['failed'] and not viewer['consoleErrors']
write(validation / 'viewer_check.json', viewer)

launches = {
    'out_models': '/tmp/openyamm-desktop-raven-final-out-models-twc_bk48',
    'out_sprites': '/tmp/openyamm-desktop-raven-final-out-sprites-zus88i09',
    'in_models': '/tmp/openyamm-desktop-raven-final-in-models-7g_xdwo5',
    'in_sprites': '/tmp/openyamm-desktop-raven-final-in-sprites-04lazv3x',
    'actions': '/tmp/openyamm-desktop-raven-final-actions-sf5zhbp1',
    'out_lods_final': '/tmp/openyamm-desktop-raven-final-wing-lods-qhqylcn8',
}
for label, directory in launches.items():
    src = Path(directory)
    record = read(src / 'run.json')
    assert record['status'] == 'completed' and record['exit_code'] == 0, label
    assert 'GPU: vendor=0x10de' in (src / 'game.log').read_text(), label
    dst = review / 'ingame/launch_records' / label
    dst.mkdir(parents=True, exist_ok=True)
    for name in ('run.json', 'game.log', 'prepare.yml', 'prepare.log', 'launch-settings.ini'):
        shutil.copyfile(src / name, dst / name)
    shutil.copytree(Path('/tmp/raven-native-final') / label, review / 'ingame' / label, dirs_exist_ok=True)
assert len(list((review / 'ingame/actions').glob('*.png'))) == 30
assert len(list((review / 'ingame/out_lods_final').glob('*.png'))) == 4
native = read(P / 'native/sources.json')
for record in native['sources'].values():
    assert sha(ROOT / record['path']) == record['sha256']
fixture = read(review / 'ingame/fixture.json')
for scene in fixture['scenes']:
    assert sha(ROOT / 'assets_dev' / scene['path']) == scene['original_sha256']

files = [P / 'export/raven_master.blend', P / 'textures/raven_ramps.json',
         *[review / f'viewer/raven_{tier}.glb' for tier in 'abc']]
sidecars = {}
for name in ('mm8_m584.glb', 'mm8_m584_polearm.glb'):
    exported = P / 'export' / name
    source = ROOT / 'assets_source/worlds/mm8/models' / name
    runtime = ROOT / 'assets_dev/worlds/mm8/models' / name
    assert sha(source) == sha(exported) == package[name]['sha256']
    files.extend((exported, source, runtime))
    document, _ = read_glb(runtime)
    for image in document['images']:
        if 'uri' in image:
            path = (runtime.parent / image['uri']).resolve()
            assert path.is_relative_to(ROOT / 'assets_dev') and path.is_file()
            sidecars[str(path.relative_to(ROOT))] = sha(path)
records = [{'path': str(path.relative_to(ROOT)), 'sha256': sha(path), 'bytes': path.stat().st_size}
           for path in files]
state_path = P / 'creature_3d_progress.json'
state = read(state_path)
credits = sum(job['consumed_credits'] for job in state['meshy']['jobs'].values())
assert credits == 55
native_review = {
    'revision': revision, 'agent_visual_review': 'complete',
    'renderer': 'NVIDIA OpenGL 3.3, SDL Wayland; engine-native screenshots',
    'comparisons': 'All three tiers in identical indoor/outdoor cameras; head/feet placement and materials reviewed.',
    'motion': 'Six posed clips; live hostile flight, melee, hit, death and normal loot-satchel transition.',
    'lods': 'Stationary combined diagnostic model, Standing at 0.25 seconds, forced LOD0-3.',
    'notes': [
        'Native wing phases and 3D motion differ intentionally; these are adapted performances.',
        'Moving-actor LOD attempts were superseded by the stationary model captures.',
        'The first stationary capture failed on console input timing; corrected timing completed.',
        'Late live comparison frames can leave the camera; front captures establish placement.',
        'Posed Dead verifies floor/weapon placement; live remains become a satchel by existing game design.',
        'Final feather LOD repair preserves LOD0/material/animation samples: work/lod_preservation.json.',
    ],
    'binary_hashes': sorted({read(Path(path) / 'run.json')['binary_sha256'] for path in launches.values()}),
}
write(validation / 'native_review.json', native_review)
receipt = {
    'identity': 'mm8:m584', 'recorded_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'technical_complete': True, 'user_artistic_acceptance': 'not_recorded',
    'meshy_credits': credits, 'credit_limit': state['meshy']['credit_limit'],
    'files': records, 'cooked_texture_sidecars': sidecars,
    'original_sprite_records_unchanged': len(native['sources']),
    'lod_correction_preservation': read(P / 'work/lod_preservation.json'),
    'production_review_maps_unchanged': True, 'package': package,
    'lods': read(P / 'export/lods.json'), 'viewer': viewer, 'native_review': native_review,
    'native_launch_records': {key: f'review/ingame/launch_records/{key}/run.json' for key in launches},
    'regression': 'review/validation/actor_regression.log',
    'build': {'command': 'cmake --build build --target openyamm -j25',
              'result': 'Passed during production; shared working-tree build, terminal output reviewed.'},
    'not_tested': ['Android', 'Vulkan'],
}
write(P / 'delivery.json', receipt)
readme = Path('/tmp/raven-readme.md').read_text()
readme += '''
## Final delivery verification

Ordinary `openyamm` build passed. The focused
`mm8_raven_man_actor_models_keep_flight_and_polearms` regression passed against the final installed body.
The shared viewer checker passed all 18 tier/clip combinations with no console errors. All three portable
exports completed normal and quarter-speed playback of all six clips, with reports bound to their final hashes.

Desktop OpenGL captures cover all tiers indoors/outdoors, the six posed actions, live hostile flight/combat,
hit/death and the ordinary loot-satchel transition. A stationary model verifies LOD0-3 at the same pose;
the earlier moving-actor LOD attempts are not used as placement evidence. See
[native review](review/validation/native_review.json) and [launch records](review/ingame/launch_records/).
The fixture's production map sources and all inventoried native sprites passed hash preservation checks.

Technical production and agent visual review are complete. Android/Vulkan rendering was not checked;
user artistic acceptance is not recorded. No commit was made.
'''
(P / 'README.md').write_text(readme)
state.update(stage='complete', technical_status='complete', artistic_acceptance='not_recorded',
             updated_at=receipt['recorded_at'], delivery_receipt='delivery.json', remaining_findings=[],
             next_action={'owner': 'user', 'action': 'Optional artistic review in the delivered viewer.'})
state['selected_artifacts'] = [
    {'role': role, 'path': str(path.relative_to(P)), 'sha256': sha(path)}
    for role, path in [('body', P / 'export/mm8_m584.glb'),
                       ('polearm', P / 'export/mm8_m584_polearm.glb'),
                       ('editable_master', P / 'export/raven_master.blend'),
                       *[(f'portable_{tier}', review / f'viewer/raven_{tier}.glb') for tier in 'abc']]]
for component in state['required_components']:
    component.update(assembly_review='complete', evidence='README.md')
state['textures'] = {'body': 'body_texture_v1', 'head': 'head_texture_v2',
                     'rejected_head': 'head_texture_v1', 'evidence': 'textures/composition.json'}
state['runtime_review'] = {'status': 'complete', 'binding': 'assets_dev/worlds/mm8/models/actors.yml',
                           'scale': 75, 'living_hover_m': .56,
                           'evidence': 'review/validation/native_review.json',
                           'regression': 'review/validation/actor_regression.log'}
state['motion']['final_review'] = 'All six exported clips, three tiers, normal/quarter speed; native posed and live checks.'
state['motion']['evidence'] = ['work/deformation_final.json', 'work/contacts_final.json',
                              'work/export_parity.json', 'review/playback', 'review/ingame/actions']
state['correction_ledger'] = [
    'Replaced fused generated wings with layered opaque articulated feathers.',
    'Fitted mesh-measured fingers, two-hand polearm grip and controlled airborne forward death.',
    'Added arm twist bones and diffused shoulder weights; final contact/deformation checks passed.',
    'Corrected square head UV packing; rejected head texture v1 and selected v2.',
    'Matched native tier ramps and corrected measured normal-map conventions.',
    'Recalibrated scale from 83.2 to 75 and added living-only 0.56 m hover after native comparison.',
    'Added required virtual flight strides; focused actor-binding regression passed.',
    'Kept authored feather shells in all LODs after native reduction exposed gaps; LOD0 and clips preserved.',
]
write(state_path, state)
print(json.dumps({'technical_complete': True, 'files': len(records), 'credits': credits,
                  'native_source_records': len(native['sources'])}))
