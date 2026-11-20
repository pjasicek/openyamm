"""Inspect exported ordinary chests, grounded feet, access and distinct local bindings."""
import csv
import hashlib
import json
import sys
from pathlib import Path

from author_props import ground_at, polygon_distance
from prepare_town_chests import PALETTE, review_fit
from review_environment import edge_samples
from review_fortifications import distance, rectangle

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file


def review():
    read = lambda name: json.loads((PROJECT/name).read_text())
    semantic = read('implementation/source/mm5_sw.semantic.json')
    props = [p for p in semantic['props'] if p.get('kind')=='town chest']
    expected = {f['id'] for f in read('layout.json')['features']
                if f['kind']=='chest' and f['id'].startswith('source_29_')}
    assert len(props)==len(expected)==5 and {p['id'] for p in props}==expected
    fit = review_fit(props,read('implementation/architecture.json'),semantic)
    native = PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    digest = hashlib.sha256(native.read_bytes()).hexdigest()
    assert digest==read('review/native/build.json')['nativeSha256']
    payload = parse_odm_file(native)['payload']
    height = bytes(payload['height_map'])
    scene = read('implementation/runtime/worlds/mm5/maps/mm5_sw.scene.yml')
    assert not scene['initial_state']['chests'], 'Closed props must not acquire native loot records'
    scenery = read('implementation/scenery.json')['records']
    rows = {int(r[0])-1:r for r in csv.reader(
        (ROOT/'assets_dev/engine/data_tables/decoration_data.txt').open(),delimiter='\t') if r and r[0].isdigit()}
    ids = read('implementation/feature_event_ids.json')
    records = []
    for prop in props:
        event, = [e for e in semantic['events'] if e['semantic_id']==prop['semanticId']]
        assert event['id']==prop['eventId']==ids[prop['semanticId']]
        assert prop['frontOrigin']==prop['sourceFeature']['point']
        assert prop['originalObject']['sprite']==15
        model = payload['bmodels'][event['bmodel_index']]
        assert len(event['faces'])==len(model['faces'])
        assert all(f['cog_triggered_number']==event['id'] for f in model['faces'])
        assert {f['texture_name'].lower() for f in model['faces']}==set(PALETTE.values())
        vertices = [[v[a] for a in 'xyz'] for v in model['vertices']]
        bottom = prop['foundation']['feetBottomZ']
        feet = [[vertices[i] for i in f['vertex_indices']] for f in model['faces']
                if all(vertices[i][2]==bottom for i in f['vertex_indices'])]
        assert len(feet)==4, (prop['id'],'four distinct supported feet',len(feet))
        burial = min(ground_at(height,p)-bottom for foot in feet
                     for a,b in zip(foot,foot[1:]+foot[:1]) for p in edge_samples(a,b))
        assert burial>=8, (prop['id'],burial)
        assert min(v[2] for v in vertices)==bottom
        assert max(v[2] for v in vertices)==prop['padHeight']+130
        body = rectangle(prop,[-96,-56,96,56])
        clearance = min(prop['padHeight']+12-ground_at(height,p)
                        for a,b in zip(body,body[1:]+body[:1]) for p in edge_samples(a,b))
        assert clearance>=16, (prop['id'],clearance)
        poly = rectangle(prop,prop['bounds'])
        start = [prop['frontOrigin'][i]+prop['frontOutward'][i]*prop['approachDistance'] for i in range(2)]
        approach = [prop['frontOrigin'][i]+prop['frontOutward'][i]*64 for i in range(2)]
        sprite_access = min(distance(s['position'][:2],start,approach)-int(rows[s['descriptorId']][4])
                            for s in scenery)
        sprite_body = min(polygon_distance(s['position'][:2],poly)-int(rows[s['descriptorId']][4])
                          for s in scenery)
        assert sprite_access>=prop['standingRadius']+32,(prop['id'],sprite_access)
        assert sprite_body>=32,(prop['id'],sprite_body)
        records.append({'id':prop['id'],'eventId':event['id'],'nativeBmodel':event['bmodel_index'],
                        'nativeFaces':len(model['faces']),'minimumFootBurial':burial,
                        'minimumBodyGroundClearance':clearance,'spriteApproachClearance':sprite_access,
                        'spriteBodyClearance':sprite_body,'standingPoint':start,
                        'sourceFeature':prop['sourceFeature'],'originalObject':prop['originalObject']})
    result = {'nativeSha256':digest,'chests':records,'architectureClearances':fit,'nativeLootRecords':0,
              'limits':'Native geometry, support, approach reserves and distinct face bindings only. '
                       'Native appearance, representative real click and unchanged save values require game review.'}
    (PROJECT/'review/native/town_chests.json').write_text(json.dumps(result,indent=2)+'\n')
    print({'townChests':len(records),'nativeFaces':sum(r['nativeFaces'] for r in records)})


if __name__=='__main__':
    review()
