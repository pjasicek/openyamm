"""Seal a fully reviewed m400 staging package. Never accepts visual art automatically."""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text())
def save(p,d):(ROOT/p).write_text(json.dumps(d,indent=2)+'\n')
decision=read('review/decision.json');assert decision['status']=='accepted'
m=read('draft_manifest.json');s=read('sources.json');r=read('registration.json');g=read('generation.json');checks=read('review/export_checks.json');browser=read('review/browser_checks.json');edges=read('review/edge_audit.json')
assert set(m['frames'])==set(s['sources'])==set(r)==set(decision['reviewed_frames'])
assert browser['status']=='passed' and browser['atlas_variant_decodes']==len(m['frames'])*3
assert browser['tracks']==192 and browser['timing_boundary_samples']==888 and browser['stored_poses']==170
assert all(checks[k] is True for k in ('full_coverage','exact_crop_reconstruction','exact_atlas_extraction','variant_alpha_unchanged','base_bypass_exact','zero_mask_unchanged'))
for item in list(s['sources'].values())+list(s['palette_sources'].values())+s['source_tables']+[s['descriptor_table']]:assert sha(REPO/item['path'])==item['sha256'],item['path']
for b in g['batches'].values():
 for item in [b['raw'],b['prompt'],*b['references']]:assert sha(ROOT/item['path'])==item['sha256'],item['path']
for n,f in m['frames'].items():
 assert f['logical_size']==s['sources'][n]['size'] and r[n]['raw_clip'] is False
 mask=np.asarray(Image.open(ROOT/f'masks_2x/{n}.png')).astype(int);assert np.all(mask[:,:,:2].sum(axis=2)<=255) and np.all(mask[:,:,2]==0)
 assert all(v['candidates_above_12']==0 for v in edges[n].values())
# Bindings retain exact ordered native records; unreferenced poses acquire no durations.
assert m['animations']==s['bindings']
for d in m['animations'].values():
 for action in d['actions'].values():
  native=action['native_group_record']['frames']
  for view,steps in action['views'].items():
   assert len(steps)==len(native)
   for step,original in zip(steps,native):
    assert step['duration_raw']==original['frame_length_raw']
    assert step['duration_ticks']==original['frame_length_raw']*8
    assert step['duration_ms']==original['frame_length_raw']*62.5
    assert step['palette']==original.get('palette_id',0)
    assert step['scale']==original.get('scale',1)
    assert step['mirrored']==('Mirror'+view in original.get('flags',[]))
    assert step['anchor']==('center' if 'Center' in original.get('flags',[]) else 'bottom-center')
checks.update(visual_review_complete=True,animation_review_complete=True,variant_review_complete=True,edge_spill_review_complete=True,
              palette_and_native_table_hashes_unchanged=True,exact_native_timing_mirrors_scale_and_anchors=True,
              generation_provenance_verified=True,full_native_file_coverage=True,review_record='review/acceptance.json',browser=browser)
save('validation.json',checks)
m.update(status='validated',review_record='review/acceptance.json',validation='validation.json',viewer='viewer.html',source_manifest='sources.json')
save('manifest.json',m)
# Status-only change retains the exact reviewed viewer renderer and encoded placement data.
p=ROOT/'viewer.html';html=p.read_text().replace('"status": "awaiting_visual_acceptance"','"status": "validated"').replace('href="draft_manifest.json"','href="manifest.json"');p.write_text(html)
files=['manifest.json','sources.json','registration.json','processing.json','generation.json','material_settings.json','validation.json','viewer.html','review/decision.json','review/browser_checks.json','review/edge_audit.json','review/final_edge_cleanup.json']
files += [page[key] for page in m['pages'] for key in ('base','mask')]
files += [str(p.relative_to(ROOT)) for pattern in ('prompts/*.txt','raw/*.png','checkpoints/*.png','review/*_final_variants.png','review/final_edges_*.png') for p in ROOT.glob(pattern)]
acceptance=dict(status='accepted',reviewed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='All 170 native files, three palette variants, all descriptor actions and eight logical views.',review=decision,artifact_hashes={p:sha(ROOT/p) for p in files})
save('review/acceptance.json',acceptance)
p=ROOT.parent/'mm8_remaining/progress.json';ledger=json.loads(p.read_text());family=ledger['families']['m400'];family.update(status='validated',processed_frames=170,completed_package='level_generation/creatures/mm8_m400/manifest.json',blockers=[],resume='Validated staging package; reuse the manifest and accepted artifact hashes. No gameplay installation performed.',gates={k:True for k in ('full_coverage','visual','animation','variants','edge_spill','atlas')})
ledger['updated_utc']=acceptance['reviewed_utc'];ledger['summary']={state:sum(f['status']==state for f in ledger['families'].values()) for state in ('pending','partial','validated','blocked')};p.write_text(json.dumps(ledger,indent=2)+'\n')
print('m400 validated: 170 native frames, 510 variants, 6 atlas/mask pairs, 192 animation tracks')
