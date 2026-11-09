"""Retain the original tower-direction and two warning contacts as readable timber signs."""
import json
import math
from pathlib import Path

from author_props import ground_at
from review_environment import edge_samples
from review_fortifications import rectangle

PROJECT = Path(__file__).resolve().parent
FACES = {'source_3_10_9':'mm5west','source_7_2_13':'mm5swim','source_7_11_2':'mm5danger'}
PALETTE = {'wood':'t05a10','metal':'gn_mtl03',**FACES}


def prepare(height):
    layout = json.loads((PROJECT/'layout.json').read_text())
    objects = json.loads((PROJECT/'source_objects.json').read_text())
    ids = json.loads((PROJECT/'implementation/feature_event_ids.json').read_text())
    result = []
    for feature in layout['features']:
        if feature['id'] not in FACES:continue
        prop = {'id':feature['id'],'semanticId':'mm5:sw/feature/'+feature['id'],
                'title':feature['title'],'kind':'source sign','sourceFeature':feature,
                'sourceIdentities':feature['sources'],'frontOrigin':feature['point'],
                'frontOutward':[0,-1],'frontTangent':[1,0],
                'bounds':[-140,-20,140,40],'radius':146,'palette':'source_sign',
                'purpose':feature['purpose'],'approachDistance':320,'standingRadius':96,
                'clearApproach':[-128,-320,128,-24],
                'behavior':'status-only placeholder; original sign meaning retained','placementChange':0,
                'faceTexture':FACES[feature['id']]}
        foot = rectangle(prop,[-16,8,16,40])
        support = [ground_at(height,p) for a,b in zip(foot,foot[1:]+foot[:1]) for p in edge_samples(a,b)]
        prop['padHeight'] = math.ceil(max(support)+4)
        prop['foundation'] = {'postBottomZ':math.floor(min(support)-24),
                              'terrainSupportRange':[min(support),max(support)]}
        prop['eventId'] = ids[prop['semanticId']]
        prop['originalObject'], = [o for o in objects if o['source'] in feature['sources']]
        assert prop['originalObject']['sprite']==38
        if feature['id']=='source_3_10_9':
            tower, = [b for b in layout['buildings'] if b['id']=='western']
            assert tower['center'][0]<feature['point'][0]
            prop['directionWorld'] = [-1,0]
        result.append(prop)
    assert len(result)==3
    return result


if __name__=='__main__':
    props = prepare((PROJECT/'landscape/heightmap.raw').read_bytes())
    output = PROJECT/'review/source_sign_study'
    output.mkdir(exist_ok=True)
    (output/'placements.json').write_text(json.dumps({'status':'Source sign proposal; not integrated',
        'props':props},indent=2)+'\n')
    print([{'id':p['id'],'point':p['frontOrigin'],'event':p['eventId']} for p in props])
