"""Read back the camp's native fire override and the closed pyramid's fitted foundation."""
import csv
import hashlib
import json
import sys
from pathlib import Path

from author_props import ground_at
from review_environment import edge_samples
from review_waymarks import fit

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[2]
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file


def review():
    read=lambda path:json.loads((PROJECT/path).read_text())
    semantic=read('implementation/source/mm5_sw.semantic.json')
    scenery=read('implementation/scenery.json')['records']
    props=[p for p in semantic['props'] if p.get('kind') in ['barbarian camp','closed pyramid']]
    assert {p['id'] for p in props}=={'source_7_13_10','cross_world'}
    path=PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest==read('review/native/build.json')['nativeSha256']
    native=parse_odm_file(path)['payload'];height=bytes(native['height_map'])
    rows={int(r[0])-1:r for r in csv.reader((ROOT/'assets_dev/engine/data_tables/decoration_data.txt').open(),
                                          delimiter='\t') if r and r[0].isdigit()}
    records=[]
    for prop in props:
        event,=[e for e in semantic['events'] if e['semantic_id']==prop['semanticId']]
        assert event['id']==prop['eventId']
        model=native['bmodels'][event['bmodel_index']]
        assert len(event['faces'])==len(model['faces'])
        assert all(f['cog_triggered_number']==event['id'] for f in model['faces'])
        vertices=[[v[a] for a in 'xyz'] for v in model['vertices']]
        record={'id':prop['id'],'eventId':event['id'],'nativeFaces':len(model['faces'])}
        def burial(index):
            points=[vertices[i] for i in model['faces'][index]['vertex_indices']]
            assert max(p[2] for p in points)==min(p[2] for p in points)
            return min(ground_at(height,p)-points[0][2] for a,b in zip(points,points[1:]+points[:1])
                       for p in edge_samples(a,b))
        if prop['kind']=='barbarian camp':
            assert prop['frontOrigin']==prop['sourceFeature']['point'] and prop['originalObject']['sprite']==11
            assert len(prop['supportFeet'])==10
            burials=[burial(i) for i in prop['supportFeet']]
            assert min(burials)>=8,burials
            fire,=prop['nativeScenery']
            index=next(i+1 for i,r in enumerate(scenery) if r['id']==fire['id'])
            entity=native['entities'][index];row=rows[entity['decoration_list_id']]
            assert entity['decoration_list_id']==307 and row[1]=='dec25'
            assert int(row[6])==fire['expectedLightRadius']==128 and int(row[11],0)==0
            assert entity['event_id_secondary']==event['id'] and entity['event_id_primary']==0
            point=[entity['position'][a] for a in 'xyz']
            assert point==fire['position']==[20736,16128,1424]
            assert point[2]==ground_at(height,point)
            assert entity['ai_attributes']==0 and entity['special_trigger']==0
            record.update({'footBurials':burials,'fireEntity':index,'firePosition':point,'fireSecondaryEvent':event['id'],
                           'fireDescriptor':307,'descriptorLightRadius':128})
        else:
            assert prop['originalObject']['sprite']==34 and prop['frontOrigin']==[-8048,-4008]
            assert prop['placementChange']==256
            bottoms=[i for i,f in enumerate(model['faces']) if all(vertices[v][2]==600 for v in f['vertex_indices'])]
            assert len(bottoms)==1
            minimum=burial(bottoms[0]);assert minimum>=32
            copied=PROJECT/'implementation/runtime/worlds/mm5/textures/mm5pyrst.bmp'
            original=ROOT/'assets_dev/worlds/mm6/textures/egymedb.bmp'
            assert copied.read_bytes()==original.read_bytes()
            assert max(v[2] for v in vertices)==1168
            record.update({'minimumFoundationBurial':minimum,'stoneSha256':hashlib.sha256(copied.read_bytes()).hexdigest()})
        own={r['id'] for r in prop.get('nativeScenery',[])}
        record['clearance']=fit([prop],read('implementation/architecture.json'),semantic,
                                [r for r in scenery if r['id'] not in own])[0]
        records.append(record)
    (PROJECT/'review/native/camp_pyramid.json').write_text(json.dumps({'nativeSha256':digest,'features':records,
        'limits':'Written grounding, identity and bindings. Fire animation/light, absence of native food reward, '
                 'pyramid street context and real clicks require game review.'},indent=2)+'\n')
    print({'campAndPyramid':len(records)})


if __name__=='__main__':review()
