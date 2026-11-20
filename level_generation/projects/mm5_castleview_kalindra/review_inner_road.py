"""Check written lane grades and real stair treads, supports and scenery clearance."""
import hashlib
import json
from pathlib import Path
import sys

from author_props import ground_at, polygon_distance
from review_environment import edge_samples

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
    assert height == (PROJECT/'landscape/heightmap.raw').read_bytes()
    crossfalls = [abs(height[61*128+c]-height[62*128+c])*32/512 for c in range(54,58)]
    assert max(crossfalls) <= .125
    binding, = [m for m in read('implementation/source/mm5_sw.semantic.json')['bmodels']
                if m['id']=='mm5:castleview/diviners/diviners_service_details']
    model = native['bmodels'][binding['index']]
    treads = []
    for face in model['faces']:
        assert face['cog_triggered_number']==0
        vertices = [[model['vertices'][i][axis] for axis in 'xyz'] for i in face['vertex_indices']]
        if len({p[2] for p in vertices})!=1:
            continue
        area = sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(vertices,vertices[1:]+vertices[:1]))/2
        if area <= 0:
            continue
        poly = [p[:2] for p in vertices]
        support = [ground_at(height,p) for a,b in zip(poly,poly[1:]+poly[:1]) for p in edge_samples(a,b)]
        top = vertices[0][2]
        assert max(support) < top
        treads.append({'top':top,'footprint':poly,'minimumGround':min(support),'maximumGround':max(support)})
    assert sorted(t['top'] for t in treads)==[800,832,864]
    bottom = min(p['z'] for p in model['vertices'])
    assert min(t['minimumGround'] for t in treads)-bottom >= 16
    leading = min(treads,key=lambda t:t['top'])
    outer_y = min(p[1] for p in leading['footprint'])
    leading_rise = leading['top']-ground_at(height,[-4144,outer_y])
    assert 0 < leading_rise <= 32
    top = max(treads,key=lambda t:t['top'])
    assert max(p[1] for p in top['footprint'])==1808
    scenery = read('implementation/scenery.json')['records']
    assert all(polygon_distance(s['position'][:2],t['footprint'])>=s.get('visualRadius',0)
               for s in scenery for t in treads)
    result = {'nativeSha256':digest,'crossfall':crossfalls,'stairModelIndex':binding['index'],
              'treads':treads,'supportBottom':bottom,'leadingRiser':leading_rise,
              'limits':'Written triangle/grounding and scenery-clearance checks. Native appearance, '
                       'ordinary walking and door click/reload require separate runtime review.'}
    (PROJECT/'review/inner_road_grade_v1/readback.json').write_text(json.dumps(result,indent=2)+'\n')
    print({'laneCrossfall':max(crossfalls),'treads':len(treads),'leadingRiser':leading_rise})


if __name__=='__main__':
    review()
