"""Refit the planned native foliage to the current buildings, roads and curtain.

Source orchard identities remain distinct; rewards are local status stubs only.
Unresolved placements are reported rather than silently dropped from the inventory.
"""
import collections
import csv
import hashlib
import json
import math
from pathlib import Path

from PIL import Image
from review_fortifications import distance, rectangle
from author_chapter_court import PLANTS as CHAPTER_PLANTS, APPROACH as CHAPTER_APPROACH

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[2]


def inside(point,poly):
    signs=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        signs.append((b[0]-a[0])*(point[1]-a[1])-(b[1]-a[1])*(point[0]-a[0]))
    return min(signs)>=-1e-6 or max(signs)<=1e-6


def polygon_distance(point,poly):
    return 0 if inside(point,poly) else min(distance(point,a,b) for a,b in zip(poly,poly[1:]+poly[:1]))


def prepare():
    plan=json.loads((PROJECT/'landscape/decorations.json').read_text())
    buffer=json.loads((PROJECT/'landscape/buffer_scenery.json').read_text())
    spec=json.loads((PROJECT/'implementation/architecture.json').read_text())
    semantic=json.loads((PROJECT/'implementation/source/mm5_sw.semantic.json').read_text())
    native_sites=[b for b in semantic['buildings']+semantic['props']+semantic['scenery_groups']
                  if b.get('nativeScenery')]
    fixed_native=[r for b in native_sites for r in b['nativeScenery']]
    native_reserves=[rectangle(b,b['clearApproach']) for b in native_sites if b['clearApproach']]
    native_reserves += [rectangle(b,b['futureGrowingGround']) for b in native_sites if b['futureGrowingGround']]
    native_reserves += [rectangle(p,p['clearApproach']) for p in spec['props'] if p.get('clearApproach')]
    roads=json.loads((PROJECT/'implementation/roads.json').read_text())
    layout=json.loads((PROJECT/'layout.json').read_text())
    arrivals=[layout['defaultArrival']['point']]+[r['plannedPoint'] for r in layout['mirrorArrivals']]
    arrivals += [r['arrival'] for r in layout['travel']]
    approaches=[([v['door'][i]+b['frontOutward'][i]*256 for i in range(2)],b['id'],128)
                for b in spec['buildings'] for v in b['venues'] if not v.get('heightAbovePad',0)]
    approaches += [([p['frontOrigin'][i]+p['frontOutward'][i]*p['approachDistance'] for i in range(2)],
                    p['id'],p['standingRadius']) for p in spec['props'] if 'approachDistance' in p]
    height=(PROJECT/'landscape/heightmap.raw').read_bytes()
    surface=list(Image.open(PROJECT/'landscape/surface_classes.png').getdata())
    table=ROOT/'assets_dev/engine/data_tables/decoration_data.txt'
    rows={int(r[0])-1:r for r in csv.reader(table.open(),delimiter='\t') if r and r[0].isdigit()}
    solids=[]
    for b in spec['buildings']:
        for c in b['components']:
            solids.append((b['id'],rectangle(b,c['bounds'])))
        for d in b['details']:
            x0,y0,z0,x1,y1,z1=d['bounds']
            solids.append((b['id'],rectangle(b,[x0,y0,x1,y1])))
    for f in semantic['fortifications']:
        if f['id']=='town_wall':
            solids.extend((r['id'],r['footprint']) for r in f['segments']+f['towers'])
        else:
            solids.extend((f['id'],rectangle(f,t['bounds'])) for t in f['towers'])
    solids.extend((p['id'],rectangle(p,p['bounds'])) for p in spec['props'] if 'bounds' in p)
    solids.extend((p['id'],polygon) for p in semantic['props'] for polygon in p.get('solidFootprints',[]))
    for bridge in semantic.get('bridges',[]):
        solids.extend((bridge['id'],[p[:2] for p in s['corners']]) for s in bridge['surfaces'])
    fitted_props={r['semanticId']:r for r in semantic['props']}
    props=[{**r,'position':fitted_props[r['id']]['frontOrigin']+[fitted_props[r['id']]['padHeight']]}
           if r['id'] in fitted_props else r
           for r in plan['records'] if r['category'] in ['props','interactive']]
    road_segments=[]
    xy=lambda cell:((cell[1]-64)*512+256,(64-cell[0])*512-256)
    for path in roads['paths']:
        road_segments.extend((xy(a),xy(b)) for a,b in zip(path['cells'],path['cells'][1:]))
    groups={g['id']:g for g in plan['groups']}
    accepted=[]
    unresolved=[]
    events=[]
    orchard=[r for r in plan['records'] if r.get('group')=='public_orchard']
    orchard_ids={r['id']:i for i,r in enumerate(orchard)}
    barrel_ids={r['id']:i for i,r in enumerate(r for r in plan['records'] if r['name']=='dec03')}
    assert len(barrel_ids)==6
    assert len(orchard_ids)==55

    def cell(point):
        return min(127,max(0,int((32768-point[1])/512)))*128+min(127,max(0,int((point[0]+32768)/512)))

    def ground(point):
        col=(point[0]+32768)/512
        row=(32768-point[1])/512
        c,r=int(col),int(row)
        u,v=col-c,row-r
        a,b,d,e=[height[index]*32 for index in [r*128+c,r*128+c+1,(r+1)*128+c,(r+1)*128+c+1]]
        return round(a+(b-a)*u+(d-a)*v if u+v<=1 else e+(d-e)*(1-u)+(b-e)*(1-v))

    for original in plan['records']+buffer['records']:
        barrel=original['id'] in barrel_ids
        if original['category'] not in ['trees','plants','rocks'] and not barrel:
            continue
        row=rows[original['descriptorId']]
        assert row[1].lower()==original['name'].lower(),original['id']
        assert int(row[11],0)==0 and (barrel or row[2] in ['tree','rock','flower','shrub']),row
        asset=ROOT/original['assetSource']
        assert asset.is_file(),asset
        visual=original['visualRadius']
        clearance=max(int(row[4])+32,visual*.65 if original['category']=='trees' else visual*.5)
        start=original['position'][:2]
        chapter_plant = original.get('group')=='chapter_garden'
        if chapter_plant:
            start = CHAPTER_PLANTS[int(original['id'].rsplit('/',1)[1])]
        original_class=surface[cell(start)]
        group=groups.get(original.get('group'))
        rejected=collections.Counter()

        def valid(point):
            if not (-32768<=point[0]<32256 and -32256<point[1]<=32768):return 'terrain edge'
            outside=max(abs(v) for v in point)>24576
            if outside!=bool(original.get('sceneryOnly')):return 'travel envelope'
            if surface[cell(point)] in [0,3,4] or surface[cell(point)]!=original_class:return 'material'
            if group and any(abs(point[i]-group['center'][i])>group['extent'][i]/2 for i in range(2)):
                return 'group boundary'
            if any(polygon_distance(point,poly)<clearance for name,poly in solids):return 'architecture'
            if chapter_plant:
                x0,y0,x1,y1 = CHAPTER_APPROACH
                if x0-clearance<point[0]<x1+clearance and y0-clearance<point[1]<y1+clearance:
                    return 'chapterhouse approach'
            if any(polygon_distance(point,poly)<clearance for poly in native_reserves):return 'natural site open space'
            if any(distance(point,a,b)<int(row[4])+64 for a,b in road_segments):return 'road'
            if any(math.dist(point,a)<256+clearance for a in arrivals):return 'arrival'
            if any(math.dist(point,a)<radius+clearance for a,name,radius in approaches):return 'interaction approach'
            if any(p['id']!=original['id'] and math.dist(point,p['position'][:2])<p['visualRadius']+clearance
                   for p in props):return 'prop reserve'
            if any(math.dist(point,p['position'][:2])<int(row[4])+p['collisionRadius']+32
                   for p in fixed_native):return 'authored site scenery'
            if original['category']=='trees' and any(
                    p['category']=='trees' and math.dist(point,p['position'][:2])<(visual+p['visualRadius'])*.45
                    for p in accepted+fixed_native):return 'canopy spacing'
            return None

        positions=[start]
        phase=int(hashlib.sha256(original['id'].encode()).hexdigest()[:8],16)%16
        for radius in [64,128,192,256,384,512]:
            if chapter_plant:
                break  # Explicit composed anchors must pass as authored, not drift out of their beds.
            positions.extend([(round(start[0]+radius*math.cos((i+phase)*math.tau/16)),
                               round(start[1]+radius*math.sin((i+phase)*math.tau/16))) for i in range(16)])
        chosen=None
        for point in positions:
            reason=valid(point)
            if reason:rejected[reason]+=1
            else:
                chosen=list(point)
                break
        if chosen is None:
            unresolved.append({'id':original['id'],'source':original,'rejections':dict(rejected)})
            continue
        record={**original,'originalPosition':original['position'],'position':chosen+[ground(chosen)],
                'descriptorNumber':int(row[0]),'assetSha256':hashlib.sha256(asset.read_bytes()).hexdigest(),
                'eventId':0,'placementChange':round(math.dist(chosen,start),2)}
        if chapter_plant:
            record['authoredPosition'] = list(start)
            record['authoredPlacementChange'] = round(math.dist(start,original['position'][:2]),2)
            record['placementReason'] = 'Compose two unequal chapterhouse beds with a clear direct southern approach'
        if original.get('sourceEffect') in ['reward_tree','food_tree']:
            record['eventId']=2000+orchard_ids[original['id']]
            label='Orchard Tree' if original['sourceEffect']=='reward_tree' else 'Food Tree'
            events.append({'id':record['eventId'],'semantic_id':original['id'],'label':label,
                           'behavior':'status-only placeholder; source food/reward deferred'})
        if barrel:
            record['eventId']=1200+barrel_ids[original['id']]
            events.append({'id':record['eventId'],'semantic_id':original['id'],'label':'Stat Barrel',
                           'behavior':'status-only placeholder; no native stat reward or depletion'})
        accepted.append(record)
    # Explicit authored groups supplement the baseline inventory. Their fixed anchors must pass, not silently move.
    for site in native_sites:
        reserves=[rectangle(site,site['clearApproach'])] if site['clearApproach'] else []
        if site['futureGrowingGround']:
            reserves.append(rectangle(site,site['futureGrowingGround']))
        for record in site['nativeScenery']:
            row=rows[record['descriptorId']]
            point=record['position'][:2]
            radius=record['collisionRadius']
            assert row[1]==record['name'] and int(row[0])==record['descriptorNumber'],record['id']
            assert int(row[11],0)==0 and int(row[6])==record.get('expectedLightRadius',0) and int(row[10])==0,row
            assert hashlib.sha256((ROOT/record['assetSource']).read_bytes()).hexdigest()==record['assetSha256']
            assert surface[cell(point)] in site.get('allowedSurfaceClasses',[1]) and max(abs(v) for v in point)<24576,record['id']
            assert record['position'][2]==ground(point),record['id']
            assert all(polygon_distance(point,poly)>=radius+32 for name,poly in solids if name!=site['id'])
            assert all(polygon_distance(point,poly)>=radius+32 for poly in reserves),record['id']
            assert all(distance(point,a,b)>=radius+64 for a,b in road_segments),record['id']
            assert all(math.dist(point,a)>=256+radius for a in arrivals),record['id']
            assert all(math.dist(point,p['position'][:2])>=radius+int(rows[p['descriptorId']][4])+16
                       for p in accepted),record['id']
            if record['category']=='trees':
                assert all(math.dist(point,p['position'][:2])>=(record['visualRadius']+p['visualRadius'])*.45
                           for p in accepted if p['category']=='trees'),record['id']
            accepted.append(record)
        for venue in site.get('venues',[]):
            if 'nativeDecorationId' not in venue:
                continue
            target=next(r for r in site['nativeScenery'] if r['id']==venue['nativeDecorationId'])
            assert target['eventId']==venue['eventId']
            events.append({'id':venue['eventId'],'semantic_id':venue['id'],'label':venue['displayLabel'],
                           'behavior':venue['behavior'],'nativeDecorationId':target['id']})
        if site.get('kind')=='barbarian camp':
            # The geometry already owns this one handler; the fire is another instance bound to it.
            fire,=site['nativeScenery']
            assert fire['name']=='dec25' and fire['expectedLightRadius']==128
            assert fire['eventId']==site['eventId'] and any(
                e['id']==fire['eventId'] and e['semantic_id']==site['semanticId'] for e in semantic['events'])
    output={'status':'first fitted native scenery pass; native visual acceptance pending',
            'descriptorTableSha256':hashlib.sha256(table.read_bytes()).hexdigest(),
            'records':accepted,'events':events,'unresolved':unresolved,
            'counts':{'accepted':len(accepted),'moved':sum(r['placementChange']>0 for r in accepted),
                      'unresolved':len(unresolved),'orchard':sum(r.get('group')=='public_orchard' for r in accepted),
                      'byCategory':dict(collections.Counter(r['category'] for r in accepted)),
                      'authoredSiteAdditions':len(fixed_native),
                      'authoredRecompositions':sum('authoredPosition' in r for r in accepted),
                      'buffer':sum(bool(r.get('sceneryOnly')) for r in accepted)},
            'rules':['Native descriptor numbers are one-based; instance ids are number minus one.',
                     'All heights sample the actual quantized native triangle split.',
                     'Original named groups and material classes are retained; automatic clearance refits are bounded to 512 units.',
                     'Chapterhouse plants use twelve explicit recomposed anchors inside their existing group, recorded separately from refits.',
                     'Thirty ordinary orchard identities remain decorative; 25 food/reward trees use local stubs.',
                     'All six stat barrels use instance-local secondary events, bypassing native reward bindings.',
                     'Explicit natural-site additions retain fixed anchors, venue ownership and clear growing/approach areas.',
                     'Unresolved records remain in this inventory and must be resolved before completion.']}
    (PROJECT/'implementation/scenery.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output['counts'],indent=2))
    return output


if __name__=='__main__':
    prepare()
