"""Fit the five source town sewer grates; proposal output is separate from active map authoring."""
import hashlib
import json
import math
from pathlib import Path

from author_props import ground_at, polygon_distance
from review_environment import edge_samples
from review_fortifications import rectangle

PROJECT = Path(__file__).resolve().parent
LABELS = {'source_29_1_13':'East Court sewer', 'source_29_2_29':'Guild Quarter sewer',
          'source_29_12_30':'South Wall sewer', 'source_29_26_1':'Northwest sewer',
          'source_29_30_18':'West Gate sewer'}
PALETTE = {'stone':'t18b01', 'metal':'gn_mtl03', 'dark':'solid01'}


def prepare(height):
    layout = json.loads((PROJECT/'layout.json').read_text())
    sources = json.loads((PROJECT/'source_objects.json').read_text())
    ids = json.loads((PROJECT/'implementation/feature_event_ids.json').read_text())
    result = []
    for feature in layout['features']:
        if feature['id'] not in LABELS:
            continue
        point = [-1568,-4762] if feature['id']=='source_29_12_30' else list(feature['point'])
        # The east side faces the open gate approach; north/south returns intersect tower reserves.
        normal = [1,0] if feature['id']=='source_29_30_18' else [0,1]
        prop = {'id':feature['id'], 'semanticId':'mm5:sw/feature/'+feature['id'],
                'title':LABELS[feature['id']], 'kind':'town sewer grate', 'sourceFeature':feature,
                'sourceIdentities':feature['sources'], 'frontOrigin':point,
                'frontOutward':normal, 'frontTangent':[-normal[1],normal[0]],
                'bounds':[-128,-96,128,96], 'radius':160, 'palette':'town_sewer',
                'purpose':feature['purpose'], 'approachDistance':320, 'standingRadius':96,
                'behavior':'status-only placeholder; distinct sewer route retained but unavailable',
                'placementChange':math.dist(point,feature['point'])}
        poly = rectangle(prop,prop['bounds'])
        support = [ground_at(height,p) for a,b in zip(poly,poly[1:]+poly[:1]) for p in edge_samples(a,b)]
        prop['padHeight'] = math.ceil(max(support)+4)
        prop['foundation'] = {'skirtBottomZ':math.floor(min(support)-16),
                              'terrainSupportRange':[min(support),max(support)],
                              'darkCoverZ':prop['padHeight'], 'rimTopZ':prop['padHeight']+12}
        if feature['id']=='source_29_30_18':
            # This road patch is planar even across the grid edge. Fit the whole closed hatch to that plane.
            center_height = ground_at(height,point)
            tangent = prop['frontTangent']
            slopes = [(ground_at(height,[point[i]+axis[i]*128 for i in range(2)])-center_height)/128
                      for axis in [tangent,[-v for v in normal]]]
            for a,b in zip(poly,poly[1:]+poly[:1]):
                for q in edge_samples(a,b):
                    delta = [q[i]-point[i] for i in range(2)]
                    local = [sum(delta[i]*axis[i] for i in range(2))
                             for axis in [tangent,[-v for v in normal]]]
                    assert abs(ground_at(height,q)-center_height-sum(local[i]*slopes[i] for i in range(2)))<.01
            prop['padHeight'] = math.ceil(center_height+4)
            prop['foundation'].update({'localSlope':slopes,'skirtBottomZ':prop['padHeight']-24,
                                      'darkCoverZ':prop['padHeight'],'rimTopZ':prop['padHeight']+12,
                                      'outerLipZ':prop['padHeight']-4})
        prop['eventId'] = ids[prop['semanticId']]
        arrival = [point[i]+normal[i]*320 for i in range(2)]
        prop['arrivals'] = [{'id':prop['semanticId']+'/ground_return',
                             'position':arrival+[round(ground_at(height,arrival))], 'active':False,
                             'purpose':'Separate future return from sewer map 30; outside the closed grate.'}]
        prop['originalObject'], = [o for o in sources if o['source'] in feature['sources']]
        assert prop['originalObject']['sprite']==22
        result.append(prop)
    assert len(result)==5
    return result


def review_fit(props, spec, semantic):
    solids = [(b['id'],rectangle(b,c['bounds'])) for b in spec['buildings'] for c in b['components']]
    solids += [(b['id'],rectangle(b,[d['bounds'][i] for i in [0,1,3,4]]))
               for b in spec['buildings'] for d in b['details']]
    for fort in semantic['fortifications']:
        if fort['id']=='town_wall':
            solids.extend((r['id'],r['footprint']) for r in fort['segments']+fort['towers'])
        else:
            solids.extend((fort['id'],rectangle(fort,t['bounds'])) for t in fort['towers'])
    result = []
    for prop in props:
        point = prop['frontOrigin']
        arrival = prop['arrivals'][0]['position'][:2]
        clearances = {
            'nearestSolidFromCenter':min(polygon_distance(point,poly) for _,poly in solids),
            'returnRadiusFromSolids':min(polygon_distance(arrival,poly) for _,poly in solids),
            'nearestPropEdge':min(math.dist(point,p['frontOrigin'])-p['radius']-prop['radius']
                                 for p in semantic['props'] if p['semanticId']!=prop['semanticId']),
            'nearestDoorApproach':min(math.dist(point,[v['door'][i]+b['frontOutward'][i]*256
                                                     for i in range(2)])
                                     for b in spec['buildings'] for v in b['venues'])}
        assert clearances['nearestSolidFromCenter']>=192,(prop['id'],clearances)
        assert clearances['returnRadiusFromSolids']>=128,(prop['id'],clearances)
        assert clearances['nearestPropEdge']>=32,(prop['id'],clearances)
        assert clearances['nearestDoorApproach']>=prop['radius']+128,(prop['id'],clearances)
        result.append({'id':prop['id'],**clearances})
    return result


if __name__=='__main__':
    spec = json.loads((PROJECT/'implementation/architecture.json').read_text())
    semantic = json.loads((PROJECT/'implementation/source/mm5_sw.semantic.json').read_text())
    height = (PROJECT/'landscape/heightmap.raw').read_bytes()
    result = prepare(height)
    clearances = review_fit(result,spec,semantic)
    output = PROJECT/'review/town_sewer_proposal'
    output.mkdir(exist_ok=True)
    (output/'placements.json').write_text(json.dumps({'status':'Fitted proposal; not in the native map yet',
        'heightSha256':hashlib.sha256(height).hexdigest(),'props':result,'clearances':clearances},indent=2)+'\n')
    print([{'id':p['id'],'point':p['frontOrigin'],'event':p['eventId']}
           for p in result])
