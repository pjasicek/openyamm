"""Retain four original water clues with bounded, documented fits toward their immediate banks."""
import json
import math
from pathlib import Path

from author_message_bottles import geometry
from author_props import ground_at

PROJECT = Path(__file__).resolve().parent
PALETTE = {'glass':'mm5glass','paper':'mm5paper'}
FITS = {
    'source_4_2_2': {'point':[-20032,-20736], 'standing':[-19712,-20736], 'title':'Queen Kalindra message bottle'},
    'source_4_8_8': {'point':[-11520,-12096], 'standing':[-11520,-12416], 'title':'Xanthus message bottle'},
    'source_7_13_0': {'point':[20736,1408], 'standing':[20736,1728], 'title':'Lakeside message bottle'},
    'source_8_7_15': {'point':[11520,-128], 'standing':[11520,192], 'title':'Rapids warning bottle'},
}


def prepare(height):
    layout = json.loads((PROJECT/'layout.json').read_text())
    objects = json.loads((PROJECT/'source_objects.json').read_text())
    ids = json.loads((PROJECT/'implementation/feature_event_ids.json').read_text())
    result = []
    for feature in layout['features']:
        if feature['id'] not in FITS: continue
        fit = FITS[feature['id']]
        normal = [(fit['standing'][i]-fit['point'][i])/320 for i in range(2)]
        tangent = [-normal[1],normal[0]]
        prop = {'id':feature['id'],'semanticId':'mm5:sw/feature/'+feature['id'],
                'title':fit['title'],'kind':'message bottle','sourceFeature':feature,
                'sourceIdentities':feature['sources'],'frontOrigin':fit['point'],
                'frontOutward':normal,'frontTangent':tangent,
                'bounds':[-56,-24,100,24],'radius':104,'palette':'message_bottle',
                'purpose':feature['purpose'],'approachDistance':320,'standingRadius':96,
                'clearApproach':[-112,-416,112,-32],
                'behavior':'status-only placeholder; original note and item effects deferred',
                'placementChange':math.dist(feature['point'],fit['point'])}
        vertices = {tuple(v) for points,_,_ in geometry() for v in points}
        support = []
        for x,y,z in vertices:
            world = [fit['point'][i]+tangent[i]*x-normal[i]*y for i in range(2)]
            support.append(ground_at(height,world)-z)
        prop['padHeight'] = math.ceil(max(support))
        prop['support'] = {'fit':'rigid bottle rests against unmodified quantized native terrain',
                           'requiredTranslationZ':max(support),'maximumRoundingGap':1}
        prop['eventId'] = ids[prop['semanticId']]
        prop['originalObject'], = [o for o in objects if o['source'] in feature['sources']]
        assert prop['originalObject']['sprite']==7
        assert prop['placementChange']<=768
        result.append(prop)
    assert len(result)==4
    return result
