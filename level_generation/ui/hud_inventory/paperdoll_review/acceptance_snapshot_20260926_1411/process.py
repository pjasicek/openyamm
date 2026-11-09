"""Stage browser approvals and honor explicit notes synchronizing armor pose offsets."""
import copy
import csv
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote

OUT = Path(__file__).resolve().parent
HERE = OUT.parent
EXCLUDED = {'Armor, weapon held', 'Gloves', 'Jewelry'}


def read(path):
    return json.loads(path.read_text())


def js(path):
    return json.loads(path.read_text().split('=', 1)[1].strip().rstrip(';'))


def write(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_offset_notes(review, previous, catalog):
    before = copy.deepcopy(review)
    updates = []
    for target in previous['held_armor_scope']:
        decision = review['decisions'].get(target)
        if not decision or not decision.get('note'):
            continue
        note = decision['note'].strip().lower()
        # These are the twelve inspected instructions in the captured feedback, not
        # a general parser for arbitrary notes or an implicit approval of other art.
        assert 'offset' in note and ('without wep' in note or 'without weapon' in note), target
        assert decision['decision'] == 'approve', target
        assert decision['candidate_hash'] == previous['repairs'][target]['sha256'], target
        name = decision['asset_name']
        empty = catalog['assets'][name+'a']['id']
        accepted = review['decisions'][empty]
        assert accepted['decision'] == 'approve', empty
        assert accepted['candidate_hash'] == previous['held_armor_bases'][target]['base_sha256'], empty
        placement = review['placements'][decision['placement']['key']]
        assert accepted['placement']['key'] == decision['placement']['key'], target
        assert placement['table'] == 'complex_item_pictures.txt' and placement['slot'] == 'Armor', target
        assert placement['doll_type'] == decision['doll_type'], target
        assert placement['reviewed_asset'] == target and placement['candidate_hash'] == decision['candidate_hash'], target
        assert placement['delta'] == decision['placement']['delta'], target
        assert placement['base'] == catalog['complex'][str(placement['item_id'])][placement['doll_type']], target
        update = {'held_target': target, 'empty_target': empty, 'note': decision['note'],
                  'key': placement['key'], 'item_id': placement['item_id'], 'doll_type': placement['doll_type'],
                  'base': placement['base'], 'previous_empty_delta': accepted['placement']['delta'],
                  'delta': placement['delta'], 'proposed': placement['proposed'],
                  'source_approval_at': decision['updated_at'], 'applied_at': review['exported_at']}
        accepted['placement'] = copy.deepcopy(decision['placement'])
        accepted['updated_at'] = review['exported_at']
        accepted['placement_sync'] = {'from_target': target, 'source_approval_at': decision['updated_at'],
                                      'instruction': decision['note'], 'receipt': str(OUT.name)+'/offset_sync.json'}
        updates.append(update)
    assert len(updates) == 12
    assert review['placements'] == before['placements']
    changed = {r['empty_target'] for r in updates}
    for target, decision in review['decisions'].items():
        original = before['decisions'][target]
        if target not in changed:
            assert decision == original, target
        else:
            for field in set(original) - {'placement', 'updated_at'}:
                assert decision[field] == original[field], (target, field)
    write(OUT/'offset_sync.json', {'authorization': 'The user approved the current web review and requested application of the additional offset notes.',
          'basis': 'Both armor poses share the item/body-type complex placement record. Keep the exact saved offsets; synchronize the twelve approved empty-hand placement snapshots as explicitly requested.',
          'updates': updates, 'artwork_changed': False, 'placement_records_changed': False})
    write(OUT/'review.applied.json', review)
    with (OUT/'armor_offset_updates.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['held_target', 'empty_target', 'item_id', 'doll_type', 'base_x', 'base_y',
                         'old_delta_x', 'old_delta_y', 'new_delta_x', 'new_delta_y', 'proposed_x', 'proposed_y', 'note'])
        for r in updates:
            writer.writerow([r['held_target'], r['empty_target'], r['item_id'], r['doll_type'], *r['base'],
                             *r['previous_empty_delta'], *r['delta'], *r['proposed'], r['note']])
    return updates


