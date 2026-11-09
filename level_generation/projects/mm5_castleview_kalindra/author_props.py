"""Independently authored well, seating and service stock, fitted to actual fortifications.

Historical source objects keep their identities when an authored wall requires a local move.
No copied native mesh, container contents or native reward behavior is introduced.
"""
import json
import math

from review_fortifications import distance, rectangle


def ground_at(height, point):
    col,row=(point[0]+32768)/512,(32768-point[1])/512
    assert 0<=col<=127 and 0<=row<=127,point
    # The outer sample row/column belongs to the final rendered quad at local coordinate one.
    c,r=min(126,math.floor(col)),min(126,math.floor(row))
    u,v=col-c,row-r
    a,b,d,e=[height[index]*32 for index in [r*128+c,r*128+c+1,(r+1)*128+c,(r+1)*128+c+1]]
    return a+(b-a)*u+(d-a)*v if u+v<=1 else e+(d-e)*(1-u)+(b-e)*(1-v)


def polygon_distance(point, polygon):
    signs=[(b[0]-a[0])*(point[1]-a[1])-(b[1]-a[1])*(point[0]-a[0])
           for a,b in zip(polygon,polygon[1:]+polygon[:1])]
    if min(signs)>=-1e-6 or max(signs)<=1e-6:
        return 0
    return min(distance(point,a,b) for a,b in zip(polygon,polygon[1:]+polygon[:1]))


def author_training_pool(author,prop,palette):
    panels=[]
    bottom=prop['foundation']['skirtBottomZ']-prop['padHeight']
    # Retaining walls use disjoint intervals; the water is above the entire unmodified grade.
    for bounds in [[-448,-256,bottom,448,-224,16],[-448,224,bottom,448,256,16],
                   [-448,-224,bottom,-416,224,16],[416,-224,bottom,448,224,16]]:
        author.box(panels,bounds,palette['stone'])
    author.box(panels,[-192,256,bottom,192,320,-16],palette['rim'])
    author.panel(panels,[(-416,-224,0),(416,-224,0),(416,224,0),(-416,224,0)],palette['water'])
    author.model(prop['id'],panels,prop)
    author.semantic['props'].append(prop)


