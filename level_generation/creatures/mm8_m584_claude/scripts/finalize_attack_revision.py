"""Record the reviewed Attack-only revision without invalidating retained production evidence."""
from pathlib import Path
import datetime,hashlib,json,shutil,sys
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];W=P/'work/attack_revision_1';revision='raven_attack_diagonal_v3'
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
validation=P/'review/attack_revision_1/validation';validation.mkdir(exist_ok=True)
contact=read(W/'contacts.json')['Attack'];deform=read(W/'deformation.json')['Attack']
assert not contact['contacts'] and min(contact['floor_min'].values())>0
assert deform['arm']['p99']<2.05 and deform['hand']['worst']['max']<2.35
assert read(P/'work/export_parity.json')['Attack']['max_position_error_m']<.0001
for t in 'abc':
 source=Path(f'/tmp/raven-attack-playback-{t}');d=read(source/'playback.json');digest=sha(P/f'review/viewer/raven_{t}.glb')
 assert not d['errors'] and {(r['clip'],r['rate']) for r in d['clips']}=={('Attack',1),('Attack',.25)}
 for row in d['clips']:
  assert len(row['frames'])==5
  assert all(f['model_sha256']==digest and f['revision']==revision for f in row['frames'])
 shutil.copytree(source,P/f'review/attack_revision_1/playback/{t}',dirs_exist_ok=True)
v=read(Path('/tmp/raven-attack-viewer-check.json'));assert v['switched']==18 and not v['failed'] and not v['consoleErrors']
write(validation/'viewer.json',v)
reg=Path('/tmp/raven-attack-regression.log').read_text();assert 'passed=1 failed=0' in reg
(validation/'actor_regression.log').write_text(reg)
native={}
for place,folder in zip(('indoor','outdoor'),sys.argv[1:]):
 source=Path(folder);run=read(source/'run.json');log=(source/'game.log').read_text()
 assert run['status']=='completed' and run['exit_code']==0
 assert 'GPU: vendor=0x10de' in log and 'Actor model load failed' not in log
 captures=Path(f'/tmp/raven-attack-native/{place}')
 assert len(list(captures.glob('Attack-*.png')))==7
 if place=='indoor':assert len(list(captures.glob('live-*.png')))==12
 dest=P/f'review/attack_revision_1/native/{place}';shutil.copytree(captures,dest,dirs_exist_ok=True)
 for name in ('run.json','game.log','prepare.yml','prepare.log','launch-settings.ini'):shutil.copyfile(source/name,dest/name)
 native[place]={'launch_record':str((dest/'run.json').relative_to(P)),'binary_sha256':run['binary_sha256'],'captures':len(list(captures.glob('*.png')))}
assert set(native)=={'indoor','outdoor'}
assert sha(P/'export/mm8_m584.glb')==sha(ROOT/'assets_source/worlds/mm8/models/mm8_m584.glb')
for row in read(W/'export_preservation.json'):assert row['static_data_and_five_other_clips_identical'] and sha(P/row['path'])==row['after_sha256']
for row in read(P/'native/sources.json')['sources'].values():assert sha(ROOT/row['path'])==row['sha256']
for row in read(P/'review/ingame/fixture.json')['scenes']:assert sha(ROOT/'assets_dev'/row['path'])==row['original_sha256']
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
record={'revision':revision,'recorded_at':now,'status':'complete','user_artistic_acceptance':'not_recorded',
 'description':'High right-side windup, backward lean, fast diagonal slash across to the left, forward body follow-through; supporting grip retained and wings swept clear.',
 'timing':{'windup_hold_seconds':[.62,.70],'impact_seconds':26/30,'follow_through_seconds':.98,'duration_seconds':35/30},
 'body_angles_degrees':{'windup_pitch':-15,'follow_pitch':22,'windup_yaw':-32,'follow_yaw':55},
 'checks':{'contacts':contact,'deformation':deform,'export_parity':read(P/'work/export_parity.json')['Attack'],'native':native,'viewer':str((validation/'viewer.json').relative_to(P)),'regression':str((validation/'actor_regression.log').relative_to(P))},
 'preservation':'work/attack_revision_1/export_preservation.json','editable_preservation':'work/attack_revision_1/checkpoint_preservation.json','new_paid_credits':0,
 'superseded_native_attempt':'Initial fixture symlink was not accepted by asset lookup; refreshed as a hard link and repeated both checks.','not_tested':['Android','Vulkan']}
