"""Seal the selected artifacts and verification receipts in the canonical progress record."""
import datetime,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
state=P/'creature_3d_progress.json';d=json.loads(state.read_text())
runtime=P/'export/mm6_fmp.glb';installed=Path('assets_dev/worlds/mm6/models/mm6_fmp.glb');assert runtime.read_bytes()==installed.read_bytes()
info=json.loads((P/'export/export_info.json').read_text());audit=json.loads((P/'work/runtime_asset_audit.json').read_text());assert audit['triangles'][0]==info['triangles']==9896
viewer=json.loads((P/'review/viewer_check.json').read_text());assert viewer['switched']==21 and not viewer['failed'] and not viewer['consoleErrors']
play=json.loads((P/'review/final_playback.json').read_text());manifest=json.loads((P/'review/viewer/manifest.json').read_text());assert play['revision']==manifest['revision']=='fmp_v2'
assert {(x['clip'],x['speed']) for x in play['rows']}=={(clip,speed) for clip in info['clips'] for speed in [1,.25]}
for model in manifest['models']:
 digest=hashlib.sha256((P/'review/viewer'/model['url'].split('?')[0]).read_bytes()).hexdigest();assert digest==model['sha256']==next(x['sha256'] for x in play['models'] if x['id']==model['id'])
assert json.loads((P/'review/loop_playback.json').read_text())['pass']
assert '[PASS] mm6_fmp_actor_model_fleeing_peasant_tiers' in (P/'review/game/peasant_regression.log').read_text()
outputs={}
paths=['export/mm6_fmp.blend','export/mm6_fmp_lod0.glb','export/mm6_fmp.glb','export/export_info.json','textures/fmp_ramps.json','review/viewer/manifest.json','review/selected_variants.jpg','README.md']
paths += [str(p.relative_to(P)) for p in (P/'textures').glob('*.png')]
for relative in paths:
 p=P/relative;outputs[relative]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
d.update(stage=3,substep='complete',technical_complete=True,updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),user_artistic_acceptance='not_recorded')
d['stage2']['status']='complete';d['stage2']['selected_motion_review']=['review/final_playback.json','review/playback/'];d['stage2']['deformation_review']='work/final_deformation_gate.json'
d['stage3']={'status':'complete','clips':info['clips'],'triangles':audit['triangles'],'rig_bones':90,'max_influences':8,'scale':info['scale'],'stride_m':info['walk_stride_m'],'runtime':str(installed),'runtime_sha256':outputs['export/mm6_fmp.glb']['sha256'],'bindings':'assets_dev/worlds/mm6/models/actors.yml','viewer':'http://192.168.1.130:8912/level_generation/creatures/mm6_fmp_codex/review/viewer/','export_parity':'work/export_parity.json','deformation':'work/final_deformation_gate.json','viewer_check':'review/viewer_check.json','playback':'review/final_playback.json','loops':'review/loop_playback.json','native_capture_count':64,'native_comparisons':['review/game/outdoor_comparison.jpg','review/game/indoor_comparison.jpg'],'peasant_regression':'pass','mm6_actor_suite':{'passed':47,'failed':4,'unrelated_failures':['Mage material layout','Guard material layout','Ooze material layout','Male Cannibal missing model binding']}}
d['outputs']=outputs;d['next_action']={'owner':'user','action':'Review the delivered PeasantF2 appearance and animations; technical production and installation are complete.'}
d['correction_ledger']=[{'region':'rig','correction':'Fitted source-frame joints and local garment/sleeve weights; ordinary hands remain rigid without fingers or grip.'},{'region':'geometry','correction':'Repaired sleeve roots, trimmed hidden legs, preserved head/hand silhouettes while reducing to 9896 triangles; removed the exact coincident two-triangle finger fold.'},{'region':'death','correction':'Replaced unstable covered-leg/skirt roll reversals with stable fall poses, solved cloth and shoes against the floor, rebuilt Dead and verified 120 Hz subframes.'},{'region':'textures','correction':'Rejected head v1, selected re-unwrapped head v2; matched neck overlap, softened head normals and corrected native region ramps to preserve fabric contrast.'},{'region':'export','correction':'Removed the obsolete UV layer; final runtime carries UV0, preserved clips, shared region maps and three LODs.'},{'region':'viewer','correction':'Disabled unnecessary frustum culling for this single animated model so switching from corpse to head close-up cannot retain stale bounds.'}]
d['limitations']=['Small generated texture irregularities visible at extreme face close-up.','User artistic acceptance not yet recorded.','Android and Vulkan not tested.','Four unrelated MM6 actor-family regressions remain.']
d['meshy_credits_consumed']=sum(j.get('consumed_credits',0) for j in d['meshy']['jobs'].values());assert d['meshy_credits_consumed']==40
state.write_text(json.dumps(d,indent=2)+'\n');print('Technical delivery complete:',info['triangles'],'triangles,',len(info['clips']),'clips,',d['meshy_credits_consumed'],'Meshy credits.')
