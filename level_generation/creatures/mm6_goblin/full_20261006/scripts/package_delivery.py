from pathlib import Path
import json,hashlib,zipfile,datetime,shutil
R=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin');O=R/'full_20261006';state_path=R/'stage1_20261006/creature_3d_progress.json';state=json.loads(state_path.read_text());now=datetime.datetime.now(datetime.timezone.utc).isoformat()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not json.loads((O/'review/full_dense_checks.json').read_text())['flags']
validation=json.loads((O/'delivery/asset_validation.json').read_text())
assert len(validation['assets'])==3 and all(a['sha256']==sha(O/a['path']) for a in validation['assets'])
checks=json.loads((O/'review/export_reimport_checks.json').read_text());assert len(checks['clips'])==7
assert len(json.loads((O/'review/source_comparisons/index.json').read_text()))==59
assert len(json.loads((O/'review/final_contacts/index.json').read_text()))==34
jobs=state['meshy']['jobs'];spent=sum(j.get('consumed_credits',0) for j in jobs.values());assert spent==20;assert all(j['status'] in ['SUCCEEDED','REJECTED','FAILED','CANCELED'] for j in jobs.values())
ledger=state['correction_ledger']
for i,e in enumerate(ledger):
 if i in [0,2]:e['status']='resolved_on_selected_delivery'
 if i==1:e['status']='three-finger repair verified; interim skirt seam repair superseded by closed strips'
 if i==5:e['status']='shortest quaternion/twist repairs verified; early walk grip superseded by forward blade and actual prop-tip fit'
 if i==7:e['status']='superseded by twelve closed leather strips'
 if i==10:e['status']='dense floor/rotation and actual export checks passed; endpoint matches Corpse'
new=[
 {'stage':3,'region':'Death early wrist roll','cause':'A constant downward blade-plane normal made the sword almost edge-on in early collapse anchors, contrary to the native broad blade face','repair':'Use the front-facing blade plane for early Death and rotate toward the floor-facing plane during contact','status':'native comparison, dense floor/rotation checks and actual export parity verified','evidence':'full_20261006/review/fixup_comparisons/death_palm_native_before_after.jpg'},
 {'stage':3,'region':'Hit left wrist release','cause':'Interpolating nearly opposite finger-direction vectors caused abrupt palm rotation and 1.156 mm export mismatch','repair':'Shortest full palm-orientation interpolation through observed anchors and Standing endpoint','status':'source poses preserved; current reimport error below 1 mm','evidence':'full_20261006/review/export_reimport_checks.json'},
 {'stage':3,'region':'final body UV charts','cause':'139 positive overlap pairs exposed 88 folded faces after initial unwrap/pack','repair':'Planar chart repair of affected faces; repack with 0.004 margin; preserve positions, weights and asymmetric details','status':'zero unintended overlaps and degenerate UV triangles','evidence':'full_20261006/delivery/uv_validation.json'},
 {'stage':3,'region':'texture review override','cause':'Inherited clay material override masked the newly applied PBR textures','repair':'Clear the preview/master material override and bind the four downloaded PNG maps to their verified UVs','status':'neutral multi-view PBR and actual export appearance reviewed','evidence':'full_20261006/review/final_materials_v2'},
 {'stage':3,'region':'skin leather teeth eyes material response','cause':'Generated metallic response and slot naming needed semantic exclusions','repair':'Set nonmetal anatomical/cloth roles to zero metallic; retain spatial metal/roughness and tangent normal maps for armor','status':'actual exported material factors verified','evidence':'full_20261006/delivery/asset_validation.json'},
 {'stage':3,'region':'blue/red pigment masks','cause':'Blender UV V orientation was incorrectly used for glTF/image-space mask rasterization, leaving coloured patches','repair':'Rasterize semantic charts in glTF image coordinates; retain pigment gating and reviewed padding','status':'consistent variant skin/leather; hardware colours intentionally shared','evidence':'full_20261006/review/fixup_comparisons/palette_native_before_after.jpg'},
 {'stage':3,'region':'clip start and duration','cause':'Exporter preserved master frame 1 as a 1/192-second offset, extending native durations','repair':'Slide export animation start to zero while retaining native fractional-collapse keys','status':'all native durations exact in all three actual consumer-loaded GLBs','evidence':'full_20261006/delivery/asset_validation.json'},
 {'stage':3,'region':'actual curved sword tip and death depth','cause':'Straight-axis assumption raised tip by 10–17 source pixels; a guessed death blade direction overstretched its front projection','repair':'Use actual 0.8940666 m curved-tip bind basis and native projected tip offsets; infer depth from fixed length, preserving physical death palm/foot contacts','status':'native tip fits verified; floor and motion export checks passed','evidence':'full_20261006/review/native_tip_fit_after.json'},
 {'stage':3,'region':'quarter-speed preview final hold','cause':'Basic setpts resampling omitted three repetitions of the last 48 fps image','repair':'Clone final preview image and trim to exactly four times native duration; exports unchanged','status':'ffprobe duration checks within 2 ms for normal and slow clips','evidence':'full_20261006/review/final_playback/playback_timing.json'}]
