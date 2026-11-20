"""Check the written three signboards and northern shrine, retaining readable faces and clear access."""
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

from PIL import Image
from author_props import ground_at, polygon_distance
from prepare_source_signs import FACES
from prepare_source_shrine import PALETTE as SHRINE_PALETTE
from review_environment import edge_samples
from review_fortifications import distance, rectangle

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file


def fit(props,spec,semantic,scenery):
    solids = [(b['id'],rectangle(b,c['bounds'])) for b in spec['buildings'] for c in b['components']]
    solids += [(b['id'],rectangle(b,[d['bounds'][i] for i in [0,1,3,4]]))
               for b in spec['buildings'] for d in b['details']]
    for fort in semantic['fortifications']:
        if fort['id']=='town_wall':
            solids.extend((r['id'],r['footprint']) for r in fort['segments']+fort['towers'])
        else:
            solids.extend((fort['id'],rectangle(fort,t['bounds'])) for t in fort['towers'])
    rows = {int(r[0])-1:r for r in csv.reader(
        (ROOT/'assets_dev/engine/data_tables/decoration_data.txt').open(),delimiter='\t') if r and r[0].isdigit()}
    records = []
    for prop in props:
        point = prop['frontOrigin']
        start = [point[i]+prop['frontOutward'][i]*prop['approachDistance'] for i in range(2)]
        center_clearance = min(polygon_distance(point,p) for _,p in solids)
        standing_clearance = min(polygon_distance(start,p) for _,p in solids)
        assert center_clearance>=prop['radius']+32,(prop['id'],center_clearance)
        assert standing_clearance>=128,(prop['id'],standing_clearance)
        assert all(math.dist(point,p['frontOrigin'])>=prop['radius']+p['radius']+32
                   for p in semantic['props'] if p['semanticId']!=prop['semanticId']),prop['id']
        end = [point[i]+prop['frontOutward'][i]*24 for i in range(2)]
        sprite_clearance = min(distance(s['position'][:2],start,end)-int(rows[s['descriptorId']][4]) for s in scenery)
        assert sprite_clearance>=128,(prop['id'],sprite_clearance)
        records.append({'id':prop['id'],'centerSolidClearance':center_clearance,
                        'standingSolidClearance':standing_clearance,'spriteApproachClearance':sprite_clearance})
    return records


def review():
    read = lambda name: json.loads((PROJECT/name).read_text())
    semantic = read('implementation/source/mm5_sw.semantic.json')
    props = [p for p in semantic['props'] if p.get('kind') in ['source sign','source shrine']]
    assert len(props)==4 and {p['id'] for p in props}==set(FACES)|{'source_3_8_14'}
    clearances = fit(props,read('implementation/architecture.json'),semantic,read('implementation/scenery.json')['records'])
    native = PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    digest = hashlib.sha256(native.read_bytes()).hexdigest()
    assert digest==read('review/native/build.json')['nativeSha256']
    payload = parse_odm_file(native)['payload']
    height = bytes(payload['height_map'])
    ids = read('implementation/feature_event_ids.json')
    records = []
    for prop in props:
        event, = [e for e in semantic['events'] if e['semantic_id']==prop['semanticId']]
        assert event['id']==prop['eventId']==ids[prop['semanticId']]
        assert prop['frontOrigin']==prop['sourceFeature']['point']
        model = payload['bmodels'][event['bmodel_index']]
        assert len(event['faces'])==len(model['faces'])
        assert all(f['cog_triggered_number']==event['id'] for f in model['faces'])
        vertices = [[v[a] for a in 'xyz'] for v in model['vertices']]
        polygons = [[vertices[i] for i in f['vertex_indices']] for f in model['faces']]
        result = {'id':prop['id'],'eventId':event['id'],'nativeBmodel':event['bmodel_index'],
                  'nativeFaces':len(model['faces']),'sourceFeature':prop['sourceFeature'],
                  'originalObject':prop['originalObject']}
        if prop['kind']=='source sign':
            assert prop['originalObject']['sprite']==38
            assert {f['texture_name'].lower() for f in model['faces']}=={'t05a10','gn_mtl03',prop['faceTexture']}
            label, = [f for f in model['faces'] if f['texture_name'].lower()==prop['faceTexture']]
            assert max(label['texture_us'])-min(label['texture_us'])==256
            assert max(label['texture_vs'])-min(label['texture_vs'])==128
            with Image.open(PROJECT/'implementation/runtime/worlds/mm5/textures'/(prop['faceTexture']+'.png')) as image:
                assert image.size==(256,128)
            bottom = prop['foundation']['postBottomZ']
            foot, = [p for p in polygons if all(v[2]==bottom for v in p)]
            burial = min(ground_at(height,v)-bottom for a,b in zip(foot,foot[1:]+foot[:1]) for v in edge_samples(a,b))
            assert burial>=24,(prop['id'],burial)
            assert max(v[2] for v in vertices)==prop['padHeight']+316
            result.update({'minimumPostBurial':burial,'labelTexture':prop['faceTexture'],'labelSize':[256,128]})
        else:
            assert prop['originalObject']['sprite']==37
            assert {f['texture_name'].lower() for f in model['faces']}==set(SHRINE_PALETTE.values())
            foot_burials = []
            for support in prop['foundation']['columns']:
                x,y = support['center']
                center = [prop['frontOrigin'][i]+prop['frontTangent'][i]*x-prop['frontOutward'][i]*y for i in range(2)]
                bottom = support['bottomZ']
                foot, = [p for p in polygons if all(v[2]==bottom for v in p) and
                          math.dist(center,[sum(v[i] for v in p)/len(p) for i in range(2)])<1]
                burial = min(ground_at(height,v)-bottom for a,b in zip(foot,foot[1:]+foot[:1]) for v in edge_samples(a,b))
                assert burial>=24,(prop['id'],center,burial)
                foot_burials.append(burial)
            low_vertices = [v for v in vertices if v[2]<prop['padHeight']+512]
            inner_edge = min(abs(sum((v[i]-prop['frontOrigin'][i])*prop['frontTangent'][i] for i in range(2)))
                             for v in low_vertices)
            assert inner_edge>=112, ('Shrine passage narrowed',inner_edge)
            assert max(v[2] for v in vertices)==prop['padHeight']+696
            result.update({'columnFootBurials':foot_burials,'minimumCentralPassageWidth':inner_edge*2,
                           'floor':'unchanged native terrain; no blocking platform'})
        records.append(result)
    output = {'nativeSha256':digest,'features':records,'clearances':clearances,
              'limits':'Written geometry, sign UV extent, support and bindings only. Native appearance, '
                       'representative actual clicks and shrine passage require game review.'}
    (PROJECT/'review/native/waymarks.json').write_text(json.dumps(output,indent=2)+'\n')
    print({'waymarks':len(records),'nativeFaces':sum(r['nativeFaces'] for r in records)})


if __name__=='__main__':
    review()
