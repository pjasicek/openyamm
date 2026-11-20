"""Carry the user's newer wand adjustment to records previously inherited from that wand."""
import copy
import csv
import json

from prepare import HERE, OUT, read, write


def main():
    original = read(OUT/'placements.json')
    effective = copy.deepcopy(original)
    catalog = json.loads((HERE/'catalog.js').read_text().split('=', 1)[1].strip().rstrip(';'))
    items = {i['id']: i for i in catalog['items']}
    changes = {}
    for key, record in effective['placements'].items():
        donor = original['placements'].get(record.get('inherited_from'))
        if not donor or record['delta'] == donor['delta']:
            continue
        definition = items[record['item_id']]
        first = items[donor['item_id']]
        assert definition['stat'] == first['stat'] == 'WeaponW'
        assert definition['icon'] == first['icon']
        assert record['doll_type'] == donor['doll_type'] and record['slot'] == donor['slot']
        assert record['basis'] == donor['basis'] and record['source_hash'] == donor['source_hash']
        assert donor['updated_at'] > record['updated_at']
        changes[key] = {'before': copy.deepcopy(record), 'donor': copy.deepcopy(donor)}
        record.update(delta=donor['delta'], proposed=[b+d for b, d in zip(record['base'], donor['delta'])],
                      candidate_hash=donor['candidate_hash'], updated_at=donor['updated_at'])
        changes[key]['after'] = record
    write(OUT/'placements.effective.json', effective)
    write(OUT/'inherited_placement_updates.json', changes)
    with (OUT/'placement_proposals.effective.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['key', 'item_id', 'doll_type', 'slot', 'table', 'base_x', 'base_y', 'delta_x', 'delta_y',
                         'proposed_x', 'proposed_y', 'inherited_from', 'active'])
        for key, r in effective['placements'].items():
            writer.writerow([key, r['item_id'], r.get('doll_type', ''), r['slot'], r['table'], *r['base'], *r['delta'],
                             *[b+d for b, d in zip(r['base'], r['delta'])], r.get('inherited_from', ''),
                             key not in original['inactive_legacy_keys']])
    print({'inherited_records_updated': len(changes), 'manual_records_changed': 0})


if __name__ == '__main__':
    main()
