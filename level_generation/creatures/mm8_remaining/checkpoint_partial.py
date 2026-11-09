"""Preserve reviewed available art without declaring a blocked family complete."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parent.parent


def read(path):
    return json.loads(path.read_text())


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(stem):
    root = BASE / ('mm8_' + stem)
    source = read(root / 'sources.json')
    manifest = read(root / 'draft_manifest.json')
    decision = read(root / 'review/partial_decision.json')
    assert decision['status'] == 'accepted_available_frames'
    for path, digest in decision['evidence_hashes'].items():
        assert sha(root / path) == digest, ('review stale', path)
    available = set(manifest['frames'])
    missing = set(source['sources']) - available
    assert missing and available < set(source['sources'])
    assert missing == set(manifest['missing_frames'])
    assert available == set(decision['reviewed_frames'])
    assert manifest['animations'] == source['bindings']
    for rec in [*source['sources'].values(), *source['palette_sources'].values(),
                *source['source_tables'], source['descriptor_table']]:
        assert sha(REPO / rec['path']) == rec['sha256'], rec['path']
    browser = read(root / 'review/browser_checks.json')
    assert browser['status'] == 'passed' and browser['stored_poses'] == len(available)
    edges = read(root / 'review/edge_audit.json')
    assert set(edges) == available
    assert all(stage['max_score'] == 0 for frame in edges.values() for stage in frame.values())
    checks = read(root / 'review/export_checks.json')
    for gate in ['source_hashes_unchanged', 'exact_crop_reconstruction', 'exact_atlas_extraction',
                 'base_mask_placement_identical', 'variant_alpha_unchanged', 'base_bypass_exact']:
        assert checks[gate], gate
    generation = read(root / 'generation.json')
    batches = read(root / 'batches.json')
    for key, batch in generation['batches'].items():
        assert set(batches[key]['frames']) <= available
        for rec in [batch['raw'], batch['prompt'], *batch['references']]:
            assert sha(root / rec['path']) == rec['sha256'], rec['path']
        batch['status'] = 'accepted_available_frames'
        batches[key]['state'] = 'accepted_available_frames'
    save(root / 'generation.json', generation)
    save(root / 'batches.json', batches)
    files = [p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts
             and p.name not in ['partial_acceptance.json', 'browser_harness.html']]
    save(root / 'checkpoints/partial_acceptance.json', {
        'status': 'accepted_available_frames', 'family_complete': False,
        'accepted_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'available_frames': sorted(available), 'missing_frames': sorted(missing),
        'browser_checks': browser, 'source_tables_and_palettes_unchanged': True,
        'artifact_hashes': {str(p.relative_to(root)): sha(p) for p in sorted(files)}})
    path = BASE / 'mm8_remaining/progress.json'
    ledger = read(path)
    family = ledger['families'][stem]
    family.update(status='blocked', processed_frames=len(available), completed_package=None,
                  missing_frames=sorted(missing), partial_checkpoint=str(root.relative_to(BASE)) +
                  '/checkpoints/partial_acceptance.json',
                  resume='Available frames reviewed and exported. See ' + str(root.relative_to(BASE)) +
                         '/RESUME.md for the exact image-service blocker and remaining batch.')
    family['available_frame_gates'] = {k: True for k in ['visual', 'animation', 'variants', 'edge_spill', 'atlas']}
    family['gates'] = {key: False for key in family['gates']}
    ledger['summary'] = {k: sum(v['status'] == k for v in ledger['families'].values())
                         for k in ['pending', 'partial', 'validated', 'blocked']}
    ledger['updated_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save(path, ledger)
    print(stem, len(available), 'reviewed available frames;', len(missing), 'missing; family remains blocked')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stem')
    run(parser.parse_args().stem)
