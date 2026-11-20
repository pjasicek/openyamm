"""Fit the six original sprite-54 roofed wells without implementing their water rewards."""
import json
import math
from pathlib import Path

from author_props import ground_at, polygon_distance
from review_environment import edge_samples
from review_fortifications import rectangle

PROJECT = Path(__file__).resolve().parent
PALETTE = {'stone':'t18b01','wood':'t05a10','roof':'t05a05','metal':'gn_mtl03','water':'wtrtyl'}
LABELS = {'source_3_2_10':'Western shelf well','source_3_3_3':'Western meadow well',
          'source_3_11_1':'Royal quarter well','source_4_3_10':'Southwestern well',
          'source_4_9_11':'Might well','source_8_2_2':'Fortune well'}


def prepare(height):
    layout = json.loads((PROJECT/'layout.json').read_text())
    objects = json.loads((PROJECT/'source_objects.json').read_text())
    ids = json.loads((PROJECT/'implementation/feature_event_ids.json').read_text())
    result = []
    for feature in layout['features']:
        if feature['kind']!='spring':
            continue
        normal = [1,0] if feature['id']=='source_3_11_1' else [0,-1]
        prop = {'id':feature['id'],'semanticId':'mm5:sw/feature/'+feature['id'],
                'title':LABELS[feature['id']],'kind':'source well','sourceFeature':feature,
                'sourceIdentities':feature['sources'],'frontOrigin':feature['point'],
                'frontOutward':normal,'frontTangent':[-normal[1],normal[0]],
                'bounds':[-176,-144,176,144],'radius':228,'palette':'source_well',
                'purpose':feature['purpose'],'approachDistance':384,'standingRadius':96,
                'clearApproach':[-128,-384,128,-136],
                'behavior':'status-only placeholder; original water and stat effects deferred','placementChange':0}
        # Sample the physical ring/posts, not the overhanging roof, for their ground support.
        poly = rectangle(prop,[-136,-136,136,136])
        support = [ground_at(height,p) for a,b in zip(poly,poly[1:]+poly[:1]) for p in edge_samples(a,b)]
        prop['padHeight'] = math.ceil(max(support)+4)
        prop['foundation'] = {'skirtBottomZ':math.floor(min(support)-16),
                              'terrainSupportRange':[min(support),max(support)]}
        prop['eventId'] = ids[prop['semanticId']]
        prop['originalObject'], = [o for o in objects if o['source'] in feature['sources']]
        assert prop['originalObject']['sprite']==54
        result.append(prop)
    assert {p['id'] for p in result}==set(LABELS)
    return result


def review_fit(props,spec,semantic):
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
        start = [point[i]+prop['frontOutward'][i]*prop['approachDistance'] for i in range(2)]
        center_clearance = min(polygon_distance(point,p) for _,p in solids)
        standing_clearance = min(polygon_distance(start,p) for _,p in solids)
        assert center_clearance>=prop['radius']+32,(prop['id'],center_clearance)
        assert standing_clearance>=128,(prop['id'],standing_clearance)
        others = {p['semanticId']:p for p in semantic['props']+props if p['semanticId']!=prop['semanticId']}
        assert all(math.dist(point,p['frontOrigin'])>=prop['radius']+p['radius']+32
                   for p in others.values()),prop['id']
        assert all(math.dist(start,p['frontOrigin'])>=128+p['radius'] for p in others.values()),prop['id']
        result.append({'id':prop['id'],'centerSolidClearance':center_clearance,
                       'standingSolidClearance':standing_clearance,'standingPoint':start})
    return result


if __name__=='__main__':
    props = prepare((PROJECT/'landscape/heightmap.raw').read_bytes())
    spec = json.loads((PROJECT/'implementation/architecture.json').read_text())
    semantic = json.loads((PROJECT/'implementation/source/mm5_sw.semantic.json').read_text())
    result = {'status':'Source-well proposal; not integrated into active architecture',
              'props':props,'fit':review_fit(props,spec,semantic),
              'limits':'Existing royal-quarter planting needs refit; native terrain/context and interaction review pending.'}
    output = PROJECT/'review/source_well_study'
    output.mkdir(exist_ok=True)
    (output/'placements.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['fit'])