# Finalization is idempotent without erasing the historical repair entries.
for e in new:
 if not any(x.get('region')==e['region'] for x in ledger):ledger.append(e)
(O/'delivery/correction_ledger.json').write_text(json.dumps({'entries':ledger,'recorded_entries':len(ledger),'count_basis':'Distinct recorded repair/review entries, not number of renders or a quality threshold','historical_reference_correction_stages':2},indent=2)+'\n')
shutil.copy2('/tmp/openyamm_goblin_README.md',O/'README.md')
review={'technical_status':'verified','agent_visual_status':'all native anchors, sequential 48 fps decoded poses and neutral/extreme/reimported material views inspected','temporal_playback_status':'unverified: this session has still-image inspection but no video viewing tool','user_artistic_acceptance':'not_recorded','visual_sampling_fps':48,'numerical_and_export_sampling_fps':192,'preview_timing':'normal exact native; quarter speed exactly 4x','correction_entries':len(ledger),'primary_material_views':'review/final_materials_v2','actual_export_views':'review/export_materials','native_comparisons':'review/source_comparisons','decoded_contacts':'review/final_contacts','remaining_findings':[{'id':'temporal_review','status':'unverified','owner':'user or video-capable reviewer','action':'Review review/review_reel.mp4 at normal and quarter speed; record force, continuity and endpoint findings separately from artistic acceptance'}],'known_inferences':['Single-view action depth and hidden joints; no native Running clip','Fixed-length chains retain about 9–16 native-pixel residuals at some inferred Attack/Hit tips or wrists; prone wrist about 16 pixels. Current measurements: native_tip_fit_after.json','B/C pigment variants retain shared gold/iron and natural ear/nose variation; not literal complete native palette index conversions'],'selected_files_sha256':{str(p.relative_to(O)):sha(p) for p in [O/'delivery/mm6_goblin.blend',*[O/f'delivery/mm6_goblin_{n}.glb' for n in [745,746,747]]]}}
(O/'review/final_review.json').write_text(json.dumps(review,indent=2)+'\n')
state['current_stage']=3;state['current_substep']='actual_normal_and_slow_temporal_review_unverified';state['furthest_produced_artifact']='Packed textured master, three verified portable pigment variants, seven native clips and review package';state['earliest_unresolved_prerequisite']='Actual playback review at normal and slower speeds; sequential image review does not establish this gate'
st=state['stages']['3_animation_and_finish'];st['status']='in_progress_review';st['substeps'].update(frame_by_frame_review='complete_at_48_fps; dense_192_hz_screens_passed',texture_return_review='complete',portable_export_and_consumer_checks='complete',actual_normal_and_slow_playback_review='unverified',delivery_package='complete_for_review')
state['generation']['meshy_jobs_submitted']=3;state['generation']['meshy_jobs_submitted_basis']='successful paid jobs; separate zero-cost DNS rejection retained';state['full_production']['motion_revision'].update(path='full_20261006/delivery/mm6_goblin.blend',sha256=sha(O/'delivery/mm6_goblin.blend'),agent_review=review['agent_visual_status'],temporal_playback_status=review['temporal_playback_status']);state['full_production']['texture_return']={'maps':'meshy/body_texture_v1','transfer_report':'full_20261006/review/texture_transfer.json','status':'verified maps applied to retained animated master'};state['full_production']['delivery_review']='full_20261006/review/final_review.json';state['full_production']['spending']={'actual_credits':spent,'limit_credits':100,'pending_reserved_credits':0}
for c in state['required_components']:c.update(state='assembled_and_export_verified; temporal_review_unverified',selected_revision='full_20261006/delivery/mm6_goblin.blend')
state['correction_ledger']=ledger;state['next_action']={'owner':'user or video-capable reviewer','action':'Review full_20261006/review/review_reel.mp4 at normal/quarter speed; record timing/force/continuity findings. Codex can then resolve findings or update the review gate without another Meshy job.'};state['next_codex_action']='Ingest actual temporal-review findings and artistic decision; preserve selected files and budget receipts';state['last_update_utc']=now;state['updated_at']=now
state['checks']['full_production']={'technical_status':'verified','agent_visual_status':'sequential_and_detail_views_reviewed','actual_temporal_playback':'unverified','user_artistic_acceptance':'not_recorded','report':'../full_20261006/review/final_review.json'}
selected=[O/'README.md',O/'delivery/mm6_goblin.blend',*[O/f'delivery/mm6_goblin_{n}.glb' for n in [745,746,747]],O/'delivery/clip_manifest.json',O/'delivery/asset_validation.json',O/'review/final_review.json',O/'review/review_reel.mp4']
state['selected_artifacts']=[a for a in state['selected_artifacts'] if not a['path'].startswith('../full_20261006/')]+[{'path':'../full_20261006/'+str(p.relative_to(O)),'sha256':sha(p),'role':'selected_full_delivery_or_review'} for p in selected]
files=set(selected)
for p in (O/'delivery').rglob('*'):
 if p.is_file() and p.suffix in ['.glb','.blend','.json','.png'] and p.name!='delivery_manifest.json':files.add(p)
