"""Preserve the northern prayer contact as an open four-column stone shrine."""
import json
import math
from pathlib import Path

from author_props import ground_at
from review_environment import edge_samples
from review_fortifications import rectangle

PROJECT = Path(__file__).resolve().parent
PALETTE = {'stone':'gcst2-bs','rim':'gstn1bot','column':'gstn1cl'}


def prepare(height):
    layout = json.loads((PROJECT/'layout.json').read_text())
    feature, = [f for f in layout['features'] if f['kind']=='shrine']
    prop = {'id':feature['id'],'semanticId':'mm5:sw/feature/'+feature['id'],
            'title':'Northern shrine','kind':'source shrine','sourceFeature':feature,
            'sourceIdentities':feature['sources'],'frontOrigin':feature['point'],
            'frontOutward':[0,-1],'frontTangent':[1,0],
            'bounds':[-304,-240,304,240],'radius':388,'palette':'source_shrine',
            'purpose':feature['purpose'],'approachDistance':768,'standingRadius':96,
            'clearApproach':[-112,-768,112,240],
            'behavior':'status-only placeholder; prayer and level reward deferred','placementChange':0,
            'columnCenters':[[-192,-128],[192,-128],[-192,128],[192,128]]}
    support = []
    foundations = []
    for x,y in prop['columnCenters']:
        poly = rectangle(prop,[x-80,y-80,x+80,y+80])
        ground = [ground_at(height,p) for a,b in zip(poly,poly[1:]+poly[:1]) for p in edge_samples(a,b)]
        support.extend(ground)
        foundations.append({'center':[x,y],'bottomZ':math.floor(min(ground)-24),
                            'terrainSupportRange':[min(ground),max(ground)]})
    prop['padHeight'] = math.ceil(max(support)+4)
    prop['foundation'] = {'columns':foundations,'terrainSupportRange':[min(support),max(support)]}
    prop['eventId'] = json.loads((PROJECT/'implementation/feature_event_ids.json').read_text())[prop['semanticId']]
    objects = json.loads((PROJECT/'source_objects.json').read_text())
    prop['originalObject'], = [o for o in objects if o['source'] in feature['sources']]
    assert prop['originalObject']['sprite']==37
    # The front/rear passage stays on native terrain, without an obstructing invented platform.
    center = prop['frontOrigin']
    line = [[center[i]-prop['frontOutward'][i]*y for i in range(2)] for y in [-768,240]]
    samples = edge_samples(*line)
    heights = [ground_at(height,p) for p in samples]
    max_grade = max(abs(b-a)/math.dist(p,q) for a,b,p,q in zip(heights,heights[1:],samples,samples[1:]))
    assert max_grade<=.5, ('Shrine approach needs a terrain fit',max_grade)
    prop['approachMaximumGrade'] = max_grade
    return prop


if __name__=='__main__':
    prop = prepare((PROJECT/'landscape/heightmap.raw').read_bytes())
    output = PROJECT/'review/source_shrine_study'
    output.mkdir(exist_ok=True)
    (output/'placement.json').write_text(json.dumps({'status':'Shrine proposal; not integrated','prop':prop},indent=2)+'\n')
    print({'point':prop['frontOrigin'],'pad':prop['padHeight'],'event':prop['eventId'],
           'approachMaximumGrade':prop['approachMaximumGrade']})
