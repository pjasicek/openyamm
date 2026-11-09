"""Reconcile milestone-one specifications with the retained layout and authored source inventory.

This is identity/specification evidence. It does not accept final terrain contact,
street composition, unavailable routes or native visual quality.
"""
import collections
import hashlib
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent


def audit():
    paths = ['layout.json', 'interior_contacts.json', 'implementation/architecture.json',
             'implementation/source/mm5_sw.semantic.json', 'implementation/source/mm5_sw.geometry.yml']
    documents = [json.loads((PROJECT/path).read_text()) for path in paths]
    layout, contacts, spec, semantic, geometry = documents
    original = {b['id']: b for b in layout['buildings']}
    prepared = {b['id']: b for b in spec['buildings']}
    authored = {b['id']: b for b in semantic['buildings']}
    assert len(original) == len(prepared) == len(authored) == 45
    assert original.keys() == prepared.keys() == authored.keys()
    assert layout['attachedInteriorContacts'] == contacts
    assert collections.Counter(b['district'] for b in prepared.values()) == {'Castleview': 24, 'Countryside': 21}
    assert len({v['id'] for b in prepared.values() for v in b['venues']}) == 52
    assert len({v['eventId'] for b in prepared.values() for v in b['venues']}) == 52
    events = {e['semantic_id']: e for e in semantic['events']}
    models = {m['geometry_id']: m for m in geometry['bmodels']}
    records = []
    for key, building in prepared.items():
        source = original[key]
        # The author adds measured support/face indices to these diagnostic collections.
        diagnostic_fields = {'geometryChecks', 'wheelContacts', 'entranceChecks', 'sewerChecks'}
        assert {k: v for k, v in building.items() if k not in diagnostic_fields} == {
            k: v for k, v in authored[key].items() if k not in diagnostic_fields}, key
        assert building['people'] == source['architecture']['people'], key
        assert building['sourceIdentities'] == source['sources'], key
        assert building['semanticId'] == source['semanticId'], key
        for field in ['quality', 'qualityEvidence', 'purpose', 'form', 'palette', 'referenceIntent']:
            assert building[field], (key, field)
        assert building['palette'] in spec['palettes']
        for material in spec['palettes'][building['palette']].values():
            assert material in spec['materials'], (key, material)
        venues = {v['id']: v for v in building['venues']}
        for venue in source.get('venues', []):
            assert venues[venue['id']]['occupants'] == venue['occupants'], venue['id']
        expected_contacts = [c for c in contacts if c['exteriorOwner'] == key]
        assert {c['id'] for c in building.get('interiorContacts', [])} == {c['id'] for c in expected_contacts}, key
        native_clearance = building.get('environmentKind') == 'native scenery clearing'
        if native_clearance:
            assert building['nativeScenery'], key
        else:
            assert building['components'], key
        for component in building['components']:
            x0, y0, x1, y1 = component['bounds']
            assert x1 > x0 and y1 > y0 and component['top'] >= component['eave'], (key, component['id'])
            model_id = building['semanticId']+'/'+key+'_'+component['id']
            if not native_clearance:
                assert model_id in models, model_id
        venue_records = []
        for venue in building['venues']:
            xy = [building['frontOrigin'][i]+building['frontTangent'][i]*venue['localOffset']
                  -building['frontOutward'][i]*venue.get('localDepth', 0) for i in range(2)]
            assert xy == venue['door'], venue['id']
            if not venue.get('interactionSurface'):
                assert venue['doorSize'] == [128, 256], venue['id']
            elif not native_clearance:
                assert len(venue['doorSize']) == 2 and min(venue['doorSize']) > 0, venue['id']
            if not native_clearance:
                event = events[venue['id']]
                assert event['id'] == venue['eventId'] and event['faces'], venue['id']
            venue_records.append({k: venue[k] for k in
                                  ['id', 'door', 'doorSize', 'interactionSurface', 'occupants', 'eventId'] if k in venue})
        ref = building.get('alvarReference') or {}
        records.append({
            'id': key, 'semanticId': building['semanticId'], 'title': building['title'],
            'district': building['district'], 'form': building['form'], 'palette': building['palette'],
            'quality': building['quality'], 'localFootprint': building['localFootprint'],
            'components': building['components'], 'venues': venue_records,
            'people': building['people'], 'sourceIdentities': building['sourceIdentities'],
            'interiorContactIds': sorted(c['id'] for c in expected_contacts),
            'nativeSceneryInterpretation': native_clearance,
            'referenceIntent': building['referenceIntent'],
            'oversizedAlvarReference': ref.get('nativeEnvelopeFitsWithQuarterTurn') is False,
            'apparentlyFittingAlvarReference': ref.get('nativeEnvelopeFitsWithQuarterTurn') is True,
            'implementationNotes': building['implementationNotes'],
        })
    assert sum(r['oversizedAlvarReference'] for r in records) == 8
    assert sum(r['apparentlyFittingAlvarReference'] for r in records) == 14
    report = {
        'status': 'Milestone-one specification and retained identity inventory verified',
        'sourceSha256': {path: hashlib.sha256((PROJECT/path).read_bytes()).hexdigest() for path in paths},
        'premises': len(records), 'town': 24, 'countryside': 21,
        'venues': sum(len(r['venues']) for r in records),
        'retainedPeopleAndServices': sum(len(r['people']) for r in records),
        'retainedInteriorContacts': len(contacts), 'oversizedReferencesRecomposed': 8,
        'apparentlyFittingReferences': 14,
        'forms': dict(collections.Counter(r['form'] for r in records)), 'records': records,
        'limits': [
            'A component specification and preserved identities do not prove final visual acceptance.',
            'Fourteen apparent reference fits remain subject to final native roof, door and terrain review.',
            'Natural clearings use native scenery; counters, descents and rope have explicit non-door surfaces.',
            'People and attached interior contacts remain planning data; none are instantiated as NPCs.',
            'Separate exterior features, contextual courts, landscape and final package have their own completion gates.',
        ],
    }
    output = PROJECT/'review/architecture_specification'
    output.mkdir(exist_ok=True)
    (output/'inventory.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    print({key: value for key, value in report.items() if key not in ['sourceSha256', 'records', 'limits', 'forms']})
    return report


if __name__ == '__main__':
    audit()
