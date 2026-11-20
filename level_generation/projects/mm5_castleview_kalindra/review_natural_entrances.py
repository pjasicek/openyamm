"""Check written natural entrance floors, buried skirts and placeholder faces against native terrain."""
import hashlib
import json
import math
import sys
from pathlib import Path

from prepare_bridges import triangle_clearance
from prepare_natural_entrances import IDS

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parents[2]/'util'))
from map_export import parse_odm_file


def review():
    semantic = json.loads((PROJECT/'implementation/source/mm5_sw.semantic.json').read_text())
    sites = [b for b in semantic['buildings'] if b['id'] in IDS]
    if not sites:
        return
    native = PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    build = json.loads((PROJECT/'review/native/build.json').read_text())
    assert hashlib.sha256(native.read_bytes()).hexdigest() == build['nativeSha256']
    payload = parse_odm_file(native)['payload']
    height = bytes(payload['height_map'])
    assert height == (PROJECT/'landscape/heightmap.raw').read_bytes()
    models = {m['id'].split('/')[-1]: m['index'] for m in semantic['bmodels'] if m['assembly'] in IDS}
    for name in models:
        path = PROJECT/'implementation/source/models'/(name+'.obj')
        assert hashlib.sha256(path.read_bytes()).hexdigest() == build['sourceObjSha256'][name+'.obj']
    checks, bindings = [], []
    for site in sites:
        for item in site['entranceChecks']:
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
                        assert n[2] > 0, (site['id'], 'downward walking face', index)
                        grades.append(math.hypot(n[0], n[1])/n[2])
            minimum = min(s['minimum'] for s in spans)
            maximum = max(s['maximum'] for s in spans)
            if item['kind'] == 'supported walking floor':
                assert minimum >= 2 and max(grades) <= .5, (site['id'], minimum, grades)
            else:
                assert maximum <= 0, (site['id'], item, maximum)
            checks.append({'site': site['id'], **item, 'minimumClearance': minimum,
                           'maximumClearance': maximum, 'maximumGrade': max(grades) if grades else None})
        assert len(site['venues']) == 1
        venue = site['venues'][0]
        event = next(e for e in semantic['events'] if e['semantic_id'] == venue['id'])
        assert event['id'] == venue['eventId']
        model = payload['bmodels'][event['bmodel_index']]
        assert all(model['faces'][i]['cog_triggered_number'] == event['id'] for i in event['faces'])
        assert all(model['faces'][i]['texture_name'].lower() == 'solid01' for i in event['faces'])
        assert site['entranceGeometry']['rearDepth'] > site['entranceGeometry']['frontDepth']
        assert not any(arrival['active'] for arrival in site['arrivals'])
        bindings.append({'site': site['id'], 'venue': venue['id'], 'eventId': event['id'],
                         'recessDepth': site['entranceGeometry']['rearDepth']-site['entranceGeometry']['frontDepth'],
                         'arrivals': site['arrivals'], 'sourceIdentities': site['sourceIdentities']})
    result = {'nativeSha256': build['nativeSha256'], 'checks': checks, 'bindings': bindings,
              'limits': 'Written walking triangles, upward winding, grade, buried skirts/supports and actual event faces. '
                        'Requires separate visual, ordinary movement, click and reload evidence. '
                        'The deeper BLV, source falling trigger and travel are deferred.'}
    (PROJECT/'review/native/natural_entrances.json').write_text(json.dumps(result, indent=2)+'\n')
    print({'naturalEntranceChecks': len(checks), 'naturalEntranceBindings': len(bindings)})


if __name__ == '__main__':
    review()
