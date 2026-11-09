"""Original cloth shelters, tent, wagon and travel equipment in native units."""
import math


def box(author,panels,bounds,key,building,model,buried=False):
    first=len(panels)
    author.box(panels,bounds,key)
    if buried:
        building.setdefault('geometryChecks',[]).append(
            {'model':model,'faces':[first+4],'kind':'buried camp foot'})


def beam(author,panels,a,b,width,key,caps=True):
    direction=[b[i]-a[i] for i in range(3)]
    length=math.sqrt(sum(v*v for v in direction))
    direction=[v/length for v in direction]
    seed=[0,0,1] if abs(direction[2])<.9 else [0,1,0]
    u=[direction[1]*seed[2]-direction[2]*seed[1],direction[2]*seed[0]-direction[0]*seed[2],
       direction[0]*seed[1]-direction[1]*seed[0]]
    length=math.sqrt(sum(v*v for v in u));u=[v/length*width/2 for v in u]
    v=[direction[1]*u[2]-direction[2]*u[1],direction[2]*u[0]-direction[0]*u[2],
       direction[0]*u[1]-direction[1]*u[0]]
    rings=[[[p[i]+u[i]*sx+v[i]*sy for i in range(3)] for sx,sy in [(1,1),(-1,1),(-1,-1),(1,-1)]]
           for p in [a,b]]
    if caps:
        author.panel(panels,list(reversed(rings[0])),key)
        author.panel(panels,rings[1],key)
    for i in range(4):
        j=(i+1)%4
        author.panel(panels,[rings[0][i],rings[0][j],rings[1][j],rings[1][i]],key)


def cloth(author,panels,points,key,thickness=4):
    # Thin closed cover; both visible sides retain the canvas material.
    a=[points[1][i]-points[0][i] for i in range(3)]
    b=[points[2][i]-points[0][i] for i in range(3)]
    normal=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
    length=math.sqrt(sum(v*v for v in normal))
    lower=[tuple(p[i]-normal[i]/length*thickness for i in range(3)) for p in points]
    author.panel(panels,points,key)
    author.panel(panels,list(reversed(lower)),key)
    for i in range(len(points)):
        j=(i+1)%len(points)
        author.panel(panels,[lower[i],lower[j],points[j],points[i]],key)


def shelter(author,panels,part,palette,building):
    x0,y0,x1,y1=part['bounds'];low,high=part['eave'],part['top']
    name=building['id']+'_'+part['id']
    def roof_z(y):return low+(high-low)*(y-y0)/(y1-y0)
    for x in [x0+24,x1-24]:
        for y in [y0+24,y1-24]:
            top=roof_z(y-8)-16
            box(author,panels,[x-8,y-8,-32,x+8,y+8,top],palette['wood'],building,name,True)
        beam(author,panels,(x,y0,low-12),(x,y1,high-12),16,palette['crosswood'])
    cloth(author,panels,[(x0,y0,low),(x1,y0,low),(x1,y1,high),(x0,y1,high)],palette['cloth'])
    # Rear windbreak leaves the front and one whole side open.
    y=y1-24
    author.box(panels,[x0+32,y-2,0,x1-32,y+2,roof_z(y)-16],palette['cloth'])
    if part['sideScreen']:
        x=x0+24;front=y0+(y1-y0)*.55
        points=[(x,front,0),(x,y,0),(x,y,roof_z(y)-16),(x,front,roof_z(front)-16)]
        cloth(author,panels,list(reversed(points)),palette['cloth'])


