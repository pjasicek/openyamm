"""Measure Alvar's original architecture and actual entrance/resident bindings for MM5 design review."""
from collections import Counter, defaultdict
import html
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import yaml
from catalogue_ravenshore import ROOT, events, table, source, points, bounds, face_measure, parse_odm_file

OUT = ROOT / 'level_generation/catalogues/mm8_alvar'
MERGED = [
    ('ogre_fort', list(range(6)), 'Ogre Raiding Fort entrance', 'dungeon'),
    ('waterfall', [6, 7, 8], 'Waterfall', 'landscape'),
    ('four_shops', [13, 14, 15], 'Four-shop block', 'service'),
    ('wasp_nest', [16, 17, 18, 19, 20, 91], 'Wasp Nest entrance complex', 'dungeon'),
    ('tents', [26, 27, 28], 'Adventurer camp tents', 'camp'),
    ('withersmythe', [33, 34], 'Withersmythe Estate', 'house'),
    ('dervish', [38, 39], 'Dervish Estate', 'house'),
    ('darkenmoore', [45, 46], 'Darkenmoore Hall', 'house'),
    ('merchant_guild', [52, 53, 54], 'Merchant Guildhouse', 'civic'),
    ('blackthorne', [56, 57], 'Blackthorne Estate', 'house'),
    ('training', [76, 77], 'Guild Training Hall', 'service'),
    ('fountain', [79, 80], 'Town fountain', 'prop'),
    ('bridge_north', [81, 82], 'Northern bridge', 'bridge'),
    ('bridge_west', [83, 84], 'Western bridge', 'bridge'),
    ('bridge_southwest', [85, 86], 'Southwestern bridge', 'bridge'),
    ('bridge_southeast', [87, 88], 'Southeastern bridge', 'bridge'),
    ('bridge_roadhouse', [89, 90], 'Roadhouse bridge', 'bridge'),
    ('roadhouse', [95, 96], "Miho's Roadhouse", 'service'),
    ('profit_house', [97, 98], 'Profit House', 'service'),
]


def family(name):
    low = name.lower()
    for tag in ['poor1', 'poor2', 'poor3', 'med1', 'med2', 'med3', 'rich1', 'rich2']:
        if 'delf_'+tag in low:
            return 'Alvar '+tag
    if '4s_' in low: return 'joined four-shop block'
    if low.startswith('moa_'): return 'merchant guild civic complex'
    if 'spellshop' in low: return 'polygonal guild tower'
    if 'temple' in low: return 'temple hall'
    if 'tav_' in low: return 'two-part inn'
    if 'train' in low: return 'training hall'
    if 'bank' in low: return 'bank'
    if 'stable' in low: return 'stables'
    return 'landmark / infrastructure / prop'


