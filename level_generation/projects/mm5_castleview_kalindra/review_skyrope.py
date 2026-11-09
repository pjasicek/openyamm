"""Check the written climbing contact, inert anchor tree and native coil grounding."""
import hashlib
import json
import math
import sys
from pathlib import Path

from author_props import ground_at
from prepare_scenery import polygon_distance
from review_fortifications import rectangle

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parents[2]/'util'))
from map_export import parse_odm_file


def review():
    semantic = json.loads((PROJECT/'implementation/source/mm5_sw.semantic.json').read_text())
    sites = [b for b in semantic['buildings'] if b['id'] == 'skyrope']
    if not sites:
        return
    site, = sites
    native = PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    build = json.loads((PROJECT/'review/native/build.json').read_text())
    assert hashlib.sha256(native.read_bytes()).hexdigest() == build['nativeSha256']
    payload = parse_odm_file(native)['payload']
    height = bytes(payload['height_map'])
    venue, = site['venues']
    event, = [e for e in semantic['events'] if e['semantic_id'] == venue['id']]
    assert event['id'] == venue['eventId'] == 151
    rope = payload['bmodels'][event['bmodel_index']]
    assert len(event['faces']) == len(rope['faces'])
    assert all(f['cog_triggered_number'] == 151 for f in rope['faces'])
    assert {f['texture_name'].lower() for f in rope['faces']} == {'t06c11'}
    vertices = [[v[a] for a in 'xyz'] for v in rope['vertices']]
    clearances = [v[2]-ground_at(height, v) for v in vertices]
    assert min(clearances) >= 0 and min(clearances) <= 2, min(clearances)
    assert max(clearances) >= 680
    degenerate = []
    for index, face in enumerate(rope['faces']):
        points = [vertices[i] for i in face['vertex_indices']]
        a, b, c = points[:3]
        u, v = [[p[j]-a[j] for j in range(3)] for p in [b, c]]
        cross = [u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        if math.sqrt(sum(n*n for n in cross)) == 0:
            degenerate.append(index)
    assert not degenerate, degenerate
    scenery = json.loads((PROJECT/'implementation/scenery.json').read_text())
    record, = site['nativeScenery']
    index = next(i+1 for i,r in enumerate(scenery['records']) if r['id'] == record['id'])
    tree = payload['entities'][index]
    assert tree['decoration_list_id'] == record['descriptorId'] == 463
    assert [tree['position'][a] for a in 'xyz'] == record['position'] == [-2304,11520,704]
    assert tree['event_id_secondary'] == tree['event_id_primary'] == 0
    approach = rectangle(site, site['clearApproach'])
    assert min(polygon_distance(p[:2], approach) for p in vertices) >= 32
    arrival, = site['arrivals']
    assert not arrival['active'] and arrival['position'] == [-2176,11104,704]
    assert ground_at(height, arrival['position']) == arrival['position'][2]
    result = {'nativeSha256':build['nativeSha256'], 'eventId':151, 'ropeFaces':len(rope['faces']),
              'minimumCoilGroundClearance':min(clearances), 'maximumRopeHeight':max(clearances),
              'degenerateFaces':degenerate, 'nativeTreeIndex':index, 'nativeTree':record,
              'arrival':arrival, 'sourceRoutes':site['ropeGeometry'],
              'limits':'Native fields, quantized coil/face validity and reserved approach only. '
                       'Requires native attachment silhouette, real clicks, ordinary access and save/reload review.'}
    (PROJECT/'review/native/skyrope.json').write_text(json.dumps(result,indent=2)+'\n')
    print({'skyropeFaces':len(rope['faces']), 'skyropeMinimumClearance':min(clearances)})


if __name__ == '__main__':
    review()
