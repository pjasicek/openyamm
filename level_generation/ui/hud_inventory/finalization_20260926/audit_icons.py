"""Verify all retained icon approvals and distinguish runtime gaps from unused variants."""
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from PIL import Image

OUT = Path(__file__).resolve().parent
HUD = OUT.parent
ROOT = HUD.parents[2]
sys.path.insert(0, str(HUD))
from queue import Queue, save


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def js(path):
    return json.loads(path.read_text().split('=', 1)[1].strip().removesuffix(';'))


def main():
    q = Queue()
    ledger_before = sha(q.state_path)
    contracts = q.targets
    bypath = {t['source_path']: t for t in contracts.values()}
    byname = {(t['namespace'], t['runtime_name'].lower()): t for t in contracts.values()}
    approved, checks, superseded = {}, [], []

    def add(target, artifact, candidate_hash, source_hash, authority):
        contract = contracts[target]
        assert source_hash == contract['source_sha256'] == sha(ROOT / contract['source_path']), target
        assert artifact.is_file() and sha(artifact) == candidate_hash, str(artifact)
        with Image.open(artifact) as image:
            image.load()
            assert list(image.size) == contract['x2_size'], (target, image.size, contract['x2_size'])
        record = dict(target=target, artifact=str(artifact), sha256=candidate_hash,
                      source_sha256=source_hash, authority=authority, x2_size=contract['x2_size'])
        checks.append(record)
        if target in approved and approved[target]['sha256'] != candidate_hash:
            superseded.append(dict(target=target, previous=approved[target], selected=record))
        approved[target] = record

    # Lowest priority: existing canonical records; later dedicated reviews supersede earlier pilot art.
    for target, contract in contracts.items():
        cells = q.target_cells[target]
        if len(cells) == 1 and q.accepted(cells[0]):
            record = q.state['cells'][cells[0]]
            add(target, Path(record['artifact']), record['sha256'], contract['source_sha256'], 'canonical_checkpoint')
    for record in csv.DictReader((HUD / 'hud_context_review/acceptance/hud_icons.csv').open()):
        add(bypath[record['native_file']]['id'], ROOT / record['x2_review_png'], record['x2_sha256'],
            record['native_sha256'], 'HUD context user signoff 2026-09-23')
    for file in ['remaining_art_review/review_acceptance.json', 'remaining_art_review/effect_acceptance.json',
                 'mm8_art_review/review_acceptance.json', 'mm8_art_review/spell_review_acceptance.json',
                 'mm8_art_review/spellbook_review_acceptance.json']:
        receipt = ROOT / 'level_generation/ui' / file
        for record in read(receipt)['items']:
            assert record['decision'] == 'approve'
            if 'native_source_sha256' in record:
                assert sha(ROOT / record['source_reference']) == record['source_sha256']
            add(record['id'], receipt.parent / record['artifact'], record['candidate_sha256'],
                record.get('native_source_sha256', record['source_sha256']), str(receipt))
    for run in ['portrait_opaque_regen_v1', 'portrait_opaque_regen_remaining_v1']:
        folder = HUD / 'review/second_pass' / run
        approval = read(folder / 'approval.json')
        manifest = read(folder / 'manifest.json')
        assert sha(folder / 'manifest.json') == approval['manifest_sha256']
        digest = hashlib.sha256()
        paths = sorted(folder.glob('*/restored/*.png'))
        assert len(paths) == approval['approved_frame_count']
        for path in paths:
            digest.update(path.relative_to(folder).as_posix().encode())
            digest.update(b'\0')
            digest.update(bytes.fromhex(sha(path)))
        assert digest.hexdigest() == approval['restored_frames_sha256']
        assert set(f['id'] for f in manifest['families']) == set(approval['approved_family_ids'])
        for family in manifest['families']:
            for sheet in family['sheets']:
                for frame in sheet['frames']:
                    path = folder / family['id'] / 'restored' / f"{frame['frame']:02d}.png"
                    target = bypath[str(Path(frame['native']).relative_to(ROOT))]['id']
                    add(target, path, sha(path), frame['native_sha256'], str(folder / 'approval.json'))
    arcomage = read(HUD / 'review/arcomage_restoration/user_acceptance.json')
    add(arcomage['target'], ROOT / arcomage['staged_path'], arcomage['artifact_sha256'],
        contracts[arcomage['target']]['source_sha256'], 'Arcomage explicit assembled atlas acceptance')
    # Current equipment and inventory signoff resolves older overlapping inventory alternatives explicitly.
    for target, record in read(OUT / 'accepted.json')['records'].items():
        add(target, Path(record['artifact']), record['sha256'], record['source_sha256'], str(OUT / 'authority.json'))

    catalog = js(HUD / 'paperdoll_review/catalog.js')
    review_targets = {x['id']: x for x in catalog['reviewTargets']}
    head_names = {person['head'] for person in catalog['characters'] if person['head']}
    backgrounds = {person['background'] for person in catalog['characters'] if person['background']}
    usage = read(HUD / 'review/second_pass/usage_scope.json')
    usage_by_path = {row['source_path']: row for row in usage['files']}
    roots = [ROOT / 'assets_dev/engine/icons', *sorted((ROOT / 'assets_dev/worlds').glob('*/icons'))]
    files = sorted(path for folder in roots for path in folder.rglob('*')
                   if path.is_file() and path.suffix.lower() in ('.bmp', '.png', '.pcx'))
    rows = []
    for path in files:
        relative = str(path.relative_to(ROOT))
        old = usage_by_path.get(relative)
        namespace = 'engine' if '/engine/' in relative else 'worlds-' + path.parts[-3]
        contract = bypath.get(relative) or byname.get((namespace, path.stem.lower()))
        target = contract['id'] if contract else None
        record = approved.get(target)
        row = dict(source=relative, source_sha256=sha(path), target=target,
                   prior_status=old['status'] if old else 'not_in_prior_census',
                   artwork_approved=bool(record), runtime_selected=None)
        if old and old['source_sha256'] != row['source_sha256']:
            row['status'] = 'source_changed_since_usage_audit'
        elif '/worlds/mm9/' in relative:
            row['status'] = 'mm9_outside_restoration_scope'
        elif record:
            row.update(status='approved_exact_2x', approved_artifact=record['artifact'],
                       approved_sha256=record['sha256'], authority=record['authority'])
            if contract['source_path'] != relative:
                row['format_or_native_override'] = contract['source_path']
        elif target in review_targets and not review_targets[target]['resolverSelected']:
            row['runtime_selected'] = False
            row['status'] = ('metadata_only_head_or_beard' if path.stem.lower() in head_names
                             else 'unused_equipment_variant')
        elif path.stem.lower() in backgrounds:
            row.update(status='paperdoll_background_needs_approval', runtime_selected=True,
                       candidate=catalog['assets'][path.stem.lower()]['candidate'],
                       review_url='http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?'
                                  'hide_accepted=1&target=' + target)
        elif old and old['status'] == 'duplicate_restoration_alias':
            canonical = bypath.get(old['canonical_source'])
            canonical_record = approved.get(canonical['id']) if canonical else None
            if canonical_record:
                row.update(status='approved_identical_source_alias', canonical_source=old['canonical_source'],
                           approved_artifact=canonical_record['artifact'], approved_sha256=canonical_record['sha256'])
            else:
                row['status'] = 'unresolved_duplicate'
        elif old and old['status'].startswith('excluded_'):
            row['status'] = old['status']
        else:
            row['status'] = 'unresolved_runtime_coverage'
            if contract and contract['source_path'] != relative:
                row['reason'] = ('The frozen native source is an override outside assets_dev. The previous review '
                                 'selected by source_path against a runtime-path usage census, omitting this item.')
                row['native_override'] = contract['source_path']
        rows.append(row)
    blocked = [r for r in rows if r['status'] in ('paperdoll_background_needs_approval',
                'unresolved_runtime_coverage', 'source_changed_since_usage_audit', 'unresolved_duplicate')]
    summary = dict(result='COMPLETE_AUDIT_REPLACEMENT_NOT_READY', current_native_files=len(rows),
        approval_records_verified=len(checks), unique_approved_targets=len(approved),
        file_dispositions=dict(Counter(r['status'] for r in rows)), blockers=len(blocked),
        blocking_names=[Path(r['source']).name for r in blocked],
        superseded_approved_candidates=len(superseded), native_folders_safe_to_retire=False,
        reviewed_equipment_and_inventory_complete=True,
        entire_inventory_coverage_complete=not any(r['target'] and
            contracts[r['target']]['treatment'] == 'inventory_items' for r in blocked),
        runtime_integration_pending=['726 active placement changes (150 complex table, 576 per-item/body/slot)',
            '79 inventory fitting records and six footprint table changes',
            'five jewelry overlay display scales and shared image aliases',
            'restored-only icon lookup; current prefer_restored_icons retains native fallback',
            'separate MM9 retained-native scope; excluded legacy assets require deliberate archive policy'],
        canonical_ledger_unchanged=sha(q.state_path) == ledger_before)
    save(OUT / 'icon_coverage.json', dict(summary=summary, files=rows, approved=approved,
                                       blockers=blocked, superseded=superseded))
    with (OUT / 'icon_coverage.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['source', 'target', 'status', 'source_sha256',
            'approved_sha256', 'approved_artifact', 'canonical_source', 'format_or_native_override'], extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    save(OUT / 'icon_coverage_summary.json', summary)
    publish_gaps(blocked, catalog)
    print(json.dumps(summary, indent=2))


