"""Check native-only clearing ownership, exact sprite grounding and open interaction/crop reservations."""
import csv
import hashlib
import json
import sys
from pathlib import Path

from author_props import ground_at
from prepare_scenery import polygon_distance
from review_fortifications import rectangle

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT/'util'))
from map_export import parse_odm_file


def review():
    semantic = json.loads((PROJECT/'implementation/source/mm5_sw.semantic.json').read_text())
    sites = [b for b in semantic['buildings'] if b.get('environmentKind') == 'native scenery clearing']
    if not sites:
        return
    build = json.loads((PROJECT/'review/native/build.json').read_text())
    scenery = json.loads((PROJECT/'implementation/scenery.json').read_text())
    native = PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    assert hashlib.sha256(native.read_bytes()).hexdigest() == build['nativeSha256']
    payload = parse_odm_file(native)['payload']
    height = bytes(payload['height_map'])
    rows = {int(r[0])-1: r for r in csv.reader(
        (ROOT/'assets_dev/engine/data_tables/decoration_data.txt').open(), delimiter='\t') if r and r[0].isdigit()}
    indices = {r['id']: i+1 for i, r in enumerate(scenery['records'])}
    checks = []
    for site in sites:
        assert not any(m['assembly'] == site['id'] for m in semantic['bmodels'])
        records = []
        for record in site['nativeScenery']:
            index = indices[record['id']]
            entity = payload['entities'][index]
            row = rows[entity['decoration_list_id']]
            point = [entity['position'][axis] for axis in 'xyz']
            assert row[1] == entity['name'].lower() == record['name']
            assert int(row[0]) == record['descriptorNumber']
            assert entity['decoration_list_id'] == record['descriptorId']
            assert point == record['position'] and abs(point[2]-ground_at(height, point)) <= .5
            assert entity['event_id_secondary'] == record['eventId'] and entity['event_id_primary'] == 0
            assert entity['ai_attributes'] == 0 and entity['special_trigger'] == 0
            records.append({'id': record['id'], 'nativeIndex': index, 'name': record['name'], 'position': point,
                            'descriptorId': record['descriptorId'], 'eventId': record['eventId']})
        assert len(records) == 8
        venue, = site['venues']
        binding, = [r for r in records if r['eventId'] == venue['eventId']]
        assert binding['id'] == venue['nativeDecorationId']
        assert binding['position'] == venue['interactionPosition']
        assert venue['occupants'] == [person['id'] for person in site['people']]
        reserves = [('clear approach', site['clearApproach'])]
        if site['futureGrowingGround']:
            reserves.append(('future growing ground', site['futureGrowingGround']))
        spaces = []
        for name, bounds in reserves:
            polygon = rectangle(site, bounds)
            margins = [polygon_distance([e['position'][axis] for axis in 'xy'], polygon)
                       -int(rows[e['decoration_list_id']][4]) for e in payload['entities'][1:]]
            assert min(margins) >= 32, (site['id'], name, min(margins))
            spaces.append({'name': name, 'localBounds': bounds, 'minimumColliderMargin': min(margins)})
        checks.append({'site': site['id'], 'records': records, 'venue': venue, 'spaces': spaces,
                       'sourceIdentities': site['sourceIdentities'], 'futurePeople': site['people']})
    result = {'nativeSha256': build['nativeSha256'], 'sites': checks,
              'limits': 'Exact native sprite IDs, positions/ground heights, flags, events, source contacts and '
                        'empty approach/crop spaces. Requires actual native player-height root/canopy inspection, '
                        'ordinary access and placeholder clicks. No actor, crop or reward implementation.'}
    (PROJECT/'review/native/clearings.json').write_text(json.dumps(result, indent=2)+'\n')
    print({'nativeClearings': len(checks), 'nativeClearingSprites': sum(len(c['records']) for c in checks)})


if __name__ == '__main__':
    review()
