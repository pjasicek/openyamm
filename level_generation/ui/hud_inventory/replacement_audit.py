"""Read-only replacement geometry checks for every original icon.

Technical checks do not approve visual quality. Unresolved extraction is reported, not
silently replaced by an assumed grid or stretched to fit the expected dimensions.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import json
import csv
import html
import os

import numpy as np
from PIL import Image

import registration
from second_pass import HERE, ROOT, OUT, digest, hash_file, queue_module, read, save


def inspect_masters():
    directory = Path(read(OUT / 'current.json')['snapshot'])
    masters = read(directory / 'masters.json')
    checked = {}
    for identifier, master in masters.items():
        raw = Path(master['raw'])
        expected = (master.get('execution_layout') or {}).get('canvas_size')
        authority = master['provenance']
        if not expected and master.get('layout'):
            authority = master['layout']
            expected = read(authority).get('reference_size')
        if not expected and master['kind'] == 'canonical_attempt':
            payload = read(master['provenance'])
            references = []
            for name, role in payload.get('reference_roles', {}).items():
                if 'EDIT TARGET' in role or role.startswith('Native source cells;'):
                    retained = payload.get('retained_references', {}).get(name)
                    references.append(retained['path'] if retained else name)
            if len(references) == 1 and Path(references[0]).is_file():
                authority = references[0]
                with Image.open(authority) as reference:
                    expected = list(reference.size)
        with Image.open(raw) as image:
            size = list(image.size)
            image.verify()
        error = abs((size[0] / size[1]) / (expected[0] / expected[1]) - 1) if expected else None
        checked[identifier] = dict(raw=str(raw), raw_size=size, expected_sheet_size=expected,
            raw_sha256=hash_file(raw), raw_hash_valid=hash_file(raw) == master['raw_sha256'],
            aspect_authority=authority, sheet_aspect_relative_error=error,
            status='sheet_aspect_unresolved' if error is None else
                   'sheet_aspect_flag' if error > 0.03 else 'sheet_aspect_guard_clear',
            note='Whole-sheet proportions only. This cannot prove individual slot sampling, internal proportions, '
                 'identity or absence of enlarged pixel blocks. A flag requires actual slot inspection.',
            visual_approval=False)
    save(OUT / 'master_geometry_audit.json', dict(summary=dict(Counter(m['status'] for m in checked.values())),
         masters=checked))
    return checked


def inspect_candidate(cell, path, q, provenance):
    member = q.members[cell][1]
    target = q.targets[member['target']]
    record = dict(path=str(path), provenance=provenance, visual_approval=False)
    if not path.is_file():
        return dict(record, status='missing_candidate')
    record['sha256'] = digest(path)
    try:
        with Image.open(path) as image:
            image.load()
            record.update(size=list(image.size), mode=image.mode, format=image.format,
                          required_x2=member['export_region'][2:])
            width, height = member['source_rect'][2:]
            record['aspect_relative_error'] = abs((image.width / image.height) / (width / height) - 1)
            record['exact_x2'] = list(image.size) == member['export_region'][2:]
            record['native_format_matches'] = path.suffix.lower() == Path(target['output_path']).suffix.lower()
            pixels = np.asarray(image.convert('RGBA'))
            record['alpha_range'] = [int(pixels[:, :, 3].min()), int(pixels[:, :, 3].max())]
            with Image.open(ROOT / member['source_path']) as source:
                x, y, width, height = member['source_rect']
                source = source.convert('RGBA').crop((x, y, x + width, y + height))
                record['exact_native_resample_matches'] = [name for name, method in
                    [('nearest', Image.Resampling.NEAREST), ('bilinear', Image.Resampling.BILINEAR),
                     ('bicubic', Image.Resampling.BICUBIC), ('lanczos', Image.Resampling.LANCZOS)]
                    if np.array_equal(pixels, np.asarray(source.resize(image.size, method)))]
        if record['exact_x2']:
            measured = registration.measurements(member, target, path)
            record['footprint'] = measured
            record['footprint_flags'] = {p: v['failures'] for p, v in measured['profiles'].items() if v['failures']}
        else:
            record['footprint_flags'] = {'dimensions': ['Not exact x2; no automatic stretch performed']}
        record['status'] = 'geometry_flag' if record['footprint_flags'] else 'geometry_guards_clear_not_visual_approval'
        record['pixelation_check'] = ('exact_resampling_detected_inspect_uniform_or_generated_role' if
            record['exact_native_resample_matches'] else 'no_exact_resample_match_visual_pixelation_check_still_required')
    except (OSError, ValueError, AssertionError) as error:
        record.update(status='unreadable_or_contract_changed', error=str(error))
    return record


def main():
    q = queue_module.Queue()
    state_hash = digest(q.state_path)
    inventory = read(OUT / 'inventory.json')
    master_checks = inspect_masters()
    by_target = defaultdict(list)
    for row in inventory['cells']:
        by_target[row['target_id']].append(row)
    results = []
    candidate_results = []
    for index, (target_id, rows) in enumerate(sorted(by_target.items())):
        target = q.targets[target_id]
        path = ROOT / target['source_path']
        result = dict(target_id=target_id, source_path=str(path), source_sha256=digest(path),
                      expected_native_size=target['native_size'], expected_x2=target['x2_size'],
                      profiles=target['compositing']['profiles'], cells=[], visual_approval=False)
        with Image.open(path) as source:
            source.load()
            result.update(actual_native_size=list(source.size), native_format=source.format,
                          native_mode=source.mode, source_hash_valid=result['source_sha256'] == target['source_sha256'],
                          native_dimensions_valid=list(source.size) == target['native_size'],
                          native_aspect_ratio=source.width / source.height,
                          x2_contract_valid=target['x2_size'] == [source.width * 2, source.height * 2])
        for row in rows:
            cell = row['cell_id']
            candidates = {}
            accepted = q.state['cells'].get(cell, {})
            if accepted.get('artifact'):
                candidates[accepted['artifact']] = 'canonical cell record'
            for historical in row['historical']:
                record = historical['record']
                candidate = record.get('extraction_path') or record.get('artifact') or record.get('candidate')
                if isinstance(candidate, str):
                    candidates[candidate] = historical['inventory']
            decision = OUT / 'decisions' / (cell + '.json')
            if decision.exists():
                reviewed = read(decision)
                candidates[reviewed['candidate']] = str(decision)
            records = [inspect_candidate(cell, Path(p), q, provenance) for p, provenance in candidates.items()]
            for record in records:
                record['cell_id'] = cell
                candidate_results.append(record)
            cell_result = dict(cell_id=cell, disposition=row['disposition'],
                               native_region=row['source_rect'], expected_x2=row['x2_size'],
                               retained_attempts=row['attempts'], candidate_checks=records,
                               explicit_second_pass_decision=str(decision) if decision.exists() else None,
                               replacement_ready=bool(q.accepted(cell)),
                               next_action=row['next_action'])
            cell_result['master_geometry_checks'] = {a: master_checks[a]['status'] for a in row['attempts']}
            if records:
                cell_result['technical_coverage'] = 'native_and_extracted_candidate_checked'
            elif row['attempts']:
                cell_result['technical_coverage'] = 'native_checked_raw_retained_extraction_unresolved'
            else:
                cell_result['technical_coverage'] = 'native_checked_no_independent_candidate'
            result['cells'].append(cell_result)
        results.append(result)
        if index % 1000 == 0:
            print(f'Checked {index + 1}/{len(by_target)} originals; {len(candidate_results)} extracted candidates', flush=True)
    cells = [cell for result in results for cell in result['cells']]
    summary = dict(timestamp=datetime.now(timezone.utc).isoformat(), original_targets_checked=len(results),
                   cells_accounted=len(cells), extracted_candidates_checked=len(candidate_results),
                   native_contract_errors=sum(not all(r[k] for k in ('source_hash_valid', 'native_dimensions_valid',
                       'x2_contract_valid')) for r in results),
                   technical_coverage=dict(Counter(c['technical_coverage'] for c in cells)),
                   candidate_statuses=dict(Counter(c['status'] for c in candidate_results)),
                   candidate_aspect_flags=sum(c.get('aspect_relative_error', 0) > 0.01 for c in candidate_results),
                   candidates_with_exact_native_resampling=sum(bool(c.get('exact_native_resample_matches'))
                                                               for c in candidate_results),
                   canonical_state_unchanged=digest(q.state_path) == state_hash,
                   all_originals_technically_accounted=True, all_artwork_visually_reviewed=False,
                   note='Correct canvas dimensions do not prove unwarped internal art or genuine restoration. '
                        'Unknown raw slot boundaries are unresolved, not inferred from the sheet ratio. '
                        'Footprint guards flag review needs, not automatic artistic rejection.')
    save(OUT / 'replacement_audit.json', dict(summary=summary, targets=results))
    publish(results, summary)
    print(json.dumps(summary, indent=2))


def publish(results, summary):
    """Expose technical findings without mixing them into visual approval counts."""
    def link(path, label):
        return '<a href="' + html.escape(os.path.relpath(path, OUT), quote=True) + '">' + html.escape(label) + '</a>'
    page = ['<!doctype html><meta charset="utf-8"><title>Original icon replacement audit</title>',
            '<style>body{font:15px sans-serif}td{padding:6px;vertical-align:top}tr:nth-child(even){background:#eee}'
            'input{width:80%;padding:10px}</style><h1>Every-original technical replacement audit</h1>',
            '<p>This is complete technical accounting, not completed visual review or runtime readiness. '
            'A correctly sized canvas can contain warped, pixelated, clipped or misplaced artwork.</p>',
            '<pre>' + html.escape(json.dumps(summary, indent=2)) + '</pre>',
            '<p>' + link(OUT / 'index.html', 'Visual review ledger') + ' · ' +
            link(OUT / 'replacement_audit.json', 'Full measured evidence') + ' · ' +
            link(OUT / 'replacement_audit.csv', 'CSV') + ' · ' +
            link(OUT / 'master_geometry_audit.json', 'Whole-master aspect checks') + '</p>',
            '<input id="filter" placeholder="Search original, disposition or check status">',
            '<table><thead><tr><th>Original</th><th>Native → required x2</th><th>Technical coverage</th>'
            '<th>Candidate findings</th><th>Visual evidence / next action</th></tr></thead><tbody>']
    csv_rows = []
    for result in results:
        candidates = [c for cell in result['cells'] for c in cell['candidate_checks']]
        statuses = sorted({cell['technical_coverage'] for cell in result['cells']})
        dispositions = sorted({cell['disposition'] for cell in result['cells']})
        flags = sum(c['status'] != 'geometry_guards_clear_not_visual_approval' for c in candidates)
        reviewed = [c for c in result['cells'] if c['explicit_second_pass_decision']]
        csv_rows.append(dict(target_id=result['target_id'], source=result['source_path'],
            native_width=result['actual_native_size'][0], native_height=result['actual_native_size'][1],
            x2_width=result['expected_x2'][0], x2_height=result['expected_x2'][1],
            disposition=' | '.join(dispositions), technical_coverage=' | '.join(statuses),
            candidate_checks=len(candidates), candidate_flags=flags,
            individually_reviewed_cells=len(reviewed), visual_complete=False))
        finding_links = [link(c['path'], c['status']) for c in candidates]
        review_links = [link(c['explicit_second_pass_decision'], c['cell_id']) for c in reviewed]
        actions = sorted({c['next_action'] for c in result['cells']})
        page.append('<tr><td>' + html.escape(result['target_id']) + '<br>' +
                    link(result['source_path'], 'native source') + '</td><td>' +
                    html.escape(str(result['actual_native_size']) + ' → ' + str(result['expected_x2'])) +
                    '</td><td>' + html.escape(' | '.join(statuses + dispositions)) + '</td><td>' +
                    '<br>'.join(finding_links) + '</td><td>' + '<br>'.join(review_links) + '<br>' +
                    '<br>'.join(html.escape(a) for a in actions) + '</td></tr>')
    page.append('</tbody></table><script>filter.oninput=()=>{let q=filter.value.toLowerCase();'
                'document.querySelectorAll("tbody tr").forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))};</script>')
    (OUT / 'replacement_index.html').write_text('\n'.join(page))
    with (OUT / 'replacement_audit.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)


if __name__ == '__main__':
    main()
