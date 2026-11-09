"""Classify ungenerated icon targets and pack dependency-aware native references. Never generates art."""
import argparse
from collections import Counter, defaultdict
import fcntl
import html
import json
import math
from pathlib import Path
import shutil
import zipfile

from PIL import Image

from dense_bundles import HERE, ROOT, OUTPUT_PIXELS, art_mode, experiment_ids, grid_for, read, save, sha
from freeze_targets import rendered


PORTRAITS = {'player_portrait_frames', 'npc_portrait_family'}
SINGLES = {'ui_background', 'spellbook_page', 'map_presentation'}
PRIOR_REJECTIONS = {f'engine--icons--maleh{i:02d}.bmp' for i in range(1, 7)}


def history(jobs, state):
    """Reconcile queue attempts and dense receipts, retaining errors separately from generated art."""
    generated, blocked = set(), set()
    evidence = []
    for attempt in state['attempts']:
        payload = read(Path(attempt['payload']))
        assert Path(attempt['raw']).is_file(), 'Missing recorded raw master'
        generated.update(payload.get('selected_cells', [m['id'] for jid in attempt.get('jobs', [attempt['job']])
                                                      for m in jobs[jid]['members']]))
    for path in sorted((HERE / 'chat_bundles/dense64_20260916').glob('dense64_*/outputs/progress.json')):
        folder = path.parent.parent
        receipts = read(path)['sheets']
        evidence.append(dict(path=str(path), sha256=sha(path)))
        for sheet in read(folder / 'manifest.json')['sheets']:
            receipt = receipts[sheet['id']]
            if receipt.get('raw_path'):
                raw = folder / receipt['raw_path']
                assert raw.is_file() and sha(raw) == receipt['raw_sha256']
                generated.update(sheet['cells'])
            elif receipt['status'] in ('failed', 'in_progress', 'submission_uncertain'):
                blocked.update(sheet['cells'])
    # Any submitted call without a retained return is uncertain, including interruptions.
    for path in sorted((HERE / 'chat_bundles').glob('*/runs/*/B*.submission.json')):
        if path.with_name(path.name.replace('.submission.json', '.return.json')).exists():
            continue
        submission = read(path)
        payload = read(Path(submission['payload']))
        blocked.update(payload['selected_cells'])
        evidence.append(dict(path=str(path), sha256=sha(path)))
    return generated, blocked, evidence


def reuse_key(target):
    return (target['namespace'], target['treatment'], target['source_sha256'],
            tuple(target['native_size']), target['compositing']['cleanup'],
            tuple(sorted((p, f['rgba_sha256']) for p, f in target['compositing']['fingerprints'].items())))