files.add(O/'motion_fit_revision.json')
for name in ['full_dense_checks.json','export_reimport_checks.json','texture_transfer.json','motion_only_refresh.json','native_tip_fit_before.json','native_tip_fit_after.json','cloth_surface_checks.json','review_reel.json']:
 files.add(O/'review'/name)
for folder in ['final_materials_v2','export_materials','final_contacts','source_comparisons','fixup_comparisons']:
 files.update(p for p in (O/'review'/folder).rglob('*') if p.is_file() and p.suffix in ['.png','.jpg','.json'])
for folder in ['final_playback','attack_wide']:
 files.update(p for p in (O/'review'/folder).glob('*') if p.is_file() and p.suffix in ['.mp4','.json'])
for name in ['ANATOMY_GUIDE.md','ANIMATION_STUDY.md','anatomy_targets.json','motion_spec.json','source_inventory.json','generation_runs.json']:
 files.add(R/'stage1_20261006'/name)
files.update((R/'stage1_20261006/submission').glob('*.png'));files.update(p for p in (R/'stage1_20261006/source').rglob('*') if p.is_file() and p.suffix in ['.png','.json','.tsv'])
files.update([O/'scripts/asset_check.py',O/'scripts/reimport_check.py',O/'scripts/openyamm_goblin_consumer_check.cpp'])
assert all(p.is_file() for p in files),[str(p) for p in files if not p.is_file()]
manifest={'date_utc':now,'identity':'mm6:gob','status':'assets_verified; actual_temporal_review_unverified','credit_limit':100,'consumed_credits':spent,'pending_jobs':0,'files':[{'path':str(p.relative_to(R)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)],'jobs':[{'name':n,'task_id':j.get('task_id'),'status':j['status'],'consumed_credits':j.get('consumed_credits',0)} for n,j in jobs.items()],'user_artistic_acceptance':'not_recorded'}
mp=O/'delivery/delivery_manifest.json';mp.write_text(json.dumps(manifest,indent=2)+'\n');files.add(mp)
archive=O/'mm6_goblin_full_review.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=4) as z:
 for p in sorted(files):z.write(p,'mm6_goblin/'+str(p.relative_to(R)))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None;assert len(z.namelist())==len(files)
state['package_history']=state.get('package_history',[])+[state['package']] if isinstance(state.get('package'),str) else state.get('package_history',[])
state['package']={'path':'../full_20261006/mm6_goblin_full_review.zip','sha256':sha(archive),'bytes':archive.stat().st_size,'status':'review_delivery; temporal_gate_unverified','path_base':'state_directory'}
state_path.write_text(json.dumps(state,indent=2)+'\n')
print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'files':len(files),'credits':spent,'repair_entries':len(ledger),'next_gate':'actual normal/slow temporal review'},indent=2))
