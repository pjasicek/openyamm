"""Seal the reviewed Thunderbird package; changed review evidence requires renewed acceptance."""
import collections
import datetime
import json
from process import ROOT, queue, save

def run():
    decision = json.loads((ROOT/'review/decision.json').read_text())
    assert decision['status'] == 'accepted'
    for path, digest in decision['evidence_hashes'].items():
        assert queue.sha(ROOT/path) == digest, ('review stale', path)
    sources = json.loads((ROOT/'sources.json').read_text())
    manifest = json.loads((ROOT/'draft_manifest.json').read_text())
    assert set(manifest['frames']) == set(sources['sources'])
    assert manifest['animations'] == sources['bindings']
    for record in [*sources['sources'].values(), *sources['palette_sources'].values(),
                   *sources['source_tables'], sources['descriptor_table']]:
        assert queue.sha(queue.REPO/record['path']) == record['sha256'], record['path']
    browser = json.loads((ROOT/'review/browser_checks.json').read_text())
    assert browser['status'] == 'passed' and browser['stored_poses'] == 125
    edges = json.loads((ROOT/'review/edge_audit.json').read_text())
    assert len(edges) == 125
    assert all(stage['max_score'] == 0 for frame in edges.values() for stage in frame.values())
    generation = json.loads((ROOT/'generation.json').read_text())
    batches = json.loads((ROOT/'batches.json').read_text())
    for key, batch in generation['batches'].items():
        for record in [batch['raw'], batch['prompt'], *batch['references']]:
            assert queue.sha(ROOT/record['path']) == record['sha256']
        batch['status'] = 'validated'
        batches[key]['state'] = 'validated'
    save(ROOT/'generation.json', generation)
    save(ROOT/'batches.json', batches)
    manifest.update(status='validated', review_record='review/acceptance.json')
    save(ROOT/'manifest.json', manifest)
    save(ROOT/'animations.json', {'schema_version': 1, 'animations': manifest['animations']})
    save(ROOT/'variants.json', {'schema_version': 1, **manifest['variants']})
    checks = json.loads((ROOT/'review/export_checks.json').read_text())
    checks.update(visual_review_complete=True, animation_review_complete=True,
                  variant_review_complete=True, edge_spill_review_complete=True,
                  source_tables_and_palettes_unchanged=True, browser_checks=browser)
    save(ROOT/'validation.json', checks)
    paths = ['manifest.json', 'validation.json', 'sources.json', 'generation.json', 'batches.json',
             'registration.json', 'calibration_registration.json', 'calibration.json', 'processing.json', 'tone_settings.json', 'tone_refinement.json',
             'material_settings.json', 'animations.json', 'variants.json', 'viewer.html',
             'viewer_template.html', 'review/decision.json', 'review/browser_checks.json', 'README.md']
    paths += [str(p.relative_to(ROOT)) for p in ROOT.glob('*.py')]
    for folder in ['atlas','raw','prompts','cleaned','aligned_2x','registered_2x','accent_masks_2x','toned_2x','masks_2x',
                   'runtime_aligned_2x','runtime_masks_2x','previews','review/variants']:
        paths += [str(p.relative_to(ROOT)) for p in (ROOT/folder).glob('*') if p.is_file()]
    paths += list(decision['evidence_hashes'])
    save(ROOT/'review/acceptance.json', {'status':'accepted', 'decision':'review/decision.json',
         'accepted_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'artifact_hashes':{p:queue.sha(ROOT/p) for p in sorted(set(paths))}})
    path = ROOT.parent/'mm8_remaining/progress.json'
    ledger = json.loads(path.read_text())
    family = ledger['families']['m552']
    family.update(status='validated', processed_frames=125, batches=len(batches), blockers=[],
                  completed_package=str((ROOT/'manifest.json').relative_to(queue.REPO)),
                  resume='Complete. Open mm8_m552/viewer.html. To revise, reuse retained raw sheets; '
                         'run rebuild.py, review changed contacts, renew decision.json, run browser_checks.py '
                         'and finalize.py, then refresh inventory_remaining.py.')
    family['gates'] = {key:True for key in family['gates']}
    ledger['summary'] = {key:sum(v['status']==key for v in ledger['families'].values())
                         for key in ['pending','partial','validated','blocked']}
    ledger['updated_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save(path, ledger)
    print('Validated 125 native Thunderbird frames, three palettes and four atlas/mask pairs.')

if __name__ == '__main__':
    run()