def main():
    review = read(OUT/'review.original.json')
    previous = js(OUT/'previous_review.js')
    catalog = js(HERE/'catalog.js')
    input_hashes = read(OUT/'input_hashes.json')
    assert digest(HERE/'catalog.js') == input_hashes['catalog_sha256']
    assert digest(HERE.parent/'checkpoint/state.json') == input_hashes['ledger_sha256']
    assert digest(OUT/'previous_review.js') == input_hashes['previous_overlay_sha256']
    offset_updates = apply_offset_notes(review, previous, catalog)
    assets = {a['id']: a for a in catalog['assets'].values()}
    items = {i['id']: i for i in catalog['items']}
    records = {}
    staged_new_files = 0
    (OUT/'staged-accepted').mkdir(exist_ok=True)
    checkpoint_before = digest(HERE.parent/'checkpoint/state.json')
    for target, decision in review['decisions'].items():
        a = assets[target]
        assert a['sourceHash'] == decision['source_hash'], target
        choices = [{'path': a['candidate'], 'sha256': a['candidateHash']}]+a.get('preparedAlternatives', [])
        choices += previous.get('history', {}).get(target, [])
        if target in previous['repairs']:
            choices.append(previous['repairs'][target])
        chosen = next(v for v in choices if v['sha256'] == decision['candidate_hash'])
        source = HERE/unquote(chosen['path'].split('?')[0])
        assert digest(source) == decision['candidate_hash'], target
        record = {'target': target, 'name': a['name'], 'decision': decision, 'reviewed_path': chosen['path'],
                  'reviewed_sha256': decision['candidate_hash'], 'source_hash': a['sourceHash']}
        if decision['decision'] == 'approve':
            old = previous['staged'].get(target, {})
            if old.get('staged_path') and old['reviewed_sha256'] == decision['candidate_hash']:
                path = HERE/old['staged_path']
            else:
                path = OUT/'staged-accepted'/(target+'.png')
                shutil.copyfile(source, path)
                staged_new_files += 1
            assert digest(path) == decision['candidate_hash'], target
            record['staged_path'] = str(path.relative_to(HERE))
        records[target] = record
    write(OUT/'stage_manifest.json', {'schema': 'paperdoll-review-stage-v2', 'staging_only': True,
          'final_ledger_acceptance_authorized': False, 'ledger_modified': False, 'records': records})
    placements = review['placements']
    write(OUT/'placements.json', {'schema': review['placement_schema'], 'placements': placements,
                                 'inactive_legacy_keys': review['inactive_legacy_placement_keys']})
    with (OUT/'placement_proposals.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['key', 'item_id', 'doll_type', 'slot', 'table', 'base_x', 'base_y', 'delta_x', 'delta_y',
                         'proposed_x', 'proposed_y', 'inherited_from', 'active'])
        for key, r in placements.items():
            writer.writerow([key, r['item_id'], r.get('doll_type', ''), r['slot'], r['table'], *r['base'], *r['delta'],
                             *[b+d for b, d in zip(r['base'], r['delta'])], r.get('inherited_from', ''),
                             key not in review['inactive_legacy_placement_keys']])

    # Fresh-load selections mirror the viewer: subsequent explicit decisions supersede repairs,
    # while older approvals/flags do not automatically approve replacement artwork.
    selected = {}
    for target, a in assets.items():
        decision = review['decisions'].get(target)
        repair = previous['repairs'].get(target)
        later = decision and repair and decision['updated_at'] > repair['review_baseline_at'] and \
            decision['candidate_hash'] != repair['old_sha256']
        selected[target] = repair['sha256'] if repair and not later else \
            decision['candidate_hash'] if decision else a['candidateHash']

    def valid_placement(record):
        if record['key'].startswith(('grip:', 'preview:')):
            return False
        source = assets.get(record['reviewed_asset'])
        definition = items.get(record['item_id'])
        if not source or not definition or source['sourceHash'] != record['source_hash']:
            return False
        complex_points = catalog['complex'].get(str(record['item_id']), [[0, 0]]*6)
        expected_base = [definition['equipX'], definition['equipY']] if record['table'] == 'items.txt' else \
            complex_points[record['doll_type']] \
            if record['table'] == 'complex_item_pictures.txt' else [0, 0]
        if expected_base != record['base']:
            return False
        if record['key'].startswith('fit:'):
            expected_basis = {'equip': [definition['equipX'], definition['equipY']],
                              'doll': catalog['types'].get(str(record['doll_type']))}
            if expected_basis != record['basis']:
                return False
        if selected[source['id']] == record['candidate_hash']:
            return True
        repairs = previous.get('history', {}).get(source['id'], [])
        if source['id'] in previous['repairs']:
            repairs = repairs+[previous['repairs'][source['id']]]
        return any(r['sha256'] == selected[source['id']] and
                   record['candidate_hash'] in r.get('placement_compatible_hashes', []) for r in repairs)

    def status(target):
        a = assets[target]
        decision = review['decisions'].get(target)
        if not decision:
            return 'ledger_accepted' if a['candidateStatus'] in {'accepted', 'hud_approved'} and \
                selected[target] == a['candidateHash'] else 'unreviewed'
        if selected[target] != decision['candidate_hash']:
            return 'replacement_needs_approval'
        placement = decision.get('placement')
        if placement:
            record = placements.get(placement['key'])
            current_delta = record['delta'] if record and valid_placement(record) else None if record else [0, 0]
            if placement['key'].startswith(('grip:', 'preview:')) or placement['delta'] != current_delta:
                return 'placement_needs_review'
        return 'staged_approved' if decision['decision'] == 'approve' else 'flagged'

    uses = defaultdict(list)

    def add(name, group, item, doll_type=None, manual=False):
        if name not in catalog['assets']:
            return
        uses[catalog['assets'][name]['id']].append({'group': group, 'item_id': item['id'],
             'doll_type': doll_type, 'manual_table_stat': manual})

    for item in catalog['items']:
        stat = item['stat']
        group = {'Weapon': 'Melee weapons', 'Weapon1or2': 'Melee weapons', 'Weapon2': 'Melee weapons',
                 'WeaponW': 'Wands', 'Missile': 'Bows', 'Shield': 'Shields', 'Ring': 'Jewelry', 'Amulet': 'Jewelry'}
        if stat in group:
            add(item['icon'], group[stat], item)
            continue
        slot = {'armor': 'Armor', 'cloak': 'Cloak'}.get(stat, stat)
        if slot not in {'Armor', 'Helm', 'Belt', 'Boots', 'Cloak', 'Gauntlets'}:
            continue
        for t in range(5):
            if slot != 'Gauntlets' and not catalog['types'][str(t)]['can'][slot.lower()]:
                continue
            variant = 1 if slot == 'Cloak' and t in {2, 3} else t+1
            suffix = f'v{variant}'
            for held in ([False, True] if slot == 'Armor' else [False]):
                suffixes = ([suffix, suffix+'a'] if held else [suffix+'a', suffix]) if slot == 'Armor' else \
                    [suffix+'a'] if slot == 'Cloak' else [suffix]
                name = next((item['icon']+s for s in suffixes if item['icon']+s in catalog['assets']), item['icon'])
                category = 'Armor, weapon held' if held else 'Armor, empty hands' if slot == 'Armor' else \
                    {'Helm': 'Helmets', 'Belt': 'Belts', 'Boots': 'Boots', 'Cloak': 'Cloaks', 'Gauntlets': 'Gloves'}[slot]
                add(name, category, item, t, stat != slot)

    rows = []
    groups = defaultdict(Counter)
    scope = set()
    for target, contexts in uses.items():
        categories = sorted({u['group'] for u in contexts})
        state = status(target)
        for group in categories:
            groups[group][state] += 1
        if any(g not in EXCLUDED for g in categories):
            scope.add(target)
        decision = review['decisions'].get(target, {})
        rows.append({'target': target, 'name': assets[target]['name'], 'groups': categories, 'status': state,
                     'excluded': all(g in EXCLUDED for g in categories), 'uses': contexts,
                     'last_decision': decision.get('decision'), 'note': decision.get('note', ''),
                     'approved_or_flagged_hash': decision.get('candidate_hash'), 'current_candidate_hash': selected[target]})
    remaining = [r for r in rows if not r['excluded'] and r['status'] not in {'staged_approved', 'ledger_accepted'}]
    remaining_held = [r for r in rows if 'Armor, weapon held' in r['groups'] and
                      r['status'] not in {'staged_approved', 'ledger_accepted'}]
    assert not remaining and not remaining_held
    assert groups['Armor, empty hands']['staged_approved'] == 270
    assert groups['Armor, weapon held'] == {'staged_approved': 266, 'ledger_accepted': 4}
    write(OUT/'completion_audit.json', {'exported_at': review['exported_at'],
          'basis': 'Latest persisted browser approvals and placements; twelve explicit offset notes synchronize the empty-hand approval snapshots. Catalog resolver, retained repair history and exact image hashes verified. Original browser untouched.',
          'excluded_groups': sorted(EXCLUDED), 'groups': dict(groups), 'remaining_main_equipment': remaining,
          'remaining_held_armor': remaining_held,
          'all_equipment': rows,
          'scope_note': 'Five supported body types. Includes legacy lowercase armor/cloak item rows as manual previews; excludes unsupported body-type slots and unused orphan variants.'})
    with (OUT/'remaining_main_equipment.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['name', 'group', 'status', 'last_decision', 'body_types', 'manual_table_stat', 'note', 'review_url'])
        for r in remaining:
            writer.writerow([r['name'], ', '.join(r['groups']), r['status'], r['last_decision'],
                 ','.join(str(t) for t in sorted({u['doll_type'] for u in r['uses'] if u['doll_type'] is not None})),
                 any(u['manual_table_stat'] for u in r['uses']), r['note'],
                 'http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?target='+r['target']])
    payload = copy.deepcopy(previous)
    payload.update(id='20260926_acceptance_1411', import_revision=1, exported_at=review['exported_at'],
                   decisions=review['decisions'], placements=placements, staged=records,
                   completion_scope=sorted(scope), stage_only_snapshot=True)
    (OUT/'review.js').write_text('window.PAPERDOLL_REPAIR_PASS = '+json.dumps(payload, separators=(',', ':'))+';\n')
    assert digest(HERE.parent/'checkpoint/state.json') == checkpoint_before
    counts = Counter(v['decision'] for v in review['decisions'].values())
    report = {'result': 'PASS', 'exported_at': review['exported_at'], 'review_sha256': digest(OUT/'review.original.json'),
              'applied_review_sha256': digest(OUT/'review.applied.json'), 'offset_note_pairs_synchronized': len(offset_updates),
              'decisions': dict(counts), 'placement_records_preserved_exactly': len(placements),
              'staged_approvals_hash_verified': sum('staged_path' in r for r in records.values()),
              'new_staged_files': staged_new_files, 'checkpoint_sha256': checkpoint_before, 'checkpoint_unchanged': True,
              'remaining_main_equipment': len(remaining), 'remaining_by_group': dict(Counter(g for r in remaining for g in r['groups'])),
              'remaining_held_armor': len(remaining_held),
              'remaining_by_status': dict(Counter(r['status'] for r in remaining))}
    write(OUT/'validation.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
