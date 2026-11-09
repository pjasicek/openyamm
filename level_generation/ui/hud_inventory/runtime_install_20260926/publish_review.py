"""Expose the installed accepted artwork while preserving the complete review feedback and offsets."""
import json
import os
from pathlib import Path

OUT = Path(__file__).resolve().parent
REVIEW = OUT.parent / 'paperdoll_review'
PRIOR = OUT.parent / 'finalization_20260926'


def js(path):
    return json.loads(path.read_text().split('=', 1)[1].strip().removesuffix(';'))


def main():
    review = js(PRIOR / 'review.js')
    accepted = json.loads((OUT / 'accepted.json').read_text())['records']
    catalog = js(REVIEW / 'catalog.js')
    asset_ids = {r['id'] for r in catalog['assets'].values()}
    review.update(id='20260926_runtime_icons', import_revision=1,
        canonical_acceptance=dict(targets=len(accepted), receipt='../runtime_install_20260926/accepted.json'))
    for target, record in accepted.items():
        if target not in asset_ids:
            continue
        path = os.path.relpath(record['artifact'], REVIEW)
        review['staged'][target] = dict(target=target, name=Path(record['source']).stem,
            source_hash=record['source_sha256'], reviewed_sha256=record['sha256'], reviewed_path=path,
            staged_path=path, canonical_accepted=True, decision=review['decisions'].get(target))
    (OUT / 'review.js').write_text('window.PAPERDOLL_REPAIR_PASS = ' + json.dumps(review) + ';\n')
    fit = js(PRIOR / 'inventory_fit.js')
    fit.update(staging_only=False, runtime_tables_modified=True,
               runtime_visual_table='assets_dev/engine/data_tables/item_visuals.txt')
    for r in fit['records']:
        record = accepted[r['target']]
        r.update(candidate=os.path.relpath(record['artifact'], REVIEW), candidate_hash=record['sha256'])
    records = {r['item_id']: r for r in fit['records']}
    for group in fit['groups']:
        representative = records[group['representative_item_id']]
        group.update(shared_candidate=representative['candidate'], shared_candidate_hash=representative['candidate_hash'])
    (OUT / 'inventory_fit.js').write_text('window.PAPERDOLL_INVENTORY_FIT = ' + json.dumps(fit) + ';\n')
    index = REVIEW / 'index.html'
    text = index.read_text().replace('../finalization_20260926/review.js', '../runtime_install_20260926/review.js')
    text = text.replace('../finalization_20260926/inventory_fit.js', '../runtime_install_20260926/inventory_fit.js')
    text = text.replace('catalog.js?v=jewelry-20260926', 'catalog.js?v=runtime-installed-20260926')
    index.write_text(text)


if __name__ == '__main__':
    main()