write(P/'review/attack_revision_1/revision.json',record)
# Keep the full-production evidence intact; its unchanged clips/materials are proved above.
receipt=read(P/'delivery.json');receipt.update(recorded_at=now,technical_complete=True,attack_revision=record,package=read(P/'work/package_check.json'),viewer=v)
for row in receipt['files']:
 path=ROOT/row['path'];row.update(sha256=sha(path),bytes=path.stat().st_size)
for path,digest in receipt['cooked_texture_sidecars'].items():assert sha(ROOT/path)==digest
write(P/'delivery.json',receipt)
state=read(P/'creature_3d_progress.json');state.update(stage='complete',technical_status='complete',updated_at=now,remaining_findings=[],next_action={'owner':'user','action':'Review the revised Attack in the viewer; artistic acceptance remains optional.'})
state['attack_revision'].update(status='complete',revision=revision,evidence='review/attack_revision_1/revision.json')
for row in state['selected_artifacts']:row['sha256']=sha(P/row['path'])
state['motion']['adaptation']='Native wingbeat and hovering legs; body-led diagonal attack with backward anticipation and forward follow-through; controlled two-hand grip and airborne death.'
state['motion']['final_review']='Original full-production review retained for unchanged clips; revised Attack checked on three exported tiers at 1x and 0.25x, with indoor/outdoor native poses and live combat.'
state['motion']['evidence'].append('review/attack_revision_1/revision.json')
state['correction_ledger'].append('User-directed stronger right-high to left-low Attack: retained fitted two-hand action, enlarged torso anticipation/rotation, forward follow-through and feather clearance; only Attack changed.')
write(P/'creature_3d_progress.json',state)
p=P/'README.md';s=p.read_text().replace('Local 2HandAxeAttack1 overhead chop, fitted two-hand grip','Body-led right-high to left-low slash, fitted two-hand grip')
s=s.replace('exports completed normal and quarter-speed playback of all six clips, with reports bound to their final hashes.','exports completed normal and quarter-speed playback of all six clips, with reports bound to the original delivery hashes.\nThe Attack-only revision below supersedes that clip; preservation checks retain the other five clips exactly.')
s+='''
## Stronger diagonal Attack — revision 3

The requested attack revision starts beside and above his own right shoulder, holds the coiled wind-up at
0.62–0.70 s, then slashes across to his left. The body leans back 15 degrees during anticipation and forward
22 degrees through the follow-through, with a 32-degree rightward coil and 55-degree leftward finish.
The pelvis and chest share the turn; the feathers sweep back to clear it. Both hands remain fitted to the shaft.
Impact remains 26/30 s and the complete action remains 35/30 s, preserving the runtime timing contract.

[Revision evidence](review/attack_revision_1/revision.json) includes the 60 Hz contact/deformation checks,
normal/quarter-speed playback for all tiers, indoor/outdoor native poses, live combat and focused actor regression.
Exported Attack surface error is under 0.05 mm. Geometry, materials, LODs, skin and all five other clips are
unchanged, verified in [export preservation](work/attack_revision_1/export_preservation.json).
The editable master and intermediate checkpoints carry the same revised action. The viewer now opens on Attack.

To reproduce this scoped revision from its retained baseline: run `revise_attack.py`, `check_attack_candidate.py`,
`publish_attack_blends.py`, then `publish_attack_clip.py`; install `export/mm8_m584.glb` with `tools/install_model.py`
and repeat the recorded browser/native checks before `finalize_attack_revision.py` with the two launch folders.
The full-production finish order above predates this revision. No additional Meshy credits were used.
Android and Vulkan were not rechecked; user artistic acceptance is not recorded.
'''
p.write_text(s)
print(json.dumps({'revision':revision,'complete':True,'body_sha256':sha(P/'export/mm8_m584.glb'),'native':native},indent=2))