def classify():
    targets = {t['id']: t for t in read(HERE / 'expected_targets.json')['targets']}
    jobs = {j['id']: j for j in read(HERE / 'jobs.json')['jobs']}
    by_target = defaultdict(list)
    for job in jobs.values():
        for member in job['members']:
            by_target[member['target']].append((job, member))
    state_hash = sha(HERE / 'checkpoint/state.json')
    state = read(HERE / 'checkpoint/state.json')
    generated, blocked, evidence = history(jobs, state)
    generated_targets = {m['target'] for job in jobs.values() for m in job['members'] if m['id'] in generated}
    scope = [t for t in targets.values() if '/icons/' in t['source_path'] and t['id'] not in generated_targets]
    experiments = experiment_ids()
    retained = generated_targets | experiments | {c for c, v in state['cells'].items() if v['status'] == 'accepted'}
    donors = {}
    for tid in sorted(retained):
        if tid in targets:
            donors.setdefault(reuse_key(targets[tid]), tid)
    rows, selected = [], []
    for target in sorted(scope, key=lambda t: t['id']):
        tid = target['id']
        assert sha(ROOT / target['source_path']) == target['source_sha256'], f'Source drift: {tid}'
        cells = by_target[tid]
        status = state['cells'].get(tid, {}).get('status')
        row = dict(id=tid, source_path=target['source_path'], source_sha256=target['source_sha256'],
                   namespace=target['namespace'], treatment=target['treatment'],
                   cleanup=target['compositing']['cleanup'], native_size=target['native_size'],
                   x2_size=target['x2_size'], cells=[m['id'] for _, m in cells])
        if tid in state.get('user_excluded_targets', {}):
            row.update(disposition='user_excluded_keep_native', evidence=state['user_excluded_targets'][tid])
        elif status == 'accepted':
            row.update(disposition='already_accepted_reuse', evidence=state['cells'][tid])
        elif tid in experiments:
            row.update(disposition='retained_experiment_review', evidence='experiments/; no duplicate generation')
        elif tid in PRIOR_REJECTIONS or any(m['id'] in blocked for _, m in cells):
            row.update(disposition='blocked_prior_submission', evidence='Existing failed/uncertain receipt; do not retry moderation blocks')
        elif any(j['id'] in state.get('claims', {}) for j, _ in cells):
            row.update(disposition='existing_claim', evidence=[j['id'] for j, _ in cells if j['id'] in state['claims']])
        elif status == 'deferred':
            row.update(disposition='deferred_existing_review', evidence=state['cells'][tid])
        elif (target['treatment'] in {'inventory_items', 'legacy_ui_art', 'npc_portrait_family'}
              and len(cells) == 1 and all(d['kind'] == 'accepted_treatment_pilot' for d in cells[0][0]['dependencies'])
              and reuse_key(target) in donors):
            row.update(disposition='reuse_candidate', donor=donors[reuse_key(target)],
                       evidence='Identical source bytes, namespace, treatment, dimensions and every consumer profile. Requires reviewed donor/reuse acceptance.')
        else:
            row['disposition'] = 'prepared_work'
            for job, member in cells:
                selected.append(dict(target=target, job=job, member=member))
            if target['treatment'] in {'inventory_items', 'legacy_ui_art', 'npc_portrait_family'}:
                donors.setdefault(reuse_key(target), tid)
        rows.append(row)
    return targets, jobs, state, state_hash, rows, selected, evidence


def geometry(entries):
    count = len(entries)
    width = max(e['member']['source_rect'][2] for e in entries)
    height = max(e['member']['source_rect'][3] for e in entries)
    if entries[0]['target']['treatment'] != 'spell_icon_pair':
        return grid_for(count, width, height)
    # A normal/hover pair must share a row, not wrap across the row boundary.
    choices = []
    for columns in range(2, count + 1, 2):
        rows = math.ceil(count / columns)
        w, h = columns * (width + 4), rows * (height + 4)
        w, h = max(w, math.ceil(h / 2)), max(h, math.ceil(w / 2))
        scale = math.sqrt(OUTPUT_PIXELS / (w * h))
        if scale >= 2.15:
            choices.append(((columns * rows - count) * .25 + abs(math.log(w / h)), columns, rows, w, h, scale))
    if not choices:
        return None
    _, columns, rows, w, h, scale = min(choices)
    return dict(columns=columns, rows=rows, native_sheet_size=[w, h], reference_size=[2 * w, 2 * h],
                predicted_sampling=scale, minimum_output=[2 * w, 2 * h], cell_size_native=[width + 4, height + 4])


