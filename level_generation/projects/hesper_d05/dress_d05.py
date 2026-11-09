# Flat landings at every door, 16-high risers and continuous sloped stair ceilings.
for rid, start, end in [('root_stair',1024,2400),('ledge1',3450,4800),('ledge2',3136,4464)]:
    r=R[rid];x,y,z,w=r['x'],r['y'],r['z'],r['w'];root=rid=='root_stair'
    horizontal(rid,z,True);horizontal(rid,z+r['ceiling'],False)
    b.rooms[rid][:]=[p for p in b.rooms[rid] if p[2] not in ((1,0,0),(-1,0,0))]
    steps,rise=64,16
    b.rooms[rid]+=kit.flight_along((x+w/2,start),(x+w/2,end),w,z,steps,'hkfloor','hkrib',rise=rise)
    b.rooms[rid]+=floor(x,y,x+w,start,z,'hkfloor')+floor(x,end,x+w,y+r['h'],z+1024,'hkfloor')
    # The Root Gallery's slab ends where this roof meets z=0; its upper flight is an open well.
    roof_end=1760 if root else end
    roof0=z+448 if root else z+528
    roof1=0 if root else z+1552
    slope=(roof1-roof0)/(roof_end-start)
    for ya,yb,za,zb in [(y,start,roof0,roof0),(start,roof_end,roof0,roof1),
                        (roof_end,y+r['h'],roof1,roof1)]:
        if not root or ya<roof_end:
            panel=([(x,ya,za),(x+w,ya,za),(x+w,yb,zb),(x,yb,zb)],'hkceil',(0,0,-1))
            b.rooms[rid] += kit.clip_to([panel],None,below=((0,0,z+1536),(0,0,1))) if not root else [panel]
        for side,wall in [('west',Wall('x',x,(1,0,0))),('east',Wall('x',x+w,(-1,0,0)))]:
            hs=[(a0,a1,z+h0,z+h1) for a0,a1,h0,h1 in holes.get(rid,{}).get(side,[])]
            panels=banded(wall,ya,yb,[(z,z+1536 if not root else 0,'hkwall')],hs)
            b.rooms[rid]+=kit.clip_to(panels,None,below=((x,ya,za),(0,-(zb-za)/(yb-ya),1)))
    if not root:
        cap_start=start+(1536-528)/slope
        b.rooms[rid]+=ceiling(x,cap_start,x+w,y+r['h'],z+1536,'hkceil')
        for k in range(3):
            a=start+(end-start)*(k+.5)/3
            tz=z+rise*math.ceil((a-start)/(end-start)*steps)
            b.rooms[rid]+=plaque(Wall('x',x+w,(-1,0,0)),a,tz+64,256,288,'hkwindow',out=3)
    b.bounds[rid]=(x,y,x+w,y+r['h'],z-1,z+1536 if not root else 768)
gallery=parts['root_gallery'][0]
horizontal(gallery,0,True,[(600,1200,1760,2686)])
# The stair well opens sideways above the gallery floor, including at the upper landing.
b.portal('root_stair',gallery,[(1200,1760,0),(1200,2686,0),(1200,2686,768),(1200,1760,768)])
b.portal('root_stair',gallery,[(600,1760,0),(1200,1760,0),(1200,1760,768),(600,1760,768)])
b.rooms[gallery]+=box((600,1760,0),(1200,1784,128),'hobone',top='hobone')
# A 45-degree return turns the stair's exit east into the Gallery without exposing its sheer side.
b.rooms[gallery]+=box((1176,1784,0),(1200,2400,128),'hobone',top='hobone')
rail=[(1176,2400),(1200,2424),(1344,2280),(1320,2256)]
b.rooms[gallery]+=kit.polygon_floor(rail,128,'hobone')
for (ax,ay),(bx,by) in zip(rail,rail[1:]+rail[:1]):
    wall=Wall.line((ax,ay),(bx,by),(by-ay,ax-bx,0))
    b.rooms[gallery]+=wall.quad(0,wall.length,0,128,'hobone')
# Separate connector sectors keep the landings' walls and bounds inside their own rooms.
for lower,upper,door,x in [('spine_lift','lift1',53,1300),('lift2','lift3',54,1700)]:
    y=3200;z=ROOMS[lower]['z'];cut=(x-256,x+256,y-256,y+256);shaft=f'lift_shaft_{door}'
    horizontal(lower,z,True,[(x-250,x+250,y-250,y+250)])
    horizontal(lower,z+448,False,[cut]);horizontal(upper,z+1024,True,[(x-250,x+250,y-250,y+250)])
    b.room(shaft,(x-256,y-256,x+256,y+256,z+448,z+1024),ROOMS[lower]['ambient'])
    for wall,a0,a1 in [(Wall('x',x-256,(1,0,0)),y-256,y+256),(Wall('x',x+256,(-1,0,0)),y-256,y+256),
                       (Wall('y',y-256,(0,1,0)),x-256,x+256),(Wall('y',y+256,(0,-1,0)),x-256,x+256)]:
        b.rooms[shaft]+=wall.quad(a0,a1,z+448,z+1024,'hkwall')
        # Mark the shaft mouth without changing any light's radius or colour.
        b.rooms[upper]+=wall.quad(a0,a1,z+992,z+1024,'hkglow',out=2)
    for a,c,height in [(lower,shaft,z+448),(shaft,upper,z+1024)]:
        b.portal(a,c,[(x-256,y-256,height),(x+256,y-256,height),(x+256,y+256,height),(x-256,y+256,height)])
    b.door(f'door_{door}',lower,box((x-250,y-250,z-32),(x+250,y+250,z),'hobone',top='hochitin',bottom='hobone'),
           door,1024,open_speed=256,close_speed=256)
