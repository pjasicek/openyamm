"""Read back the chapter court: supported native solids, clear path, retained plant identities."""
import hashlib
import json
import math
from pathlib import Path
import sys

from author_props import ground_at, polygon_distance
from review_environment import edge_samples
from review_fortifications import distance

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parents[2]/'util'))
from map_export import parse_odm_file


def review():
    read = lambda name: json.loads((PROJECT/name).read_text())
    native = PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    digest = hashlib.sha256(native.read_bytes()).hexdigest()
    assert digest == read('review/native/build.json')['nativeSha256']
    payload = parse_odm_file(native)['payload']
    height = bytes(payload['height_map'])
    assert height == (PROJECT/'landscape/heightmap.raw').read_bytes()
    semantic = read('implementation/source/mm5_sw.semantic.json')
    court = read('implementation/chapter_court.json')
    scenery = read('implementation/scenery.json')['records']
    plants = [p for p in scenery if p.get('group')=='chapter_garden']
    original = [p for p in read('landscape/decorations.json')['records'] if p.get('group')=='chapter_garden']
    assert len(plants)==12 and {p['id'] for p in plants}=={p['id'] for p in original}
    approach = court['clearApproach']
    corridor = [[approach[x], approach[y]] for x,y in [(0,1),(2,1),(2,3),(0,3)]]
    xy = lambda cell: [(cell[1]-64)*512+256, (64-cell[0])*512-256]
    roads = [(xy(a),xy(b)) for path in read('implementation/roads.json')['paths']
             for a,b in zip(path['cells'],path['cells'][1:])]
    records = []
    for prop in court['props']:
        binding, = [b for b in semantic['bmodels'] if b['assembly']==prop['id']]
        model = payload['bmodels'][binding['index']]
        vertices = [[v[a] for a in 'xyz'] for v in model['vertices']]
        assert all(f['cog_triggered_number']==0 for f in model['faces'])
        assert {f['texture_name'].lower() for f in model['faces']} <= set(prop['materialKeys'].values())
        burial = []
        for support in prop['groundSupports']:
            poly = support['footprint']
            # Confirm that each planned support really exists in the written model.
            # Native positive coordinates round half upward; Python round uses ties-to-even.
            bottom = math.floor(support['bottom']+.5)
            assert all([round(x),round(y),bottom] in vertices for x,y in poly)
            burial.extend(ground_at(height,p)-bottom for a,b in zip(poly,poly[1:]+poly[:1])
                          for p in edge_samples(a,b))
        assert min(burial)>=15
        road_clearance = min(distance(p,a,b) for poly in prop['solidFootprints'] for p in poly for a,b in roads)
        assert road_clearance>=96, (prop['id'],road_clearance)
        assert all(polygon_distance(p,corridor)>0 for poly in prop['solidFootprints'] for p in poly)
        records.append({'id':prop['id'], 'nativeBmodel':binding['index'], 'nativeFaces':len(model['faces']),
                        'minimumSupportBurial':min(burial), 'minimumRoadCenterlineClearance':road_clearance})
    for plant in plants:
        assert polygon_distance(plant['position'][:2],corridor)>=plant['visualRadius']
        assert any([e['position'][a] for a in 'xyz']==plant['position']
                   and e['decoration_list_id']==plant['descriptorId']
                   for e in payload['entities']), plant['id']
    result = {'nativeSha256':digest, 'props':records, 'retainedPlantIdentities':12,
              'clearApproach':approach, 'newFaceEvents':0,
              'limits':'Geometry, texture keys, support and declared approach only. Actual plant appearance, '
                       'ordinary walking and door/reload review are separate game evidence.'}
    (PROJECT/'review/chapter_court_v1/native_geometry.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result)


if __name__=='__main__':
    review()
