"""Seal the reviewed 95-frame Boulder package and its exact native metadata."""
import json,hashlib,datetime,copy
import numpy as np
from PIL import Image
from process import ROOT,queue,save
def read(p):return json.loads((ROOT/p).read_text())
def run():
 decision=read('review/decision.json');assert decision['status']=='accepted'
 m=read('draft_manifest.json');s=read('sources.json');reg=read('registration.json');g=read('generation.json');checks=read('review/export_checks.json');browser=read('review/browser_checks.json');edges=read('review/edge_audit.json')
 assert set(m['frames'])==set(s['sources'])==set(reg)==set(decision['reviewed_frames']) and len(reg)==95
 assert browser=={'status':'passed','atlas_variant_decodes':95,'tracks':192,'timing_boundary_samples':720,'stored_poses':95}
 assert all(checks[k] is True for k in ['full_coverage','exact_crop_reconstruction','exact_atlas_extraction','variant_alpha_unchanged','base_bypass_exact','zero_mask_unchanged'])
 for item in list(s['sources'].values())+list(s['palette_sources'].values())+s['source_tables']+[s['descriptor_table']]:assert queue.sha(queue.REPO/item['path'])==item['sha256'],item['path']
 for b in g['batches'].values():
  for item in [b['raw'],b['prompt'],*b['references']]:assert queue.sha(ROOT/item['path'])==item['sha256'],item['path']
 for n,f in m['frames'].items():
  assert f['logical_size']==s['sources'][n]['size']==[256,256] and reg[n]['raw_clip'] is False
  mask=Image.open(ROOT/f'masks_2x/{n}.png');assert mask.mode=='L' and not np.asarray(mask).any();base=Image.open(ROOT/f'aligned_2x/{n}.png');variant=Image.open(ROOT/f'previews/{n}_588.png');assert np.array_equal(base,variant)
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
     if step['frame']:assert step['palette']==588
 batches=read('batches.json')
 for key,b in batches.items():b['state']='validated';g['batches'][key]['status']='validated'
 save(ROOT/'batches.json',batches);save(ROOT/'generation.json',g)
 checks.update(visual_review_complete=True,animation_review_complete=True,variant_review_complete=True,edge_spill_review_complete=True,palette_and_native_table_hashes_unchanged=True,exact_native_timing_mirrors_scale_and_anchors=True,exact_native_glow_radius=True,generation_provenance_verified=True,full_native_file_coverage=True,browser=browser,review_record='review/acceptance.json');save(ROOT/'validation.json',checks)
 m.update(status='validated',review_record='review/acceptance.json',validation='validation.json',source_manifest='sources.json');save(ROOT/'manifest.json',m)
 p=ROOT/'viewer.html';p.write_text(p.read_text().replace('"status": "awaiting_visual_acceptance"','"status": "validated"').replace('href="draft_manifest.json"','href="manifest.json"'))
 files=['manifest.json','sources.json','registration.json','processing.json','tone_settings.json','effect_settings.json','generation.json','material_settings.json','validation.json','viewer.html','viewer_template.html','batches.json','review/decision.json','review/browser_checks.json','review/edge_audit.json','review/effect_calibration.json']
 files += [page[k] for page in m['pages'] for k in ['base','mask']]
 files += [str(p.relative_to(ROOT)) for pattern in ['*.py','prompts/*.txt','raw/*.png','checkpoints/*.json','checkpoints/*.png','review/*_final_edges.png','review/transition_*.png','review/viewer_*.png'] for p in ROOT.glob(pattern)]
 acceptance={'status':'accepted','reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'95 native Boulder frames including 53 unbound poses; one shared palette, all 3 native actors and 8 logical views.','review':decision,'artifact_hashes':{p:queue.sha(ROOT/p) for p in sorted(set(files))}};save(ROOT/'review/acceptance.json',acceptance)
 p=ROOT.parent/'mm8_remaining/progress.json';ledger=json.loads(p.read_text());ledger['families']['m588'].update(status='validated',processed_frames=95,completed_package='level_generation/creatures/mm8_m588/manifest.json',blockers=[],resume='Reuse validated staging package and accepted artifact hashes. No gameplay installation performed.',gates={k:True for k in ['full_coverage','visual','animation','variants','edge_spill','atlas']});ledger['updated_utc']=acceptance['reviewed_utc'];ledger['summary']={state:sum(f['status']==state for f in ledger['families'].values()) for state in ['pending','partial','validated','blocked']};p.write_text(json.dumps(ledger,indent=2)+'\n')
 print('m588 validated: 95 native frames, six RGBA8/R8 atlas pairs, all 192 tracks and 720 timing boundaries checked.')
if __name__=='__main__':run()
