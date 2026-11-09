"""Check the written sewer landing, buried supports, grating and reserved return marker."""
import hashlib
import json
import math
import sys
from pathlib import Path

from prepare_bridges import triangle_clearance

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parents[2]/'util'))
from map_export import parse_odm_file


def review():
    semantic = json.loads((PROJECT/'implementation/source/mm5_sw.semantic.json').read_text())
    sites = [b for b in semantic['buildings'] if b['id'] == 'sewer_out']
    if not sites:
        return
    site, = sites
    native = PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    build = json.loads((PROJECT/'review/native/build.json').read_text())
    assert hashlib.sha256(native.read_bytes()).hexdigest() == build['nativeSha256']
    payload = parse_odm_file(native)['payload']
    height = bytes(payload['height_map'])
    assert height == (PROJECT/'landscape/heightmap.raw').read_bytes()
    models = {m['id'].split('/')[-1]: m['index'] for m in semantic['bmodels'] if m['assembly'] == site['id']}
    for name in models:
        path = PROJECT/'implementation/source/models'/(name+'.obj')
        assert hashlib.sha256(path.read_bytes()).hexdigest() == build['sourceObjSha256'][name+'.obj']
    checks = []
    walking = []
    for item in site['sewerChecks']:
        model = payload['bmodels'][models[item['model']]]
        spans, grades = [], []
        for index in item['faces']:
            face = model['faces'][index]
            points = [[model['vertices'][i][axis] for axis in ['x', 'y', 'z']]
                      for i in face['vertex_indices']]
            for i in range(1, len(points)-1):
                triangle = [points[0], points[i], points[i+1]]
                spans.append(triangle_clearance(height, triangle))
                if item['kind'] == 'supported walking floor':
                    a, b, c = triangle
                    u, v = [[p[j]-a[j] for j in range(3)] for p in [b, c]]
                    n = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
                    assert n[2] > 0, ('downward walking face', index)
                    grades.append(math.hypot(n[0], n[1])/n[2])
                    walking.append(triangle)
        minimum = min(s['minimum'] for s in spans)
        maximum = max(s['maximum'] for s in spans)
        if item['kind'] == 'supported walking floor':
            assert minimum >= 2 and max(grades) <= .25, (item, minimum, grades)
        else:
            assert maximum <= 0, (item, maximum)
        checks.append({**item, 'minimumClearance': minimum, 'maximumClearance': maximum,
                       'maximumGrade': max(grades) if grades else None})
    assert len(walking) == 6
    water = site['sewerGeometry']['waterLevel']
    assert min(p[2] for t in walking for p in t) == water+32
    # The supported threshold ends short of the rear closure: overlapping skirts previously rendered black.
    landing = payload['bmodels'][models['sewer_out_bank_landing']]
    rear = site['frontOrigin'][1]+site['sewerGeometry']['vaultDepth']
    assert max(v['y'] for v in landing['vertices']) == rear-8
    venue, = site['venues']
    event = next(e for e in semantic['events'] if e['semantic_id'] == venue['id'])
    assert event['id'] == venue['eventId'] == 145
    model = payload['bmodels'][event['bmodel_index']]
    assert len(event['faces']) == len(model['faces'])
    assert all(f['cog_triggered_number'] == event['id'] for f in model['faces'])
    materials = {f['texture_name'].lower() for f in model['faces']}
    assert materials == {'gn_mtl03', 'solid01'}
    assert venue['door'] == [-768, -10480] and venue['doorSize'] == [256, 288]
    arrival, = site['arrivals']
    assert not arrival['active'] and arrival['position'] == [-768, -10592, 288]
    result = {'nativeSha256': build['nativeSha256'], 'checks': checks,
              'binding': {'venue': venue['id'], 'eventId': event['id'], 'faces': len(event['faces']),
                          'materials': sorted(materials), 'arrival': arrival},
              'minimumWaterClearance': 32, 'rearSkirtSeparation': 8,
              'limits': 'Written support, upward winding, grade, water-level clearance and event fields only. '
                        'Actual water appearance, ordinary bank access, collision, clicks and reload require gameplay review. '
                        'No sewer BLV transfer is implemented.'}
    (PROJECT/'review/native/sewer.json').write_text(json.dumps(result, indent=2)+'\n')
    print({'sewerChecks': len(checks), 'sewerBindings': 1})


if __name__ == '__main__':
    review()
