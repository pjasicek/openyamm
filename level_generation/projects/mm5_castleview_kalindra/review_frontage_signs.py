"""Read back frontage sign artwork, mounts and unchanged venue-door ownership."""
import hashlib
import itertools
import json
from pathlib import Path
import sys

from PIL import Image

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parents[2] / 'util'))
from map_export import parse_odm_file


def review():
    read = lambda name: json.loads((PROJECT / name).read_text())
    semantic = read('implementation/source/mm5_sw.semantic.json')
    native = PROJECT / 'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    digest = hashlib.sha256(native.read_bytes()).hexdigest()
    assert digest == read('review/native/build.json')['nativeSha256']
    payload = parse_odm_file(native)['payload']
    results = []
    for building in semantic['buildings']:
        if not building.get('exteriorSigns'):
            continue
        binding, = [b for b in semantic['bmodels'] if b['assembly'] == building['id']
                    and b['id'].endswith('_service_details')]
        model = payload['bmodels'][binding['index']]
        assert all(f['attributes'] == 0 and f['cog_triggered_number'] == 0 for f in model['faces'])
        vertices = [tuple(v[a] for a in 'xyz') for v in model['vertices']]
        def transform(point):
            x, y, z = point
            return tuple(building['frontOrigin'][i] + building['frontTangent'][i] * x
                         - building['frontOutward'][i] * y for i in range(2)) + (building['padHeight'] + z,)
        for sign in building['exteriorSigns']:
            face, = [f for f in model['faces'] if f['texture_name'].lower() == sign['texture']]
            points = [vertices[i] for i in face['vertex_indices']]
            x0, y, z0, x1, _, z1 = sign['artBounds']
            assert set(points) == {transform(p) for p in [(x0,y,z0),(x1,y,z0),(x1,y,z1),(x0,y,z1)]}
            a, b = [[points[j][i] - points[0][i] for i in range(3)] for j in [1,2]]
            normal = (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
            assert sum(normal[i]*building['frontOutward'][i] for i in range(2)) > 0
            with Image.open(PROJECT / 'implementation/runtime/worlds/mm5/textures' / (sign['texture'] + '.png')) as art:
                size = art.size
            assert (max(face['texture_us'])-min(face['texture_us']),
                    max(face['texture_vs'])-min(face['texture_vs'])) == size
            for bounds in [sign['bounds']] + sign.get('hangers', []):
                assert all(transform(p) in vertices for p in itertools.product(
                    [bounds[0],bounds[3]], [bounds[1],bounds[4]], [bounds[2],bounds[5]]))
            venue, = [v for v in building['venues'] if v['id'] == sign['venueId']]
            event, = [e for e in semantic['events'] if e['semantic_id'] == venue['id']]
            assert event['id'] == venue['eventId'] and event['bmodel_index'] != binding['index']
            door = payload['bmodels'][event['bmodel_index']]
            assert all(door['faces'][i]['cog_triggered_number'] == event['id'] for i in event['faces'])
            results.append({'id':sign['id'], 'nativeModel':binding['index'], 'artSize':size,
                            'separateDoorEvent':event['id'], 'signEvents':0})
    assert len(results) == 5
    output = {'nativeSha256':digest, 'signs':results,
              'limits':'Written artwork, UV extent, outward winding, mount vertices and inert sign faces. '
                       'Visual support contact and ordinary access/click behavior require in-game review.'}
    (PROJECT / 'review/frontage_signs_v1/readback.json').write_text(json.dumps(output, indent=2) + '\n')
    print({'frontageSigns':len(results), 'nativeSha256':digest})


if __name__ == '__main__':
    review()
