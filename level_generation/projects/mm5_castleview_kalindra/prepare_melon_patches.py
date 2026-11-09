"""Retain all four original quest-food patches independently of Nibbler's future growing-ground reservation."""
import json
import math
import random
from pathlib import Path

from author_melon_patches import fruit_geometry
from author_props import ground_at
from review_environment import edge_samples

PROJECT = Path(__file__).resolve().parent
PALETTE = {'fruit':'mm5melon','leaf':'mm5vine','stem':'mm5glass'}


def prepare(height):
    layout = json.loads((PROJECT/'layout.json').read_text())
    objects = json.loads((PROJECT/'source_objects.json').read_text())
    ids = json.loads((PROJECT/'implementation/feature_event_ids.json').read_text())
    result = []
    for feature in layout['features']:
        if feature['kind']!='quest_item': continue
        rng = random.Random(feature['id'])
        prop = {'id':feature['id'],'semanticId':'mm5:sw/feature/'+feature['id'],
                'title':'Monga Melon patch','kind':'melon patch','sourceFeature':feature,
                'sourceIdentities':feature['sources'],'frontOrigin':feature['point'],
                'frontOutward':[0,-1],'frontTangent':[1,0],
                'bounds':[-256,-224,256,224],'radius':341,'palette':'melon_patch',
                'purpose':feature['purpose'],'approachDistance':416,'standingRadius':96,
                'clearApproach':[-112,-512,112,-224],'placementChange':0,
                'behavior':'status-only placeholder; quest food pickup and encounters deferred',
                'padHeight':ground_at(height,feature['point']),'fruit':[],'vines':[],'leaves':[], 'leafStalks':[]}
        for x,y in [(-120,-64),(0,-96),(116,-28),(-80,64),(32,36),(136,96)]:
            x,y = x+rng.randrange(-12,13),y+rng.randrange(-12,13)
            radii = [rng.randrange(28,41),rng.randrange(22,29),rng.randrange(22,29)]
            angle = rng.uniform(-math.pi,math.pi)
            geometry = fruit_geometry(radii,angle)
            lift = []
            for points,_ in geometry:
                for a,b in zip(points,points[1:]+points[:1]):
                    length = math.dist(a[:2],b[:2])
                    if length==0:continue
                    first = [feature['point'][0]+x+a[0],feature['point'][1]+y+a[1]]
                    last = [feature['point'][0]+x+b[0],feature['point'][1]+y+b[1]]
                    for sample in edge_samples(first,last):
                        t = math.dist(first,sample)/length
                        lift.append(ground_at(height,sample)-(a[2]+t*(b[2]-a[2])))
            prop['fruit'].append({'center':[x,y,math.ceil(max(lift))-prop['padHeight']],
                                  'radii':radii,'angle':angle})
            middle = [x*.45+rng.randrange(-18,19),y*.45+rng.randrange(-18,19)]
            prop['vines'].append([[0,0],middle,[x,y]])
            for lx,ly in [middle,[x*.72,y*.72],[x+rng.choice([-42,42]),y+rng.choice([-36,36])]]:
                leaf_angle,scale = rng.uniform(-math.pi,math.pi),rng.uniform(.8,1.15)
                prop['leaves'].append([lx,ly,leaf_angle,scale])
                base = [lx+28*math.sin(leaf_angle)*scale,ly-28*math.cos(leaf_angle)*scale]
                prop['leafStalks'].append([middle,base])
        prop['eventId'] = ids[prop['semanticId']]
        prop['originalObject'], = [o for o in objects if o['source'] in feature['sources']]
        assert prop['originalObject']['sprite']==31
        result.append(prop)
    assert len(result)==4
    return result
