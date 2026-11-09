"""Import the explicitly approved equipment/inventory slice into the canonical icon ledger.

The dry run validates exact reviewed bytes and preserves all placement proposals. --apply
records the authorized decision, keeping old ledger entries and staged artwork as history.
It does not install assets or move native icon folders.
"""
import argparse
import copy
import csv
import fcntl
import hashlib
import json
import shutil
import sys
from pathlib import Path
from urllib.parse import unquote

OUT = Path(__file__).resolve().parent
HUD = OUT.parent
ROOT = HUD.parents[2]
REVIEW = HUD / 'paperdoll_review'
sys.path.insert(0, str(HUD))
from queue import Queue, save
from native_sources import native_source

METHOD = 'user_approved_equipment_inventory_20260926'


def read(path):
    return json.loads(path.read_text())


def js(path):
    return json.loads(path.read_text().split('=', 1)[1].strip().removesuffix(';'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def immutable_json(path, value):
    if path.exists():
        assert read(path) == value, f'Immutable receipt differs: {path}'
    else:
        save(path, value)


def collect(q):
    catalog = js(REVIEW / 'catalog.js')
    assets = {a['id']: a for a in catalog['assets'].values()}
    previous = js(OUT / 'previous_review.js')
    captured = read(OUT / 'browser_state.original.json')
    decisions = json.loads(captured['storage']['openyamm-paperdoll-context-review-v1'])
    placements = json.loads(captured['storage']['openyamm-paperdoll-placement-v1'])
    fit = js(REVIEW / 'jewelry_repairs_20260926/inventory_fit.js')
    assert len(decisions) == 1260 and len(placements) == 728
    # Explicit chat acceptance covers the two final repair candidates, even if a tab did not persist both.
    for target in previous['new_targets']:
        repair = previous['repairs'][target]
        original = copy.deepcopy(decisions.get(target))
        if original and original['decision'] == 'approve' and original['candidate_hash'] == repair['sha256']:
            continue
        record = copy.deepcopy(original or {})
        record.update(target=target, decision='approve', source_hash=repair['source_hash'],
                      candidate_hash=repair['sha256'], attempt='repair:' + repair['sha256'][:12],
                      updated_at=captured['captured_at'], authority='explicit_user_chat_acceptance_20260926')
        decisions[target] = record
    fits = {r['item_id']: r for r in fit['records']}
    aliases = {r['target']: fits[r['representative_item_id']]['target'] for r in fit['records']}
    scope = set(previous['completion_scope'] + previous['held_armor_scope'] + list(aliases))
    records = {}

    def source_record(target, path, expected_hash, source_hash, authority, detail):
        contract = q.targets[target]
        assert q.target_cells[target] == [target], f'Expected single complete sprite: {target}'
        assert target not in q.state.get('user_excluded_targets', {})
        assert source_hash == contract['source_sha256'] == sha(native_source(contract['source_path'])), target
        assert path.is_file() and sha(path) == expected_hash, str(path)
        from PIL import Image
        with Image.open(path) as image:
            image.load()
            assert list(image.size) == contract['x2_size'], (target, image.size)
            assert image.mode in ('RGB', 'RGBA'), (target, image.mode)
        return dict(target=target, source=contract['source_path'], source_sha256=source_hash,
                    artifact=str(path.resolve()), sha256=expected_hash, x2_size=contract['x2_size'],
                    runtime_output_path=contract['runtime_output_path'], authority=authority, review=detail)

    # Inventory-only slice already has explicit, source/candidate-bound approval receipts.
    inventory_file = ROOT / 'level_generation/ui/remaining_art_review/review_acceptance.json'
    inventory_ids = set()
    for record in read(inventory_file)['items']:
        if record['category'] != 'Inventory items':
            continue
        assert record['decision'] == 'approve'
        target = record['id']
        inventory_ids.add(target)
        records[target] = source_record(target, inventory_file.parent / record['artifact'],
            record['candidate_sha256'], record['source_sha256'], str(inventory_file), record)
    assert len(inventory_ids) == 770

    for target in sorted(scope):
        representative = aliases.get(target, target)
        asset = assets[representative]
        decision = decisions.get(representative)
        if decision:
            assert decision['decision'] == 'approve', (target, decision)
            selected_hash = decision['candidate_hash']
            assert decision['source_hash'] == asset['sourceHash']
            placement = decision.get('placement')
            if placement:
                saved = placements.get(placement['key'])
                assert placement['delta'] == (saved['delta'] if saved else [0, 0]), (target, 'stale placement')
            authority = 'explicit_user_browser_and_chat_acceptance'
            detail = copy.deepcopy(decision)
        else:
            assert asset['candidateStatus'] in ('accepted', 'hud_approved'), (target, 'unreviewed')
            selected_hash = asset['candidateHash']
            authority = 'existing_canonical_or_HUD_approval'
            detail = dict(status=asset['candidateStatus'])
        choices = [dict(path=asset['candidate'], sha256=asset['candidateHash'])] + asset['preparedAlternatives']
        choices += previous.get('history', {}).get(representative, [])
        if representative in previous['repairs']:
            choices.append(previous['repairs'][representative])
        chosen = next(x for x in choices if x['sha256'] == selected_hash)
        path = REVIEW / unquote(chosen['path'].split('?')[0])
        if target != representative:
            a = next(r for r in fit['records'] if r['target'] == target)
            b = next(r for r in fit['records'] if r['target'] == representative)
            assert a['native_visual_sha256'] == b['native_visual_sha256'] and a['native_size'] == b['native_size']
            detail['shared_image_approval'] = dict(representative=representative,
                                                  native_visual_sha256=a['native_visual_sha256'])
        records[target] = source_record(target, path, selected_hash, assets[target]['sourceHash'], authority, detail)

    # Bodies and limbs were already accepted explicitly; include their canonical exports in this stage.
    doll_ids = set()
    for person in catalog['characters']:
        for field in ('body', 'leftClosed', 'leftHold', 'leftOpen', 'rightFingers', 'rightOpen', 'rightHold'):
            asset = catalog['assets'].get(person[field])
            if not asset:
                continue
            target = asset['id']
            doll_ids.add(target)
            record = q.state['cells'][target]
            assert q.accepted(target), target
            records[target] = source_record(target, Path(record['artifact']), record['sha256'], asset['sourceHash'],
                                            'previous_explicit_Real_ESRGAN_acceptance', record['review'])
    assert len(doll_ids) == 466
    # Validate the current table basis and hashes without dropping inactive historical proposals.
    for key, record in placements.items():
        if key.startswith(('grip:', 'preview:')):
            continue
        asset = assets[record['reviewed_asset']]
        definition = next(i for i in catalog['items'] if i['id'] == record['item_id'])
        assert record['source_hash'] == asset['sourceHash']
        if record['table'] == 'complex_item_pictures.txt':
            base = catalog['complex'].get(str(definition['id']), [[0, 0]] * 6)[record['doll_type']]
            assert base == record['base'], key
        else:
            assert record['base'] == [0, 0] and record['basis'] == {
                'equip': [definition['equipX'], definition['equipY']],
                'doll': catalog['types'][str(record['doll_type'])]}, key
    return records, decisions, placements, fit, dict(equipment=len(scope), inventory=len(inventory_ids),
        equipment_inventory_overlap=len(scope & inventory_ids), doll_parts=len(doll_ids), unique_targets=len(records))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    with (HUD / 'checkpoint/state.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        q = Queue()
        records, decisions, placements, fit, counts = collect(q)
        report = dict(result='PASS', **counts, decisions=len(decisions), placements=len(placements),
                      active_placements=sum(not k.startswith(('grip:', 'preview:')) for k in placements),
                      runtime_installed=False, native_folders_moved=False)
        if not args.apply:
            save(OUT / 'equipment_validation.json', report)
            print(json.dumps(report, indent=2))
            return
        if (OUT / 'accepted.json').exists():
            manifest = read(OUT / 'accepted.json')
            assert set(records) == set(manifest['records'])
            assert all(q.accepted(t) and q.state['cells'][t]['sha256'] == r['sha256'] for t, r in records.items())
            print('Equipment/inventory acceptance already applied and verified.')
            return
        assert not (OUT / 'checkpoint.before.json').exists(), 'Inspect incomplete prior import before retrying'
        shutil.copy2(q.state_path, OUT / 'checkpoint.before.json')
        authority = dict(schema='openyamm-user-acceptance-v1', date='2026-09-26', method=METHOD,
            instruction='OK, accepted; stage the completed equipment and inventory icon slice properly in the icons restoration ledger.',
            browser_capture_sha256=sha(OUT / 'browser_state.original.json'), counts=counts,
            two_final_repairs=['engine--icons--item150.bmp', 'engine--icons--ring1.bmp'],
            placement_policy='All 728 records retained, including two inactive legacy records; runtime integration pending.',
            new_generated_art=False)
        immutable_json(OUT / 'authority.json', authority)
        immutable_json(OUT / 'decisions.json', decisions)
        immutable_json(OUT / 'placements.json', placements)
        immutable_json(OUT / 'inventory_fit.json', fit)
        for filename in ('placement_proposals.csv', 'shared_image_proposals.csv', 'inventory_fit.csv', 'items_table_proposals.csv'):
            shutil.copy2(REVIEW / 'jewelry_repairs_20260926' / filename, OUT / filename)
        accepted = {}
        for target, record in records.items():
            contract = q.targets[target]
            relative = Path(contract['runtime_output_path']).relative_to('assets_dev')
            destination = OUT / 'icons_x2_stage' / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                assert sha(destination) == record['sha256'], target
            else:
                shutil.copy2(record['artifact'], destination)
            assert sha(destination) == record['sha256']
            receipt = OUT / 'receipts' / (target + '.json')
            immutable_json(receipt, record)
            evidence = {str(receipt): sha(receipt), str(OUT / 'authority.json'): sha(OUT / 'authority.json')}
            old = q.state['cells'].get(target)
            if not (old and q.accepted(target) and old['sha256'] == record['sha256']):
                q.state['cells'][target] = dict(status='accepted', artifact=str(destination), sha256=record['sha256'],
                    acceptance_method=METHOD, review=dict(authority=record['authority'], decision=str(receipt),
                    notes='User-approved exact image, including agreed shared-image aliases; prior receipt archived.'),
                    evidence_hashes=evidence, dependency_cells={}, layout_sha256=q.layout_hash(target))
            reconstruction = dict(target=target, path=str(destination), sha256=record['sha256'], size=contract['x2_size'],
                                  cells={target:record['sha256']}, status='user_approved_full_canvas')
            q.state.setdefault('reconstructed_targets', {})[target] = reconstruction
            staged = dict(target=target, source_path=contract['source_path'], source_sha256=contract['source_sha256'],
                artifact=str(destination), sha256=record['sha256'], native_size=contract['native_size'],
                x2_size=contract['x2_size'], runtime_output_path=contract['runtime_output_path'],
                cells=reconstruction['cells'], review=dict(authority=record['authority'], decision=str(receipt),
                full_canvas_review=True, notes='Explicit user acceptance imported; fitting proposals retained alongside.'),
                evidence_hashes=evidence, status='staged_for_runtime_integration_not_installed')
            q.state.setdefault('staged_targets', {})[target] = staged
            if target in q.state.get('restoration_inventory', {}):
                previous = q.state['restoration_inventory'][target]
                q.state['restoration_inventory'][target] = dict(previous, previous_status=previous['status'],
                    status='accepted', canonical_artifact=str(destination), canonical_sha256=record['sha256'],
                    acceptance_receipt=str(receipt))
            accepted[target] = staged
        save(q.state_path, q.state)
        save(q.storage_root() / 'exports/manifest.json', dict(targets=list(q.state['staged_targets'].values())))
        assert all(q.accepted(t) for t in records)
        report.update(canonical_accepted=len(records), canonical_ledger_sha256=sha(q.state_path))
        save(OUT / 'accepted.json', dict(authority=str(OUT / 'authority.json'), records=accepted, summary=report))
        save(OUT / 'equipment_validation.json', report)
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
