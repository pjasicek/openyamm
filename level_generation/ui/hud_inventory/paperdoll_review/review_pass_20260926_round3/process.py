"""Stage the exact latest approvals and audit remaining equipment by image and placement."""
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


def main():
    review = read(OUT/'review.original.json')
    previous = js(OUT/'previous_review.js')
    repairs = read(OUT/'repairs.json')
    for target, repair in repairs.items():
        old = previous['repairs'].get(target)
        history = previous.setdefault('history', {}).setdefault(target, [])
        if old and not any(r['sha256'] == old['sha256'] for r in history):
            history.append(old)
        previous['repairs'][target] = repair
    previous['new_targets'] = sorted(repairs)
    previous['magenta_scan']['records'] += read(OUT/'magenta_scan.json')['records']
    catalog = js(HERE/'catalog.js')
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
    write(OUT/'completion_audit.json', {'exported_at': review['exported_at'],
          'basis': 'Latest persisted browser decisions captured from an isolated copy of Chrome Local Storage, catalog resolver, retained repair history, and saved placements. Original browser untouched.',
          'excluded_groups': sorted(EXCLUDED), 'groups': dict(groups), 'remaining_main_equipment': remaining,
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
    payload.update(id='20260926_round3', import_revision=1, exported_at=review['exported_at'],
                   decisions=review['decisions'], placements=placements, staged=records,
                   completion_scope=sorted(scope), stage_only_snapshot=True)
    (OUT/'review.js').write_text('window.PAPERDOLL_REPAIR_PASS = '+json.dumps(payload, separators=(',', ':'))+';\n')
    assert digest(HERE.parent/'checkpoint/state.json') == checkpoint_before
    counts = Counter(v['decision'] for v in review['decisions'].values())
    report = {'result': 'PASS', 'exported_at': review['exported_at'], 'review_sha256': digest(OUT/'review.original.json'),
              'decisions': dict(counts), 'placement_records_preserved_exactly': len(placements),
              'staged_approvals_hash_verified': sum('staged_path' in r for r in records.values()),
              'new_staged_files': staged_new_files, 'checkpoint_sha256': checkpoint_before, 'checkpoint_unchanged': True,
              'remaining_main_equipment': len(remaining), 'remaining_by_group': dict(Counter(g for r in remaining for g in r['groups'])),
              'remaining_by_status': dict(Counter(r['status'] for r in remaining))}
    write(OUT/'validation.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
