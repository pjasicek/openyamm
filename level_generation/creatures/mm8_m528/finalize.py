"""Seal the reviewed 56-frame Wisp package and its exact native metadata."""
import json,hashlib,datetime,copy
import numpy as np
from PIL import Image
from process import ROOT,queue,save
def read(p):return json.loads((ROOT/p).read_text())
def run():
 decision=read('review/decision.json');assert decision['status']=='accepted'
 m=read('draft_manifest.json');s=read('sources.json');reg=read('registration.json');g=read('generation.json');checks=read('review/export_checks.json');browser=read('review/browser_checks.json');edges=read('review/edge_audit.json')
 assert set(m['frames'])==set(s['sources'])==set(reg)==set(decision['reviewed_frames']) and len(reg)==56
 assert browser=={'status':'passed','atlas_variant_decodes':56,'tracks':192,'timing_boundary_samples':1584,'stored_poses':56}
 assert all(checks[k] is True for k in ['full_coverage','exact_crop_reconstruction','exact_atlas_extraction','variant_alpha_unchanged','base_bypass_exact','zero_mask_unchanged'])
 for item in list(s['sources'].values())+list(s['palette_sources'].values())+s['source_tables']+[s['descriptor_table']]:assert queue.sha(queue.REPO/item['path'])==item['sha256'],item['path']
 for b in g['batches'].values():
  for item in [b['raw'],b['prompt'],*b['references']]:assert queue.sha(ROOT/item['path'])==item['sha256'],item['path']
 for n,f in m['frames'].items():
  assert f['logical_size']==s['sources'][n]['size']==[128,128] and reg[n]['raw_clip'] is False
  mask=Image.open(ROOT/f'masks_2x/{n}.png');assert mask.mode=='L' and not np.asarray(mask).any();base=Image.open(ROOT/f'aligned_2x/{n}.png');variant=Image.open(ROOT/f'previews/{n}_528.png');assert np.array_equal(base,variant)
  assert all(e['candidates_above_12']==0 for e in edges[n].values()),n
  bb=f['crop_in_aligned_px'];tile=Image.open(ROOT/f'trimmed_2x/{n}.png');out=Image.new('RGBA',base.size);out.paste(tile,bb[:2]);assert np.array_equal(base,out)
 for id,d in m['animations'].items():
  assert d['native_descriptor']==s['bindings'][id]['native_descriptor']
  for action,a in d['actions'].items():
   original=s['bindings'][id]['actions'][action];assert a['native_group_record']==original['native_group_record'] and a['playback']==original['playback']
   for view,steps in a['views'].items():
    assert len(steps)==len(original['views'][view])
    for step,source,native in zip(steps,original['views'][view],a['native_group_record']['frames']):
     stripped=dict(step);glow=stripped.pop('glow_radius');assert stripped==source and glow==native.get('glow_radius',0)
     assert step['duration_ms']==native['frame_length_raw']*62.5 and step['duration_ticks']==native['frame_length_raw']*8
     assert step['scale']==native.get('scale',1) and step['palette']==native.get('palette_id',0)
     assert step['anchor']==('center' if 'Center' in native['flags'] else 'bottom-center')
     assert step['mirrored']==('Mirror'+view in native['flags'])
     if step['frame']:assert step['palette']==528 and 'Image1' in step['flags']
 attempts=read('checkpoints/generation_attempts.json');attempts['attempts'][-1].update(status='accepted_identity',reason='Pale filament refinement accepted with deterministic contour repair and native core calibration; see identity_acceptance and final decision.')
 attempts['rejected_action_attempts']=[{'raw':'raw/native_a_v0_1_v1.png','prompt':'prompts/native_a_v0_1_v2.txt','references':['references/native_a_v0_1_matte.png','checkpoints/accepted_identity_v1.png'],'reason':'Native first five bright attack flash cores were replaced with a quiet dark core, and blue-violet sparks were omitted. Superseded by native_a_v0_1_v2.png with action-specific v3 prompt.'}];save(ROOT/'checkpoints/generation_attempts.json',attempts)
 batches=read('batches.json')
 for key,b in batches.items():b['state']='validated';g['batches'][key]['status']='validated'
 save(ROOT/'batches.json',batches);save(ROOT/'generation.json',g)
 checks.update(visual_review_complete=True,animation_review_complete=True,variant_review_complete=True,edge_spill_review_complete=True,palette_and_native_table_hashes_unchanged=True,exact_native_timing_mirrors_scale_and_anchors=True,exact_native_glow_radius=True,generation_provenance_verified=True,full_native_file_coverage=True,browser=browser,review_record='review/acceptance.json');save(ROOT/'validation.json',checks)
 m.update(status='validated',review_record='review/acceptance.json',validation='validation.json',source_manifest='sources.json');save(ROOT/'manifest.json',m)
 p=ROOT/'viewer.html';p.write_text(p.read_text().replace('"status": "awaiting_visual_acceptance"','"status": "validated"').replace('href="draft_manifest.json"','href="manifest.json"'))
 files=['manifest.json','sources.json','registration.json','processing.json','alignment_settings.json','generation.json','material_settings.json','validation.json','viewer.html','viewer_template.html','batches.json','review/decision.json','review/browser_checks.json','review/edge_audit.json','review/final_edge_cleanup.json','review/core_registration_audit.json']
 files += [page[k] for page in m['pages'] for k in ['base','mask']]
 files += [str(p.relative_to(ROOT)) for pattern in ['*.py','prompts/*.txt','raw/*.png','checkpoints/*.json','checkpoints/*.png','review/*_final_edges.png','review/transition_*.png','review/viewer_*.png'] for p in ROOT.glob(pattern)]
 acceptance={'status':'accepted','reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'56 native Wisp frames including 23 unbound poses; one shared palette, all 3 native actors and 8 logical views.','review':decision,'artifact_hashes':{p:queue.sha(ROOT/p) for p in sorted(set(files))}};save(ROOT/'review/acceptance.json',acceptance)
 p=ROOT.parent/'mm8_remaining/progress.json';ledger=json.loads(p.read_text());ledger['families']['m528'].update(status='validated',processed_frames=56,completed_package='level_generation/creatures/mm8_m528/manifest.json',blockers=[],resume='Reuse validated staging package and accepted artifact hashes. No gameplay installation performed.',gates={k:True for k in ['full_coverage','visual','animation','variants','edge_spill','atlas']});ledger['updated_utc']=acceptance['reviewed_utc'];ledger['summary']={state:sum(f['status']==state for f in ledger['families'].values()) for state in ['pending','partial','validated','blocked']};p.write_text(json.dumps(ledger,indent=2)+'\n')
 print('m528 validated: 56 native frames, one RGBA8/R8 atlas pair, all 192 tracks and 1584 timing boundaries checked.')
if __name__=='__main__':run()
