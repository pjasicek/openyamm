"""Verify Kalindra's exported courtyard, buried feet and single interior entrance."""
import hashlib
import json
import sys
from pathlib import Path

from prepare_bridges import triangle_clearance

PROJECT=Path(__file__).resolve().parent
sys.path.insert(0,str(PROJECT.parents[2]/'util'))
from map_export import parse_odm_file


def review():
    semantic=json.loads((PROJECT/'implementation/source/mm5_sw.semantic.json').read_text())
    castle=next((b for b in semantic['buildings'] if b['id']=='kalindra'),None)
    if castle is None:
        return
    native=PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    build=json.loads((PROJECT/'review/native/build.json').read_text())
    assert hashlib.sha256(native.read_bytes()).hexdigest()==build['nativeSha256']
    payload=parse_odm_file(native)['payload']
    height=bytes(payload['height_map'])
    indices={m['id'].split('/')[-1]:m['index'] for m in semantic['bmodels'] if m['assembly']=='kalindra'}
    for name in indices:
        digest=hashlib.sha256((PROJECT/'implementation/source/models'/(name+'.obj')).read_bytes()).hexdigest()
        assert build['sourceObjSha256'][name+'.obj']==digest,name

    def vertices(model,face):
        return [[model['vertices'][i][axis] for axis in ['x','y','z']] for i in face['vertex_indices']]

    checks=[]
    for item in castle['geometryChecks']:
        model=payload['bmodels'][indices[item['model']]]
        spans=[]
        for face_index in item['faces']:
            polygon=vertices(model,model['faces'][face_index])
            for i in range(1,len(polygon)-1):
                spans.append(triangle_clearance(height,[polygon[0],polygon[i],polygon[i+1]]))
        minimum=min(s['minimum'] for s in spans)
        maximum=max(s['maximum'] for s in spans)
        if item['kind']=='walking surface':
            assert minimum==maximum==6,(item,minimum,maximum)
            assert sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(polygon,polygon[1:]+polygon[:1]))>0
        else:
            assert item['kind'].startswith('buried') and maximum<=0,(item,maximum)
        checks.append({**item,'minimumClearance':minimum,'maximumClearance':maximum})

    assert len(castle['venues'])==1
    venue=castle['venues'][0]
    event=next(e for e in semantic['events'] if e['semantic_id']==venue['id'])
    model=payload['bmodels'][event['bmodel_index']]
    assert len(event['faces'])==1
    face=model['faces'][event['faces'][0]]
    expected=sorted([venue['door'][0]+castle['frontTangent'][0]*offset,
                     venue['door'][1]+castle['frontTangent'][1]*offset,castle['padHeight']+z]
                    for offset,z in [(-64,0),(64,0),(64,256),(-64,256)])
    assert sorted(vertices(model,face))==expected
    assert face['cog_triggered_number']==event['id']
    assert len(castle['interiorContacts'])==15
    assert all(not arrival['active'] for arrival in castle['arrivals'])
    result={'nativeSha256':build['nativeSha256'],'checks':checks,
            'door':{'id':venue['id'],'eventId':event['id'],'vertices':expected},
            'retainedInteriorContacts':castle['interiorContacts'],'inactiveArrivals':castle['arrivals'],
            'limits':'Actual native courtyard clearance, pier/bench foot burial and door event/quad checks. '
                     'Passage collision, visual composition, native clicks and ordinary movement/save-reload '
                     'require the separate recorded game review.'}
    (PROJECT/'review/native/kalindra.json').write_text(json.dumps(result,indent=2)+'\n')
    print({'kalindraContactChecks':len(checks),'kalindraDoorEvent':event['id']})


if __name__=='__main__':
    review()
