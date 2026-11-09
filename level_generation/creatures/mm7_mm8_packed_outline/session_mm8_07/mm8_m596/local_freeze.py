"""Compact artifact-bound local MM8 acceptance bridge; no runtime installation or global ledger writes."""
from pathlib import Path
import json,hashlib,sys
from datetime import datetime,timezone
import session_workflow as w
from PIL import Image
import numpy as np
REPO=w.REPO
STAGE=Path(__file__).resolve().parent.parent

def freeze(stem):
 root=STAGE/f'mm8_{stem}';out=root/'redo_2x';review=out/'review';sign=w.read(review/'visual_signoff.json');run=w.read(out/'run.json');records=w.read(out/'registration.json');manifest=w.read(out/'draft_manifest.json');source=w.read(root/'sources.json');checks=w.read(review/'export_checks.json')
 assert sign['all_selected_pose_instances_reviewed'] and sign['all_palette_mask_poses_reviewed'] and sign['independent_features_reviewed'] and sign['representative_100_percent_detail_and_alpha_reviewed'] and sign['final_atlas_edge_contact_reviewed']
 assert set(sign['reviewed_jobs'])=={j['id'] for j in run['jobs'] if j.get('selected_raw')}
 assert not [n for n,v in records.items() if v['raw_clip']]
 assert checks['exact_atlas_extraction'] and checks['exact_crop_reconstruction'] and checks['exact_native_animation_bindings'] and checks['exact_fractional_anchor_mapping'] and checks['exact_mirrored_anchor_mapping']
 assert manifest['animations']==source['bindings']
 inventory=w.read(w.CREATURES/'remaining_inventory.json')['families'];row=next(r for r in inventory if r['world']=='mm8' and r['label']==source['label']);tables=w.validate_native(source,row);assert tables==run['current_native_tables']
 attempts=[]
 for job in run['jobs']:
  for ai,a in enumerate(job['attempts']):
   if a.get('status')=='interrupted_before_imagegen_call':continue
   refs=a['referenced_image_paths'];inputs=a['submitted_inputs'];assert refs==[v['path'] for v in inputs]
   assert len(refs) in (2,3) and refs[0].endswith(job['id']+'_native.png') and refs[1].endswith(job['id']+'_outline.png')
   assert inputs[0]['role']=='untouched_native_complete_animation' and inputs[1]['role']=='outline_only_geometry_no_shading'
   assert len(refs)==3 or a.get('bootstrap_exception')
   for i in inputs:assert w.sha(Path(i['path']))==i['sha256']
   prompt=Path(a['prompt_path']);assert w.sha(prompt)==a['prompt_sha256'] and prompt.read_text().startswith(w.HEADER)
   selected=a.get('raw')==job.get('selected_raw') and job.get('selected_raw') is not None
   attempts.append(dict(job=job['id'],attempt=ai+1,selected=selected,status=a['status'],submitted_inputs=inputs,prompt_path=str(prompt.relative_to(REPO)),prompt_sha256=a['prompt_sha256'],bootstrap_exception=a.get('bootstrap_exception'),raw=a.get('raw'),raw_sha256=a.get('raw_sha256',a.get('sha256'))))
  if job.get('selected_raw'):
   assert any(a['selected'] for a in attempts if a['job']==job['id'])
   for a in [a for a in attempts if a['job']==job['id'] and a['selected']]:assert w.sha(REPO/a['raw'])==a['raw_sha256']
 missing=manifest['missing_frames'];full=not missing;status='complete_local_acceptance' if full else 'partial_generation_blocked_local_acceptance'
 for v in records.values():v['review_status']='accepted_static_native_anatomy_and_independent_placement'
 w.save(out/'registration.json',records)
 for n in ('material_checks.json','expanded_contact_checks.json','final_edge_checks.json'):
  d=w.read(review/n);d['status']='accepted_static_visual_review';d['review_notes']=sign.get('notes');w.save(review/n,d)
 checks.update(visual_review_complete=True,animation_review_complete=True,timed_playback_viewed=False,all_selected_pose_instances_reviewed=True,all_native_palette_mask_poses_reviewed=True,independent_placement_features_reviewed=True,actual_outline_attachment_validated=True,final_atlas_edge_review_complete=True)
 w.save(review/'export_checks.json',checks)
 manifest.update(status=status,acceptance_record='review/acceptance.json',review_method='Every selected pose inspected statically in native order, independent placement features and complete palette/mask contacts, representative unresized detail and alpha, final cleaned/atlas residual audit.',installed=False)
 w.save(out/'manifest.json',manifest);run['status']=status;w.save(out/'run.json',run)
 files=[root/'sources.json',root/'config.json',out/'manifest.json',out/'run.json',out/'processing.json',out/'registration.json',out/'material_settings.json',out/'calibration.json',review/'visual_signoff.json',review/'export_checks.json',review/'material_checks.json',review/'material_strips.json',review/'expanded_contact_checks.json',review/'detail_alpha_100pct.json',review/'detail_alpha_100pct.png',review/'final_edge_checks.json',review/'final_atlas_edge_100pct.png']
 files.extend(out/p[k] for p in manifest['pages'] for k in ('base','mask'))
 for f in ('aligned_2x','masks_2x','native_palettes','unrestored_native_art'):
  files.extend(p for p in (out/f).glob('*') if p.is_file())
 for j in run['jobs']:
  if j.get('selected_raw'):
   files.append(REPO/j['selected_raw']);files.append(review/(j['id']+'_extraction.json'));files.append(review/(j['id']+'_registered.png'))
   ep=review/(j['id']+'_expanded_registered.png')
   if ep.exists():files.append(ep)
 for v in records.values():files.append(REPO/v['clean_path'])
 for n in ('material_checks.json','material_strips.json'):
  for page in w.read(review/n)['pages']:
   pp=Path(page['path']);files.append((REPO if n=='material_checks.json' else out)/pp)
 hashes={str(p.relative_to(REPO)):w.sha(p) for p in sorted(set(files))}
 acceptance=dict(status=status,updated_utc=datetime.now(timezone.utc).isoformat(),local_final_acceptance=full,selected_generated_subset_accepted=True,scope_complete=full,label=source['label'],native_source_frames=len(source['sources']),enhanced_frames=len(records),missing_frames=missing,all_playback_art_restored=manifest['all_playback_art_restored'],review=sign,reviewed_frame_names=sorted(records),actual_generated_sampling=manifest['actual_generated_sampling'],submitted_attempts=attempts,artifact_sha256=hashes,checks=checks,installed=False)
 w.save(review/'acceptance.json',acceptance)
 text=f"# {source['label']} — packed outline restoration\n\nStatus: **{status}**. Enhanced {len(records)} of {len(source['sources'])} native frame names; missing {len(missing)}. All native playback art restored: {manifest['all_playback_art_restored']}. No gameplay installation.\n\nThe local package is [manifest](redo_2x/manifest.json) and its frozen [acceptance record](redo_2x/review/acceptance.json). Actual minimum generated sampling: {manifest['actual_generated_sampling']['minimum']:.4f}×; checked physical masters are 2×. Whole animations were retained for reviewed lower-sampling sheets.\n\n{sign['notes']}\n"
 (root/'README.md').write_text(text)
 print(stem,status,len(records),'frames;',len(hashes),'frozen artifact hashes')
if __name__=='__main__':
 for stem in sys.argv[1:]:freeze(stem)