def pack(entries):
    groups = defaultdict(list)
    for entry in entries:
        job, member, target = entry['job'], entry['member'], entry['target']
        # Preserve frozen family/seed ownership, modes and namespace. Do not combine unrelated body types.
        key = (job['id'], target['namespace'], member['cleanup'], tuple(target['compositing']['profiles']))
        if target['treatment'] == 'spell_icon_pair':
            key = (job['id'], target['namespace'], 'paired_page_states', ())
        groups[key].append(entry)
    sheets, deterministic = [], []
    for key, items in sorted(groups.items()):
        items.sort(key=lambda e: (e['target'].get('frame', {}).get('ordinal', 0) if e['target'].get('frame') else 0,
                                  e['member']['id']))
        if items[0]['member']['method'] != 'imagegen_sheet':
            deterministic.append(dict(job=key[0], cells=[e['member']['id'] for e in items],
                                      method=items[0]['member']['method']))
            continue
        kind = items[0]['target']['treatment']
        # Adjacent spell states are indivisible; retain order from the authoritative job.
        if kind == 'spell_icon_pair':
            order = {m['id']: i for i, m in enumerate(items[0]['job']['members'])}
            items.sort(key=lambda e: order[e['member']['id']])
            assert len(items) % 2 == 0, 'Partial retained spell pair needs explicit reconciliation'
            units = [items[i:i + 2] for i in range(0, len(items), 2)]
        else:
            units = [[e] for e in items]
        cap = 1 if kind in SINGLES else 12 if kind == 'spell_icon_pair' else 64
        current = []
        for unit in units:
            proposed = current + unit
            if current and (len(proposed) > cap or geometry(proposed) is None):
                sheets.append(dict(entries=current, grid=geometry(current)))
                current = []
            current += unit
            if geometry(current) is None:
                # Never shrink a large canvas to fit the observed output budget.
                sheets.append(dict(entries=current, grid=None, requires_large_master=True))
                current = []
        if current:
            sheets.append(dict(entries=current, grid=geometry(current)))
    # Pack compatible whole units across frozen jobs without changing their ownership.
    # Equipment/body variants, animation seeds, pages and atlas regions keep specialized groups.
    combined, cohorts = [], defaultdict(list)
    for sheet in sheets:
        entry = sheet['entries'][0]
        job, target = entry['job'], entry['target']
        same_character = target['treatment'] == 'player_portrait_frames'
        if (not same_character and (target['treatment'] not in {'inventory_items', 'npc_portrait_family', 'legacy_ui_art',
                                        'ui_state_set', 'ui_frame_or_panel'}
                or any(d['kind'] != 'accepted_treatment_pilot' for d in job['dependencies']))
                or sheet.get('requires_large_master')):
            combined.append(sheet)
            continue
        width = max(e['member']['source_rect'][2] for e in sheet['entries'])
        height = max(e['member']['source_rect'][3] for e in sheet['entries'])
        profiles = tuple(target['compositing']['profiles'])
        fingerprints = target['compositing']['fingerprints'].values()
        if art_mode(target) == 'opaque' and len({f['rgba_sha256'] for f in fingerprints}) == 1:
            profiles = ()  # Identical decoded pixels across consumers; retain individual contracts.
        key = (target['namespace'], target['treatment'], art_mode(target),
               profiles, json.dumps(job['dependencies'], sort_keys=True) if not same_character else '',
               math.ceil(width / 64), math.ceil(height / 64))
        cohorts[key].append(sheet)
    for _, units in sorted(cohorts.items()):
        # Largest whole groups first; fill compatible existing sheets before opening another.
        bins = []
        for unit in sorted(units, key=lambda s: -len(s['entries'])):
            for current in bins:
                proposed = current + unit['entries']
                if len(proposed) <= 64 and geometry(proposed) is not None:
                    current.extend(unit['entries'])
                    break
            else:
                bins.append(list(unit['entries']))
        combined.extend(dict(entries=current, grid=geometry(current)) for current in bins)
    return combined, deterministic