# Grafted panels on long uninterrupted wall stretches, clear of every doorway.
for rid,r in R.items():
    if r['base'] in ('shaft','root_stair','ledge1','ledge2'):continue
    for side,wall,a0,a1 in [('south',Wall('y',r['y'],(0,1,0)),r['x'],r['x']+r['w']),
                           ('north',Wall('y',r['y']+r['h'],(0,-1,0)),r['x'],r['x']+r['w'])]:
        src=ROOMS[r['base']]
        if (side=='south' and r['y']!=src['y']) or (side=='north' and r['y']+r['h']!=src['y']+src['h']):continue
        for i,a in enumerate(range(round(a0+650),round(a1-200),1300)):
            if any(h[0]-200<a<h[1]+200 for h in holes.get(rid,{}).get(side,[])):continue
            b.rooms[rid]+=plaque(wall,a,r['z']+64,192,min(384,r['ceiling']-224),['hkgraft','hkgraft2','hkgrlite'][i%3],out=2)
# Canisters, described as wall clusters in section 7.
for base,count in [('root_hall',4),('root_gallery',10),('coil',3)]:
    r=ROOMS[base]
    for k in range(count):
        x=r['x']+500+(k//5)*2600+(k%5)*90;y=r['y']+140
        b.decoration('hes_drum',x,y,r['z'],k*37)
# Accepted eight 480-wide sleeping ledges and one trestle.
r=ROOMS['barracks'];z=r['z']
for k in range(8):
    x=r['x']+275+k*550;name=owner('barracks',x,5150,z)
    b.rooms[name]+=box((x-240,5000,z+300),(x+240,5300,z+364),'hochitin',top='hochitin')
    for sign in (-1,1):
        # Four posts stood in the fire bowls; inset them under their ledges without moving the planned lights.
        offset=150 if (k,sign) in ((1,1),(2,-1),(5,1),(6,-1)) else 245
        px=x+sign*offset
        b.rooms[name]+=box((px-10,5010,z),(px+10,5300,z+550),'hobone',top='hobone')
for name in parts['barracks']:
    r=R[name];x0=max(2000,r['x']);x1=min(4400,r['x']+r['w'])
    b.rooms[name]+=box((x0,4200,z),(x1,4500,z+400),'hkwall',top='hochitin')
# Fitted salvage backs, with a 200-deep bone frame inside each 1200 x 448 envelope.
for wall,a in [(Wall('x',1000,(1,0,0)),2050),(Wall('x',2686,(-1,0,0)),1850),(Wall('y',1000,(0,1,0)),1900)]:
    b.rooms['armoury']+=plaque(wall,a,1024,1200,448,'hkgraft2',out=4)
    for along in (a-584,a+584):
        p=wall.point(along,1024,100)
        dx,dy=(100,16) if wall.axis=='x' else (16,100)
        b.rooms['armoury']+=box((p.x-dx,p.y-dy,1024),(p.x+dx,p.y+dy,1472),'hobone',top='hobone')
    for height in (1040,1456):
        b.rooms['armoury']+=beam(wall.point(a-600,height,184),wall.point(a+600,height,184),32,'hobone')
# Firing line and targets, exactly the listed dimensions.
for name in parts['drill']:
    r=R[name];x0=max(2900,r['x']);x1=min(4900,r['x']+r['w'])
    b.rooms[name]+=box((x0,1900,1024),(x1,2050,1324),'hkwall',top='hochitin')
for y in (1250,1650,2050,2450):
    name=owner('drill',5150,y,1024);b.rooms[name]+=prism(5150,y,150,1024,1600,'hochitin',top='hochitin')
# Loom banks: four frames in each bank, with fitted long faces on a bone body.
for bank in (2100,4200):
    for k in range(4):
        x=bank-525+k*350;y=4500;name=owner('looms',x,y,2048)
        body=box((x-150,y-500,2048),(x+150,y+500,2568),'hobone',top='hobone')
        b.rooms[name]+=body
        for wall in [Wall('x',x-152,(-1,0,0)),Wall('x',x+152,(1,0,0))]:
            b.surface(f'loom_{bank}_{k}_{wall.plane}',name,plaque(wall,y,2048,1000,520,'hkloom',out=1),cog=176)
b.rooms['loom_ctrl']+=box((1450,1200,2048),(2450,1500,2496),'hobone',top='hobone')
b.surface('master_loom','loom_ctrl',plaque(Wall('y',1500,(0,1,0)),1950,2080,936,384,'hkloom',out=2),cog=176)
for x in (3100,3700,4300,4900):b.rooms['weaver']+=prism(x,2350,200,2048,2496,'hkloomx',top='hobone')
# Nest cups: resin lower bowl, ivory rim, resting against each outer wall.
for base in ('nests_n','nests_s'):
    r=ROOMS[base];y=r['y']+r['h']-150 if base=='nests_n' else r['y']+150
    for k in range(4):
        x=r['x']+500+k*1000;name=owner(base,x,y,r['z'])
        b.rooms[name]+=prism(x,y,260,r['z']+250,r['z']+400,'hochitin',top='hochitin')
        b.rooms[name]+=prism(x,y,300,r['z']+400,r['z']+448,'hobone',top='hochitin')
# Rib windows: two in the Barracks, three behind the looms, four per Crown wall.
for base,count in [('barracks',2),('looms',3),('crown',4)]:
    r=ROOMS[base];sides=('north',) if base!='crown' else ('north','south','east','west')
    for side in sides:
        along_x=side in ('north','south');a0=r['x'] if along_x else r['y'];length=r['w'] if along_x else r['h']
        plane=(r['y']+r['h'] if side=='north' else r['y']) if along_x else (r['x']+r['w'] if side=='east' else r['x'])
        normal={'north':(0,-1,0),'south':(0,1,0),'east':(-1,0,0),'west':(1,0,0)}[side]
        wall=Wall('y' if along_x else 'x',plane,normal)
        for k in range(count):
            a=a0+(k+.5)*length/count
            if base=='looms' and k==1:a+=600
            if base=='crown':a=max(a0+608,min(a0+length-608,a))
            x,y=(a,plane) if along_x else (plane,a)
            name=owner(base,x,y,r['z'])
            if any(h[0]-256<a<h[1]+256 for h in holes.get(name,{}).get(side,[])):continue
            b.rooms[name]+=plaque(wall,a,r['z']+160,512,min(640,r['ceiling']-288),'hkwindow',out=4)
# Crown pillars, perches, ribbed ceiling and the dishes.
for x in (2300,4100):
    for y in (2300,4100):
        name=owner('crown',x,y,4096);b.rooms[name]+=prism(x,y,180,4096,5120,'hobone')
for x,y in ((1900,3200),(4850,4400),(4850,2000)):
    name=owner('crown',x,y,4096);b.rooms[name]+=box((x-300,y-300,4096),(x+300,y+300,4480),'hkrib',top='hochitin')
# A coarse curved shell stays inside the prescribed 1024 ceiling budget.
def dome_z(x,y):
    return 4864+256*math.cos((x-3500)/1900*math.pi/2)*math.cos((y-3200)/1600*math.pi/2)
for name in parts['crown']:
    r=R[name];horizontal(name,5120,False)
    xs=[r['x']+r['w']*k/4 for k in range(5)]
    ys=[r['y']+r['h']*k/4 for k in range(5)]
    for xa,xb in zip(xs,xs[1:]):
        for ya,yb in zip(ys,ys[1:]):
            corners=[kit.Vector((x,y,dome_z(x,y))) for x,y in ((xa,ya),(xb,ya),(xb,yb),(xa,yb))]
            for indices in ((0,1,2),(0,2,3)):
                triangle=[corners[i] for i in indices]
                normal=-(triangle[1]-triangle[0]).cross(triangle[2]-triangle[0]).normalized()
                b.rooms[name].append((triangle,'hkceil',tuple(normal)))
    x=r['x']+r['w']/2;y=r['y']+r['h']/2
    dish_z=min(dome_z(x+dx,y+dy) for dx in (-256,256) for dy in (-256,256))-8
    panels=ceiling(x-256,y-256,x+256,y+256,dish_z,'hkdish')
    b.rooms[name]+=[(*p,Fit((x-256,y-256,dish_z),(1,0,0),(0,1,0),512,512)) for p in panels]
    for k in range(4):
        x0=r['x']+r['w']*k/4;y0=r['y']+r['h']*k/4
        x1=r['x']+r['w']*(k+1)/4;y1=r['y']+r['h']*(k+1)/4
        b.rooms[name]+=beam((x0,y0,dome_z(x0,y0)-32),(x1,y1,dome_z(x1,y1)-32),64,'hobone')
b.rooms['cradle']+=box((3050,5350,4224),(3350,5650,4480),'hsrib',top='hsfloor')
# The short Cradle approach keeps 32-high treads, with its sheer sides railed and the floor cut below.
for name in parts['crown']:
    horizontal(name,4096,True,[pit,(3008,3392,4608,4800)])
    r=R[name]
    stair=kit.flight_along((3200,4608),(3200,4800),384,4096,4,'hkfloor','hkrib',rise=32,
                           sides='hkrib',rail=128,rail_role='hobone')
    b.rooms[name]+=kit.clip_to(stair,[(r['x'],r['y']),(r['x']+r['w'],r['y']),
        (r['x']+r['w'],r['y']+r['h']),(r['x'],r['y']+r['h'])])
