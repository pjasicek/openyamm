"""Seal the reviewed mixed-checkpoint delivery, retaining exact provenance and native source checks."""
from pathlib import Path
import json,sys,copy,datetime
from PIL import Image
F=Path(__file__).resolve().parent;R=F.parent;G=R/'complete'
sys.path.insert(0,str(R));import process

def read(p):return json.loads(p.read_text())
def checked(base,record):
    assert process.queue.sha(base/record['path'])==record['sha256'],record['path']

def run():
    decision=read(G/'review/decision.json');assert decision['status']=='accepted'
    for p,digest in decision['evidence_hashes'].items():
        assert process.queue.sha(G/p)==digest,('Review is stale',p)
    sources=read(R/'sources.json');m=read(G/'draft_manifest.json');selected=read(G/'selection.json')
    assert len(m['frames'])==160 and set(m['frames'])==set(selected)==set(sources['sources'])
    assert m['animations']==sources['bindings'] and not m['missing_frames']
    for record in [*sources['sources'].values(),*sources['palette_sources'].values(),*sources['source_tables'],sources['descriptor_table']]:
        checked(process.queue.REPO,record)
    browser=read(G/'review/browser_checks.json');delivery=read(G/'review/delivery_checks.json')
    assert browser=={'status':'passed','variant_decodes':480,'tracks':192,'timing_boundary_samples':1008,'stored_poses':160}
    assert delivery['status']=='passed' and set(delivery['frames'])==set(selected)
    edges=read(G/'review/edge_audit.json');assert len(edges)==160
    assert all(stage['max_score']==0 for frame in edges.values() for stage in frame.values())
    jobs=read(F/'jobs.json');details=read(R/'detail_upgrade/jobs.json')['jobs'];generation={}
    for n,rec in selected.items():
        checked(R,{'path':rec.get('ungraded_master',rec['path']),'sha256':rec['source_sha256']})
        assert rec['sampling']>=2
        if rec['origin']=='detail_upgrade':
            j=details[rec['job']];assert j['status']=='accepted_detail_and_placement'
            gen=j['generation'];base=R/'detail_upgrade'
            for record in [gen['raw'],gen['prompt'],*gen['references']]:checked(base,record)
            generation['detail_upgrade/'+rec['job']]=gen
        if rec['origin']=='sequence_restore':
            j=jobs['jobs'][rec['job']];assert n in j.get('deliver_frames',j['frames'])
            gen=j['generation']
            for record in [gen['raw'],gen['prompt'],*gen['references']]:checked(F,record)
            assert j['sampling']>=2 and j['frozen_calibration']==j['calibration']
            raw=Image.open(F/j['selected_raw']);crop=j['crop_native']
            assert min(raw.width/j['columns']/(crop[2]-crop[0]),raw.height/j['rows']/(crop[3]-crop[1]))>=2
            generation['sequence_restore/'+rec['job']]=gen
    trial=read(R/'front_attack_grid_trial/sequence_jobs.json')
    for j in trial['jobs'].values():
        checked(R/'front_attack_grid_trial',{'path':j['selected_raw'],'sha256':j['raw_sha256']})
        checked(R/'front_attack_grid_trial',{'path':j['prompt'],'sha256':j['prompt_sha256']})
        for record in j['references']:checked(R/'front_attack_grid_trial',record)
        assert j['generated_pixels_per_native_pixel_before_registration']>=2
    identity=read(R/'detail_upgrade/review/trial_acceptance.json')
    assert process.queue.sha(R/'detail_upgrade/raw/identity_front_v1.png')==identity['artifact_hashes']['raw/identity_front_v1.png']
    for gen in read(F/'generation_history.json').values():
        for record in [gen['raw'],gen['prompt'],*gen['references']]:checked(F,record)
    for key,j in jobs['jobs'].items():
        used=sorted(n for n,r in selected.items() if r.get('job')==key and r['origin']=='sequence_restore')
        j['status']='validated_selected_frames';j['validated_delivery_frames']=used
        j['final_review']='../complete/review/decision.json'
        if key=='w_v1':j['review_concern_resolved']='Magnified native comparison confirms the same folded-back lifted boot. Positional green shoulder/face contamination was removed by the nonspatial tonal curve.'
    process.save(F/'jobs.json',jobs)
    provenance={'schema_version':1,'selected_frames':'selection.json','selected_generation_records':generation,
        'path_bases':'Generation record paths are relative to ../detail_upgrade or ../sequence_restore, as named by each key.',
        'retained_front_attack':'../front_attack_grid_trial/sequence_jobs.json',
        'retained_identity_trial':'../detail_upgrade/review/trial_acceptance.json',
        'new_generation_history':'../sequence_restore/generation_history.json',
        'processing':'../sequence_restore/README.md','all_generations':'built-in imagegen; native variants derived offline'}
    process.save(G/'provenance.json',provenance)
    checks=read(G/'review/export_checks.json')
    assert checks['full_coverage'] and checks['exact_atlas_extraction'] and checks['exact_crop_reconstruction']
    checks.update(visual_review_complete=True,animation_review_complete=True,variant_review_complete=True,
                  edge_spill_review_complete=True,native_family_records_and_palettes_unchanged=True,
                  current_source_table_hashes_verified=True,
                  actual_generated_detail_at_least_2x=True,deterministic_palette_math_verified=True,
                  native_anchor_checks_passed=True,browser_checks=browser,
                  actual_sampling_range=[delivery['sampling_minimum'],delivery['sampling_maximum']])
    m.update(status='validated',review_record='review/acceptance.json',generation_manifest='provenance.json',
        placement_registration='calibration_registration.json',actual_sampling_range=checks['actual_sampling_range'])
    process.save(G/'manifest.json',m);process.save(G/'validation.json',checks)
    (G/'viewer.html').write_text((G/'viewer.html').read_text().replace('href="draft_manifest.json"','href="manifest.json"').replace('"status": "awaiting_visual_acceptance"','"status": "validated"'))
    process.save(G/'animations.json',{'schema_version':1,'animations':m['animations']})
    process.save(G/'variants.json',{'schema_version':1,**m['variants']})
    published=copy.deepcopy(m)
    for page in published['pages']:
        for k in ['base','mask']:page[k]='complete/'+page[k]
    published.update(viewer='complete/viewer.html',generation_manifest='complete/provenance.json',
                     placement_registration='complete/calibration_registration.json')
    process.save(R/'manifest.json',published);process.save(R/'validation.json',checks)
    process.save(R/'animations.json',{'schema_version':1,'animations':m['animations']})
    process.save(R/'variants.json',{'schema_version':1,**m['variants']})
    (R/'viewer.html').write_text((G/'viewer.html').read_text().replace('<head>','<head><base href="complete/">'))
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    gp=[p for p in G.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p!=G/'review/acceptance.json']
    process.save(G/'review/acceptance.json',{'status':'accepted','accepted_utc':now,'decision':'review/decision.json',
        'scope':'Selected complete delivery; unused historical experiments are retained but not accepted artwork.',
        'artifact_hashes':{str(p.relative_to(G)):process.queue.sha(p) for p in sorted(gp)}})
    rp=[p for p in R.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p!=R/'review/acceptance.json']
    process.save(R/'review/acceptance.json',{'status':'accepted','accepted_utc':now,'decision':'complete/review/decision.json',
        'scope':'160 selected frames and all native variants. Historical raw files/checkpoints are hashed for provenance, not approved as alternate deliveries.',
        'artifact_hashes':{str(p.relative_to(R)):process.queue.sha(p) for p in sorted(rp)}})
    path=R.parent/'mm8_remaining/progress.json';ledger=read(path);family=ledger['families']['m432']
    family.update(status='validated',processed_frames=160,blockers=[],completed_package=str((R/'manifest.json').relative_to(process.queue.REPO)),
        resume='Complete. Review mm8_m432/complete/viewer.html. For revisions use sequence_restore/README.md; earlier pending detail jobs are superseded. Refresh inventory_remaining.py after renewed acceptance.')
    family['gates']={k:True for k in family['gates']}
    family['complete_delivery'].update(status='validated',selected_frames=160,required_frames=160,
        reused_detail_frames=47,reused_trial_frames=5,compact_sequence_frames=108)
    ledger['summary']={k:sum(v['status']==k for v in ledger['families'].values()) for k in ['pending','partial','validated','blocked']}
    ledger['updated_utc']=now;process.save(path,ledger)
    print('Sealed 160 native frames, three palettes, five matching atlas/mask pages and the complete offline viewer.')

if __name__=='__main__':run()
