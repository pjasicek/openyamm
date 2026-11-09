#!/usr/bin/env python3
"""Family consistency and suggested bindings. For every family: each model's LOD0 bounds height (work/<id>/model.json,
after the card cut) must equal the summer model's within 1 mm, so one binding height gives every season the same
trunk. Prints a table and the suggested decorations.yml bindings (height = the summer sprite's art height from
../inventory.json, equal within the family). Usage: family_check.py"""
import json, os
import common

FAMILIES = [['7tree13', '7tree14', '7tree15'], ['7tree16', '7tree17', '7tree18'], ['7tree19', '7tree20', '7tree21'],
            ['7tree07', '7tree08', '7tree09'], ['7tree25', 'tree26', 'tree27'], ['7tree22', '7tree24'],
            ['7tree28', '7tree30'], ['tree38', 'tree37']]
SEASON = {0: 'summer', 1: 'autumn', 2: 'winter'}
inventory = {d['name']: d for d in json.load(open(os.path.join(common.TREES, '..', 'inventory.json')))}
ok = True
rows, yaml = [], []
for family in FAMILIES:
    first = family[0]
    height = inventory[first]['art_height']
    ref = None
    for k, sid in enumerate(family):
        spec = common.load(sid)
        model = json.load(open(os.path.join(spec['work'], 'model.json')))
        span = (model['bounds_min'][1], model['bounds_max'][1])
        ref = ref or span
        same = abs(span[0] - ref[0]) < 1e-3 and abs(span[1] - ref[1]) < 1e-3
        ok &= same
        season = ('with fruit' if sid == 'tree38' else 'picked' if sid == 'tree37'
                  else 'winter' if spec['season'] == 'bare' else SEASON[k])
        rows.append((sid, season, spec['output'], model['lod_triangles'], round(model['file_bytes'] / 1e6, 1),
                     round(span[1] - span[0], 3), 'ok' if same else 'MISMATCH', inventory[sid]['count']))
        yaml.append(f"  - name: {sid}\n    model: engine/models/{spec['output']}\n    height: {height}\n"
                    f"    height_jitter: 0.12\n    lod_pixels: [650, 320, 180]")
for r in rows:
    print('{:8} {:10} {:24} {:26} {:5} MB  LOD0 height {:6} m  {:8}  placements {}'.format(
        r[0], r[1], r[2], str(r[3]), r[4], r[5], r[6], r[7]))
print('\n'.join(yaml))
print('FAMILIES', 'consistent' if ok else 'MISMATCH')
