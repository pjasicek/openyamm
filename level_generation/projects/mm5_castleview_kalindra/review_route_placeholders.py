"""Inspect written route contacts against native ground, bindings and retained travel plans."""
import hashlib
import json
from pathlib import Path
import sys

from author_props import ground_at, polygon_distance
from author_route_placeholders import ATTRIBUTES, ROUTES

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parents[2]/'util'))
from map_export import parse_odm_file


def review():
    read = lambda name: json.loads((PROJECT/name).read_text())
    path = PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == read('review/native/build.json')['nativeSha256']
    native = parse_odm_file(path)['payload']
    height = bytes(native['height_map'])
    plan = read('implementation/route_placeholders.json')
    assert hashlib.sha256(height).hexdigest() == plan['heightSha256']
    source = {r['id']: r for r in read('layout.json')['travel']}
    semantics = read('implementation/source/mm5_sw.semantic.json')
    scenery = read('implementation/scenery.json')['records']
    assert len(plan['routes']) == len(source) == 2
    checks = []
    for route in plan['routes']:
        for key in ['point', 'arrival', 'kind', 'days']:
            assert route[key] == source[route['id']][key]
        assert route['days'] is None
        model = native['bmodels'][route['bmodelIndex']]
        event, = [e for e in semantics['events'] if e['semantic_id'] == route['semanticId']]
        assert event['legacy_attributes'] == ATTRIBUTES
        assert event['bmodel_index'] == route['bmodelIndex']
        assert len(model['faces']) == route['faces'] == 6
        points = [[v[a] for a in 'xyz'] for v in model['vertices']]
        bounds = [min(p[0] for p in points), min(p[1] for p in points),
                  max(p[0] for p in points), max(p[1] for p in points)]
        assert bounds == ROUTES[route['id']]['bounds']
        faces = []
        for face in model['faces']:
            assert face['attributes'] & 0x26002000 == ATTRIBUTES
            assert face['cog_triggered_number'] == route['eventId']
            vertices = [points[i] for i in face['vertex_indices']]
            assert len(vertices) == 3
            area = sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(vertices,vertices[1:]+vertices[:1]))/2
            assert area > 0
            center = [sum(v[i] for v in vertices)/3 for i in range(3)]
            for v in vertices+[center]:
                assert abs(v[2]-ground_at(height,v[:2])-1) < .001
            polygon = [v[:2] for v in vertices]
            assert all(polygon_distance(s['position'][:2],polygon) > s.get('visualRadius',0)
                       for s in scenery)
            faces.append({'area': area, 'groundOffset': 1, 'center': center})
        checks.append({'id': route['id'], 'eventId': route['eventId'], 'bounds': bounds, 'faces': faces})
    result = {'nativeSha256': digest, 'routes': checks,
              'limits': 'Static native contact/grounding checks only; actual approach, feedback and return require game review.'}
    (PROJECT/'review/travel_placeholder_v1/readback.json').write_text(json.dumps(result,indent=2)+'\n')
    print({'routeContacts': len(checks), 'nativeGroundOffset': 1, 'sourceTravelPlansRetained': True})


if __name__ == '__main__':
    review()
