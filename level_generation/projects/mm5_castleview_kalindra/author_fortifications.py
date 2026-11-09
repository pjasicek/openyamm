"""Independent gate geometry using measured Garrote material roles, never donor vertices."""
import math


def terrain_range(points, heights):
    c0=math.floor((min(p[0] for p in points)+32768)/512)
    c1=math.ceil((max(p[0] for p in points)+32768)/512)
    r0=math.floor((32768-max(p[1] for p in points))/512)
    r1=math.ceil((32768-min(p[1] for p in points))/512)
    values=[heights[r*128+c]*32 for r in range(r0,r1+1) for c in range(c0,c1+1)]
    return min(values),max(values)


def outside_gate_intervals(a,b,gates):
    """Clip a wall centreline against gate assemblies, retaining only exterior spans."""
    intervals=[(0.,1.)]
    for gate in gates:
        def local(p):
            d=[p[i]-gate['frontOrigin'][i] for i in range(2)]
            return [sum(d[i]*gate['frontTangent'][i] for i in range(2)),
                    -sum(d[i]*gate['frontOutward'][i] for i in range(2))]
        p,q=local(a),local(b)
        # The towers connect the curtain across this envelope. The centre opening stays empty.
        bounds=[min(t['bounds'][0] for t in gate['towers']),-128,
                max(t['bounds'][2] for t in gate['towers']),
                max(t['bounds'][3] for t in gate['towers'])]
        lo,hi=0.,1.
        for axis in range(2):
            delta=q[axis]-p[axis]
            if abs(delta)<1e-8:
                if not bounds[axis]<=p[axis]<=bounds[axis+2]:
                    lo,hi=1.,0.
                    break
            else:
                first,last=sorted([(bounds[axis]-p[axis])/delta,(bounds[axis+2]-p[axis])/delta])
                lo,hi=max(lo,first),min(hi,last)
        if hi<=lo:
            continue
        remaining=[]
        for start,end in intervals:
            if hi<=start or lo>=end:
                remaining.append((start,end))
            else:
                if start<lo: remaining.append((start,lo))
                if hi<end: remaining.append((hi,end))
        intervals=remaining
    return intervals


def author_curtain(author,spec,heights):
    wall=spec['fortifications']
    palette=spec['palettes']['garrote_curtain']
    frame={'id':'town_wall','semanticId':'mm5:sw/town_wall','frontOrigin':[0,0],
           'frontTangent':[1,0],'frontOutward':[0,-1],'padHeight':0}
    polygon=wall['polygon']
    records=[]
    for index,a in enumerate(polygon):
        b=polygon[(index+1)%len(polygon)]
        length=math.dist(a,b)
        tangent=[(b[i]-a[i])/length for i in range(2)]
        outward=[tangent[1],-tangent[0]]
        intervals=outside_gate_intervals(a,b,spec['gates'])
        for run,(start,end) in enumerate(intervals):
            count=math.ceil((end-start)*length/1024)
            for part in range(count):
                t0=start+(end-start)*part/count
                t1=start+(end-start)*(part+1)/count
                p=[a[i]+(b[i]-a[i])*t0 for i in range(2)]
                q=[a[i]+(b[i]-a[i])*t1 for i in range(2)]
                ring=[(p[0]+outward[0]*128,p[1]+outward[1]*128),
                      (q[0]+outward[0]*128,q[1]+outward[1]*128),
                      (q[0]-outward[0]*128,q[1]-outward[1]*128),
                      (p[0]-outward[0]*128,p[1]-outward[1]*128)]
                low,high=terrain_range(ring,heights)
                deck=high+wall['architecture']['wallHeight']-128
                top=deck+128
                panels=[]
                for i,c in enumerate(ring):
                    d=ring[(i+1)%4]
                    points=[(*c,low-64),(*d,low-64),(*d,deck),(*c,deck)]
                    uv=[((x*tangent[0]+y*tangent[1])/128,z/256) for x,y,z in points]
                    if i%2: uv=[((x*outward[0]+y*outward[1])/128,z/256) for x,y,z in points]
                    author.panel(panels,points,palette['wall'],uv)
                author.panel(panels,[(*v,deck) for v in ring],palette['floor'])
                inner=[(p[0]+outward[0]*64,p[1]+outward[1]*64),
                       (q[0]+outward[0]*64,q[1]+outward[1]*64)]
                parapet=[ring[0],ring[1],inner[1],inner[0]]
                for i,c in enumerate(parapet):
                    d=parapet[(i+1)%4]
                    author.panel(panels,[(*c,deck),(*d,deck),(*d,top-32),(*c,top-32)],palette['stone'])
                    author.panel(panels,[(*c,top-32),(*d,top-32),(*d,top),(*c,top)],palette['trim'])
                author.panel(panels,[(*v,top) for v in parapet],palette['stone'])
                name=f'town_wall_{index:02}_{run}_{part:02}'
                author.model(name,panels,frame)
                records.append({'id':name,'start':p,'end':q,'footprint':ring,
                                'foundationBottom':low-64,'deck':deck,'top':top,
                                'terrainSupportRange':[low,high]})
    # Original octagonal corner towers cover angled curtain junctions. The south gate
    # itself occupies perimeter corner 8 and must not receive a blocking tower.
    towers=[]
    for index,(x,y) in enumerate(polygon):
        if index==8:
            continue
        ring=[(x+384*math.cos((i+.5)*math.tau/8),y+384*math.sin((i+.5)*math.tau/8)) for i in range(8)]
        inner=[(x+320*math.cos((i+.5)*math.tau/8),y+320*math.sin((i+.5)*math.tau/8)) for i in range(8)]
        low,high=terrain_range(ring,heights)
        top=high+wall['architecture']['towerTop']
        deck=top-160
        panels=[]
        for i,a in enumerate(ring):
            b,c,d=ring[(i+1)%8],inner[(i+1)%8],inner[i]
            author.panel(panels,[(*a,low-64),(*b,low-64),(*b,top-32),(*a,top-32)],palette['wall'])
            author.panel(panels,[(*a,top-32),(*b,top-32),(*b,top),(*a,top)],palette['trim'])
            author.panel(panels,[(*c,deck),(*d,deck),(*d,top),(*c,top)],palette['stone'])
            author.panel(panels,[(*a,top),(*b,top),(*c,top),(*d,top)],palette['stone'])
        for i in range(8):
            author.panel(panels,[(x,y,deck),(*inner[i],deck),(*inner[(i+1)%8],deck)],palette['floor'])
        name=f'town_corner_{index:02}'
        author.model(name,panels,frame)
        towers.append({'id':name,'center':[x,y],'radius':384,'footprint':ring,
                       'foundationBottom':low-64,'top':top,'terrainSupportRange':[low,high]})
    author.semantic['fortifications'].append({**frame,'segments':records,'towers':towers,
                  'status':'full perimeter authored; native contact, gate joins and contextual acceptance pending'})


