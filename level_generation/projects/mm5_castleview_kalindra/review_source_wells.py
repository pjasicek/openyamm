"""Check the six written roofed wells, ground contact, roof winding and local interaction reserves."""
import csv
import hashlib
import json
import sys
from pathlib import Path

from author_props import ground_at, polygon_distance
from prepare_source_wells import LABELS, PALETTE, review_fit
from review_environment import edge_samples
from review_fortifications import distance, rectangle

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file


def review():
    read = lambda name: json.loads((PROJECT/name).read_text())
    semantic = read('implementation/source/mm5_sw.semantic.json')
    props = [p for p in semantic['props'] if p.get('kind')=='source well']
    assert len(props)==6 and {p['id'] for p in props}==set(LABELS)
    fit = review_fit(props,read('implementation/architecture.json'),semantic)
    native = PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    digest = hashlib.sha256(native.read_bytes()).hexdigest()
    assert digest==read('review/native/build.json')['nativeSha256']
    payload = parse_odm_file(native)['payload']
    height = bytes(payload['height_map'])
    scenery = read('implementation/scenery.json')['records']
    rows = {int(r[0])-1:r for r in csv.reader(
        (ROOT/'assets_dev/engine/data_tables/decoration_data.txt').open(),delimiter='\t') if r and r[0].isdigit()}
    ids = read('implementation/feature_event_ids.json')
    records = []
    for prop in props:
        event, = [e for e in semantic['events'] if e['semantic_id']==prop['semanticId']]
        assert event['id']==prop['eventId']==ids[prop['semanticId']]
        assert prop['frontOrigin']==prop['sourceFeature']['point']
        assert prop['originalObject']['sprite']==54
        model = payload['bmodels'][event['bmodel_index']]
        assert len(event['faces'])==len(model['faces'])
        assert all(f['cog_triggered_number']==event['id'] for f in model['faces'])
        assert {f['texture_name'].lower() for f in model['faces']}==set(PALETTE.values())
        vertices = [[v[a] for a in 'xyz'] for v in model['vertices']]
        assert min(v[2] for v in vertices)==prop['foundation']['skirtBottomZ']
        assert max(v[2] for v in vertices)==prop['padHeight']+432
        bottom = prop['foundation']['skirtBottomZ']
        edges = []
        for face in model['faces']:
            points = [vertices[i] for i in face['vertex_indices']]
            edges.extend((a,b) for a,b in zip(points,points[1:]+points[:1]) if a[2]==b[2]==bottom)
        burial = min(ground_at(height,v)-bottom for a,b in edges for v in edge_samples(a,b))
        assert burial>=16,(prop['id'],burial)
        water, = [f for f in model['faces'] if f['texture_name'].lower()==PALETTE['water']]
        water_points = [vertices[i] for i in water['vertex_indices']]
        assert all(v[2]==prop['padHeight']+8 for v in water_points)
        water_clearance = min(water_points[0][2]-ground_at(height,v) for a,b in
                              zip(water_points,water_points[1:]+water_points[:1]) for v in edge_samples(a,b))
        assert water_clearance>=12,(prop['id'],water_clearance)
        roofs = [f for f in model['faces'] if f['texture_name'].lower()==PALETTE['roof']]
        assert len(roofs)==2
        for roof in roofs:
            a,b,c = [vertices[i] for i in roof['vertex_indices'][:3]]
            assert (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])>0, (prop['id'],'roof winding')
        poly = rectangle(prop,prop['bounds'])
        start = [prop['frontOrigin'][i]+prop['frontOutward'][i]*prop['approachDistance'] for i in range(2)]
        approach = [prop['frontOrigin'][i]+prop['frontOutward'][i]*136 for i in range(2)]
        sprite_access = min(distance(s['position'][:2],start,approach)-int(rows[s['descriptorId']][4])
                            for s in scenery)
        sprite_body = min(polygon_distance(s['position'][:2],poly)-int(rows[s['descriptorId']][4])
                          for s in scenery)
        assert sprite_access>=128,(prop['id'],sprite_access)
        assert sprite_body>=32,(prop['id'],sprite_body)
        records.append({'id':prop['id'],'eventId':event['id'],'nativeBmodel':event['bmodel_index'],
                        'nativeFaces':len(model['faces']),'minimumFootBurial':burial,
                        'minimumWaterGroundClearance':water_clearance,'upwardRoofFaces':len(roofs),
                        'spriteApproachClearance':sprite_access,'spriteBodyClearance':sprite_body,
                        'standingPoint':start,'sourceFeature':prop['sourceFeature'],
                        'originalObject':prop['originalObject']})
    result = {'nativeSha256':digest,'wells':records,'architectureClearances':fit,
              'limits':'Native faces, material keys, support, winding and approach reserves only. '
                       'Native context, representative real click and unchanged save values require game review.'}
    (PROJECT/'review/native/source_wells.json').write_text(json.dumps(result,indent=2)+'\n')
    print({'sourceWells':len(records),'nativeFaces':sum(r['nativeFaces'] for r in records)})


if __name__=='__main__':
    review()