def build():
    for child in ['images', 'models']: (OUT/child).mkdir(parents=True, exist_ok=True)
    base = ROOT/'assets_dev/worlds/mm8'
    mp, sp, lp = base/'maps/out03.odm', base/'maps/out03.scene.yml', base/'events/maps/out03.lua'
    native = parse_odm_file(mp)['payload']; scene = yaml.safe_load(sp.read_text()); event_map = events(lp)
    assert len(native['bmodels']) == 99
    assert not scene['initial_state']['face_attribute_overrides']
    for override in scene['bmodel_faces']['interactive_faces']:
        f = native['bmodels'][override['bmodel_index']]['faces'][override['face_index']]
        for key in ['cog_number', 'cog_triggered_number', 'cog_trigger']: f[key] = override[key]
        f['attributes'] = override['legacy_attributes']
    hs, npcs, topics = table('house_data.txt'), table('npc.txt'), table('npc_topic.txt')
    def house(identity):
        row = hs[identity]['row']; residents = []
        for ni, npc in npcs.items():
            r = npc['row']
            if len(r) > 15 and r[6].isdigit() and int(r[6]) == identity:
                residents.append(dict(id=ni, name=r[1].strip(), portrait=r[2], line=npc['line'],
                    topics=[dict(id=int(t), title=topics[int(t)]['row'][1]) for t in r[10:16] if t.isdigit() and int(t)]))
        return dict(id=identity, name=row[5].strip(), type=row[2], line=hs[identity]['line'],
                    proprietor=row[6] if row[6] != 'Placeholder' else None, proprietor_title=row[7],
                    resident_candidates=residents)
    paths = {}
    for package in [base, ROOT/'assets_dev/engine']:
        for category in ['textures', 'terrain']:
            for path in sorted((package/category).glob('*.bmp')): paths.setdefault(path.stem.lower(), path)
    models = []; used = set()
    for i, model in enumerate(native['bmodels']):
        faces = [face_measure(model, f, paths) for f in model['faces']]
        assert all(f['texture'] or f['invisible'] for f in faces), ('Untextured visible face', i)
        used.update(f['texture'].lower() for f in faces if f['texture'])
        direct, labels = defaultdict(list), defaultdict(list)
        for f in faces:
            e = event_map.get(f['event'], {})
            if e.get('houses') or e.get('destinations'): direct[e['id']].append(f['index'])
            elif e.get('label_for_event'): labels[e['label_for_event']].append(f['index'])
        services = []
        for number in sorted(set(direct)|set(labels)):
            e = event_map[number]
            services.append(dict(event=number, title=e['title'], active_faces=direct[number],
                label_only_faces=labels[number], houses=[house(h) for h in e['houses']],
                destinations=e['destinations'], conditional=e['conditional'], line=e['line']))
        models.append(dict(index=i, name=model['name'], family=family(model['name']), bounds=bounds(points(model)),
            vertices=len(model['vertices']), faces=len(faces), face_records=faces,
            materials=dict(Counter(f['texture'] for f in faces)), services=services,
            has_active_entry=bool(direct), catalogue_building=True,
            hint_events=[dict(id=j, title=event_map[j]['title']) for j in sorted({f['event'] for f in faces})
                         if j in event_map and event_map[j]['title']]))
    assigned = {i for _, ids, _, _ in MERGED for i in ids}
    groups = list(MERGED)
    for m in models:
        i = m['index']
        if i in assigned: continue
        actual = [s for s in m['services'] if s['active_faces']]
        title = ' / '.join(s['title'] for s in actual) or (m['hint_events'][0]['title'] if m['hint_events'] else m['name'])
        if any(s['destinations'] for s in actual): kind = 'dungeon'
        elif actual: kind = 'house' if m['family'].startswith('Alvar ') else 'service'
        else: kind = 'prop'
        groups.append((f'part_{i:03d}', [i], title, kind))
    groups.sort(key=lambda g:min(g[1])); assemblies = []
    for identity, ids, title, kind in groups:
        houses = {}; destinations = set(); doors = []
        for i in ids:
            models[i]['assembly'] = identity
            for service in models[i]['services']:
                if not service['active_faces']: continue
                houses.update({h['id']:h for h in service['houses']}); destinations.update(service['destinations'])
                for fi in service['active_faces']:
                    f = models[i]['face_records'][fi]; size = f['bounds']['size']
                    if not f['invisible'] and abs(f['normal'][2]) < .5:
                        doors.append(dict(model=i, face=fi, event=service['event'], texture=f['texture'],
                            width=round(float(np.hypot(size[0],size[1])),2), height=size[2],
                            texture_dimensions=f['texture_dimensions'], units_per_texel=f['edge_units_per_texel_median']))
        assemblies.append(dict(id=identity, models=ids, title=title, purpose=title, kind=kind,
            bounds=bounds(np.concatenate([points(native['bmodels'][i]) for i in ids])), houses=list(houses.values()),
            destinations=sorted(destinations), entrance_faces=doors,
            npcCount=sum(len(h['resident_candidates']) for h in houses.values()),
            note='Count unique active destinations; auxiliary wings and hint-only faces are not additional homes.'))
    bound = {h['id'] for a in assemblies for h in a['houses']}
    script_houses = {h for e in event_map.values() for h in e['houses']}
    unbound = [dict(house=house(h), events=[e['id'] for e in event_map.values() if h in e['houses']],
                    status='Script destination without an active BModel entrance; not assigned to a nearby building by guess.')
               for h in sorted(script_houses-bound)]
    assert used <= paths.keys(), sorted(used-paths.keys())
    textures = {key:dict(source(paths[key]),size=list(Image.open(paths[key]).size)) for key in sorted(used)}
    houses = {h['id']:h for a in assemblies for h in a['houses']}
    views = [dict(id=a['id'], models=a['models'], purpose=a['title']) for a in assemblies if len(a['models'])>1]
    views += [dict(id='civic_center', models=[11,12,13,14,15,65,76,77,78,94,97,98], purpose='Civic/service centre at original spacing'),
              dict(id='western_residences', models=list(range(33,52))+[79,80,92], purpose='Western residences and fountain at original spacing'),
              dict(id='eastern_cottages', models=list(range(66,72))+[10], purpose='Eastern cottage group at original spacing')]
    coverage = dict(all_bmodels=len(models), physical_assemblies=len(assemblies), house_destinations=len(houses),
        npc_rows=sum(len(h['resident_candidates']) for h in houses.values()),
        service_proprietors=sum(bool(h['proprietor']) for h in houses.values()),
        residential_assemblies=sum(a['kind']=='house' for a in assemblies),
        residential_occupancy_histogram=dict(Counter(a['npcCount'] for a in assemblies if a['kind']=='house')),
        unbound_script_house_destinations=len(unbound))
    c = dict(format_version=1,title='Alvar',map='mm8/out03.odm',study_scene='Alvar building catalogue',
        object_prefix='AlvarCatalogue',models=models,assemblies=assemblies,assembly_views=views,textures=textures,
        sources=[source(p) for p in [mp,sp,lp]+[ROOT/'assets_dev/engine/data_tables'/n for n in ['house_data.txt','npc.txt','npc_topic.txt']]],
        coverage=coverage,unbound_script_houses=unbound,
        limits=['Original geometry and UVs are rendered for reference only; no MM5 geometry is copied.',
                'Residents are initial merged-base table candidates, separate from named service proprietors; no quest-state simulation.',
                'The merchant guild event changes dialogue with quest state; these are not extra houses or occupants.',
                'Some script house events lack active outdoor mesh faces; recorded explicitly rather than inventing an exterior.',
                'Independently fitted renders do not show relative physical scale. Use dimensions and equal-scale figures.',
                'Source poor/med/rich names identify art families, not proven wealth.'])
    (OUT/'catalogue.json').write_text(json.dumps(c,indent=2)+'\n')
    (OUT/'textures.json').write_text(json.dumps(textures,indent=2)+'\n')
    print(json.dumps(coverage,indent=2))
    print('Unbound',[(r['house']['id'],r['house']['name'],r['events']) for r in unbound])
    print('Textures',len(textures),Counter(k[:3] for k in textures))
    return c,native


if __name__ == '__main__': build()
