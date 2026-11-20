"""Read back the Western Tower's two door elevations and usable roof surface."""
import hashlib
import json
import sys
from pathlib import Path

PROJECT=Path(__file__).resolve().parent
sys.path.insert(0,str(PROJECT.parents[2]/'util'))
from map_export import parse_odm_file
from prepare_scenery import inside


def review():
    semantic=json.loads((PROJECT/'implementation/source/mm5_sw.semantic.json').read_text())
    tower=next((b for b in semantic['buildings'] if b['id']=='western'),None)
    if tower is None:
        return
    build=json.loads((PROJECT/'review/native/build.json').read_text())
    native=PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    assert hashlib.sha256(native.read_bytes()).hexdigest()==build['nativeSha256']
    payload=parse_odm_file(native)['payload']
    models={m['id'].split('/')[-1]:payload['bmodels'][m['index']]
            for m in semantic['bmodels'] if m['assembly']=='western'}
    for name in models:
        digest=hashlib.sha256((PROJECT/'implementation/source/models'/(name+'.obj')).read_bytes()).hexdigest()
        assert build['sourceObjSha256'][name+'.obj']==digest,name

    def vertices(model,face):
        return [[model['vertices'][i][axis] for axis in ['x','y','z']] for i in face['vertex_indices']]

    doors=[]
    for venue in tower['venues']:
        event=next(e for e in semantic['events'] if e['semantic_id']==venue['id'])
        model=payload['bmodels'][event['bmodel_index']]
        assert len(event['faces'])==1
        face=model['faces'][event['faces'][0]]
        z=tower['padHeight']+venue.get('heightAbovePad',0)
        expected=sorted([venue['door'][0]+tower['frontTangent'][0]*x,
                         venue['door'][1]+tower['frontTangent'][1]*x,z+height]
                        for x,height in [(-64,0),(64,0),(64,256),(-64,256)])
        assert sorted(vertices(model,face))==expected,venue['id']
        assert face['cog_triggered_number']==event['id']
        doors.append({'id':venue['id'],'eventId':event['id'],'vertices':expected})
    levels=sorted({p[2] for model in models.values() for p in
                   [[v[axis] for axis in ['x','y','z']] for v in model['vertices']]})
    assert levels[0]==736 and levels[-1]==3616,levels
    roof_z=tower['padHeight']+tower['components'][0]['eave']
    shaft=models['western_shaft']
    terrace=[(i,vertices(shaft,f)) for i,f in enumerate(shaft['faces'])
             if f['texture_name'].lower()=='t32a05b'
             and all(p[2]==roof_z for p in vertices(shaft,f))]
    assert len(terrace)==1,terrace
    terrace_index,polygon=terrace[0]
    assert sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(polygon,polygon[1:]+polygon[:1]))>0
    arrival=next(a for a in tower['arrivals'] if a['id'].endswith('/skyroad_roof'))
    assert arrival['position'][2]==roof_z and not arrival['active']
    upper=next(v for v in tower['venues'] if v.get('heightAbovePad'))
    standing=[upper['door'][i]+tower['frontOutward'][i]*64 for i in range(2)]
    samples=[]
    for step in range(9):
        p=[arrival['position'][i]+(standing[i]-arrival['position'][i])*step/8 for i in range(2)]
        for dx,dy in [(-32,-32),(-32,32),(32,-32),(32,32)]:
            q=[p[0]+dx,p[1]+dy]
            assert inside(q,[v[:2] for v in polygon]),q
            samples.append(q+[roof_z])
    access=models['western_roof_access']
    access_bottom=min(v['z'] for v in access['vertices'])
    assert access_bottom==roof_z-64
    report={'nativeSha256':build['nativeSha256'],'doors':doors,'verticalExtent':[levels[0],levels[-1]],
            'terrace':{'nativeFace':terrace_index,'vertices':polygon,'approachSupportSamples':samples},
            'roofAccessFoundationBottom':access_bottom,'arrivals':tower['arrivals'],
            'limits':'Actual native door quads, terrace support and upper-hut skirt elevation. '
                     'Does not prove complete collision clearance, normal movement, real clicks or save/reload; '
                     'those require the recorded game captures.'}
    (PROJECT/'review/native/western_tower.json').write_text(json.dumps(report,indent=2)+'\n')
    print({'westernDoorElevations':[d['vertices'][0][2] for d in doors],
           'roofSupportSamples':len(samples)})


if __name__=='__main__':
    review()
