"""Seal the reviewed Wererat Ratman Form delivery and update the resumable family ledger."""
import datetime
import json
from process import ROOT, queue, save


def read(path):
    return json.loads(path.read_text())


def run():
    decision = read(ROOT / 'review/decision.json')
    assert decision['status'] == 'accepted'
    for path, digest in decision['evidence_hashes'].items():
        assert queue.sha(ROOT / path) == digest, ('Stale review', path)
    source = read(ROOT / 'sources.json')
    manifest = read(ROOT / 'draft_manifest.json')
    delivery = read(ROOT / 'review/delivery_checks.json')
    browser = read(ROOT / 'review/browser_checks.json')
    jobs = read(ROOT / 'compact_jobs.json')['jobs']
    assert set(manifest['frames']) == set(source['sources']) and len(manifest['frames']) == 165
    assert manifest['animations'] == source['bindings'] and not manifest['missing_frames']
    assert delivery['status'] == browser['status'] == 'passed'
    assert delivery['frames'] == browser['stored_poses'] == 165
    assert delivery['contacts'] == delivery['unique_generated_frames'] == 160
    assert browser['variant_decodes'] == delivery['variants'] == 495 and browser['tracks'] == 192
    assert delivery['generation_sampling_min'] >= 2
    for record in [*source['sources'].values(), *source['palette_sources'].values(),
                   *source['source_tables'], source['descriptor_table']]:
        assert queue.sha(queue.REPO / record['path']) == record['sha256'], record['path']
    for job in jobs.values():
        assert job['status'] in ['accepted_identity', 'accepted_visual', 'accepted_subset']
        for record in [job['generation']['raw'], job['generation']['prompt'], *job['generation']['references']]:
            assert queue.sha(ROOT / record['path']) == record['sha256'], record['path']
    checks = read(ROOT / 'review/export_checks.json')
    assert checks['full_coverage'] and checks['exact_crop_reconstruction'] and checks['exact_atlas_extraction']
    checks.update(visual_review_complete=True, animation_review_complete=True, variant_review_complete=True,
                  edge_spill_review_complete=True, actual_generated_detail_at_least_2x=True,
                  native_contacts_verified=True, source_bindings_and_hashes_verified=True,
                  deterministic_variants_verified=True, browser_checks=browser,
                  actual_sampling_range=[delivery['generation_sampling_min'], delivery['generation_sampling_max']])
    provenance = {'schema_version': 1, 'tool': 'built-in imagegen',
                  'generation_records': {k: j['generation'] for k, j in jobs.items()},
                  'selected_frame_to_batch': 'registration.json', 'compact_queue': 'compact_jobs.json',
                  'identity_checkpoint': 'checkpoints/identity_acceptance.json',
                  'processing': 'README.md', 'palette_generation': 'Deterministic offline only; base exact bypass.'}
    save(ROOT / 'provenance.json', provenance)
    manifest.update(status='validated', review_record='review/acceptance.json',
                    generation_manifest='provenance.json', placement_registration='calibration_registration.json',
                    actual_sampling_range=checks['actual_sampling_range'])
    save(ROOT / 'manifest.json', manifest)
    save(ROOT / 'validation.json', checks)
    save(ROOT / 'animations.json', {'schema_version': 1, 'animations': manifest['animations']})
    save(ROOT / 'variants.json', {'schema_version': 1, **manifest['variants']})
    save(ROOT / 'placement.json', {'schema_version': 1, 'pixels_per_logical_pixel': 2,
                                  'frames': manifest['frames'], 'registration': 'calibration_registration.json'})
    viewer = (ROOT / 'viewer.html').read_text()
    (ROOT / 'viewer.html').write_text(viewer.replace('href="draft_manifest.json"', 'href="manifest.json"')
                                    .replace('"status": "awaiting_visual_acceptance"', '"status": "validated"'))
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    artifacts = [p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts
                 and p != ROOT / 'review/acceptance.json']
    save(ROOT / 'review/acceptance.json', {'status': 'accepted', 'accepted_utc': now,
         'decision': 'review/decision.json',
         'scope': '165 native filenames (160 unique generated poses) and three palettes; historical rejected raw art retained as provenance.',
         'artifact_hashes': {str(p.relative_to(ROOT)): queue.sha(p) for p in sorted(artifacts)}})
    path = ROOT.parent / 'mm8_remaining/progress.json'
    ledger = read(path)
    family = ledger['families']['m448']
    family.update(status='validated', processed_frames=165, blockers=[],
                  completed_package=str((ROOT / 'manifest.json').relative_to(queue.REPO)),
                  resume='Complete. Review mm8_m448/viewer.html. Follow README.md for revisions and renewed acceptance.')
    family['gates'] = {key: True for key in family['gates']}
    ledger['summary'] = {key: sum(f['status'] == key for f in ledger['families'].values())
                         for key in ['pending', 'partial', 'validated', 'blocked']}
    ledger['updated_utc'] = now
    save(path, ledger)
    print('Validated 165 native filenames from 160 unique generated poses, three palettes and matching atlas/mask pages.')


if __name__ == '__main__':
    run()
