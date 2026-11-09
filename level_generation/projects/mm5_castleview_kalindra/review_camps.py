"""Read back temporary-site feet, wheel contact and visible interaction bindings."""
import hashlib
import json
import sys
from pathlib import Path

from prepare_bridges import triangle_clearance
from prepare_camps import IDS

PROJECT=Path(__file__).resolve().parent
sys.path.insert(0,str(PROJECT.parents[2]/'util'))
from map_export import parse_odm_file


def review():
    semantic=json.loads((PROJECT/'implementation/source/mm5_sw.semantic.json').read_text())
    sites=[b for b in semantic['buildings'] if b['id'] in IDS]
    if not sites:return
    native=PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    build=json.loads((PROJECT/'review/native/build.json').read_text())
    assert hashlib.sha256(native.read_bytes()).hexdigest()==build['nativeSha256']
    payload=parse_odm_file(native)['payload'];height=bytes(payload['height_map'])
    models={m['id'].split('/')[-1]:m['index'] for m in semantic['bmodels'] if m['assembly'] in IDS}
    for name in models:
        digest=hashlib.sha256((PROJECT/'implementation/source/models'/(name+'.obj')).read_bytes()).hexdigest()
        assert build['sourceObjSha256'][name+'.obj']==digest,name

    def clearance(item):
        model=payload['bmodels'][models[item['model']]]
        spans=[]
        for index in item['faces']:
            face=model['faces'][index]
            poly=[[model['vertices'][i][axis] for axis in ['x','y','z']] for i in face['vertex_indices']]
            for i in range(1,len(poly)-1):
                spans.append(triangle_clearance(height,[poly[0],poly[i],poly[i+1]]))
        return min(s['minimum'] for s in spans),max(s['maximum'] for s in spans)

    checks=[];bindings=[]
    for site in sites:
        for item in site['geometryChecks']:
            minimum,maximum=clearance(item)
            assert maximum<=0,(site['id'],item,minimum,maximum)
            checks.append({'site':site['id'],**item,'minimumClearance':minimum,'maximumClearance':maximum})
        for item in site.get('wheelContacts',[]):
            minimum,maximum=clearance(item)
            assert minimum==0 and maximum>0,(site['id'],item,minimum,maximum)
            checks.append({'site':site['id'],**item,'kind':'wheel tread meets ground',
                           'minimumClearance':minimum,'maximumClearance':maximum})
        assert len(site['venues'])==1
        venue=site['venues'][0]
        assert venue['occupants']==[p['id'] for p in site['people']]
        event=next(e for e in semantic['events'] if e['semantic_id']==venue['id'])
        model=payload['bmodels'][event['bmodel_index']]
        assert all(model['faces'][i]['cog_triggered_number']==event['id'] for i in event['faces'])
        assert venue['interactionSurface'] in ['tent flap','camp counter']
        bindings.append({'site':site['id'],'venue':venue['id'],'surface':venue['interactionSurface'],
                         'eventId':event['id'],'occupants':venue['occupants']})
    result={'nativeSha256':build['nativeSha256'],'checks':checks,'bindings':bindings,
            'limits':'Native structural feet, counter supports, supply bases, wheel tread and semantic/event bindings. '
                     'Does not establish appearance, full movement clearance or real click behavior; '
                     'the separately inspected game views supply that evidence.'}
    (PROJECT/'review/native/camps.json').write_text(json.dumps(result,indent=2)+'\n')
    print({'campSupportChecks':len(checks),'campVenueBindings':len(bindings)})


if __name__=='__main__':review()