def tent(author,panels,part,palette,building):
    x0,y0,x1,y1=part['bounds'];top=part['top'];name=building['id']+'_'+part['id']
    for points in [[(x0,y0,-16),(0,y0,top),(0,y1,top),(x0,y1,-16)],
                   [(0,y0,top),(x1,y0,-16),(x1,y1,-16),(0,y1,top)]]:
        cloth(author,panels,points,palette['cloth'])
    cloth(author,panels,[(x1,y1,-16),(x0,y1,-16),(0,y1,top)],palette['cloth'])
    # Frame front around a normal 128 by 256 cloth flap.
    for points in [[(x0,y0,-16),(-64,y0,-16),(-64,y0,256)],
                   [(x0,y0,-16),(-64,y0,256),(0,y0,top)],
                   [(64,y0,-16),(x1,y0,-16),(64,y0,256)],
                   [(x1,y0,-16),(0,y0,top),(64,y0,256)],
                   [(-64,y0,256),(64,y0,256),(0,y0,top)]]:
        cloth(author,panels,points,palette['cloth'])
    for y in [y0+16,y1-16]:
        for x in [x0+16,x1-16]:
            first=len(panels)
            beam(author,panels,(x,y,-24),(0,y,top-16),16,palette['wood'])
            building.setdefault('geometryChecks',[]).append(
                {'model':name,'faces':[first],'kind':'buried tent frame foot'})
    beam(author,panels,(0,y0,top-8),(0,y1,top-8),12,palette['wood'])
    for x in [x0-32,x1+32]:
        for y in [y0-32,y1+24]:
            box(author,panels,[x-8,y-8,-32,x+8,y+8,48],palette['wood'],building,name,True)
            attach_z=top-(top+16)*abs(x*.5)/x1
            beam(author,panels,(x,y,24),(x*.5,y0 if y<y0 else y1,attach_z-2),4,palette['wood'])


def wheel(author,panels,x,y,z,radius,palette,building,model,record=True):
    count=12
    def ring(r,depth):
        return [(x+r*math.sin(i*math.tau/count),depth,z-r*math.cos(i*math.tau/count)) for i in range(count)]
    front,back=ring(radius,y-10),ring(radius,y+10)
    inner_front,inner_back=ring(radius-20,y-10),ring(radius-20,y+10)
    first=len(panels)
    for i in range(count):
        j=(i+1)%count
        author.panel(panels,[back[i],back[j],front[j],front[i]],palette['metal'])
        author.panel(panels,[inner_front[j],inner_front[i],front[i],front[j]],palette['crosswood'])
        author.panel(panels,[inner_back[i],inner_back[j],back[j],back[i]],palette['crosswood'])
        author.panel(panels,[inner_back[j],inner_back[i],inner_front[i],inner_front[j]],palette['wood'])
    for i in range(6):
        a=i*math.tau/6
        # Ends terminate inside the unchanged hub and wheel rim.
        beam(author,panels,(x,y,z),(x+(radius-16)*math.sin(a),y,z+(radius-16)*math.cos(a)),
             16,palette['wood'],caps=False)
    author.box(panels,[x-20,y-16,z-20,x+20,y+16,z+20],palette['metal'])
    if record:
        building.setdefault('wheelContacts',[]).append({'model':model,'faces':[first,first+44],
                                                        'localContact':[x,y,z-radius]})


def wagon(author,panels,part,palette,building):
    name=building['id']+'_'+part['id']
    for x in [-208,176]:
        author.box(panels,[x-10,196,78,x+10,476,98],palette['wood'])
        for y in [206,466]:wheel(author,panels,x,y,88,88,palette,building,name)
    for y in [256,400]:author.box(panels,[-320,y-16,96,256,y+16,112],palette['wood'])
    author.box(panels,[-320,224,112,256,448,128],palette['crosswood'])
    for y in [224,432]:author.box(panels,[-320,y,128,256,y+16,240],palette['wood'])
    for x in [-320,240]:author.box(panels,[x,240,128,x+16,432,240],palette['wood'])
    # Original bowed cover, with three narrower timber hoops below its outer cloth.
    curve=[(336-112*math.cos(i*math.pi/8),256+128*math.sin(i*math.pi/8)) for i in range(9)]
    for (ya,za),(yb,zb) in zip(curve,curve[1:]):
        cloth(author,panels,[(-304,ya,za+8),(240,ya,za+8),(240,yb,zb+8),(-304,yb,zb+8)],palette['cloth'])
    for y,reverse in [(224,False),(448,True)]:
        points=[(-304,y,240),(240,y,240),(240,y,264),(-304,y,264)]
        cloth(author,panels,list(reversed(points)) if reverse else points,palette['cloth'])
    for x in [-288,-32,224]:
        for (ya,za),(yb,zb) in zip(curve,curve[1:]):
            beam(author,panels,(x,ya,za),(x,yb,zb),12,palette['wood'])
        for y in [224,448]:author.box(panels,[x-6,y-6,240,x+6,y+6,256],palette['wood'])
    end=[(240,y,z+8) for y,z in reversed(curve)]+[(240,224,240),(240,448,240)]
    cloth(author,panels,end,palette['cloth'])
    # Short shafts are folded upward within the yard instead of blocking its approach.
    for y in [272,400]:beam(author,panels,(256,y,128),(368,y,288),16,palette['wood'])