def author_props(author,spec,project):
    records=json.loads((project/'landscape/decorations.json').read_text())['records']
    sources=[r for r in records if r['category']=='props' or r.get('featureId')=='water_well']
    height=(project/'landscape/heightmap.raw').read_bytes()
    roads=json.loads((project/'implementation/roads.json').read_text())
    layout=json.loads((project/'layout.json').read_text())
    arrivals=[layout['defaultArrival']['point']]+[r['plannedPoint'] for r in layout['mirrorArrivals']]
    arrivals += [r['arrival'] for r in layout['travel']]
    solids=[rectangle(b,c['bounds']) for b in spec['buildings'] for c in b['components']]
    solids += [rectangle(b,[d['bounds'][i] for i in [0,1,3,4]]) for b in spec['buildings'] for d in b['details']]
    solids += [rectangle(p,p['bounds']) for p in spec['props'] if 'bounds' in p]
    for fort in author.semantic['fortifications']:
        if fort['id']=='town_wall':
            solids += [r['footprint'] for r in fort['segments']+fort['towers']]
        else:
            solids += [rectangle(fort,t['bounds']) for t in fort['towers']]
    xy=lambda cell:((cell[1]-64)*512+256,(64-cell[0])*512-256)
    segments=[(xy(a),xy(b)) for path in roads['paths'] for a,b in zip(path['cells'],path['cells'][1:])]
    approaches=[[v['door'][i]+b['frontOutward'][i]*256 for i in range(2)]
                for b in spec['buildings'] for v in b['venues']]
    placed=[]
    palette=spec['palettes']['working_props']
    for source in sources:
        start=source['position'][:2]
        radius=source['visualRadius']
        candidates=[start]
        for shift in [64,128,192,256,384,512]:
            candidates += [[round(start[0]+shift*math.cos(i*math.tau/16)),
                            round(start[1]+shift*math.sin(i*math.tau/16))] for i in range(16)]
        chosen=None
        for point in candidates:
            if any(polygon_distance(point,p)<radius+32 for p in solids):continue
            if any(distance(point,a,b)<radius+64 for a,b in segments):continue
            if any(math.dist(point,p)<radius+128 for p in approaches):continue
            if any(math.dist(point,p)<radius+256 for p in arrivals):continue
            others=[r for r in records if r['category']=='interactive' and r['id']!=source['id']]
            others += [r for r in sources if r['id']!=source['id'] and not any(p['semanticId']==r['id'] for p in placed)]
            if any(math.dist(point,p['position'][:2])<radius+p['visualRadius']+32 for p in others):continue
            if any(math.dist(point,p['frontOrigin'])<radius+p['radius']+32 for p in placed):continue
            chosen=point
            break
        assert chosen is not None,('Unresolved prop; retain its source reservation',source['id'])
        bench=source['name']=='mm5:prop/bench'
        well=source.get('featureId')=='water_well'
        # Seating looks out into usable yard/approach space, with its back toward the associated premises.
        owner=next((b for b in spec['buildings']+spec['gates'] if b['id']==source.get('owner')),None)
        normal=[0,-1]
        if bench and owner:
            delta=[chosen[i]-owner['frontOrigin'][i] for i in range(2)]
            length=math.hypot(*delta)
            normal=[v/length for v in delta]
            if owner.get('kind')=='gate':normal=list(owner['frontOutward'])
        tangent=[-normal[1],normal[0]]
        support=[ground_at(height,[chosen[0]+radius*math.cos(i*math.tau/16),
                                   chosen[1]+radius*math.sin(i*math.tau/16)]) for i in range(16)]
        pad=math.ceil(max(support)/32)*32
        prop={'id':source['id'].split('/')[-1],'semanticId':source['id'],
              'title':'Well' if well else 'Bench' if bench else 'Service stock',
              'frontOrigin':chosen,'frontOutward':normal,'frontTangent':tangent,'padHeight':pad,
              'radius':radius,'palette':'working_props','purpose':source['purpose'],'sourceRecord':source,
              'position':chosen+[ground_at(height,chosen)],'visualRadius':radius,
              'placementChange':round(math.dist(start,chosen),2),'terrainSupportRange':[min(support),max(support)],
              'foundation':{'platformZ':pad,'skirtBottomZ':math.floor(min(support)/32)*32-32},
              'behavior':'status-only placeholder' if well else 'inert architectural scenery'}
        panels=[]
        def box(bounds,key='wood'):
            author.box(panels,bounds,palette[key])
        def feet(bounds,key='wood'):
            x0,y0,_,x1,y1,z1=bounds
            support=[ground_at(height,[chosen[i]+tangent[i]*x-normal[i]*y for i in range(2)])-pad
                     for x in [x0,x1] for y in [y0,y1]]
            box([x0,y0,min(support)-16,x1,y1,z1],key)
        if bench:
            # Three individual seat planks, two grounded trestles and a modest backrest.
            for y in [-32,-9,14]:box([-144,y,64,144,y+20,80])
            for x in [-108,84]:
                feet([x,-26,0,x+24,30,64])
                box([x,22,64,x+24,38,160])
            box([-144,26,110,144,42,138])
        elif well:
            def ring(radius,z):
                return [(radius*math.cos(i*math.tau/12),radius*math.sin(i*math.tau/12),z) for i in range(12)]
            def band(r0,z0,r1,z1):
                a,b=ring(r0,z0),ring(r1,z1)
                for i in range(12):author.panel(panels,[a[i],a[(i+1)%12],b[(i+1)%12],b[i]],palette['stone'])
            band(100,prop['foundation']['skirtBottomZ']-pad,100,96)
            band(100,96,70,96)
            band(70,96,70,-32)
            water=ring(70,-16)
            author.panel(panels,water,palette['water'],[(x/128,y/128) for x,y,z in water])
            for x in [-112,88]:feet([x,-12,0,x+24,12,240])
            box([-128,-16,224,128,16,248])
            # Hanging rope and small timber bucket; geometry remains within the reserved 128 radius.
            box([-3,-3,24,3,3,224])
            box([-18,-18,16,18,18,48])
            box([120,-12,204,128,12,224])
            box([112,-12,188,128,12,204])
            prop['eventId']=1100
            prop['futureInteraction']=source['interaction']
        else:
            # Two unequal small stock crates; each face gets a complete native crate bitmap.
            for bounds in [[-96,-64,-16,16,48,96],[16,-32,-16,96,48,64]]:
                before=len(panels)
                feet(bounds,'crate')
                for index in range(before,len(panels)):
                    points,key,uv=panels[index]
                    panels[index]=(points,key,[(0,0),(1,0),(1,1),(0,1)])
        event={'id':1100,'semantic_id':source['id'],'label':'Well',
               'behavior':'status-only placeholder; charity reward deferred'} if well else None
        author.model(prop['id'],panels,prop,event)
        author.semantic['props'].append(prop)
        placed.append(prop)
    (project/'implementation/prop_placements.json').write_text(json.dumps({
        'records':placed,'counts':{'accepted':len(placed),'moved':sum(p['placementChange']>0 for p in placed)},
        'limits':'Initial fitted prop pass; inspect native grounding and paths before acceptance.'},indent=2)+'\n')