def publish_gaps(blocked, catalog):
    import html
    import os
    review = HUD / 'paperdoll_review'
    cards = []
    for row in blocked:
        name = Path(row['source']).stem.lower()
        asset = catalog['assets'].get(name)
        if not asset:
            continue
        native = os.path.relpath(review / asset['native'], OUT)
        candidate = os.path.relpath(review / asset['candidate'], OUT) if asset['candidate'] else None
        card = '<article><h2>' + html.escape(name) + '</h2><p>' + html.escape(row['status']) + '</p>'
        card += '<div class="pair"><figure><img class="native" src="' + html.escape(native, quote=True) + '" ' \
                'width="' + str(asset['size'][0] * 2) + '"><figcaption>Original ×2</figcaption></figure>'
        card += ('<figure><img src="' + html.escape(candidate, quote=True) + '"><figcaption>Candidate awaiting approval'
                 '</figcaption></figure>') if candidate else '<p>No restored candidate was included in the reviewed slice.</p>'
        card += '</div>'
        if row.get('review_url'):
            card += '<p><a href="' + html.escape(row['review_url'] + '&review=all', quote=True) + '">Open in paperdoll review</a></p>'
        if row.get('reason'):
            card += '<p>' + html.escape(row['reason']) + '</p>'
        cards.append(card + '</article>')
    (OUT / 'remaining.html').write_text('<!doctype html><meta charset="utf-8"><title>Icon replacement gaps</title>'
        '<style>body{background:#222;color:#ddd;font:16px sans-serif;margin:24px}a{color:#9cf}'
        '.pair{display:flex;gap:20px;flex-wrap:wrap}figure{margin:0}img{max-width:420px;object-fit:contain}'
        '.native{image-rendering:pixelated}article{border-top:1px solid #666;padding:16px 0}</style>'
        '<h1>Eight remaining icon artwork gaps</h1><p>The approved equipment, inventory and doll slice is recorded '
        'in the canonical ledger. These files prevent retiring the original icon folders.</p>' + '\n'.join(cards))


if __name__ == '__main__':
    main()
