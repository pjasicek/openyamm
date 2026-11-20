"""Preserve the five ordinary town chests as closed, status-only exterior props."""
import json
import math
from pathlib import Path

from author_props import ground_at, polygon_distance
from review_environment import edge_samples
from review_fortifications import overlap, rectangle

PROJECT = Path(__file__).resolve().parent
PALETTE = {'wood':'t06a10','metal':'gn_mtl03','dark':'solid01'}


def prepare(height):
    layout = json.loads((PROJECT/'layout.json').read_text())
    objects = json.loads((PROJECT/'source_objects.json').read_text())
    ids = json.loads((PROJECT/'implementation/feature_event_ids.json').read_text())
    result = []
    for feature in layout['features']:
        if feature['kind']!='chest' or not feature['id'].startswith('source_29_'):
            continue
        normal = ([1,0] if feature['id']=='source_29_18_30' else
                  [-1,0] if feature['id']=='source_29_20_11' else [0,1])
        prop = {'id':feature['id'],'semanticId':'mm5:sw/feature/'+feature['id'],
                'title':feature['title'],'kind':'town chest','sourceFeature':feature,
                'sourceIdentities':feature['sources'],'frontOrigin':feature['point'],
                'frontOutward':normal,'frontTangent':[-normal[1],normal[0]],
                'bounds':[-96,-64,96,64],'radius':116,'palette':'town_chest',
                'purpose':feature['purpose'],'approachDistance':256,'standingRadius':96,
                'behavior':'status-only placeholder; chest stays closed and grants no loot',
                'placementChange':0}
        poly = rectangle(prop,prop['bounds'])
        support = [ground_at(height,p) for a,b in zip(poly,poly[1:]+poly[:1]) for p in edge_samples(a,b)]
        prop['padHeight'] = math.ceil(max(support)+4)
        prop['foundation'] = {'feetBottomZ':math.floor(min(support)-8),
                              'terrainSupportRange':[min(support),max(support)]}
        prop['eventId'] = ids[prop['semanticId']]
        prop['originalObject'], = [o for o in objects if o['source'] in feature['sources']]
        assert prop['originalObject']['sprite']==15
        result.append(prop)
    assert len(result)==5
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
    report = []
    for prop in props:
        poly = rectangle(prop,prop['bounds'])
        assert not any(overlap(poly,p) for _,p in solids),prop['id']
        shell_clearance = min(min(polygon_distance(v,p) for v in poly) for _,p in solids)
        assert shell_clearance>=32,(prop['id'],shell_clearance)
        start = [prop['frontOrigin'][i]+prop['frontOutward'][i]*256 for i in range(2)]
        standing = min(polygon_distance(start,p) for _,p in solids)
        assert standing>=128,(prop['id'],standing)
        for other in semantic['props']+props:
            if other['semanticId']==prop['semanticId']:
                continue
            assert math.dist(prop['frontOrigin'],other['frontOrigin'])>=prop['radius']+other['radius']+32, (
                prop['id'],other['id'])
            assert math.dist(start,other['frontOrigin'])>=96+other['radius'],(prop['id'],other['id'],'approach')
        report.append({'id':prop['id'],'shellClearance':shell_clearance,'standingClearance':standing,
                       'standingPoint':start,'placementChange':0})
    return report


if __name__=='__main__':
    props = prepare((PROJECT/'landscape/heightmap.raw').read_bytes())
    spec = json.loads((PROJECT/'implementation/architecture.json').read_text())
    semantic = json.loads((PROJECT/'implementation/source/mm5_sw.semantic.json').read_text())
    report = {'status':'Fitted proposal; not yet in the active authoring specification',
              'props':props,'fit':review_fit(props,spec,semantic)}
    (PROJECT/'review/exterior_feature_study/chest_placements.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['fit'])
