"""Resolve explicitly authored inert native scenery against the shared descriptor table and art catalogue."""
import csv
import hashlib
import json
from pathlib import Path

from author_props import ground_at
from prepare_natural_entrances import world

ROOT = Path(__file__).resolve().parents[3]


def native_records(site, height, placements, group, light_radii=None):
    text = (ROOT/'level_generation/catalogues/outdoor_decorations/data.js').read_text()
    types = {t['name']: t for t in json.loads(text[text.index('{'):].strip().rstrip(';'))['types']}
    table = ROOT/'assets_dev/engine/data_tables/decoration_data.txt'
    rows = {r[1]: r for r in csv.reader(table.open(), delimiter='\t') if r and r[0].isdigit()}
    records = []
    for index, (name, x, y, purpose) in enumerate(placements):
        row, kind = rows[name], types[name]
        art = kind['previews']['mm8']
        assert int(row[0])-1 == kind['id'], (name, 'catalogue/runtime descriptor mismatch')
        expected_light=(light_radii or {}).get(name,0)
        assert int(row[11], 0) == 0 and int(row[6]) == expected_light and int(row[10]) == 0, row
        assert int(row[12]) == kind['sprite_id'], row
        point = [round(v) for v in world(site, [x, y, 0])[:2]]
        position = point+[round(ground_at(height, point))]
        records.append({
            'id': site['semanticId']+'/native/'+str(index), 'nativeSite': site['id'],
            'name': name, 'position': position, 'originalPosition': position, 'localPoint': [x, y],
            'category': 'fire_lights' if expected_light else 'trees' if name.startswith('tree') else
                        'rocks' if name.startswith('rock') else 'plants',
            'group': group, 'purpose': purpose,
            'descriptorId': int(row[0])-1, 'descriptorNumber': int(row[0]),
            'descriptorTableSha256': hashlib.sha256(table.read_bytes()).hexdigest(),
            'collisionRadius': int(row[4]), 'collisionHeight': int(row[5]),
            'visualRadius': art['pixel_size'][0]*art['frame_scale']/2,
            'visualHeight': art['pixel_size'][1]*art['frame_scale'],
            'assetSource': art['source'], 'assetSha256': hashlib.sha256((ROOT/art['source']).read_bytes()).hexdigest(),
            'nativeArt': art, 'originalUse': kind['maps'], 'placementChange': 0, 'eventId': 0})
        if expected_light: records[-1]['expectedLightRadius']=expected_light
    return records
