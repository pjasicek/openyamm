"""Read back Goldur's working props, fixed garden anchors and the open lodge approach."""
import hashlib
import json
import math
from pathlib import Path
import sys

from author_props import ground_at
from review_environment import edge_samples
from review_fortifications import rectangle
from prepare_scenery import polygon_distance

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parents[2]/'util'))
from map_export import parse_odm_file


def review():
    read = lambda path: json.loads((PROJECT/path).read_text())
    native = PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    digest = hashlib.sha256(native.read_bytes()).hexdigest()
    assert digest == read('review/native/build.json')['nativeSha256']
    payload = parse_odm_file(native)['payload']
    height = bytes(payload['height_map'])
    semantic = read('implementation/source/mm5_sw.semantic.json')
    prop, = [p for p in semantic['props'] if p['id']=='ranger_woodcraft']
    binding, = [b for b in semantic['bmodels'] if b['assembly']==prop['id']]
    model = payload['bmodels'][binding['index']]
    vertices = [[v[a] for a in 'xyz'] for v in model['vertices']]
    assert all(f['cog_triggered_number']==0 for f in model['faces'])
    palette = read('implementation/architecture.json')['palettes']['working_props']
    assert {f['texture_name'].lower() for f in model['faces']} == {palette['wood'],palette['metal']}
    burial = []
    for support in prop['groundSupports']:
        poly = support['footprint']
        bottom = math.floor(support['bottom']+.5)
        assert all([math.floor(x+.5),math.floor(y+.5),bottom] in vertices for x,y in poly)
        burial.extend(ground_at(height,p)-bottom for a,b in zip(poly,poly[1:]+poly[:1])
                      for p in edge_samples(a,b))
    assert len(prop['groundSupports'])==6 and min(burial)>=15
    corridor = rectangle(prop,prop['clearApproach'])
    assert all(polygon_distance(p,corridor)>0 for p in rectangle(prop,prop['bounds']))
    records = read('implementation/scenery.json')['records']
    plants = [p for p in records if p.get('group')=='ranger_practice_garden']
    assert len(plants)==5 and {p['id'] for p in plants}=={p['id'] for p in prop['nativeScenery']}
    for plant in plants:
        assert plant['name'] in ['plant26','plant32'] and plant['eventId']==0
        assert plant['position'][2]==round(ground_at(height,plant['position'][:2]))
        assert polygon_distance(plant['position'][:2],corridor)>=plant['visualRadius']
        matches = [e for e in payload['entities'] if [e['position'][a] for a in 'xyz']==plant['position']
                   and e['decoration_list_id']==plant['descriptorId']]
        assert len(matches)==1 and matches[0]['event_id_secondary']==0
    result = {'nativeSha256':digest,'bmodel':binding['index'],'nativeFaces':len(model['faces']),
              'groundSupports':len(prop['groundSupports']),'minimumSupportBurial':min(burial),
              'gardenPlants':5,'clearLodgeApproach':prop['clearLodgeApproach'],'newEvents':0,
              'limits':'Written prop support and fixed native plant identity/grounding only. Actual scale, '
                       'foliage appearance and ordinary lodge access require game review.'}
    output = PROJECT/'review/ranger_yard_v3'
    output.mkdir(parents=True,exist_ok=True)
    (output/'readback.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result)


if __name__=='__main__':
    review()