def author_gate(author, gate, palette):
    def parapet(panels, bounds, floor, top):
        x0,y0,x1,y1 = bounds
        outer = [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
        inner = [(x0+32,y0+32),(x1-32,y0+32),(x1-32,y1-32),(x0+32,y1-32)]
        author.panel(panels,[(*p,floor) for p in inner],palette['floor'])
        for i,a in enumerate(outer):
            b,c,d = outer[(i+1)%4],inner[(i+1)%4],inner[i]
            author.panel(panels,[(*a,floor),(*b,floor),(*b,top-32),(*a,top-32)],palette['wall'])
            author.panel(panels,[(*a,top-32),(*b,top-32),(*b,top),(*a,top)],palette['trim'])
            author.panel(panels,[(*c,floor),(*d,floor),(*d,top),(*c,top)],palette['stone'])
            author.panel(panels,[(*a,top),(*b,top),(*c,top),(*d,top)],palette['stone'])

    for tower in gate['towers']:
        x0,y0,x1,y1 = tower['bounds']
        panels=[]
        top = max(tower['top'],gate['headerHeight']+64)
        body_top = top-160
        ring = [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
        for i,a in enumerate(ring):
            b=ring[(i+1)%4]
            author.wall(panels,a,b,gate['foundationBottom'],0,palette,windows=False)
            for lower in range(0,body_top,256):
                author.wall(panels,a,b,lower,min(lower+256,body_top),palette,
                            windows=tower['id']!='right_shoulder' and lower in [512,1024])
        # The parapet owns the exposed floor. A closed trim box would duplicate that plane.
        cornice = [(x0-16,y0-16),(x1+16,y0-16),(x1+16,y1+16),(x0-16,y1+16)]
        for i,a in enumerate(cornice):
            b = cornice[(i+1)%4]
            author.panel(panels,[(*a,body_top),(*b,body_top),(*b,body_top+32),(*a,body_top+32)],
                         palette['trim'])
        author.panel(panels,[(*p,body_top) for p in reversed(cornice)],palette['trim'])
        parapet(panels,[x0-16,y0-16,x1+16,y1+16],body_top+32,top)
        author.model(gate['id']+'_'+tower['id'],panels,gate)

    half, depth = gate['openingWidth']/2,gate['passageDepth']
    spring,rise,header = gate['springHeight'],gate['archRise'],gate['headerHeight']
    points=[(-half*math.cos(i*math.pi/8),spring+rise*math.sin(i*math.pi/8)) for i in range(9)]
    panels=[]
    for (x0,z0),(x1,z1) in zip(points,points[1:]):
        author.panel(panels,[(x0,0,z0),(x1,0,z1),(x1,0,header),(x0,0,header)],palette['wall'])
        author.panel(panels,[(x1,depth,z1),(x0,depth,z0),(x0,depth,header),(x1,depth,header)],palette['wall'])
        # Soffit points into the open passage; the passage has no floor slab or gate leaf.
        author.panel(panels,[(x0,depth,z0),(x1,depth,z1),(x1,0,z1),(x0,0,z0)],palette['stone'])
    parapet(panels,[-half,0,half,depth],header,header+96)
    author.model(gate['id']+'_arch',panels,gate)

    # The original pass rule remains deferred. A small heraldic face provides explicit
    # local feedback without making the passage itself a barrier or inventing a resident.
    tower=gate['towers'][0]
    cx=(tower['bounds'][0]+tower['bounds'][2])/2
    y=tower['bounds'][1]-2
    panels=[]
    author.panel(panels,[(cx-64,y,64),(cx+64,y,64),(cx+64,y,320),(cx-64,y,320)],
                 palette['plaque'],[(0,0),(1,0),(1,1),(0,1)])
    author.model(gate['id']+'_plaque',panels,gate,{'semantic_id':gate['semanticId']+'/plaque',
                 'id':gate['eventId'],'label':gate['title'],'behavior':gate['behavior']})
    author.semantic['fortifications'].append(gate)
