"""Review authored wall footprints against all planned premises and actual road chains."""
import json
import math
from pathlib import Path

PROJECT=Path(__file__).resolve().parent


def overlap(a,b):
    for poly in [a,b]:
        for p,q in zip(poly,poly[1:]+poly[:1]):
            axis=(-(q[1]-p[1]),q[0]-p[0])
            aa=[sum(v[i]*axis[i] for i in range(2)) for v in a]
            bb=[sum(v[i]*axis[i] for i in range(2)) for v in b]
            if max(aa)<=min(bb)+1e-4 or max(bb)<=min(aa)+1e-4:
                return False
    return True


def distance(p,a,b):
    delta=[b[i]-a[i] for i in range(2)]
    t=max(0,min(1,sum((p[i]-a[i])*delta[i] for i in range(2))/sum(d*d for d in delta)))
    return math.dist(p,[a[i]+t*delta[i] for i in range(2)])


def rectangle(frame,bounds):
    x0,y0,x1,y1=bounds
    return [(frame['frontOrigin'][0]+frame['frontTangent'][0]*x-frame['frontOutward'][0]*y,
             frame['frontOrigin'][1]+frame['frontTangent'][1]*x-frame['frontOutward'][1]*y)
            for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]]


def main():
    semantic=json.loads((PROJECT/'implementation/source/mm5_sw.semantic.json').read_text())
    spec=json.loads((PROJECT/'implementation/architecture.json').read_text())
    roads=json.loads((PROJECT/'implementation/roads.json').read_text())
    solid=[]
    for f in semantic['fortifications']:
        if f['id']=='town_wall':
            solid += [(v['id'],v['footprint']) for v in f['segments']+f['towers']]
        else:
            solid += [(f['id']+'/'+t['id'],rectangle(f,t['bounds'])) for t in f['towers']]
    building_hits=[]
    for b in spec['buildings']:
        for component in b['components']:
            poly=rectangle(b,component['bounds'])
            for name,shape in solid:
                if overlap(poly,shape):
                    building_hits.append({'premises':b['id'],'component':component['id'],'fortification':name})
    road_hits=[]
    closest=None
    edges=0
    for path in roads['paths']:
        xy=lambda cell:((cell[1]-64)*512+256,(64-cell[0])*512-256)
        for a,b in zip(path['cells'],path['cells'][1:]):
            a,b=xy(a),xy(b)
            edges+=1
            for name,poly in solid:
                clearance=0 if overlap([a,b],poly) else min(
                    [distance(p,a,b) for p in poly]+
                    [distance(p,c,d) for p in [a,b] for c,d in zip(poly,poly[1:]+poly[:1])])
                record={'road':path['id'],'start':a,'end':b,'fortification':name,'clearance':round(clearance,2)}
                if closest is None or clearance<closest['clearance']:
                    closest=record
                if clearance<64:
                    road_hits.append(record)
    report={'status':'authoring footprint audit; native rendering and movement remain separate evidence',
            'plannedPremises':len(spec['buildings']),'solidFootprints':len(solid),'roadEdges':edges,
            'premisesOverlaps':building_hits,'roadCorridorRadius':64,'blockedRoadEdges':road_hits,
            'closestRoadApproach':closest,
            'gates':[{'id':g['id'],'openingWidth':g['openingWidth'],
                      'conservativeVerticalClearance':g['padHeight']+g['springHeight']-g['terrainSupportRange'][1],
                      'adjustment':g['layoutAdjustment']} for g in spec['gates']],
            'limits':['Tower/curtain and gate/curtain overlaps are intentional construction joints.',
                      'Checks all planned premises; native geometry presence is tracked in the interaction inventory.',
                      'This does not establish native movement, visual acceptance or final decoration clearance.']}
    output=PROJECT/'review/fortifications'
    output.mkdir(parents=True,exist_ok=True)
    (output/'footprints.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    assert not building_hits and not road_hits


if __name__=='__main__':
    main()
