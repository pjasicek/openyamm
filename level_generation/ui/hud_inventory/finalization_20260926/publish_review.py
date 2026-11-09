"""Publish the accepted slice without modifying the original browser capture."""
import copy
import json
import os
from pathlib import Path

OUT = Path(__file__).resolve().parent
REVIEW = OUT.parent / 'paperdoll_review'


def read(path):
    return json.loads(path.read_text())


def main():
    previous = json.loads((OUT / 'previous_review.js').read_text().split('=', 1)[1].strip().removesuffix(';'))
    accepted = read(OUT / 'accepted.json')
    decisions = read(OUT / 'decisions.json')
    placements = read(OUT / 'placements.json')
    previous.update(id='20260926_canonical_equipment_inventory', import_revision=1,
                    decisions=decisions, placements=placements, new_targets=[], stage_only_snapshot=False,
                    canonical_acceptance={'targets': len(accepted['records']), 'receipt': '../finalization_20260926/accepted.json'})
    staged = copy.deepcopy(previous['staged'])
    for target, record in accepted['records'].items():
        staged[target] = dict(target=target, name=Path(record['source_path']).stem,
            source_hash=record['source_sha256'], reviewed_sha256=record['sha256'],
            reviewed_path=os.path.relpath(record['artifact'], REVIEW),
            staged_path=os.path.relpath(record['artifact'], REVIEW),
            decision=decisions.get(target), canonical_accepted=True)
    previous['staged'] = staged
    (OUT / 'review.js').write_text('window.PAPERDOLL_REPAIR_PASS = ' + json.dumps(previous) + ';\n')
    fit = read(OUT / 'inventory_fit.json')
    for record in fit['records']:
        source = accepted['records'][record['target']]
        record.update(review_status='canonical', candidate=os.path.relpath(source['artifact'], REVIEW),
                      candidate_hash=source['sha256'])
    records = {record['item_id']: record for record in fit['records']}
    for group in fit['groups']:
        representative = records[group['representative_item_id']]
        group.update(review_status='canonical', shared_candidate=representative['candidate'],
                     shared_candidate_hash=representative['candidate_hash'])
    fit['group_summary']['review'] = {'canonical': len(fit['groups'])}
    for summary in fit['summary'].values():
        summary['review'] = {'canonical': summary['total']}
    (OUT / 'inventory_fit.js').write_text('window.PAPERDOLL_INVENTORY_FIT = ' + json.dumps(fit) + ';\n')
    (OUT / 'current_inventory_fit.json').write_text(json.dumps(fit, indent=2) + '\n')


if __name__ == '__main__':
    main()
