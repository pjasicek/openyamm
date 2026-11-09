"""Reconcile second-pass scope and evidence without manufacturing visual approval.

Snapshots are immutable. Reports can be refreshed after individually authored decisions.
This does not generate artwork, change canonical state, or install runtime assets.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import csv
import fcntl
from functools import lru_cache
import html
import hashlib
import importlib.util
import json
import os
from pathlib import Path

from PIL import Image
import registration

from finalize_classification import HERE, ROOT, digest

spec = importlib.util.spec_from_file_location('hud_queue', HERE / 'queue.py')
queue_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue_module)
OUT = HERE / 'review/second_pass'


def read(path):
    return json.loads(Path(path).read_text())


def save(path, data):
    queue_module.save(path, data)


@lru_cache(maxsize=None)
def hash_file(path):
    path = Path(path)
    return digest(path) if path.is_file() else None


def snapshot():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    directory = OUT / 'snapshots' / stamp
    assert not directory.exists()
    with (HERE / 'checkpoint/state.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        q = queue_module.Queue()
        state_hash = digest(q.state_path)
        save(directory / 'state.json', q.state)
    sources = {}
    issues = []

    def verify(path, expected=None):
        path = str(Path(path).resolve())
        actual = hash_file(path)
        sources[path] = actual
        if actual is None or (expected and actual != expected):
            issues.append(dict(path=path, expected=expected, actual=actual))
        return actual

    by_cell = defaultdict(list)
    masters = {}

    def master(key, raw, expected, cells, provenance, prompt=None, prompt_hash=None, **extra):
        raw_hash = verify(raw, expected)
        entry = dict(id=key, raw=str(raw), raw_sha256=raw_hash, expected_raw_sha256=expected,
                     selected_cells=cells, provenance=str(provenance), **extra)
        verify(provenance)
        if prompt:
            entry.update(prompt=str(prompt), prompt_sha256=verify(prompt, prompt_hash))
        if raw_hash:
            with Image.open(raw) as image:
                entry['raw_size'] = list(image.size)
        masters[key] = entry
        for cell in cells:
            by_cell[cell].append(key)

    for attempt in q.state['attempts']:
        payload = read(attempt['payload'])
        cells = payload.get('selected_cells', [m['id'] for jid in attempt.get('jobs', [attempt['job']])
                                               for m in q.jobs[jid]['members']])
        master(attempt['id'], attempt['raw'], attempt['sha256'], cells, attempt['payload'],
               kind='canonical_attempt', prompt_text_sha256=hashlib.sha256(
                   payload.get('prompt', '').encode()).hexdigest(),
               execution_layout=payload.get('execution_layout'))
        for name, expected in payload.get('reference_hashes', {}).items():
            retained = payload.get('retained_references', {}).get(name)
            verify(retained['path'] if retained else name, expected)
        submitted_prompt = Path(attempt['payload']).parent / 'submitted_prompt.txt'
        if submitted_prompt.exists():
            verify(submitted_prompt, hashlib.sha256(payload.get('prompt', '').encode()).hexdigest())
        for cell, expected in payload.get('source_hashes', {}).items():
            if cell in q.members:
                verify(ROOT / q.members[cell][1]['source_path'], expected)

    canonical_hashes = defaultdict(list)
    for key, value in masters.items():
        canonical_hashes[value['raw_sha256']].append(key)
    for path in sorted((HERE / 'chat_bundles/dense64_20260916').glob('dense64_*/outputs/progress.json')):
        folder = path.parent.parent
        verify(path)
        manifest = read(folder / 'manifest.json')
        verify(folder / 'manifest.json')
        receipts = read(path)['sheets']
        for sheet in manifest['sheets']:
            receipt = receipts[sheet['id']]
            if not receipt.get('raw_path'):
                continue
            key = f'dense:{folder.name}:{sheet["id"]}'
            master(key, folder / receipt['raw_path'], receipt['raw_sha256'], sheet['cells'], path,
                   folder / receipt['submitted_prompt_path'], receipt.get('submitted_prompt_sha256'),
                   kind='dense_receipt', canonical_aliases=canonical_hashes.get(receipt['raw_sha256'], []),
                   historical_notes=receipt.get('notes'), manifest=str(folder / 'manifest.json'),
                   layout=str(folder / sheet['layout']))

    for path in sorted((HERE / 'experiments').rglob('manifest.json')):
        data = read(path)
        raw = path.parent / 'raw.png'
        if not raw.exists():
            continue
        cells = [c.get('id') or c.get('cell') or c.get('member', {}).get('id')
                 for c in data.get('cells', data.get('rows', []))]
        receipt = read(path.parent / data['receipt']) if data.get('receipt') else {}
        master('experiment:' + str(path.parent.relative_to(HERE)), raw,
               data.get('raw_sha256') or receipt.get('sha256'), [c for c in cells if c], path,
               path.parent / data['prompt'] if data.get('prompt') else None, data.get('prompt_sha256'),
               kind='experiment', measurements=str(path.parent / 'measurements.json'))

    for path in sorted((HERE / 'chat_bundles/dense64_20260916/quality_trials').glob('*/receipt.json')):
        receipt = read(path)
        master('quality_trial:' + path.parent.name, path.parent / receipt['raw'], receipt['raw_sha256'],
               receipt['target_ids'], path, path.parent / 'prompt.txt', receipt['submitted_prompt_sha256'],
               kind='quality_trial', historical_review=receipt.get('visual_review'))
        for reference in receipt.get('references', []):
            verify(reference['path'], reference['sha256'])

    historical = defaultdict(list)
    inventory_paths = {v['inventory'] for v in q.state.get('restoration_inventory', {}).values()
                       if v.get('inventory')}
    inventory_paths.add(str(HERE / 'chat_returns/inventory.json'))
    for name in sorted(inventory_paths):
        verify(name)
        for row in read(name).get('cells', []):
            cell = row.get('cell_id') or row.get('cell') or row.get('id')
            if cell:
                historical[cell].append(dict(inventory=name, record=row))

    ownership_path = ROOT / 'output/restoration_handoff_v3/ownership.json'
    verify(ownership_path)
    owners = {c['id']: job['owner'] for job in read(ownership_path)['jobs'] for c in job['cells']}
    catalogue = {}
    for name in ('remaining_icons_20260922', 'remaining_icons_dense_v2_20260922'):
        path = HERE / 'chat_bundles' / name / 'catalogue.json'
        verify(path)
        catalogue.update({row['id']: row for row in read(path)['scope']})
    submission_holds = {c: dict(id=key, **hold) for key, hold in
                        q.state.get('external_submission_holds', {}).items() for c in hold['cells']}
    accepted = {c: q.accepted(c) for c, v in q.state['cells'].items() if v.get('status') == 'accepted'}
    rows = []
    for cell, (jid, member) in sorted(q.members.items()):
        target = q.targets[member['target']]
        if '/icons/' not in target['source_path']:
            continue
        verify(ROOT / member['source_path'], member['source_sha256'])
        record = q.state['cells'].get(cell, {})
        restoration = q.state.get('restoration_inventory', {}).get(cell, {})
        hold = record.get('hold_kind') or restoration.get('status', '')
        prior = catalogue.get(member['target'], {})
        donor = record.get('reuse_candidate_donor') or restoration.get('donor') or prior.get('donor')
        excluded = member['target'] in q.state.get('user_excluded_targets', {})
        if excluded:
            disposition = 'excluded'
        elif accepted.get(cell):
            disposition = 'accepted_existing'
        elif record.get('status') == 'accepted':
            disposition = 'acceptance_evidence_invalid'
        elif by_cell[cell]:
            disposition = 'retained_pending_review'
        elif donor or 'reuse' in hold:
            disposition = 'reuse_candidate'
        elif 'hold' in hold:
            disposition = hold
        elif cell in submission_holds or prior.get('disposition') == 'blocked_prior_submission':
            disposition = 'tool_or_uncertain_hold'
        elif member['target'] in {'engine--icons--seg_scrl.pcx', 'engine--icons--title.png'}:
            disposition = 'oversized'
        elif record.get('status') == 'deferred':
            disposition = 'ungenerated_deferred'
        elif member['method'] != 'imagegen_sheet':
            disposition = 'deterministic_pending'
        else:
            disposition = 'never_generated'
        dependencies = q.dependency_cells(q.jobs[jid])
        blocked = [c for c in dependencies if not accepted.get(c, False)]
        next_action = {
            'retained_pending_review': 'Inspect all linked alternatives; select by observed quality, resolve actual '
                                       'slot/crop and sampling, then inspect native-logical and exact-x2 comparisons.',
            'accepted_existing': 'Preserve valid canonical acceptance; verify staged target evidence separately.',
            'acceptance_evidence_invalid': 'Identify changed artifact/evidence/dependency hash before reopening artwork.',
            'excluded': 'Preserve user skip; do not generate or stage.',
            'reuse_candidate': 'Review linked donor then check destination namespace, consumer and canonical reuse limits.',
            'oversized': 'Demonstrate at least two actual returned pixels per native pixel before generation.',
            'never_generated': 'Reconcile outstanding assignment and any unindexed receipts before first generation.',
            'deterministic_pending': 'Run documented deterministic region reconstruction and inspect joins.',
        }.get(disposition, 'Investigate cited hold evidence and representative family result; do not auto-retry.')
        rows.append(dict(cell_id=cell, target_id=member['target'], job=jid, family=q.jobs[jid]['family'],
                         treatment=target['treatment'], source_path=member['source_path'],
                         source_sha256=member['source_sha256'], source_rect=member['source_rect'],
                         x2_size=member['export_region'][2:], disposition=disposition,
                         attempts=by_cell[cell], selected_attempt=None, selection_status='not_yet_visually_selected',
                         historical=historical[cell], canonical_record=record, restoration_record=restoration,
                         catalogue_record=prior, submission_hold=submission_holds.get(cell),
                         external_assignment=q.state.get('external_assignments', {}).get(cell),
                         dependencies=dependencies, blocked_dependencies=blocked, donor=donor,
                         previous_owner=owners.get(cell), owner='root', assignment_status='queued',
                         second_pass_status='not_reviewed', next_action=next_action))

    staged = []
    for tid, entry in q.state.get('staged_targets', {}).items():
        if tid not in {r['target_id'] for r in rows}:
            continue
        artifact_valid = verify(entry['artifact'], entry['sha256']) == entry['sha256']
        evidence_valid = all(verify(p, h) == h for p, h in entry.get('evidence_hashes', {}).items())
        cells_valid = all(accepted.get(c, False) for c in q.target_cells[tid])
        with Image.open(entry['artifact']) as image:
            dimensions_valid = list(image.size) == q.targets[tid]['x2_size']
        staged.append(dict(target=tid, artifact=entry['artifact'], sha256=entry['sha256'],
                           valid=artifact_valid and evidence_valid and cells_valid and dimensions_valid))
    assert len({r['cell_id'] for r in rows}) == len(rows)
    assert {r['target_id'] for r in rows} == {t['id'] for t in q.targets.values() if '/icons/' in t['source_path']}
    target_states = defaultdict(set)
    for row in rows:
        target_states[row['target_id']].add(row['disposition'])
    summary = dict(timestamp=stamp, original_state_sha256=state_hash, cells=len(rows),
                   targets=len({r['target_id'] for r in rows}), canonical_attempts=len(q.state['attempts']),
                   master_records=len(masters), unique_raw_hashes=len({m['raw_sha256'] for m in masters.values()}),
                   cell_dispositions=dict(Counter(r['disposition'] for r in rows)),
                   target_dispositions=dict(Counter('|'.join(sorted(v)) for v in target_states.values())),
                   accepted_valid=sum(accepted.values()), accepted_invalid=sum(not v for v in accepted.values()),
                   staged_valid=sum(s['valid'] for s in staged), provenance_issues=len(issues),
                   historical_ownership='Retained as provenance only; no live worker inferred. Root owns this sequential pass.')
    save(directory / 'inventory.json', dict(summary=summary, cells=rows))
    save(directory / 'masters.json', masters)
    save(directory / 'provenance.json', dict(files=sources, issues=issues))
    save(directory / 'accepted_staged.json', dict(accepted=accepted, staged=staged))
    save(OUT / 'current.json', dict(snapshot=str(directory), timestamp=stamp))
    report()
    print(json.dumps(summary, indent=2))


def report():
    directory = Path(read(OUT / 'current.json')['snapshot'])
    data = read(directory / 'inventory.json')
    decisions = {p.stem: read(p) for p in (OUT / 'decisions').glob('*.json')}
    rows = data['cells']
    usage_path = OUT / 'usage_scope.json'
    usage = read(usage_path) if usage_path.exists() else None
    usage_by_source = {r['source_path']: r for r in usage['files']} if usage else {}
    reuse_path = OUT / 'reuse_contracts.json'
    reuse_checks = {r['cell_id']: r for r in read(reuse_path)['cells']} if reuse_path.exists() else {}
    tool_path = OUT / 'tool_hold_reconciliation.json'
    tool_checks = {r['cell_id']: r for r in read(tool_path)['cells']} if tool_path.exists() else {}
    for row in rows:
        if row['cell_id'] in tool_checks:
            row['tool_reconciliation'] = tool_checks[row['cell_id']]
            row['next_action'] = tool_checks[row['cell_id']]['next_action']
        if row['cell_id'] in reuse_checks:
            row['reuse_contract_check'] = reuse_checks[row['cell_id']]
            row['next_action'] = reuse_checks[row['cell_id']]['next_action']
        if row['cell_id'] in decisions:
            row['second_pass'] = decisions[row['cell_id']]
            row['second_pass_status'] = row['second_pass']['status']
            row['next_action'] = row['second_pass']['next_action']
            row['selected_attempt'] = row['second_pass']['attempt']
            row['selection_status'] = row['second_pass']['selection_reason']
            row['assignment_status'] = row['second_pass_status']
        scope = usage_by_source.get(row['source_path'])
        row['restoration_active'] = scope['restoration_active'] if scope else True
        row['usage_scope_status'] = scope['status'] if scope else 'not_audited'
        if scope:
            assert scope['source_sha256'] == row['source_sha256'], 'Usage scope source changed; rerun audit'
            row['restoration_canonical_source'] = scope['canonical_source']
        if not row['restoration_active']:
            row['assignment_status'] = row['usage_scope_status']
            row['next_action'] = ('No artwork work: ' + row['usage_scope_status'] + '. '
                'See usage_scope.json; preserve historical evidence and runtime sources. '
                'Resolve usage or duplicate destination contract before any restoration.')
    investigations = []
    investigation_path = OUT / 'family_investigations.json'
    if investigation_path.exists():
        for authored in read(investigation_path)['investigations']:
            needles = authored.get('held_reason_contains_any', [authored.get('held_reason_contains')])
            selected = [r['cell_id'] for r in rows if r['disposition'] == 'family_quality_hold' and
                        any(n and n in r['canonical_record'].get('reason', '') for n in needles)]
            evidence = [str((HERE if p.startswith('chat_bundles/') else ROOT) / p) for p in authored['inspected']]
            assert all(Path(p).is_file() for p in evidence)
            investigation = dict(authored, selected_held_cells=selected,
                                  evidence_hashes={p: digest(Path(p)) for p in evidence})
            investigations.append(investigation)
            for row in rows:
                if row['cell_id'] in selected:
                    row['hold_investigation'] = authored['id']
                    if row['restoration_active']:
                        row['next_action'] = authored['next_action']
    summary = dict(data['summary'], second_pass_decisions=len(decisions),
                   second_pass_statuses=dict(Counter(r['second_pass_status'] for r in rows)),
                   investigated_family_holds=len({c for i in investigations for c in i['selected_held_cells']}),
                   retained_cells_without_second_pass_decision=sum(
                       bool(r['attempts']) and r['disposition'] != 'accepted_existing' and
                       r['disposition'] != 'excluded' and r['cell_id'] not in decisions for r in rows),
                   reuse_contract_statuses=dict(Counter(r['status'] for r in reuse_checks.values())),
                   tool_reconciliation_statuses=dict(Counter(r['status'] for r in tool_checks.values())),
                   complete=False)
    if usage:
        summary['usage_scope'] = usage['summary']
        summary['active_retained_without_decision'] = sum(r['restoration_active'] and bool(r['attempts']) and
            r['disposition'] not in ('accepted_existing', 'excluded') and r['cell_id'] not in decisions for r in rows)
        summary['usage_scope_cell_statuses'] = dict(Counter(r['usage_scope_status'] for r in rows))
    audit_path = OUT / 'replacement_audit.json'
    if audit_path.exists():
        summary['technical_replacement_audit'] = read(audit_path)['summary']
    save(OUT / 'inventory.json', dict(summary=summary, cells=rows))
    with (OUT / 'inventory.csv').open('w', newline='') as stream:
        columns = ['cell_id', 'target_id', 'treatment', 'disposition', 'second_pass_status',
                   'usage_scope_status', 'restoration_active', 'owner', 'next_action']
        writer = csv.DictWriter(stream, columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    groups = defaultdict(list)
    for row in rows:
        if row['restoration_active'] and row['disposition'] not in ('excluded', 'accepted_existing'):
            key = row['attempts'][0] if row['attempts'] else 'family:' + row['job']
            groups[key].append(row['cell_id'])
    by_cell = {r['cell_id']: r for r in rows}
    save(OUT / 'assignments.json', [dict(id=key, owner='root', selected_cells=cells,
        cell_statuses={c: by_cell[c]['assignment_status'] for c in cells},
        family_jobs=sorted({by_cell[c]['job'] for c in cells}),
        contract_context=str(HERE / 'jobs.json'),
        note='Only selected_cells are assigned; other frozen-job members are context, not claimed.')
        for key, cells in groups.items()])
    save(OUT / 'holds.json', [r for r in rows if 'hold' in r['disposition'] or r['disposition'] in
                            ('ungenerated_deferred', 'oversized', 'never_generated')])
    save(OUT / 'hold_investigations.json', investigations)
    repairs = [d for d in decisions.values() if d['status'] in ('needs_repair', 'rejected_pixelation')
               and by_cell[d['cell_id']]['restoration_active']]
    save(OUT / 'repair_batches.json', dict(generation_authorized=False, preparation_only=True,
                                          cells=repairs))
    save(OUT / 'workers/root.json', dict(status='incomplete', decisions_recorded=len(decisions),
                                        execution='Foreground only; no background review worker is scheduled.',
                                        scope='Usage-gated icons only; resolve lean-scope audit before more visual review',
                                        snapshot=str(directory)))
    def link(path, label):
        return f'<a href="{html.escape(os.path.relpath(path, OUT), quote=True)}">{html.escape(label)}</a>'
    page = ['<!doctype html><meta charset="utf-8"><title>Second-pass restoration review</title>',
            '<style>body{font:15px sans-serif}td{padding:6px;vertical-align:top}tr:nth-child(even){background:#eee}',
            'input{width:80%;padding:10px}table{border-collapse:collapse}</style>',
            '<h1>Second-pass restoration review — in progress</h1>',
            '<p>Automated provenance checks are not visual approval. Historical findings remain attributed.</p>',
            '<pre>' + html.escape(json.dumps(summary, indent=2)) + '</pre>',
            '<p>' + link(OUT / 'inventory.json', 'Inventory JSON') + ' · ' + link(OUT / 'inventory.csv', 'CSV') +
            ' · ' + link(directory / 'accepted_staged.json', 'Existing acceptance/staging audit') +
            ' · ' + link(OUT / 'replacement_index.html', 'Every-original technical replacement audit') + '</p>',
            '<input id="filter" placeholder="Search target, treatment, status, next action">',
            '<table><thead><tr><th>Cell</th><th>Disposition</th><th>Second pass</th><th>Evidence / next action</th></tr></thead><tbody>']
    masters = read(directory / 'masters.json')
    for row in rows:
        evidence = ' '.join(link(masters[a]['raw'], f'raw {i + 1}') for i, a in enumerate(row['attempts']))
        decision = OUT / 'decisions' / (row['cell_id'] + '.json')
        if decision.exists():
            evidence += ' ' + link(decision, 'second-pass decision')
        page.append('<tr><td>' + html.escape(row['cell_id']) + '<br>' + html.escape(row['treatment']) +
                    '</td><td>' + html.escape(row['disposition']) + '</td><td>' +
                    html.escape(row['second_pass_status']) + '</td><td>' + evidence + '<br>' +
                    html.escape(row['next_action']) + '</td></tr>')
    page.append('</tbody></table><script>filter.oninput=()=>{let q=filter.value.toLowerCase();'
                'document.querySelectorAll("tbody tr").forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))};</script>')
    (OUT / 'index.html').write_text('\n'.join(page))
    audit_summary = summary.get('technical_replacement_audit')
    technical_status = (f"Technical coverage: {audit_summary['original_targets_checked']:,} original files checked; "
                        f"{audit_summary['extracted_candidates_checked']:,} retained diagnostic exports measured. "
                        f"{audit_summary['candidate_statuses'].get('geometry_flag', 0):,} export geometry warnings. "
                        'These are not automatic visual pass/fail decisions.\n\n') if audit_summary else ''
    (OUT / 'STATUS.md').write_text('# Second pass — in progress\n\n' +
        ('Scope correction: [runtime usage audit](USAGE_SCOPE.md) supersedes whole-folder assignments. '
         'Legacy UI, usage-unknown files and same-name duplicate aliases are not artwork assignments. '
         f"Active retained cells without a decision: {summary['active_retained_without_decision']:,}. "
         + ('The original 1,882 usage holds are resolved (1,829 exclusions, 53 protected dynamic states). '
            if usage['summary'].get('restoration_holds_resolved') else 'Usage holds remain unresolved. ')
         + 'Broader candidate reachability/deletion auditing remains separate; counts below preserve '
           'the historical census.\n\n' if usage else '') +
        f"Scope: {summary['targets']:,} unique icon targets / {summary['cells']:,} cells.\n\n" +
        technical_status +
        f"Individual second-pass decisions: {len(decisions)}. This is not a completed pass.\n\n" +
        f"Decisions: {sum(d['status'] == 'needs_repair' for d in decisions.values())} targeted repairs; " +
        f"{sum(d['status'] == 'rejected_pixelation' for d in decisions.values())} failed-restoration rejections; " +
        f"{sum(d['status'] == 'needs_review' for d in decisions.values())} partially reviewed with explicit " +
        'remaining checks. No new canonical acceptance or staging.\n\n' +
        f"Retained cells still lacking a second-pass decision: " +
        f"{summary['retained_cells_without_second_pass_decision']:,}. " +
        f"Representative quality-hold investigations cover {summary['investigated_family_holds']:,} " +
        'ungenerated cells; this is not individual visual approval.\n\n' +
        '[Searchable inventory](index.html) · [CSV](inventory.csv) · [Assignments](assignments.json) · '
        '[Every-original technical replacement audit](replacement_index.html) · '
        '[Holds](holds.json) · [Hold investigations](hold_investigations.json) · '
        '[Reuse contracts](reuse_contracts.json) · [Tool receipt reconciliation](tool_hold_reconciliation.json) · '
        '[Repair preparation](repair_batches.json) · [Validation](validation.json)\n\n' +
        'Prior valid acceptance is preserved. No new runtime installation. Unperformed reviews are explicitly '
        '`not_reviewed`; historical repair labels are not automatically second-pass failures.\n')


def extract(cell, attempt, rect, queue=None, provisional_reason=None):
    """Extract a verified canvas, or an explicitly provisional diagnostic with no sampling claim."""
    q = queue or queue_module.Queue()
    directory = Path(read(OUT / 'current.json')['snapshot'])
    master = read(directory / 'masters.json')[attempt]
    assert cell in master['selected_cells']
    assert digest(Path(master['raw'])) == master['raw_sha256']
    _, member = q.members[cell]
    target = q.targets[member['target']]
    x, y, width, height = rect
    with Image.open(master['raw']) as raw:
        assert x >= 0 and y >= 0 and x + width <= raw.width and y + height <= raw.height
        ratios = [width / member['source_rect'][2], height / member['source_rect'][3]]
        assert min(ratios) >= 2, f'Insufficient returned sampling: {ratios}'
        output = OUT / 'evidence' / cell / attempt.replace(':', '_')
        output.mkdir(parents=True, exist_ok=False)
        cropped = raw.crop((x, y, x + width, y + height)).convert('RGBA')
        cropped.save(output / 'raw-crop.png')
        candidate = cropped.convert('RGBa').resize(tuple(member['export_region'][2:]),
                                                  Image.Resampling.LANCZOS).convert('RGBA')
        candidate.save(output / 'candidate.png')
    registration.evidence(member, target, output / 'candidate.png', output / 'registration')
    for profile, native, final in registration.images(member, target, output / 'candidate.png'):
        native.save(output / (profile + '-native-x2.png'))
        final.save(output / (profile + '-restored-x2.png'))
        native.resize(tuple(member['source_rect'][2:]), Image.Resampling.NEAREST).save(
            output / (profile + '-native-logical.png'))
        final.resize(tuple(member['source_rect'][2:]), Image.Resampling.LANCZOS).save(
            output / (profile + '-restored-logical.png'))
    processing = dict(cell_id=cell, attempt=attempt, raw=master['raw'],
         raw_sha256=master['raw_sha256'], source_sha256=member['source_sha256'],
         raw_rect=None if provisional_reason else rect,
         actual_sampling=None if provisional_reason else ratios, candidate=str(output / 'candidate.png'),
         candidate_sha256=digest(output / 'candidate.png'),
         operation='Reviewed full-canvas crop; premultiplied Lanczos downsample. No mask, fit or translation.',
         visual_approval=False)
    if provisional_reason:
        processing.update(provisional_raw_rect=rect, extraction_status=provisional_reason,
            operation='Provisional diagnostic crop/downsample only. Full-canvas mapping and actual sampling '
                      'are unverified; no alpha-bound fitting, canonical export or geometry approval.')
    save(output / 'processing.json', processing)
    print(output)


def extract_grid(attempt, columns, rows):
    from review_dense_sheet import opaque_rectangles, trim_gutter
    directory = Path(read(OUT / 'current.json')['snapshot'])
    master = read(directory / 'masters.json')[attempt]
    with Image.open(master['raw']) as image:
        rectangles = opaque_rectangles(image, columns, rows)
        assert len(rectangles) == len(master['selected_cells']), 'Resolve unused/missing slots explicitly'
        rectangles = [trim_gutter(image, rect) for rect in rectangles]
    for cell, rect in zip(master['selected_cells'], rectangles):
        extract(cell, attempt, rect)


def record_notes(path):
    """Bind explicitly authored review notes to their evidence, never infer approval."""
    authored = read(path)
    inventory = {r['cell_id']: r for r in read(OUT / 'inventory.json')['cells']}
    for group in authored['reviews']:
        group = {**authored.get('common', {}), **group}
        for cell in group['cells']:
            row = inventory[cell]
            attempt = group['attempt']
            assert attempt in row['attempts']
            directory = OUT / 'evidence' / cell / attempt.replace(':', '_')
            processing = read(directory / 'processing.json')
            if processing.get('provisional_raw_rect'):
                assert group['status'] in ('needs_review', 'needs_repair', 'rejected_pixelation')
                assert 'slot_extraction' in group['follow_up_types']
            registration_path = directory / 'registration' / (cell + '-registration.json')
            measurements = read(registration_path)
            evidence = [processing['raw'], str(directory / 'raw-crop.png'), str(directory / 'candidate.png'),
                        *measurements['comparison_images'], *group.get('additional_evidence', [])]
            assert all(Path(p).is_file() for p in evidence)
            decision = dict(target_id=row['target_id'], **processing,
                            status=group['status'], reviewer='root', date=datetime.now(timezone.utc).isoformat(),
                            authored_notes=str(path.resolve()), registration_record=str(registration_path),
                            registration_measurements=measurements['measurements'],
                            check_results=group['checks'], observation=group['observation'],
                            material_defects=group.get('material_defects', []),
                            acceptable_variations=group.get('acceptable_variations', []),
                            follow_up_types=group['follow_up_types'], next_action=group['next_action'],
                            selection_reason=group['selection_reason'],
                            alternatives=group.get('alternatives', []),
                            dependencies=row['dependencies'], blocked_dependencies=row['blocked_dependencies'],
                            related_family=row['family'], evidence_hashes={p: digest(Path(p)) for p in evidence},
                            generation_status=row['disposition'], canonical_accepted=False, staged=False,
                            runtime_installed=False)
            destination = OUT / 'decisions' / (cell + '.json')
            if destination.exists():
                raise AssertionError('Preserve existing decisions; append a dated revision instead')
            save(destination, decision)
    report()


def audit_reuse():
    """Read-only contract preflight. Equality never substitutes for destination review."""
    q = queue_module.Queue()
    rows = read(OUT / 'inventory.json')['cells']
    checks = []
    for row in rows:
        if row['disposition'] != 'reuse_candidate':
            continue
        cell, donor = row['cell_id'], row['donor']
        failures = []
        if donor not in q.members:
            failures.append('Donor cell is not in frozen jobs')
        else:
            jid, member = q.members[cell]
            donor_jid, donor_member = q.members[donor]
            target, donor_target = q.targets[member['target']], q.targets[donor_member['target']]
            for m, t, job in ((member, target, jid), (donor_member, donor_target, donor_jid)):
                if (q.target_cells[t['id']] != [m['id']] or
                        m['source_rect'] != [0, 0, *t['native_size']] or
                        m['export_region'] != [0, 0, *t['x2_size']]):
                    failures.append(f'{m["id"]}: not a complete single-cell canvas')
                if digest(ROOT / m['source_path']) != m['source_sha256'] or m['source_sha256'] != t['source_sha256']:
                    failures.append(f'{m["id"]}: native source hash mismatch')
                if t.get('page_dependencies'):
                    failures.append(f'{m["id"]}: page-backed art requires its own assembly')
                for dependency in q.jobs[job]['dependencies']:
                    seed = dependency['kind'] == 'accepted_seed_job'
                    allowed_seed = seed and ((m['id'] == cell and dependency.get('job') == donor_jid) or
                                             jid == donor_jid)
                    if dependency['kind'] != 'accepted_treatment_pilot' and not allowed_seed:
                        failures.append(f'{m["id"]}: unsupported dependency {dependency}')
            for key in ('source_sha256', 'namespace', 'native_size', 'x2_size', 'treatment', 'logical_canvas',
                        'placement', 'frame', 'native_palette_sha256', 'native_rgba_sha256', 'compositing'):
                if target[key] != donor_target[key]:
                    failures.append('Different target contract: ' + key)
            for key in ('source_rect', 'export_region', 'method', 'cleanup'):
                if member[key] != donor_member[key]:
                    failures.append('Different cell contract: ' + key)
        accepted = donor in q.members and q.accepted(donor)
        status = 'incompatible_contract' if failures else ('destination_review_needed' if accepted else 'donor_not_accepted')
        action = ('Resolve the specific reuse contract differences; do not copy the donor: ' + '; '.join(failures)
                  if failures else
                  'Review the accepted donor at this destination, produce destination registration/compositing evidence, '
                  'then use canonical reuse only after all dependency checks pass.' if accepted else
                  f'Review and canonically accept donor {donor}, then inspect destination registration, consumers and '
                  'current dependencies before canonical reuse. No independent regeneration is prescribed.')
        checks.append(dict(cell_id=cell, donor=donor, status=status, contract_failures=failures,
                           donor_accepted=accepted, dependency_blockers=row['blocked_dependencies'],
                           visual_approval=False, canonical_reused=False, next_action=action))
    save(OUT / 'reuse_contracts.json', dict(date=datetime.now(timezone.utc).isoformat(),
         scope='Read-only preliminary structural checks; canonical reuse rechecks live contracts and visual evidence.',
         summary=dict(Counter(r['status'] for r in checks)), cells=checks))
    report()
    print(json.dumps(Counter(r['status'] for r in checks), indent=2))


def record_existing_notes(path):
    """Record actual review of retained exports without claiming their crop mapping was verified."""
    authored = read(path)
    inventory = {r['cell_id']: r for r in read(OUT / 'inventory.json')['cells']}
    q = queue_module.Queue()
    for note in authored['reviews']:
        cell = note['cell']
        row = inventory[cell]
        assert row.get('restoration_active', True), 'Target is outside active usage-gated restoration scope'
        historical = next(h['record'] for h in row['historical'] if
                          h['record'].get('candidate') or h['record'].get('artifact'))
        attempt = historical.get('attempt') or historical.get('canonical_attempt')
        assert attempt in row['attempts']
        raw = historical.get('raw') or historical['raw_path']
        candidate = historical.get('candidate') or historical['artifact']
        record_path = historical.get('registration_record') or historical['registration']
        registration_record = read(record_path)
        measurements = registration.measurements(q.members[cell][1], q.targets[row['target_id']], Path(candidate))
        assert measurements == registration_record['measurements'], 'Retained geometry evidence is stale'
        evidence = [raw, candidate, record_path, *registration_record['comparison_images']]
        decision = dict(cell_id=cell, target_id=row['target_id'], attempt=attempt, raw=raw,
            raw_sha256=digest(Path(raw)), source_sha256=row['source_sha256'], candidate=candidate,
            candidate_sha256=digest(Path(candidate)), raw_rect=None, actual_sampling=None,
            extraction_status='Retained diagnostic export inspected; historical crop mapping not yet verified.',
            historical_extraction=historical.get('extraction') or historical.get('worker_review'),
            status=note['status'], reviewer='root', date=datetime.now(timezone.utc).isoformat(),
            authored_notes=str(path.resolve()), registration_record=record_path,
            registration_measurements=measurements, check_results=note['checks'],
            observation=note['observation'], material_defects=note.get('material_defects', []),
            acceptable_variations=note.get('acceptable_variations', []),
            follow_up_types=note['follow_up_types'], next_action=note['next_action'],
            selection_reason='Retained exact-x2 diagnostic inspected individually with native and raw master; '
                             'selection is provisional pending extraction verification.',
            dependencies=row['dependencies'], blocked_dependencies=row['blocked_dependencies'],
            related_family=row['family'], evidence_hashes={p: digest(Path(p)) for p in evidence},
            generation_status=row['disposition'], canonical_accepted=False, staged=False, runtime_installed=False)
        destination = OUT / 'decisions' / (cell + '.json')
        assert not destination.exists(), 'Preserve existing decisions'
        save(destination, decision)
    report()


def audit_tool_holds():
    """Reconcile retained receipts only; never retry or clear a canonical tool hold."""
    rows = read(OUT / 'inventory.json')['cells']
    old_run = HERE / 'chat_bundles/remaining_icons_20260922/runs/generate_ready_96_20260922'
    checks = []
    for row in rows:
        if row['disposition'] not in ('tool_hold', 'tool_or_uncertain_hold'):
            continue
        assignment = row.get('external_assignment') or {}
        bundle, sheet = assignment.get('bundle'), assignment.get('dense_sheet')
        receipt = None
        evidence = []
        status = 'missing_terminal_receipt'
        if row.get('submission_hold'):
            path = Path(row['submission_hold']['receipt'])
            receipt = read(path)
            evidence.append(path)
        elif 'armory' in row['cell_id']:
            path = old_run / 'B1004.unresolved.json'
            receipt = read(path)
            evidence.append(path)
            if row['cell_id'] != 'engine--icons--6armory.bmp':
                authority = next(r for r in rows if r['cell_id'] == 'engine--icons--6armory.bmp')
                assert row['source_sha256'] == authority['source_sha256']
                status = 'same_source_as_terminal_rejection'
        elif bundle == 'dense64_legacy_small_001' and sheet == 'S008':
            path = HERE / 'chat_bundles/dense64_20260916' / bundle / 'outputs/progress.json'
            receipt = read(path)['sheets'][sheet]
            evidence.append(path)
        elif bundle == 'remaining_icons_20260922':
            path = old_run / (sheet + '.unresolved.json')
            if path.exists():
                receipt = read(path)
                evidence.append(path)
            submission = old_run / (sheet + '.submission.json')
            if submission.exists():
                evidence.append(submission)
        elif bundle == 'restoration_200_015':
            path = HERE / 'chat_returns/dropbox_archives/download_validation.json'
            entry = next(e for e in read(path) if e['name'] == 'resto_200_015_partial.zip')
            assert row['cell_id'] in entry['unreturned_cells']
            receipt = dict(archive=entry['name'], unreturned_sheets=entry['unreturned_sheets'],
                           unreturned_cells=entry['unreturned_cells'])
            evidence.append(path)
            status = 'partial_archive_missing_sheet'
        if receipt and status == 'missing_terminal_receipt':
            if receipt.get('status') == 'submitted_no_return':
                status = 'parallel_group_failure_unattributed'
            elif 'moderation_blocked' in json.dumps(receipt):
                status = 'terminal_rejection'
        actions = {
            'terminal_rejection': 'Preserve the terminal receipt and request ID. No retry, rephrasing or alias submission. '
                                  'External resolution of the original tool rejection is required.',
            'same_source_as_terminal_rejection': 'Preserve the original B1004 rejection and same-source alias hold. '
                                                'Renaming or changing world namespace does not clear it; do not submit.',
            'parallel_group_failure_unattributed': 'Recover the original parallel-call logs for request '
                '02dfc624-216a-453d-baf0-dd36fe681577 and identify each outcome. No raw exists in the indexed returns; '
                'do not assume this individual cell was rejected or safely resubmit it.',
            'partial_archive_missing_sheet': 'Obtain the original S026 receipt or retained return from '
                'resto_200_015_partial. The archive audit proves six maleh cells are absent, not why; '
                'reconcile the original session outcome before any new submission.',
            'missing_terminal_receipt': f'Recover the original outcome for {sheet} using the retained submission '
                'execution ID/payload. No terminal receipt or indexed raw is linked; submission preparation alone '
                'does not prove a tool call occurred. Preserve uncertainty and do not resubmit automatically.'}
        assert evidence, f'No receipt or submission evidence for {row["cell_id"]}'
        checks.append(dict(cell_id=row['cell_id'], status=status, retained_receipt=receipt,
                           evidence_hashes={str(p): digest(p) for p in evidence},
                           next_action=actions[status], auto_retry=False, canonical_hold_changed=False))
    save(OUT / 'tool_hold_reconciliation.json', dict(date=datetime.now(timezone.utc).isoformat(),
         summary=dict(Counter(r['status'] for r in checks)), cells=checks))
    report()
    print(json.dumps(Counter(r['status'] for r in checks), indent=2))


def validate():
    directory = Path(read(OUT / 'current.json')['snapshot'])
    data = read(OUT / 'inventory.json')
    cells = data['cells']
    assert len(cells) == len({r['cell_id'] for r in cells}) == data['summary']['cells']
    targets = {t['id'] for t in read(HERE / 'expected_targets.json')['targets'] if '/icons/' in t['source_path']}
    assert {r['target_id'] for r in cells} == targets
    assert sum(data['summary']['cell_dispositions'].values()) == len(cells)
    assert sum(data['summary']['target_dispositions'].values()) == len(targets)
    assignments = read(OUT / 'assignments.json')
    assigned = [c for a in assignments for c in a['selected_cells']]
    expected = {r['cell_id'] for r in cells if r.get('restoration_active', True)
                and r['disposition'] not in ('excluded', 'accepted_existing')}
    assert len(assigned) == len(set(assigned)) and set(assigned) == expected
    usage_path = OUT / 'usage_scope.json'
    if usage_path.exists():
        usage = read(usage_path)
        sources = {r['source_path']: r for r in usage['files']}
        for row in sources.values():
            assert hash_file(ROOT / row['source_path']) == row['source_sha256']
            if row['status'] in ('excluded_legacy_ui', 'excluded_unreferenced_art'):
                assert not row['references'] and not row['dynamic_evidence']
            if row['status'] == 'excluded_unreferenced_art':
                assert row['hold_review']['source_sha256'] == row['source_sha256']
                assert row['hold_review']['status'] == row['status']
                assert row['hold_review']['reason'] and row['hold_review']['rule']
            if row['canonical_source']:
                donor = sources[row['canonical_source']]
                assert donor['restoration_active']
                assert donor['source_sha256'] == row['source_sha256']
                assert Path(donor['source_path']).name.lower() == Path(row['source_path']).name.lower()
        for name, value in usage['input_hashes'].items():
            assert hash_file(ROOT / name) == value, f'Usage evidence changed: {name}'
    checked = 0
    for name, expected_hash in read(directory / 'provenance.json')['files'].items():
        assert expected_hash is not None, f'Missing snapshot evidence: {name}'
        assert hash_file(name) == expected_hash, f'Evidence changed after snapshot: {name}'
        checked += 1
    assert not read(directory / 'provenance.json')['issues'], 'Resolve provenance issues before publication'
    masters = read(directory / 'masters.json')
    decisions = list((OUT / 'decisions').glob('*.json'))
    for path in decisions:
        decision = read(path)
        assert not decision['canonical_accepted'] and not decision['staged']
        for name, expected_hash in decision['evidence_hashes'].items():
            assert hash_file(name) == expected_hash, f'Review evidence changed: {name}'
        with Image.open(decision['candidate']) as image:
            member = next(r for r in cells if r['cell_id'] == decision['cell_id'])
            assert list(image.size) == member['x2_size']
        if decision['actual_sampling'] is not None:
            assert min(decision['actual_sampling']) >= 2
        else:
            assert decision.get('extraction_status') and decision['raw_rect'] is None
            if decision.get('provisional_raw_rect'):
                assert decision['status'] in ('needs_review', 'needs_repair', 'rejected_pixelation')
                assert 'slot_extraction' in decision['follow_up_types']
                x, y, width, height = decision['provisional_raw_rect']
                with Image.open(decision['raw']) as raw:
                    assert min(x, y) >= 0 and x + width <= raw.width and y + height <= raw.height
                    crop = raw.crop((x, y, x + width, y + height)).convert('RGBA')
                with Image.open(Path(decision['candidate']).parent / 'raw-crop.png') as saved:
                    assert crop.tobytes() == saved.convert('RGBA').tobytes()
        assert decision['next_action'] and decision['check_results']
        master = masters[decision['attempt']]
        assert decision['cell_id'] in master['selected_cells']
        assert master['raw_sha256'] == decision['raw_sha256']
        if decision['raw_rect'] is not None:
            x, y, width, height = decision['raw_rect']
            with Image.open(master['raw']) as raw:
                assert min(x, y) >= 0 and x + width <= raw.width and y + height <= raw.height
            assert decision['actual_sampling'] == [width / member['source_rect'][2], height / member['source_rect'][3]]
    for name in ('hold_investigations.json', 'tool_hold_reconciliation.json'):
        records = read(OUT / name)
        records = records if isinstance(records, list) else records['cells']
        for record in records:
            for path, expected_hash in record['evidence_hashes'].items():
                assert hash_file(path) == expected_hash, f'Investigation evidence changed: {path}'
    audit_path = OUT / 'replacement_audit.json'
    if audit_path.exists():
        audit = read(audit_path)
        assert {r['target_id'] for r in audit['targets']} == targets
        assert len(audit['targets']) == len(targets)
        assert audit['summary']['native_contract_errors'] == 0
        for target in audit['targets']:
            assert hash_file(target['source_path']) == target['source_sha256']
            for cell in target['cells']:
                for candidate in cell['candidate_checks']:
                    if candidate.get('sha256'):
                        assert hash_file(candidate['path']) == candidate['sha256']
    result = dict(scope_accounting=True, exclusive_ownership=True, provenance_files_verified=checked,
                  decision_evidence_verified=len(decisions), exact_x2=True,
                  verified_sampling_decisions=sum(read(p)['actual_sampling'] is not None for p in decisions),
                  unresolved_extraction_decisions=sum(read(p)['actual_sampling'] is None for p in decisions),
                  canonical_state_unchanged=digest(HERE / 'checkpoint/state.json') ==
                  data['summary']['original_state_sha256'], visual_completion=False)
    save(OUT / 'validation.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['snapshot', 'report', 'extract', 'extract-grid', 'record-notes',
                                          'record-existing-notes', 'audit-reuse', 'audit-tool-holds', 'validate'])
    parser.add_argument('--cell')
    parser.add_argument('--attempt')
    parser.add_argument('--rect', nargs=4, type=int)
    parser.add_argument('--columns', type=int)
    parser.add_argument('--rows', type=int)
    parser.add_argument('--notes', type=Path)
    args = parser.parse_args()
    if args.action == 'snapshot':
        snapshot()
    elif args.action == 'extract':
        extract(args.cell, args.attempt, args.rect)
    elif args.action == 'extract-grid':
        extract_grid(args.attempt, args.columns, args.rows)
    elif args.action == 'record-notes':
        record_notes(args.notes)
    elif args.action == 'record-existing-notes':
        record_existing_notes(args.notes)
    elif args.action == 'validate':
        validate()
    elif args.action == 'audit-reuse':
        audit_reuse()
    elif args.action == 'audit-tool-holds':
        audit_tool_holds()
    else:
        report()
