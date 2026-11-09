"""Measure initial NPC-table occupancy of native house destinations and physical assemblies."""
import collections
import hashlib
import json
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'level_generation/scripts'))
from catalogue_ravenshore import events, table, parse_odm_file


def build():
    houses, npcs = table('house_data.txt'), table('npc.txt')
    report = {'method': 'Native event-bearing faces -> EnterHouse destination -> NPC table column 6. '
              'Unique numeric NPC rows, initial table state. Proprietors counted separately. '
              'Quest moves, removed/replacement NPCs and hired party members are not simulated. '
              'Physical assembly membership follows measure_settlement_density.py; Merchant House added explicitly.',
              'maps': {}, 'sources': []}
    paths = [ROOT / 'assets_dev/engine/data_tables' / n for n in ['house_data.txt', 'npc.txt']]
    for name, map_id in [('Ravenshore', 'out02'), ('Garrote Gorge', 'out05')]:
        prefix = ROOT / 'assets_dev/worlds/mm8'
        odm, lua, scene = prefix / f'maps/{map_id}.odm', prefix / f'events/maps/{map_id}.lua', prefix / f'maps/{map_id}.scene.yml'
        paths.extend([odm, lua, scene])
        native = parse_odm_file(odm)['payload']
        event_map = events(lua)
        scene_data = yaml.safe_load(scene.read_text())
        for override in scene_data.get('bmodel_faces', {}).get('interactive_faces', []):
            native['bmodels'][override['bmodel_index']]['faces'][override['face_index']]['cog_triggered_number'] = override['cog_triggered_number']
        model_houses = {}
        for i, model in enumerate(native['bmodels']):
            model_houses[i] = sorted({h for f in model['faces'] for h in event_map.get(f['cog_triggered_number'], {}).get('houses', [])})
        ids = sorted({h for hs in model_houses.values() for h in hs})
        records = []
        for h in ids:
            row = houses[h]['row']
            residents = [{'id': i, 'name': n['row'][1], 'tableLine': n['line']} for i, n in npcs.items()
                         if len(n['row']) > 6 and n['row'][6].isdigit() and int(n['row'][6]) == h]
            records.append({'house': h, 'name': row[5], 'type': row[2], 'proprietor': row[6],
                            'npcCount': len(residents), 'npcs': residents,
                            'bmodels': [i for i, hs in model_houses.items() if h in hs]})
        if map_id == 'out02':
            groups = [[i] for i in range(8, 63) if not 46 <= i <= 57] + [[89]]
            groups += [[66, 67], [107,108,109,110], [71,72], [81,82], [46,47,48,49], [50,51,52,53,54], [78,79,80], [55,56,57]]
        else:
            groups = [{35:[35,36],37:[37,38],40:[39,40]}.get(i,[i]) for i in [24,25,27,28,29,31,32,35,37,40,41,42,43,44,45,46,47]]
            groups += [[21,22] if i == 22 else [i] for i in [16,17,18,19,20,22]]
            assigned = {i for g in groups for i in g}
            groups += [[i] for i, hs in model_houses.items() if hs and i not in assigned]
        assemblies = []
        for g in groups:
            hs = sorted({h for i in g for h in model_houses[i]})
            if hs:
                assemblies.append({'models': g, 'houses': hs,
                    'npcCount': sum(r['npcCount'] for r in records if r['house'] in hs)})
        occupied = [r for r in records if r['npcCount']]
        report['maps'][name] = {'houseDestinations': len(records), 'occupiedDestinations': len(occupied),
            'npcRows': sum(r['npcCount'] for r in records),
            'npcCountHistogramAllDestinations': dict(sorted(collections.Counter(r['npcCount'] for r in records).items())),
            'npcCountHistogramOccupiedDestinations': dict(sorted(collections.Counter(r['npcCount'] for r in occupied).items())),
            'housesPerAssemblyHistogram': dict(sorted(collections.Counter(len(a['houses']) for a in assemblies).items())),
            'assemblies': assemblies, 'houses': records}
    report['sources'] = [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]
    (OUT / 'reference_occupancy.json').write_text(json.dumps(report, indent=2) + '\n')
    for n, d in report['maps'].items():
        print(n, {k:v for k,v in d.items() if k not in ['houses','assemblies']})
        for h in d['houses']:
            if h['npcCount'] > 1: print(h['house'], h['name'], [n['name'] for n in h['npcs']])

if __name__ == '__main__':
    build()
