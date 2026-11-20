"""Grounded, invisible local triggers at the two unbuilt regional foot routes.

The route floor follows native terrain triangles one unit above ground. Navigation
bounds and all visible landscape stay unchanged. Future travel replaces these local
status-only contacts; no nonexistent destination or invented travel duration is used.
"""
import hashlib
import json

from author_props import ground_at

ATTRIBUTES = 0x04002000  # Invisible | PressurePlate; intentionally not Clickable or Untouchable.
ROUTES = {
    'sw_sc': {'label': 'Eastern road travel', 'event': 4000, 'bounds': [24064, 4608, 24576, 6144]},
    'sw_nw': {'label': 'Northern overland travel', 'event': 4001, 'bounds': [-12288, 24064, -10752, 24576]},
}


def author_routes(author, project):
    layout = json.loads((project/'layout.json').read_text())
    height = (project/'landscape/heightmap.raw').read_bytes()
    assert {route['id'] for route in layout['travel']} == set(ROUTES)
    records = []
    for route in layout['travel']:
        definition = ROUTES[route['id']]
        assert route['days'] is None
        x0, y0, x1, y1 = definition['bounds']
        assert x0 <= route['point'][0] <= x1 and y0 <= route['point'][1] <= y1
        assert not (x0 <= route['arrival'][0] <= x1 and y0 <= route['arrival'][1] <= y1)
        record = {
            **route, 'semanticId': 'mm5:sw/route/'+route['id'], 'label': definition['label'],
            'eventId': definition['event'], 'bounds': definition['bounds'],
            'frontOrigin': [0, 0], 'frontTangent': [1, 0], 'frontOutward': [0, -1], 'padHeight': 0,
            'behavior': 'status-only on grounded route-floor entry; no map transition',
            'legacyAttributes': ATTRIBUTES, 'groundOffset': 1,
        }
        panels = []
        for x in range(x0, x1, 512):
            for y in range(y0, y1, 512):
                nw, sw, se, ne = [(px, py, ground_at(height, [px, py])+1)
                                  for px, py in [(x, y+512), (x, y), (x+512, y), (x+512, y+512)]]
                for points in [(nw, sw, ne), (sw, se, ne)]:
                    author.panel(panels, points, 'rctyl')
        event = {'semantic_id': record['semanticId'], 'label': record['label'], 'id': record['eventId'],
                 'behavior': record['behavior'], 'legacy_attributes': ATTRIBUTES}
        record['bmodelIndex'] = len(author.metadata['bmodels'])
        author.model('route_'+route['id'], panels, record, event)
        for obj in author.scene.objects:
            if obj.get('assembly_id') == route['id']:
                obj.hide_render = True
                obj['route_contact_only'] = True
        record['faces'] = len(panels)
        records.append(record)
    author.semantic['routes'] = records
    (project/'implementation/route_placeholders.json').write_text(json.dumps({
        'routes': records, 'heightSha256': hashlib.sha256(height).hexdigest(),
        'status': 'Source authored; native movement and visual review required',
        'policy': 'No travel target/duration, reward, timer or persistent state. Returning remains ordinary walking.',
    }, indent=2)+'\n')
