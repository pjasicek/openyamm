"""Rebuild the frozen restoration run index without accepting or changing queue work."""
import hashlib
import html
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BATCH = HERE / 'chat_bundles/dense64_20260916'
RUN = BATCH / 'runs/finish_159_20260921'


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    scope = read(RUN / 'scope.json')
    state = read(HERE / 'checkpoint/state.json')
    assessment_path = RUN / 'assessments.json'
    assessments = {(a['bundle'], a['sheet']): a for a in read(assessment_path)['sheets']} if assessment_path.exists() else {}
    repairs_path = RUN / 'repair_attempts.json'
    repairs = read(repairs_path)['attempts'] if repairs_path.exists() else []
    for repair in repairs:
        assert digest(Path(repair['raw'])) == repair['raw_sha256']
    rows, cells = [], []
    for job in scope['jobs']:
        folder = BATCH / job['bundle']
        manifest = read(folder / 'manifest.json')
        receipt_path = folder / 'outputs/progress.json'
        receipts = read(receipt_path if receipt_path.exists() else folder / 'progress.template.json')['sheets']
        for sheet in manifest['sheets']:
            sid = sheet['id']
            if sid not in job['remaining_sheets']:
                continue
            receipt = receipts[sid]
            layout_path = folder / sheet['layout']
            assert digest(layout_path) == sheet['layout_sha256']
            layout = read(layout_path)
            raw = receipt.get('raw_path')
            if raw:
                assert digest(folder / raw) == receipt['raw_sha256']
            row = dict(bundle=job['bundle'], sheet=sid, targets=len(sheet['cells']),
                       status=receipt['status'], raw_path=raw,
                       raw_sha256=receipt.get('raw_sha256'),
                       detail_review=receipt.get('restoration_detail_review'),
                       notes=receipt.get('notes', ''))
            assessment = assessments.get((job['bundle'], sid))
            if assessment:
                assert assessment['raw_sha256'] == row['raw_sha256']
            row['assessment'] = assessment
            row['reference_path'] = str(folder / sheet['reference'])
            row['raw_absolute_path'] = str(folder / raw) if raw else None
            rows.append(row)
            for cell in layout['cells']:
                member = cell['member']
                current = state['cells'].get(cell['id'], {})
                cells.append(dict(id=cell['id'], bundle=job['bundle'], sheet=sid, slot=cell['slot'],
                                  treatment=member['treatment'], cleanup=member['cleanup'],
                                  family=cell['job_contract']['family'], original_job=cell['original_job'],
                                  source_sha256=cell['source_sha256'], native_size=cell['native_size'],
                                  layout_sha256=sheet['layout_sha256'], raw_sha256=row['raw_sha256'],
                                  queue_status=current.get('status', 'externally_assigned'),
                                  queue_reason=current.get('reason'),
                                  review_status='pending_individual_review' if raw else receipt['status'],
                                  sheet_observation=row['notes']))
    assert len(rows) == scope['sheets'] == 159
    assert len(cells) == scope['targets'] == 4644
    assert len({c['id'] for c in cells}) == len(cells)
    counts = dict(returned=sum(bool(r['raw_path']) for r in rows),
                  returned_targets=sum(r['targets'] for r in rows if r['raw_path']),
                  unattempted=sum(r['status'] == 'unattempted' for r in rows),
                  in_progress=sum(r['status'] == 'in_progress' for r in rows),
                  failed=sum(r['status'] == 'failed' for r in rows),
                  accepted=sum(c['queue_status'] == 'accepted' for c in cells),
                  staged=sum(c['id'] in state['staged_targets'] for c in cells),
                  deferred=sum(c['queue_status'] == 'deferred' for c in cells),
                  explicit_sheet_repair_assessments=len(assessments),
                  rejected_repair_attempts=sum(r['disposition'] == 'rejected' for r in repairs))
    report = dict(updated_at=datetime.now(timezone.utc).isoformat(), **counts, sheets=rows)
    (RUN / 'progress.json').write_text(json.dumps(report, indent=2) + '\n')
    (RUN / 'review_index.json').write_text(json.dumps(dict(
        note='Sheet observations are not per-cell acceptance or completed repairs.',
        treatment_counts=dict(Counter(c['treatment'] for c in cells)),
        cleanup_counts=dict(Counter(c['cleanup'] for c in cells)), cells=cells), indent=2) + '\n')
    intro = (f"Raw returns: {counts['returned']}/159 sheets; {counts['returned_targets']}/4644 targets. "
             f"Failed submissions: {counts['failed']}. Accepted: {counts['accepted']}. Staged: {counts['staged']}.")
    table = []
    for row in rows:
        links = '<a href="' + html.escape(str(Path(row['reference_path']).relative_to(BATCH)), quote=True) + '">Native</a>'
        # The report lives two directories below the batch root.
        links = links.replace('href="', 'href="../../')
        if row['raw_path']:
            links += ' / <a href="../../' + html.escape(row['bundle'] + '/' + row['raw_path'], quote=True) + '">Raw</a>'
        table.append('<tr>' + ''.join('<td>' + html.escape(str(row[k] or '')) + '</td>'
                                    for k in ('bundle', 'sheet', 'targets', 'status', 'detail_review'))
                     + '<td>' + links + '</td><td>' + html.escape(row['notes']) + '</td></tr>')
    (RUN / 'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Restoration review</title>'
        '<style>body{font:16px sans-serif;max-width:1500px;margin:2em auto}td,th{padding:.6em;'
        'border:1px solid #aaa;vertical-align:top}table{border-collapse:collapse}</style>'
        '<h1>Frozen 159-sheet restoration run</h1><p>' + intro + '</p>'
        '<p>Detail pass is not acceptance. Classification and cleanup contracts are preserved by cell ID '
        'in <a href="review_index.json">review_index.json</a>. Individual registration, repairs and staging remain pending.</p>'
        '<p>Explicit <a href="assessments.json">sheet repair assessments</a> and '
        '<a href="repair_attempts.json">rejected repair attempts</a> retain hash-bound evidence.</p>'
        '<table><tr><th>Bundle</th><th>Sheet</th><th>Targets</th><th>Status</th><th>Detail</th>'
        '<th>Images</th><th>Observed defects and review notes</th></tr>' + ''.join(table) + '</table>')
    (RUN / 'STATUS.md').write_text('# Active restoration run\n\n' + intro + '\n\n'
        'User authorized completion, repair and isolated staging on 2026-09-21. Earlier stopped-by-user '
        'records are historical. This run remains incomplete.\n\n'
        'See [sheet observations](index.html) and [per-cell classification index](review_index.json). '
        'Detail passes do not accept artwork. No individual review is inferred from sheet-level notes.\n\n'
        f"Explicit sheet repair assessments: {len(assessments)}. Rejected repair attempts: {counts['rejected_repair_attempts']}. "
        'See [assessments](assessments.json) and [repair attempts](repair_attempts.json). '
        'The legacy pilot remains deferred after pixelation, registration and missing-background failures. '
        'Legacy-small-001/S008 returned no artwork after a tool moderation block. '
        'This is a retained review/repair set, not a ready-to-use asset export.\n')
    print(json.dumps(counts))


if __name__ == '__main__':
    main()
