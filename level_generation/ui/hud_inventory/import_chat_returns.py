"""Retain and inventory external imagegen returns. Never execute returned code or auto-accept art."""
import argparse
import fcntl
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile

from PIL import Image

from finalize_classification import ROOT, digest
import registration

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('hud_queue', HERE / 'queue.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def save(path, data):
    module.save(path, data)


def extract(archive, destination):
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None, 'Archive CRC failure'
        assert sum(i.file_size for i in z.infolist()) < 4 * 1024**3, 'Unexpected archive size'
        names = set()
        for info in z.infolist():
            path = PurePosixPath(info.filename)
            assert not path.is_absolute() and '..' not in path.parts and '\\' not in info.filename
            assert info.filename not in names, 'Duplicate ZIP path'
            names.add(info.filename)
            assert not stat.S_ISLNK(info.external_attr >> 16), 'ZIP symlink'
            if info.is_dir():
                continue
            out = destination.joinpath(*path.parts)
            out.parent.mkdir(parents=True, exist_ok=True)
            data = z.read(info)
            if out.exists():
                assert out.read_bytes() == data, 'Retained return changed'
            else:
                out.write_bytes(data)


def provenance_receipts(document):
    """Read the explicit ledger formats returned by the external chats, rejecting conflicting receipts."""
    if isinstance(document, list):
        rows = document
    elif isinstance(document, dict) and 'generation_calls' in document:
        rows = document['generation_calls'] + document.get('model_returned_files', [])
    elif isinstance(document, dict) and 'sheets' in document:
        rows = document['sheets']
    elif isinstance(document, dict) and all(re.fullmatch(r'S\d{3}', k) for k in document):
        rows = [dict(value, sheet=key) for key, value in document.items()]
    else:
        raise AssertionError('Unknown provenance ledger format; inspect before importing')
    if isinstance(rows, dict):
        assert all(re.fullmatch(r'S\d{3}', k) for k in rows)
        assert all('sheet' not in v or v['sheet'] == k for k, v in rows.items()), 'Conflicting provenance sheet ID'
        rows = [dict(value, sheet=key) for key, value in rows.items()]
    assert isinstance(rows, list)
    aliases = dict(raw_sha256=('raw_sha256', 'sha256'),
                   submitted_prompt_sha256=('submitted_prompt_sha256', 'prompt_sha256'),
                   reference_sha256=('reference_sha256',),
                   model_returned_filename=('model_returned_filename', 'actual_model_returned_filename',
                                            'returned_filename', 'filename'))
    receipts = {}
    for row in rows:
        assert isinstance(row, dict) and re.fullmatch(r'S\d{3}', row.get('sheet', ''))
        receipt = receipts.setdefault(row['sheet'], dict(records=[]))
        receipt['records'].append(row)
        for key, fields in aliases.items():
            values = {row[name] for name in fields if row.get(name)}
            if receipt.get(key):
                values.add(receipt[key])
            assert len(values) <= 1, f'Conflicting {key} receipts for {row["sheet"]}'
            if values:
                receipt[key] = values.pop()
    return receipts


def reconcile_prior_intake(path, returned, incoming, q):
    """Extend an explicitly identified partial return only when its artwork and prompts are unchanged."""
    prior = json.loads(path.read_text())
    assert prior['bundle'] == returned['bundle_id'], 'Reconciliation belongs to another bundle'
    assert digest(Path(prior['archive'])) == prior['archive_sha256'], 'Prior return archive changed'
    sheets = {s['id']: s for s in returned['sheets']}
    attempts = {a['id']: a for a in q.state['attempts']}
    recorded = {}
    for cell in prior['cells']:
        sid = cell['sheet']
        assert cell['cell'] in sheets[sid]['cells']
        attempt = attempts[cell['attempt']]
        payload = json.loads(Path(attempt['payload']).read_text())
        assert payload['external_return']['bundle'] == prior['bundle']
        assert payload['external_return']['sheet'] == sid
        assert set(payload['selected_cells']) == set(sheets[sid]['cells'])
        assert digest(Path(attempt['raw'])) == attempt['sha256']
        assert digest(incoming / 'outputs/raw' / (sid + '.png')) == attempt['sha256'], 'Rebuilt raw differs'
        assert (incoming / 'outputs/prompts' / (sid + '.txt')).read_text() == payload['prompt'], 'Rebuilt prompt differs'
        if cell.get('artifact'):
            artifact = incoming / 'outputs/processed' / sid / (cell['cell'] + '.png')
            assert digest(artifact) == cell['artifact_sha256'], 'Rebuilt candidate differs'
            assert digest(Path(cell['artifact'])) == cell['artifact_sha256'], 'Prior candidate changed'
        assert sid not in recorded or recorded[sid]['id'] == attempt['id'], 'Ambiguous prior sheet attempts'
        recorded[sid] = attempt
    return prior, recorded


def ingest(archive, extends_intake=None):
    archive_hash = digest(archive)
    destination = HERE / 'chat_returns' / (archive.stem + '-' + archive_hash[:12])
    incoming = destination / 'incoming'
    extract(archive, incoming)
    returned = json.loads((incoming / 'manifest.json').read_text())
    progress_path = incoming / 'outputs/progress.json'
    progress = json.loads(progress_path.read_text())
    bundle = progress.get('bundle', progress.get('bundle_id'))
    assert bundle and '/' not in bundle and '..' not in bundle
    original = HERE / 'chat_bundles' / bundle
    if returned != json.loads((original / 'manifest.json').read_text()):
        history_path = HERE / 'chat_bundles/manifest_history.json'
        history = json.loads(history_path.read_text()) if history_path.exists() else {}
        matches = [Path(p).parent for p in history.get(bundle, [])
                   if json.loads(Path(p).read_text()) == returned]
        assert len(matches) == 1, 'Returned manifest is not a known bundle revision'
        original = matches[0]
    assert returned == json.loads((original / 'manifest.json').read_text()), 'Returned input manifest mismatch'
    original_manifest_hash = digest(original / 'manifest.json')
    worker_cells = progress['cells']
    if isinstance(worker_cells, list):
        worker_cells = {c['id']: c for c in worker_cells}
    valid_ids = {c for sheet in returned['sheets'] for c in sheet['cells']}
    assert set(worker_cells) == valid_ids, 'Incomplete/foreign cell ledger'
    provenance_path = incoming / 'outputs/provenance.json'
    receipts = provenance_receipts(json.loads(provenance_path.read_text())) if provenance_path.exists() else {}
    assert set(receipts) <= {s['id'] for s in returned['sheets']}, 'Foreign provenance sheet'
    report = dict(bundle=bundle, archive=str(archive), archive_sha256=archive_hash,
                  manifest_verified=True, returned_sheets=[], cells=[], unreturned=[], unreturned_details=[],
                  diagnostic_decode_failures=[])
    previous_path = destination / 'intake.json'
    if previous_path.exists():
        previous = json.loads(previous_path.read_text()).get('reconciliation')
        if previous:
            remembered = Path(previous['prior_intake'])
            assert extends_intake is None or extends_intake.resolve() == remembered
            assert digest(remembered) == previous['prior_intake_sha256'], 'Reconciled intake changed'
            extends_intake = remembered
    # Inventory every diagnostic; corrupt returned comparisons are retained, never used as acceptance evidence.
    for path in (incoming / 'outputs').rglob('*.png'):
        try:
            with Image.open(path) as image:
                image.load()
        except Exception as error:
            report['diagnostic_decode_failures'].append(dict(path=str(path), error=str(error)))
    with (HERE / 'checkpoint/state.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        q = module.Queue()
        recorded = {}
        prior_cells = {}
        if extends_intake:
            prior, recorded = reconcile_prior_intake(extends_intake, returned, incoming, q)
            prior_cells = {c['cell']: c for c in prior['cells']}
            report['reconciliation'] = dict(prior_intake=str(extends_intake.resolve()),
                prior_intake_sha256=digest(extends_intake), reused_sheets=len(recorded), reused_cells=len(prior_cells))
        for attempt in q.state['attempts']:
            payload = json.loads(Path(attempt['payload']).read_text())
            external = payload.get('external_return', {})
            if external.get('archive_sha256') == archive_hash:
                recorded[external['sheet']] = attempt
        for sheet in returned['sheets']:
            sid = sheet['id']
            raw = incoming / 'outputs/raw' / (sid + '.png')
            if not raw.exists():
                report['unreturned'].extend(sheet['cells'])
                report['unreturned_details'].append(dict(sheet=sid, cells=sheet['cells'],
                    worker_sheet=progress.get('sheets', {}).get(sid, {}), worker_receipt=receipts.get(sid, {})))
                continue
            with Image.open(raw) as im:
                im.load()
            layout = json.loads((original / sheet['layout']).read_text())
            if (incoming / sheet['layout']).exists():
                assert json.loads((incoming / sheet['layout']).read_text()) == layout
            prompt_path = incoming / 'outputs/prompts' / (sid + '.txt')
            assert prompt_path.is_file(), 'Missing returned prompt'
            receipt = receipts.get(sid, {})
            if receipt.get('raw_sha256'):
                assert receipt['raw_sha256'] == digest(raw), 'Raw differs from worker receipt'
            if receipt.get('submitted_prompt_sha256'):
                assert receipt['submitted_prompt_sha256'] == digest(prompt_path), 'Prompt differs from worker receipt'
            if receipt.get('reference_sha256'):
                assert receipt['reference_sha256'] == digest(original / sheet['reference']), 'Reference differs from receipt'
            for cell in sheet['cells']:
                if worker_cells[cell].get('master_sha256'):
                    assert worker_cells[cell]['master_sha256'] == digest(raw), 'Cell raw receipt mismatch'
            prompt_matches = prompt_path.read_bytes() == (original / sheet['prompt']).read_bytes()
            jobs = sorted({q.members[c][0] for c in sheet['cells']})
            policies = {q.state.get('external_assignments', {}).get(c, {}).get('dependency_policy')
                        for c in sheet['cells']}
            native_identity = policies == {'external_portrait_native_identity_first_pass'}
            independent = policies == {'independent_external_portrait_first_pass'} or native_identity
            policy_payload = dict(dependency_policy=next(iter(policies)),
                                  external_return=dict(bundle=bundle)) if independent else {}
            identity_references = {}
            if native_identity:
                assert returned.get('preparation_mode') == 'external_portrait_native_identity_first_pass'
                hashes = sheet['native_identity_sources']
                assert progress.get('sheets', {}).get(sid, {}).get('native_identity_sources') == hashes, (
                    'Missing or mismatched worker native identity references')
                policy_payload['native_identity_sources'] = hashes
                for cell, relative in sheet.get('native_identity_files', {}).items():
                    source = original / relative
                    assert digest(source) == hashes[cell] == q.members[cell][1]['source_sha256']
                    identity_references[str(source)] = hashes[cell]
                if hashes:
                    assert set(sheet['native_identity_files']) == set(hashes)
                    reference = original / sheet['native_identity_reference']
                    assert digest(reference) == sheet['native_identity_reference_sha256']
                    identity_references[str(reference)] = digest(reference)
            dependencies = {}
            for job in jobs:
                required = q.generation_dependencies(q.jobs[job], policy_payload)
                assert all(q.accepted(c) for c in required), 'Current dependency blocked'
                current = {c: q.state['cells'][c]['sha256'] for c in required}
                if dependencies:
                    assert dependencies == current, 'Incompatible dependency groups'
                dependencies = current
            if independent:
                assert not progress.get('sheets', {}).get(sid, {}).get('dependency_cells', {}), (
                    'Independent first pass must not silently discard references the worker actually used')
            elif returned.get('preparation_mode') == 'portraits_with_explicit_pilot_prerequisites':
                supplied = progress.get('sheets', {}).get(sid, {}).get('dependency_cells')
                assert supplied == dependencies, 'Missing or mismatched accepted portrait pilot hashes'
            for entry in layout['cells']:
                cell = entry['id']
                assert q.members[cell][1] == entry['member'], 'Frozen member changed'
                assert digest(ROOT / entry['member']['source_path']) == entry['original_sha256'], 'Source drift'
                assigned = q.state.get('external_assignments', {}).get(cell)
                assert assigned and original_manifest_hash in [assigned['manifest_sha256'],
                    *assigned.get('previous_manifest_sha256', [])]
            provenance = ('Input prompt recovered; historical submission log unavailable, as disclosed in return'
                          if bundle.endswith('001') else 'Returned prompt/provenance supplied by external chat')
            execution_id = 'return-' + archive_hash[:12] + '-' + sid
            if sid not in recorded:
                reference = original / sheet['reference']
                payload = dict(job=jobs[0], jobs=jobs, batch_id=execution_id, selected_cells=sheet['cells'],
                    prompt=prompt_path.read_text(), source_hashes={c['id']: c['original_sha256'] for c in layout['cells']},
                    dependency_cells=dependencies, reference_hashes={str(reference): digest(reference)},
                    execution_layout=dict(canvas_size=layout['reference_size'],
                        cell_rects={c['id']: c['native_canvas_rect'] for c in layout['cells']},
                        slot_rects={c['id']: c['slot_rect'] for c in layout['cells']}),
                    external_return=dict(bundle=bundle, sheet=sid, archive_sha256=archive_hash,
                        worker_progress=str(progress_path), prompt_provenance=provenance,
                        prompt_matches_input=prompt_matches, original_master_prompt=str(original/'MASTER_PROMPT.md'),
                        provenance_path=str(provenance_path) if provenance_path.exists() else None,
                        provenance_sha256=digest(provenance_path) if provenance_path.exists() else None,
                        worker_receipt=receipt))
                if independent:
                    payload['dependency_policy'] = policy_payload['dependency_policy']
                    if native_identity:
                        payload['native_identity_sources'] = policy_payload['native_identity_sources']
                    payload['reference_hashes'].update(identity_references)
                save(q.payload_root / execution_id / 'payload.json', payload)
                result = q.record(execution_id, raw)
                recorded[sid] = next(a for a in q.state['attempts'] if a['id'] == result['attempt'])
            attempt = recorded[sid]
            assert attempt['sha256'] == digest(raw)
            processing_path = incoming / 'outputs/processed' / sid / 'processing.json'
            processing = json.loads(processing_path.read_text()) if processing_path.exists() else {}
            records = {r['id']: r for r in processing.get('cells', [])}
            if processing:
                assert processing['raw_sha256'] == digest(raw), 'Candidate processing belongs to a different raw'
            for entry in layout['cells']:
                cell = entry['id']
                if cell in prior_cells:
                    # Keep prior registration evidence, local review state and attempt ownership intact.
                    report['cells'].append(prior_cells[cell])
                    continue
                artifact = processing_path.parent / (cell + '.png')
                record = dict(cell=cell, sheet=sid, attempt=attempt['id'], status='returned_needs_local_review',
                              worker_review=worker_cells[cell], prompt_provenance=provenance)
                if artifact.exists():
                    with Image.open(artifact) as im:
                        im.load()
                        assert list(im.size) == entry['x2_size'], 'Candidate is not exact native x2'
                    if records.get(cell, {}).get('artifact_sha256'):
                        assert records[cell]['artifact_sha256'] == digest(artifact), 'Candidate hash differs from receipt'
                    record_path = destination / 'registration' / (cell + '-registration.json')
                    if record_path.exists():
                        retained = json.loads(record_path.read_text())
                        measured = registration.measurements(q.members[cell][1], q.targets[cell], artifact)
                        assert retained['measurements'] == measured, 'Retained registration changed'
                        for image_path, sha in retained['comparison_images'].items():
                            assert digest(Path(image_path)) == sha, 'Retained comparison changed'
                        evidence = dict(registration_record=str(record_path),
                            review_images=list(retained['comparison_images']),
                            failures={p: v['failures'] for p, v in measured['profiles'].items() if v['failures']})
                    else:
                        evidence = registration.evidence(q.members[cell][1], q.targets[cell], artifact,
                                                         destination / 'registration')
                    record.update(artifact=str(artifact), artifact_sha256=digest(artifact), **evidence)
                else:
                    record['status'] = 'raw_only_needs_extraction_review'
                current_state = q.state['cells'].get(cell, {})
                if q.accepted(cell):
                    record['status'] = 'preserved_already_accepted'
                elif (not current_state or current_state.get('reason', '').startswith(
                        'External return retained; local acceptance review pending. Worker reports: ')):
                    worker = worker_cells[cell]
                    reason = worker.get('reason') or worker.get('observations') or worker.get('sheet_level_visual_observation')
                    if isinstance(reason, list):
                        reason = '; '.join(reason)
                    failures = record.get('failures', {})
                    q.state['cells'][cell] = dict(status='deferred' if failures else 'review_pending',
                        attempt=attempt['id'], footprint_failures=failures,
                        reason='External return retained; local acceptance review pending. Worker reports: ' +
                               (reason or worker.get('pending') or 'Needs inspection'),
                        external_return=str(destination / 'intake.json'))
                q.state['external_assignments'][cell].update(status='returned', archive_sha256=archive_hash,
                                                             attempt=attempt['id'])
                report['cells'].append(record)
            module.save(q.state_path, q.state)
            report['returned_sheets'].append(sid)
            save(destination / 'intake.json', report)
            print(bundle, sid, 'retained', flush=True)
    report['counts'] = dict(attempted=len(report['cells']), unreturned=len(report['unreturned']),
        candidates=sum('artifact' in c for c in report['cells']),
        raw_only=sum(c['status']=='raw_only_needs_extraction_review' for c in report['cells']),
        footprint_pass=sum('artifact' in c and not c['failures'] for c in report['cells']),
        accepted_by_importer=0, staged_by_importer=0)
    save(destination / 'intake.json', report)
    print(json.dumps(dict(bundle=bundle, counts=report['counts'], report=str(destination/'intake.json'))), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archives', nargs='+', type=Path)
    parser.add_argument('--extends-intake', type=Path, help='Reconcile an unchanged partial intake with its rebuilt return')
    args = parser.parse_args()
    assert not args.extends_intake or len(args.archives) == 1
    for archive in args.archives:
        ingest(archive.resolve(), args.extends_intake.resolve() if args.extends_intake else None)
