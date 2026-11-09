"""Seal the reviewed 135-file Dragon Turtle package and its exact native metadata."""
import json,hashlib,datetime,copy
import numpy as np
from PIL import Image
from process import ROOT,queue,save
from materials import recolor
def read(p):return json.loads((ROOT/p).read_text())
def run():
 decision=read('review/decision.json');assert decision['status']=='accepted'
 m=read('draft_manifest.json');s=read('sources.json');reg=read('registration.json');g=read('generation.json');checks=read('review/export_checks.json');browser=read('review/browser_checks.json');edges=read('review/edge_audit.json')
 assert set(m['frames'])==set(s['sources'])==set(decision['reviewed_frames']) and len(m['frames'])==135
 assert set(reg)==set(s['sources'])-set(s['pixel_aliases']) and len(reg)==120
 assert set(decision['reviewed_batches'])==set(read('batches.json'))
 assert all(browser[k]==v for k,v in {'status':'passed','atlas_variant_decodes':405,'tracks':192,'timing_boundary_samples':1056,'stored_poses':135,'max_premultiplied_rgb_error':0,'max_opaque_rgb_error':0}.items())
 assert all(checks[k] is True for k in ['full_coverage','exact_crop_reconstruction','exact_atlas_extraction','variant_alpha_unchanged','base_bypass_exact','zero_mask_unchanged'])
 for item in list(s['sources'].values())+list(s['palette_sources'].values())+s['source_tables']+[s['descriptor_table']]:assert queue.sha(queue.REPO/item['path'])==item['sha256'],item['path']
 for b in g['batches'].values():
  for item in [b['raw'],b['prompt'],*b['references']]:assert queue.sha(ROOT/item['path'])==item['sha256'],item['path']
 for n,f in m['frames'].items():
  assert f['logical_size']==s['sources'][n]['size']==[256,256] and reg[f['canonical_frame']]['raw_clip'] is False
  mask=Image.open(ROOT/f'runtime_masks_2x/{n}.png');assert mask.mode=='RGB';w=np.asarray(mask);assert w.astype(int).sum(axis=2).max()<=255
  base=Image.open(ROOT/f'runtime_aligned_2x/{n}.png');a=np.asarray(base)
  for pal in [581,582,583]:
   variant=Image.open(ROOT/f'previews/{n}_{pal}.png');assert np.array_equal(recolor(base,w,pal,m['variants']),variant)
   assert np.array_equal(np.asarray(variant)[:,:,3],a[:,:,3])
  canonical=f['canonical_frame'];assert queue.sha(ROOT/f'runtime_aligned_2x/{canonical}.png')==queue.sha(ROOT/f'runtime_aligned_2x/{n}.png')
  assert f['atlas_xywh']==m['frames'][canonical]['atlas_xywh'] and f['page']==m['frames'][canonical]['page']
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
     if step['frame']:assert step['palette'] in [581,582,583]
 batches=read('batches.json')
 for key,b in batches.items():b['state']='validated';g['batches'][key]['status']='validated'
 save(ROOT/'batches.json',batches);save(ROOT/'generation.json',g)
 checks.update(visual_review_complete=True,animation_review_complete=True,variant_review_complete=True,edge_spill_review_complete=True,palette_and_native_table_hashes_unchanged=True,exact_native_timing_mirrors_scale_and_anchors=True,exact_native_glow_radius=True,generation_provenance_verified=True,full_native_file_coverage=True,browser=browser,review_record='review/acceptance.json');save(ROOT/'validation.json',checks)
 m.update(status='validated',review_record='review/acceptance.json',validation='validation.json',source_manifest='sources.json');save(ROOT/'manifest.json',m)
 p=ROOT/'viewer.html';p.write_text(p.read_text().replace('"status": "awaiting_visual_acceptance"','"status": "validated"').replace('href="draft_manifest.json"','href="manifest.json"'))
 files=['manifest.json','sources.json','registration.json','processing.json','tone_settings.json','lighting_settings.json','generation.json','material_settings.json','validation.json','viewer.html','viewer_template.html','batches.json','review/decision.json','review/browser_checks.json','review/edge_audit.json']
 files += [page[k] for page in m['pages'] for k in ['base','mask']]
 files += [str(p.relative_to(ROOT)) for pattern in ['*.py','prompts/*.txt','raw/*.png','checkpoints/*.json','checkpoints/*.png','review/*_final_edges.png','review/transition_*.png','review/viewer_*.png','review/variants/*.png','review/lighting/*.png','viewer_rgb/*.png','final_2x/*.png','runtime_aligned_2x/*.png','runtime_masks_2x/*.png','README.md'] for p in ROOT.glob(pattern)]
 acceptance={'status':'accepted','reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'135 native Dragon Turtle files, 120 unique poses and 15 exact aliases; 3 native palettes and actors, all 8 logical views.','review':decision,'artifact_hashes':{p:queue.sha(ROOT/p) for p in sorted(set(files))}};save(ROOT/'review/acceptance.json',acceptance)
 p=ROOT.parent/'mm8_remaining/progress.json';ledger=json.loads(p.read_text());ledger['families']['m580'].update(status='validated',processed_frames=120,completed_package='level_generation/creatures/mm8_m580/manifest.json',blockers=[],resume='Reuse validated staging package and accepted artifact hashes. No gameplay installation performed.',gates={k:True for k in ['full_coverage','visual','animation','variants','edge_spill','atlas']});ledger['updated_utc']=acceptance['reviewed_utc'];ledger['summary']={state:sum(f['status']==state for f in ledger['families'].values()) for state in ['pending','partial','validated','blocked']};p.write_text(json.dumps(ledger,indent=2)+'\n')
 print('m580 validated: 135 native files / 120 unique poses, five RGBA8/RGB8 atlas pairs; 192 tracks, 1056 boundaries and 405 exact browser variants checked.')
if __name__=='__main__':run()