def supplies(author,panels,building,palette):
    name=building['id']+'_service_details'
    placements={'dreyfus':[(-304,352,128),(-272,192,64)],
                'justine':[(128,576,96)],'yog':[(224,24,96)],'kramer':[(-320,32,96),(-200,64,64)]}
    for x,y,size in placements[building['id']]:
        box(author,panels,[x,y,-8,x+size,y+size,size],palette['crate'],building,name,True)
    if building['id']=='yog':
        # A cold cooking tripod identifies camp activity without importing a native fire effect.
        for x,y in [(-288,24),(-192,24),(-240,104)]:
            first=len(panels)
            beam(author,panels,(x,y,-16),(-240,64,176),12,palette['wood'])
            building.setdefault('geometryChecks',[]).append(
                {'model':name,'faces':[first],'kind':'buried tripod foot'})
        rings=[[( -240+r*math.cos(i*math.tau/8),64+r*math.sin(i*math.tau/8),z)
                for i in range(8)] for r,z in [(16,56),(32,72),(32,96),(24,96),(24,80)]]
        for lower,upper in zip(rings,rings[1:]):
            for i in range(8):
                j=(i+1)%8
                author.panel(panels,[lower[i],lower[j],upper[j],upper[i]],palette['metal'])
        author.panel(panels,list(reversed(rings[0])),palette['metal'])
        author.panel(panels,rings[-1],palette['metal'])
        for x in [-264,-216]:beam(author,panels,(x,64,96),(x,64,128),4,palette['metal'])
        beam(author,panels,(-264,64,128),(-216,64,128),4,palette['metal'])
        beam(author,panels,(-240,64,128),(-240,64,168),4,palette['metal'])
    # Folded bedding is inert equipment, not an outdoor bed/service interaction.
    if building['id'] in ['dreyfus','justine']:
        x,y=(144,416) if building['id']=='dreyfus' else (-176,576)
        box(author,panels,[x,y,0,x+96,y+96,24],palette['cloth'],building,name,True)
        author.box(panels,[x+8,y,24,x+88,y+80,40],palette['cloth'])
        for dx in [24,64]:author.box(panels,[x+dx,y-2,0,x+dx+8,y+82,44],palette['wood'])


def interaction(author,panels,building,palette,venue):
    if venue['interactionSurface']=='tent flap':
        y=venue['localDepth']
        cloth(author,panels,[(-64,y,0),(64,y,0),(64,y,256),(-64,y,256)],palette['cloth'])
        author.box(panels,[-4,y-4,0,4,y,256],palette['wood'])
    else:
        author.box(panels,[-128,0,80,128,64,96],palette['crosswood'])
        for x in [-112,96]:
            box(author,panels,[x,8,-16,x+16,56,80],palette['wood'],building,
                building['id']+'_door_0',True)
        if building['id']=='dreyfus':
            author.box(panels,[-80,12,96,-16,56,112],palette['cloth'])
            author.box(panels,[-84,8,112,-12,60,116],palette['wood'])
