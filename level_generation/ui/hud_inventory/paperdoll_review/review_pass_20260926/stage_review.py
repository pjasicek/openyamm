"""Snapshot the user's review and stage files/offset proposals without changing the ledger."""
import csv
import hashlib
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote

OUT = Path(__file__).resolve().parent
HERE = OUT.parent
SOURCE = Path('/home/pjasicek/Downloads/openyamm-paperdoll-review_2.json')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def main():
    snapshot = OUT / 'review.original.json'
    if not snapshot.exists():
        shutil.copyfile(SOURCE, snapshot)
        shutil.copyfile(HERE / 'catalog.js', OUT / 'catalog.original.js')
        write_json(OUT / 'baseline.json', {'review_sha256': digest(SOURCE),
            'checkpoint_sha256': digest(HERE.parent / 'checkpoint/state.json'), 'source': str(SOURCE)})
    review = json.loads(snapshot.read_text())
    catalog = json.loads((OUT / 'catalog.original.js').read_text().removeprefix('window.PAPERDOLL_REVIEW_DATA = ').removesuffix(';\n'))
    assets = {a['id']: a for a in catalog['assets'].values()}
    (OUT / 'staged-accepted').mkdir(exist_ok=True)
    records = {}
    for target, decision in review['decisions'].items():
        asset = assets[target]
        assert decision['source_hash'] == asset['sourceHash'], target
        choices = [{'sha256': asset['candidateHash'], 'path': asset['candidate']}] + asset['preparedAlternatives']
        chosen = next(o for o in choices if o['sha256'] == decision['candidate_hash'])
        source = HERE / unquote(chosen['path'])
        assert digest(source) == decision['candidate_hash'], source
        record = {'target': target, 'name': asset['name'], 'decision': decision,
                  'reviewed_path': chosen['path'], 'reviewed_sha256': digest(source), 'source_hash': asset['sourceHash']}
        if decision['decision'] == 'approve':
            destination = OUT / 'staged-accepted' / (target + '.png')
            shutil.copyfile(source, destination)
            record['staged_path'] = str(destination.relative_to(HERE))
        records[target] = record
    # Include every exported automatic finding, even if it was not manually reviewed.
    repairs = {}
    for target, record in records.items():
        decision = record['decision']
        if decision['decision'] == 'flag' or decision.get('note'):
            repairs[target] = {**record, 'note': decision.get('note', ''), 'automatic': []}
    for finding in review.get('automatic_findings', []):
        target = finding['target']
        if target not in repairs:
            asset = assets[target]
            repairs[target] = {'target': target, 'name': asset['name'], 'note': '',
                'reviewed_path': finding['path'], 'reviewed_sha256': finding['candidate_hash'],
                'source_hash': asset['sourceHash'], 'automatic': []}
        repairs[target]['automatic'].append(finding)
    for record in repairs.values():
        note = record['note'].lower()
        record['categories'] = [name for name, pattern in {
            'crop': r'cut|crop|til(?:e|ed)|wrong scale|wrong size|too big|enlar|too small',
            'magenta': r'magent|purple', 'green': r'green', 'openings': r'insid|opening|neckline|armpit',
            'quality': r'quality|pixelat', 'identity': r'serrat|cracks|skull|moss|grass|hooves|symmetr|sharp',
            'handle': r'thick', 'regenerate': r'regenerat',
        }.items() if re.search(pattern, note)]
        if record['automatic'] and 'magenta' not in record['categories']:
            record['categories'].append('magenta')
        if not record['categories']:
            record['categories'] = ['visual_inspection']
    placements = dict(review['placements'])
    inherited = {}
    conflicts = []
    by_icon = defaultdict(list)
    for item in catalog['items']:
        if item['stat'] == 'WeaponW':
            by_icon[item['icon']].append(item)
    for icon, items in by_icon.items():
        ids = {i['id'] for i in items}
        for body_type in range(5):
            for slot in ['MainHand', 'OffHand']:
                sources = [(key, value) for key, value in review['placements'].items()
                           if key.startswith('fit:') and value['item_id'] in ids and value.get('doll_type') == body_type and value.get('slot') == slot]
                if not sources:
                    continue
                deltas = {tuple(v['delta']) for _, v in sources}
                if len(deltas) > 1:
                    conflicts.append({'icon': icon, 'doll_type': body_type, 'slot': slot, 'sources': sources})
                sources.sort(key=lambda pair: (pair[1].get('updated_at', ''), pair[1]['item_id']))
                donor_key, donor = sources[0]
                for item in items:
                    key = f"fit:{item['id']}:{body_type}:{slot}"
                    if key in placements:
                        continue
                    inherited[key] = {**donor, 'key': key, 'item_id': item['id'],
                        'basis': {**donor['basis'], 'equip': [item['equipX'], item['equipY']]},
                        'inherited_from': donor_key, 'shared_display_sprite': icon}
    placements.update(inherited)
    write_json(OUT / 'placements.json', {'schema': review['placement_schema'], 'placements': placements,
        'inactive_legacy_keys': review['inactive_legacy_placement_keys'], 'inheritance_conflicts': conflicts})
    with (OUT / 'placement_proposals.csv').open('w', newline='') as stream:
        fields = ['key','item_id','doll_type','slot','table','base_x','base_y','delta_x','delta_y','proposed_x','proposed_y','inherited_from','active']
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for key, value in placements.items():
            base, delta = value['base'], value['delta']
            writer.writerow({**{k: value.get(k, '') for k in fields[:5]}, 'key': key,
                'base_x': base[0], 'base_y': base[1], 'delta_x': delta[0], 'delta_y': delta[1],
                'proposed_x': base[0]+delta[0], 'proposed_y': base[1]+delta[1],
                'inherited_from': value.get('inherited_from',''), 'active': key not in review['inactive_legacy_placement_keys']})
    report = {'schema': 'paperdoll-review-stage-v1', 'ledger_modified': False, 'records': records,
        'summary': {'decisions': dict(Counter(v['decision'] for v in review['decisions'].values())),
                    'repair_targets': len(repairs), 'repair_categories': dict(Counter(c for r in repairs.values() for c in r['categories'])),
                    'original_placements': len(review['placements']), 'inherited_wand_placements': len(inherited),
                    'wand_conflicts': len(conflicts)}}
    write_json(OUT / 'stage_manifest.json', report)
    write_json(OUT / 'repair_queue.json', repairs)
    print(json.dumps(report['summary'], indent=2))


if __name__ == '__main__':
    main()