def build(output):
    targets, jobs, state, state_hash, rows, selected, receipts = classify()
    output.mkdir(parents=True, exist_ok=False)
    save(output / 'state_before.json', state)
    sheets, deterministic = pack(selected)
    selected_jobs = {e['job']['id'] for e in selected}
    target_ids = {r['id'] for r in rows}
    save(output / 'contracts.json', dict(targets={i: targets[i] for i in target_ids}, jobs={i: jobs[i] for i in selected_jobs}))
    shutil.copy2(HERE / 'BATCHING_DENSE64.md', output / 'BATCHING_DENSE64.md')
    shutil.copy2(HERE / 'MATTE_AND_FITTING.md', output / 'MATTE_AND_FITTING.md')
    detail = (HERE / 'chat_bundles/dense64_20260916/RESTORATION_DETAIL_V2.txt').read_text()
    records = []
    for index, sheet in enumerate(sheets, 1):
        bid = f'B{index:04d}'
        folder = output / 'batches' / bid
        folder.mkdir(parents=True)
        entries, grid = sheet['entries'], sheet['grid']
        if grid is None:
            assert len(entries) == 1, 'Oversized pair requires specialized preparation'
            w, h = entries[0]['member']['source_rect'][2:]
            nw, nh = max(w, math.ceil(h / 2)), max(h, math.ceil(w / 2))
            grid = dict(columns=1, rows=1, reference_size=[2 * nw, 2 * nh],
                        cell_size_native=[nw, nh], predicted_sampling=math.sqrt(OUTPUT_PIXELS / (nw * nh)))
        reference = Image.new('RGBA', tuple(grid['reference_size']), '#ff00ff')
        cells = []
        for slot, entry in enumerate(entries):
            t, m = entry['target'], entry['member']
            original = output / 'sources' / t['id']
            if not original.exists():
                original.parent.mkdir(exist_ok=True)
                shutil.copy2(ROOT / m['source_path'], original)
            with Image.open(original) as source:
                native = source.convert('RGBA') if art_mode(t) == 'indexed_keys' else rendered(source, t['compositing']['profiles'][0])
                x, y, w, h = m['source_rect']
                native = native.crop((x, y, x + w, y + h))
            cw, ch = grid['cell_size_native']
            rect = [slot % grid['columns'] * cw * 2 + cw - w,
                    slot // grid['columns'] * ch * 2 + ch - h, w * 2, h * 2]
            reference.alpha_composite(native.resize((w * 2, h * 2), Image.Resampling.NEAREST), tuple(rect[:2]))
            cells.append(dict(id=m['id'], target=m['target'], original_job=entry['job']['id'],
                              source_rect=m['source_rect'], source_sha256=m['source_sha256'],
                              reference_rect=rect, x2_size=m['export_region'][2:], cleanup=m['cleanup']))
        reference.convert('RGB').save(folder / 'reference.png')
        job = entries[0]['job']
        kind = entries[0]['target']['treatment']
        native_portrait = kind in PORTRAITS
        mode = art_mode(entries[0]['target'])
        background = dict(opaque='Retain complete opaque backgrounds edge to edge inside every native canvas.',
                          cutout='Keep native opaque artwork, including any opaque panel/tab behind the subject. Only native transparent regions and sheet gutters use uniform opaque RGB(255,0,255). Do not remove panel backgrounds.',
                          indexed_keys='Preserve every distinct original indexed/key-color region and its boundary; never flatten different consumer masks to one alpha interpretation.')[mode]
        if kind == 'spell_icon_pair':
            background = ('These are inseparable page-backed state pairs. Preserve each cell\'s own opacity/key '
                          'contract and compose against its accepted page crop supplied at execution. '
                          'Do not replace opaque page pixels with transparency or invent rectangular paper backgrounds.')
        prompt = (detail + '\n\nRestore image 1 in place. It is the packed native EDIT TARGET. '
                  f'Exactly {grid["columns"]} columns, {grid["rows"]} rows, {len(cells)} occupied cells in row-major order. '
                  'Empty slots and gutters remain flat magenta. No labels, extra ornaments, cell merging or rearrangement. '
                  + background + '\nPreserve the full canvas, margins, all states, poses, symbols, native palette, '
                  'frame order and logical anchors. Do not turn edge-on poses into front views or brighten disabled states. '
                  'Keep at least two actual generated pixels per native pixel in both axes for EVERY cell. '
                  f'Retain sheet aspect {grid["reference_size"][0]}:{grid["reference_size"][1]}. '
                  'Render new continuous detail; reject enlarged source pixels, mosaic shading, blur-only output and stepped curves. '
                  'Inspect the original master at 1:1 and exact x2 extraction. Dimensions alone do not prove quality.\n'
                  'Accepted seeds/page crops supplied at execution are supporting references, not extra output cells. '
                  'Retain their identity, material and page substrate; opaque page-backed icons must use the accepted page pixels.\n'
                  + '\n'.join(f'{i + 1}. {c["id"]}: native region {c["source_rect"]}; full output x2 {c["x2_size"]}; '
                              f'reference rectangle {c["reference_rect"]}; cleanup {c["cleanup"]}.' for i, c in enumerate(cells)))
        (folder / 'prompt.template.txt').write_text(prompt + '\n')
        spec = dict(id=bid, schema='openyamm.remaining-icons.batch.v1', status='prepared_only',
                    treatment=kind, namespace=entries[0]['target']['namespace'], group=job['family'],
                    jobs=sorted({e['job']['id'] for e in entries}), cells=cells, grid=grid,
                    dependencies=[json.loads(d) for d in sorted({json.dumps(d, sort_keys=True)
                        for e in entries for d in e['job']['dependencies']})],
                    dependency_policy='native_portrait_first_pass' if native_portrait else 'accepted_dependencies_required',
                    requires_large_master=sheet.get('requires_large_master', False),
                    reference='reference.png', reference_sha256=sha(folder / 'reference.png'),
                    prompt='prompt.template.txt', prompt_sha256=sha(folder / 'prompt.template.txt'),
                    instruction='Use prepare_remaining_icons.py payload to recheck ownership/history and bind current dependencies before generation.')
        save(folder / 'manifest.json', spec)
        records.append(dict(id=bid, treatment=kind, cells=[c['id'] for c in cells],
                            targets=sorted({c['target'] for c in cells}), manifest=f'batches/{bid}/manifest.json',
                            manifest_sha256=sha(folder / 'manifest.json'),
                            predicted_sampling=grid['predicted_sampling'], requires_large_master=spec['requires_large_master']))
    for row in rows:
        row['batches'] = [r['id'] for r in records if row['id'] in r['targets']]
        row['deterministic_jobs'] = [d['job'] for d in deterministic if set(d['cells']) & set(row['cells'])]
        assert row['disposition'] != 'prepared_work' or row['batches'] or row['deterministic_jobs']
    summary = dict(scope_targets=len(rows), dispositions=dict(Counter(r['disposition'] for r in rows)),
                   treatments=dict(Counter(r['treatment'] for r in rows)),
                   packed_sheets=len(records), packed_cells=sum(len(r['cells']) for r in records),
                   large_master_sheets=sum(r['requires_large_master'] for r in records),
                   deterministic_jobs=len(deterministic), deterministic_cells=sum(len(d['cells']) for d in deterministic),
                   maximum_cells=max(len(r['cells']) for r in records), generation_calls=0)
    by_cell = {cell: r['id'] for r in records for cell in r['cells']}
    member_ids = defaultdict(list)
    for job in jobs.values():
        for m in job['members']:
            member_ids[m['target']].append(m['id'])
    for record in records:
        spec = read(output / record['manifest'])
        required = set()
        if spec['dependency_policy'] != 'native_portrait_first_pass':
            for dep in spec['dependencies']:
                if 'job' in dep:
                    required.update(m['id'] for m in jobs[dep['job']]['members'])
                else:
                    required.update(member_ids[dep['target']])
        record['required_cells'] = sorted(required)
        pending = {c for c in required if state['cells'].get(c, {}).get('status') != 'accepted'}
        record['dependency_batches'] = sorted({by_cell[c] for c in pending if c in by_cell})
        record['external_review_dependencies'] = sorted(pending - set(by_cell))
        record['snapshot_ready'] = not pending and not record['requires_large_master']
    order, resolved = [], set()
    while len(order) < len(records):
        ready = [r for r in records if r['id'] not in resolved and set(r['dependency_batches']) <= resolved]
        assert ready, 'Batch dependency cycle'
        for record in ready:
            order.append(record['id'])
            resolved.add(record['id'])
    summary['snapshot_ready_sheets'] = sum(r['snapshot_ready'] for r in records)
    catalogue = dict(schema='openyamm.remaining-icons.v1', source_state_sha256=state_hash,
                     jobs_sha256=sha(HERE / 'jobs.json'), targets_sha256=sha(HERE / 'expected_targets.json'),
                     contracts_sha256=sha(output / 'contracts.json'), receipt_evidence=receipts,
                     summary=summary, scope=rows, batches=records, deterministic=deterministic,
                     execution_order=order)
    save(output / 'catalogue.json', catalogue)
    save(output / 'summary.json', summary)
    work = ['# Ordered work batches', '',
            'Preparation only. Dependencies must be accepted, not merely generated. Read README.md first. '
            'Snapshot readiness is rechecked by the payload command. IDs below are in dependency order.', '',
            '| Batch | Cells | State | Earlier batches | External cells needing acceptance |',
            '| --- | ---: | --- | --- | ---: |']
    by_id = {r['id']: r for r in records}
    for bid in order:
        r = by_id[bid]
        status = 'larger master needed' if r['requires_large_master'] else 'ready for payload check' if r['snapshot_ready'] else 'awaiting dependencies'
        work.append(f'| [{bid}](batches/{bid}/manifest.json) | {len(r["cells"])} | {status} | '
                    + ', '.join(r['dependency_batches']) + f' | {len(r["external_review_dependencies"])} |')
    (output / 'WORK_JOBS.md').write_text('\n'.join(work) + '\n')
    lines = ['# Remaining icon work — 2026-09-22', '',
             'Preparation only. No generated or accepted artwork is produced by this package.', '',
             'All targets from the previously reported count are accounted for in catalogue.json; retained experiments, '
             'accepted reuse, donor candidates, existing claims and blocked submissions are not duplicate generation jobs.', '',
             '## Counts', '', '```json', __import__('json').dumps(summary, indent=2), '```', '',
             '## Execution', '',
             'Use `python3 level_generation/ui/hud_inventory/prepare_remaining_icons.py payload ' + str(output) + ' '
             + next(r['id'] for r in records if r['snapshot_ready']) + '`.',
             'The command refuses unresolved seeds/pages, occupied work, retained attempts and undersized-master plans. '
             'It emits exact tool arguments and a queue-compatible payload; it never calls imagegen. '
             'Inspect every supplied reference before a future authorized call. Use queue.py record with the returned execution_id. '
             'Keep the unchanged raw, exact prompt and hashes; accept/stage only after actual per-cell review.', '',
             'Follow batch dependencies in contracts.json: accept treatment pilots and family seeds first; '
             'spell pairs require actual accepted page crops. Portrait first passes use same-character native seed context; '
             'follower acceptance still needs the accepted identity. Preserve body types and state/animation groups.', '',
             'Two oversized whole-background plans need a proven larger output budget. Do not shrink inputs or '
             'upsample undersized returns. Atlas glyph/uniform regions use the existing deterministic queue recipes, '
             'then reconstruct the complete atlas. Reuse candidates require donor acceptance and consumer review. '
             'Blocked moderation submissions remain recorded and must not be retried or rephrased to bypass the block.', '',
             'See [gallery](index.html), [catalogue](catalogue.json), [batching policy](BATCHING_DENSE64.md) '
             ', [ordered work](WORK_JOBS.md) and [fitting/cleanup](MATTE_AND_FITTING.md).', '',
             '| Sheet | Treatment | Cells | Predicted sampling |', '| --- | --- | ---: | ---: |']
    cards = []
    for record in records:
        bid = record['id']
        lines.append(f'| [{bid}](batches/{bid}/manifest.json) | {record["treatment"]} | {len(record["cells"])} | {record["predicted_sampling"]:.2f} |')
        cards.append(f'<article><a href="batches/{bid}/manifest.json">{bid}</a> '
                     f'{html.escape(record["treatment"])} — {len(record["cells"])} cells'
                     f'<a href="batches/{bid}/reference.png"><img loading="lazy" src="batches/{bid}/reference.png"></a></article>')
    (output / 'README.md').write_text('\n'.join(lines) + '\n')
    (output / 'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Remaining icon batches</title>'
        '<style>body{font:16px sans-serif;background:#222;color:#eee}main{display:flex;flex-wrap:wrap}'
        'article{width:300px;padding:10px}img{display:block;max-width:290px;max-height:260px}a{color:#9df}</style>'
        '<h1>Prepared native references — not restored artwork</h1><p>Dependency gates apply before execution. '
        'See README.md and catalogue.json for every target disposition.</p><main>' + ''.join(cards) + '</main>')
    assert sha(HERE / 'checkpoint/state.json') == state_hash, 'Queue changed during preparation; reconcile before reservation'
    return summary


def validate(output):
    catalogue = read(output / 'catalogue.json')
    assert sha(output / 'contracts.json') == catalogue['contracts_sha256']
    contracts = read(output / 'contracts.json')
    seen = set()
    for record in catalogue['batches']:
        path = output / record['manifest']
        assert sha(path) == record['manifest_sha256']
        batch = read(path)
        for field in ('reference', 'prompt'):
            assert sha(path.parent / batch[field]) == batch[field + '_sha256']
        with Image.open(path.parent / batch['reference']) as image:
            assert list(image.size) == batch['grid']['reference_size']
        assert 1 <= len(batch['cells']) <= 64
        assert batch['requires_large_master'] or batch['grid']['predicted_sampling'] >= 2.15
        for cell in batch['cells']:
            assert cell['id'] not in seen, 'Duplicate generation assignment'
            seen.add(cell['id'])
            x, y, w, h = cell['reference_rect']
            assert [w, h] == [v * 2 for v in cell['source_rect'][2:]] == cell['x2_size']
            assert x >= 0 and y >= 0 and x + w <= batch['grid']['reference_size'][0] and y + h <= batch['grid']['reference_size'][1]
            assert sha(output / 'sources' / cell['target']) == cell['source_sha256']
            assert sha(ROOT / contracts['targets'][cell['target']]['source_path']) == cell['source_sha256']
    for row in catalogue['scope']:
        if row['disposition'] == 'prepared_work':
            deterministic = {c for d in catalogue['deterministic'] for c in d['cells']}
            assert set(row['cells']) <= seen | deterministic
        else:
            assert not set(row['cells']) & seen
    return dict(validated=True, **catalogue['summary'])


def reserve(output):
    catalogue = read(output / 'catalogue.json')
    with (HERE / 'checkpoint/state.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = HERE / 'checkpoint/state.json'
        assert sha(path) == catalogue['source_state_sha256'], 'Queue changed; reconcile reservation explicitly'
        state = read(path)
        changes = []
        for record in catalogue['batches']:
            for cell in record['cells']:
                assert cell not in state['cells']
                previous = state['external_assignments'].get(cell)
                assert not previous or previous['status'] == 'assigned'
                replacement = dict(bundle=output.name, batch_set=str(output), dense_sheet=record['id'],
                                   manifest=str(output / record['manifest']), manifest_sha256=record['manifest_sha256'],
                                   status='assigned', generation_policy='dependency_aware_remaining_icons')
                changes.append(dict(cell=cell, previous=previous, replacement=replacement,
                                    reason='user_requested_remaining_icon_packing_20260922'))
                state['external_assignments'][cell] = replacement
        state['external_assignment_history'].extend(changes)
        save(output / 'assignment_history.json', changes)
        temporary = path.with_suffix('.remaining.tmp')
        save(temporary, state)
        temporary.replace(path)
        save(output / 'reservation.json', dict(assigned=len(changes), before_sha256=catalogue['source_state_sha256'],
                                              after_sha256=sha(path)))
    return dict(assigned=len(changes))


def payload(output, bid):
    # Import by explicit location: Python's standard queue module is unrelated.
    from review_dense_sheet import queue_module
    import uuid
    catalogue = read(output / 'catalogue.json')
    record = next(b for b in catalogue['batches'] if b['id'] == bid)
    path = output / record['manifest']
    assert sha(path) == record['manifest_sha256']
    batch = read(path)
    assert not batch['requires_large_master'], 'Needs a demonstrated larger master budget; no upsampling workaround'
    q = queue_module.Queue()
    generated, blocked, _ = history(q.jobs, q.state)
    for c in batch['cells']:
        assert c['target'] not in q.state.get('user_excluded_targets', {}), 'User excluded target; keep native for now'
        assert c['id'] not in generated | blocked | experiment_ids() | PRIOR_REJECTIONS, 'Retained/blocked work; reconcile instead of resubmitting'
        assert c['id'] not in q.state['cells'], 'Existing review/acceptance; reconcile before resubmission'
        assert c['original_job'] not in q.state.get('claims', {}), 'Existing claim'
        assignment = q.state.get('external_assignments', {}).get(c['id'])
        assert assignment and assignment['manifest_sha256'] == record['manifest_sha256'], 'Reserve this package before execution'
        assert sha(ROOT / q.members[c['id']][1]['source_path']) == c['source_sha256']
    execution_id = 'remaining-' + bid + '-' + uuid.uuid4().hex
    folder = q.payload_root / execution_id
    folder.mkdir(parents=True)
    reference = path.parent / batch['reference']
    assert sha(reference) == batch['reference_sha256']
    prompt_path = path.parent / batch['prompt']
    assert sha(prompt_path) == batch['prompt_sha256']
    refs, deps, native_identity = [str(reference)], {}, {}
    roles = {str(reference): 'EDIT TARGET: packed native cells; preserve every recorded slot and full canvas.'}
    page_crops, reference_layouts = [], {}
    policy = None
    if batch['dependency_policy'] == 'native_portrait_first_pass':
        policy = ('external_portrait_native_identity_first_pass' if batch['treatment'] == 'player_portrait_frames'
                  else 'independent_external_portrait_first_pass')
        from dense_bundles import identity_context
        entries = [dict(job=q.jobs[c['original_job']], target=q.targets[c['target']]) for c in batch['cells']]
        for ref in identity_context(entries, q.jobs, folder):
            name = str(folder / ref['path'])
            refs.append(name)
            roles[name] = 'Original same-character identity context only; do not output these seed cells or replace target expressions.'
        for j in batch['jobs']:
            native_identity.update(q.native_identity_sources(q.jobs[j]))
    else:
        for job_id in batch['jobs']:
            assert not q.blockers(q.jobs[job_id]), f'Accept dependencies first: {q.blockers(q.jobs[job_id])}'
            support = q.payload(job_id)
            deps.update(support['dependency_cells'])
            page_crops.extend(support['page_crops'])
            for ref, role in support['reference_roles'].items():
                if role.startswith(('Accepted', 'One accepted', 'Full native atlas')):
                    dest = folder / ('support-' + str(len(refs)) + Path(ref).suffix)
                    shutil.copy2(ref, dest)
                    refs.append(str(dest))
                    roles[str(dest)] = role
                    if ref in support['reference_layouts']:
                        reference_layouts[str(dest)] = support['reference_layouts'][ref]
    prompt = prompt_path.read_text() + '\nReference roles:\n' + json.dumps(roles, sort_keys=True)
    if page_crops:
        prompt += '\nAccepted page crop registration:\n' + json.dumps(page_crops, sort_keys=True)
    result = dict(job=batch['jobs'][0], jobs=batch['jobs'], selected_cells=[c['id'] for c in batch['cells']],
                  prompt=prompt, source_hashes={c['id']: c['source_sha256'] for c in batch['cells']},
                  reference_hashes={p: sha(Path(p)) for p in refs}, dependency_cells=deps,
                  reference_roles=roles, page_crops=page_crops, reference_layouts=reference_layouts,
                  layout_sha256=q.state.get('layout_revision', {}).get('sha256'),
                  execution_layout=dict(canvas_size=batch['grid']['reference_size'],
                                        cell_rects={c['id']: c['reference_rect'] for c in batch['cells']}),
                  external_return=dict(bundle=output.name, sheet=bid, manifest_sha256=record['manifest_sha256']),
                  tool_args=dict(prompt=prompt, referenced_image_paths=refs))
    if policy:
        result.update(dependency_policy=policy, native_identity_sources=native_identity)
    save(folder / 'payload.json', result)
    (folder / 'submitted_prompt.txt').write_text(result['prompt'])
    return dict(execution_id=execution_id, payload=str(folder / 'payload.json'), tool_args=result['tool_args'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['build', 'validate', 'reserve', 'payload', 'archive'])
    parser.add_argument('output', type=Path)
    parser.add_argument('batch', nargs='?')
    args = parser.parse_args()
    root = args.output.resolve()
    if args.action == 'archive':
        archive_path = root.with_suffix('.zip')
        with zipfile.ZipFile(archive_path, 'x', zipfile.ZIP_DEFLATED) as archive:
            for f in sorted(root.rglob('*')):
                if f.is_file():
                    archive.write(f, f.relative_to(root))
        result = dict(archive=str(archive_path), sha256=sha(archive_path))
    else:
        result = payload(root, args.batch) if args.action == 'payload' else globals()[args.action](root)
    print(__import__('json').dumps(result, indent=2))
