"""Check written town grilles, native ground contact, clear approaches and distinct local stubs."""
import csv
import hashlib
import json
import sys
from pathlib import Path

from author_props import ground_at, polygon_distance
from prepare_town_sewers import LABELS, PALETTE, review_fit
from review_environment import edge_samples
from review_fortifications import distance, rectangle

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file


def review():
    read = lambda name: json.loads((PROJECT/name).read_text())
    semantic = read('implementation/source/mm5_sw.semantic.json')
    spec = read('implementation/architecture.json')
    props = [p for p in semantic['props'] if p.get('kind')=='town sewer grate']
    assert {p['id'] for p in props}==set(LABELS)
    fit = review_fit(props,spec,semantic)
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
        model = payload['bmodels'][event['bmodel_index']]
        assert len(event['faces'])==len(model['faces'])
        assert all(f['cog_triggered_number']==event['id'] for f in model['faces'])
        assert {f['texture_name'].lower() for f in model['faces']}==set(PALETTE.values())
        vertices = [[v[a] for a in 'xyz'] for v in model['vertices']]
        slope = prop['foundation'].get('localSlope',[0,0])
        def plane_delta(point):
            delta = [point[i]-prop['frontOrigin'][i] for i in range(2)]
            return sum(delta[i]*prop['frontTangent'][i] for i in range(2))*slope[0] - sum(
                delta[i]*prop['frontOutward'][i] for i in range(2))*slope[1]
        cover, = [f for f in model['faces'] if f['texture_name'].lower()==PALETTE['dark']]
        cover_points = [vertices[i] for i in cover['vertex_indices']]
        assert all(abs(p[2]-plane_delta(p)-prop['padHeight'])<=.5 for p in cover_points)
        cover_clearance = min(prop['padHeight']+plane_delta(p)-ground_at(height,p) for a,b in
                              zip(cover_points,cover_points[1:]+cover_points[:1])
                              for p in edge_samples(a,b))
        assert cover_clearance>=4,(prop['id'],cover_clearance)
        poly = rectangle(prop,prop['bounds'])
        minimum_burial = min(ground_at(height,p)-prop['foundation']['skirtBottomZ']-plane_delta(p)
                             for a,b in zip(poly,poly[1:]+poly[:1]) for p in edge_samples(a,b))
        assert minimum_burial>=16,(prop['id'],minimum_burial)
        assert abs(min(v[2]-plane_delta(v) for v in vertices)-prop['foundation']['skirtBottomZ'])<=.5
        assert abs(max(v[2]-plane_delta(v) for v in vertices)-prop['padHeight']-20)<=.5
        arrival, = prop['arrivals']
        assert not arrival['active'] and abs(arrival['position'][2]-ground_at(height,arrival['position']))<=.5
        point, start = prop['frontOrigin'], arrival['position'][:2]
        approach = [point[i]+prop['frontOutward'][i]*96 for i in range(2)]
        sprite_clearance = min(distance(s['position'][:2],start,approach)-int(rows[s['descriptorId']][4])
                               for s in scenery)
        body_clearance = min(polygon_distance(s['position'][:2],poly)-int(rows[s['descriptorId']][4])
                             for s in scenery)
        assert sprite_clearance>=prop['standingRadius']+32,(prop['id'],sprite_clearance)
        assert body_clearance>=32,(prop['id'],body_clearance)
        records.append({'id':prop['id'],'eventId':event['id'],'nativeBmodel':event['bmodel_index'],
                        'nativeFaces':len(model['faces']),'minimumCoverClearance':cover_clearance,
                        'minimumSkirtBurial':minimum_burial,'spriteApproachClearance':sprite_clearance,
                        'spriteBodyClearance':body_clearance,'arrival':arrival,
                        'sourceFeature':prop['sourceFeature'],'originalObject':prop['originalObject']})
    result = {'nativeSha256':digest,'grates':records,'architectureClearances':fit,
              'limits':'Native geometry, distinct stubs, ground and approach reserves only. '
                       'Actual click, ordinary movement over the West Gate road grille and context require game review.'}
    (PROJECT/'review/native/town_sewers.json').write_text(json.dumps(result,indent=2)+'\n')
    print({'townSewerGrates':len(records),'nativeFaces':sum(r['nativeFaces'] for r in records)})


if __name__=='__main__':
    review()
