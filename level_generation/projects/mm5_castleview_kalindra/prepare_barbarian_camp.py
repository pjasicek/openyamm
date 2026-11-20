"""Retain the original raiding-camp fire with two modest shelters and a clear southern approach."""
import json
import math
from pathlib import Path

from author_props import ground_at
from native_scenery import native_records

PROJECT=Path(__file__).resolve().parent
PALETTE={'wood':'t06a10','cloth':'gnecclg2','crate':'crate_w64'}


def local_world(prop,point):
    return [prop['frontOrigin'][0]+point[0],prop['frontOrigin'][1]+point[1]]


def prepare(height):
    layout=json.loads((PROJECT/'layout.json').read_text())
    feature,=[f for f in layout['features'] if f['id']=='source_7_13_10']
    original,=[o for o in json.loads((PROJECT/'source_objects.json').read_text()) if o['source'] in feature['sources']]
    assert original['sprite']==11
    semantic='mm5:sw/feature/'+feature['id']
    ids=json.loads((PROJECT/'implementation/feature_event_ids.json').read_text())
    prop={'id':feature['id'],'semanticId':semantic,'title':'Barbarian camp','kind':'barbarian camp',
          'sourceFeature':feature,'sourceIdentities':feature['sources'],'originalObject':original,
          'frontOrigin':feature['point'],'frontOutward':[0,-1],'frontTangent':[1,0],
          'bounds':[-896,-256,832,896],'radius':1268,'padHeight':ground_at(height,feature['point']),
          'palette':'barbarian_camp','purpose':feature['purpose'],'approachDistance':416,'standingRadius':96,
          'clearApproach':[-112,-512,112,-96],'placementChange':0,'eventId':ids[semantic],
          'behavior':'status-only placeholder; camp destruction and experience reward deferred','shelters':[]}
    for center,width,depth,angle,top in [([-576,416],384,416,-.55,320),([496,560],320,352,.65,288)]:
        def xy(x,y):return [center[0]+x*math.cos(angle)-y*math.sin(angle),
                            center[1]+x*math.sin(angle)+y*math.cos(angle)]
        corners=[xy(x,y) for x in [-width/2,width/2] for y in [-depth/2,depth/2]]
        heights=[ground_at(height,local_world(prop,p)) for p in corners]
        prop['shelters'].append({'center':center,'width':width,'depth':depth,'angle':angle,'top':top,
                                'baseZ':math.ceil(max(heights))-prop['padHeight'],
                                'groundRange':heights})
    prop['nativeScenery']=native_records(prop,height,[('dec25',0,0,
        'Original camp focal fire; Garrote Gorge out05 entity 265 supplies appearance reference.')],
        'barbarian_camp_fire',light_radii={'dec25':128})
    fire,=prop['nativeScenery']
    fire['eventId']=prop['eventId']
    fire['behavior']='Reuse the camp local placeholder via secondary event; do not grant native campfire food.'
    prop['futureGrowingGround']=None
    prop['allowedSurfaceClasses']=[2]
    return [prop]
