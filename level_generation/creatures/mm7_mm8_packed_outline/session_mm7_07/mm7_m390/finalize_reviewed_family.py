import importlib.util,sys,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
p=Path(__file__).with_name('session_pipeline.py');s=importlib.util.spec_from_file_location('session',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
viewer=m.CREATURES/'mm6_remaining/acceptance_viewer/serve.py';sys.path.insert(0,str(viewer.parent));s=importlib.util.spec_from_file_location('session_reviewer',viewer);v=importlib.util.module_from_spec(s);sys.modules[s.name]=v;s.loader.exec_module(v)
mode=sys.argv[1];collection_path=m.STAGE/'mm7_m390/review_collection.json';collection=m.read(collection_path)
for stem in sys.argv[2:]:
 assert stem!='m410';root=m.STAGE/('mm7_'+stem);out=root/'redo_2x';a=m.read(out/'review/acceptance.json');review=m.read(out/'review/all_pose_review.json');placement=m.read(out/'review/complete_placement.json');manifest=m.read(out/'manifest.json');validation=m.read(out/'validation.json');sources=m.read(root/'sources.json');run=m.read(out/'run.json')
 assert review['status'] in ['static_visual_review_complete','accepted_after_static_visual_review'];assert placement['status']=='independent_anatomical_review_passed';assert all(f['status']=='resolved' for f in a['findings']);assert not any(j.get('status')=='blocked_tool_return' or not j.get('selected_raw') for j in run['jobs'])
 assert set(manifest['frames'])==set(sources['sources']);assert validation['source_hashes_unchanged'] and validation['exact_atlas_extraction'] and validation['base_bypass_exact'] and validation['variant_alpha_unchanged'] and validation['mask_weights_valid'] and validation['raw_cells_unclipped']
 for src in list(sources['sources'].values())+list(sources['palette_sources'].values()):assert m.sha(m.REPO/src['path'])==src['sha256']
 returns=0
 for j in run['jobs']:
  for attempt in j['attempts']:
   assert m.sha(m.REPO/attempt['raw'])==attempt['sha256'];assert m.sha(m.REPO/attempt['prompt'])==attempt['prompt_sha256'];assert (m.REPO/attempt['prompt']).read_text().startswith(m.HEADER)
   for ref in attempt['references']:assert m.sha(m.REPO/ref['path'])==ref['sha256']
   returns+=1
 for page in review['palette_pages']+review['detail_pages']:assert page['status']=='visual_review_passed' and m.sha(out/page['path'])==page['sha256']
 record=next(r for r in collection['families'] if (collection_path.parent/r['manifest']).resolve()==out/'manifest.json')
 if mode=='mark':
  manifest.update(quality_status='accepted_after_static_visual_review',review_label=m.read(root/'config.json')['title']+' — packed session 07 accepted');manifest['coverage']['accepted']=True
  manifest['limitations']=['Native chronological pose, independent anatomy/placement, all palettes/masks and 100% detail/alpha contacts inspected. Timed playback was not watched.','Whole-cycle sampling is measured on returned pixels; physical 2x export does not add generated detail.']
  if manifest['generated_detail']['measured_minimum']<2:manifest['limitations'].append(f"Reviewed complete sheets have minimum actual generated sampling {manifest['generated_detail']['measured_minimum']:.6f}x.")
  validation['visual_acceptance']=True;m.save(out/'manifest.json',manifest);m.save(out/'validation.json',validation)
  review.update(status='accepted_after_static_visual_review',accepted=True);m.save(out/'review/all_pose_review.json',review)
  record.update(label=manifest['review_label'],pipeline_status='accepted_after_static_visual_review')
 elif mode=='freeze':
  browser=m.read(out/'review/browser_validation.json');assert browser['rendering_validation_passed'] and browser['manifest_sha256']==m.sha(out/'manifest.json')
  a.update(status='accepted_after_static_visual_review',accepted=True,reviewer='Codex — native chronology, independent features, material/alpha and all native palette contacts',reviewed_utc=datetime.now(timezone.utc).isoformat(),coverage=manifest['coverage'],generated_detail=manifest['generated_detail'],limitations=manifest['limitations'],blocked_jobs=[],installed=False,browser_validation=browser)
  a['source_integrity'].update(verified_utc=a['reviewed_utc'],returned_raw_sha256_verified=returns,complete_submitted_preparations_verified=returns,all_recorded_source_hashes_unchanged=True)
  a['manifest_sha256']=m.sha(out/'manifest.json');a['review_artifact_sha256']=v.artifact_digest(out,(out/'manifest.json').read_bytes(),manifest)
  paths=set(a.get('artifact_hashes',{}));paths.update(page['path'] for page in review['palette_pages']+review['detail_pages']);paths.update(placement['pages']);paths.update(['review/all_pose_review.json','review/complete_placement.json'])
  a['artifact_hashes']={str(p):m.sha(out/p) for p in sorted(paths) if (out/p).is_file()}
  d=hashlib.sha256()
  for name in sorted(manifest['frames']):d.update(name.encode());d.update((out/'masks_2x'/f'{name}.png').read_bytes())
  a['aligned_material_masks_sha256']=d.hexdigest();a['acceptance_hashes_frozen_utc']=a['reviewed_utc'];m.save(out/'review/acceptance.json',a);record['accepted']=True
 else:raise ValueError(mode)
 record['manifest_sha256']=m.sha(out/'manifest.json');record['artifact_sha256']=v.artifact_digest(out,(out/'manifest.json').read_bytes(),manifest)
 print(stem,mode,'passed',len(manifest['frames']),'native frames',returns,'returned complete sheets')
collection['coverage_summary']['accepted_families']=sum(r['accepted'] for r in collection['families']);collection['title']='MM7 session 07 — '+str(collection['coverage_summary']['accepted_families'])+' accepted families; repairs in progress';m.save(collection_path,collection)
