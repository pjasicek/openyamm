"""Original facade-panel architecture calibrated against native Ravenshore measurements.

Coordinates remain in game units. UVs follow physical panel lengths at one unit per texel;
wall bands/window art are native bitmaps, while the footprints and compositions are authored here.
"""
import math


def house(building):
    w, d = building['local_footprint']
    form = building['form']
    floor = building['floor_z']
    step = 32 if form in ['gable', 'hipped'] else 0
    z = floor + step
    door_x = building['door_offset_x']
    panels, uvs = [], []
    family = 'b' if form in ['gable', 'barn'] else 'c' if form in ['hipped', 'chapel', 'manor'] else 'a'
    blank, window = 't14' + family + '01', 't14' + family + '04c'
    if family == 'a':
        window = 't14a04c'
    door_key = 't14' + family + '03'

    def panel(points, key, coords):
        panels.append((points, key))
        uvs.extend(coords)

    def projected(points, key, size=128):
        # Roof plane basis preserves texel size along its sloping surface.
        a, b = points[0], points[1]
        edge = [b[i] - a[i] for i in range(3)]
        length = math.sqrt(sum(v*v for v in edge))
        axis = [v / length for v in edge]
        other = [points[-1][i] - a[i] for i in range(3)]
        dot = sum(other[i]*axis[i] for i in range(3))
        tangent = [other[i] - dot*axis[i] for i in range(3)]
        length = math.sqrt(sum(v*v for v in tangent))
        tangent = [v / length for v in tangent]
        coords = [(sum((p[i]-a[i])*axis[i] for i in range(3))/size,
                   sum((p[i]-a[i])*tangent[i] for i in range(3))/size) for p in points]
        panel(points, key, coords)

    def wall(a, b, bottom, top, front=False, wall_key=None, windows=True):
        length = math.dist(a, b)
        # Door edges participate in panel boundaries; the actual event plane sits one unit outside.
        cuts = {0., length}
        cuts.update(float(v) for v in range(128, math.ceil(length), 128))
        if front:
            for x in [door_x-64, door_x+64]:
                if a[0] < x < b[0]: cuts.add(x-a[0])
        cuts = sorted(cuts)
        for level in range(bottom, top, 256):
            upper = min(level+256, top)
            for index, (u0, u1) in enumerate(zip(cuts, cuts[1:])):
                p = (a[0]+(b[0]-a[0])*u0/length, a[1]+(b[1]-a[1])*u0/length)
                q = (a[0]+(b[0]-a[0])*u1/length, a[1]+(b[1]-a[1])*u1/length)
                is_door = front and level == z and abs((p[0]+q[0])/2-door_x)<64
                key = wall_key or (door_key if is_door else window if windows and index%3==1 and u1-u0==128 else blank)
                if not wall_key and not is_door and u1-u0==128 and index in [0,len(cuts)-2]:
                    key = 't14'+family+('06' if index==0 else '07')
                # Use the same phase for neighbouring facade pieces and for split door panels.
                uv0 = (p[0]-(door_x-64))/128 if is_door else 0
                v0 = 1-(upper-level)/256 if wall_key == 't14d01' else 0
                panel([(p[0],p[1],level),(q[0],q[1],level),(q[0],q[1],upper),(p[0],p[1],upper)],
                      key,[(uv0,v0),(uv0+(u1-u0)/128,v0),(uv0+(u1-u0)/128,v0+(upper-level)/256),(uv0,v0+(upper-level)/256)])

    def volume(x0,y0,x1,y1,bottom,top,front=False,wall_key=None,windows=True):
        corners=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
        for i in range(4):
            wall(corners[i],corners[(i+1)%4],bottom,top,front and i==0,wall_key,windows)
        projected([(x0,y0,top),(x1,y0,top),(x1,y1,top),(x0,y1,top)],'t14a05b')
        projected([(x0,y1,bottom),(x1,y1,bottom),(x1,y0,bottom),(x0,y0,bottom)],'t14a05b')

    def roof(x0,y0,x1,y1,eave,peak,hip=True,key='t14b05'):
        middle=(y0+y1)/2
        inset=min((x1-x0)*.23,(y1-y0)*.4) if hip else 0
        a,b=(x0+inset,middle,peak),(x1-inset,middle,peak)
        for points in [[(x0,y0,eave),(x1,y0,eave),b,a],
                       [a,b,(x1,y1,eave),(x0,y1,eave)],
                       [(x0,y1,eave),(x0,y0,eave),a],
                       [(x1,y0,eave),(x1,y1,eave),b]]:
            projected(points,key)

    def chamfered_body(bottom,top,wall_key=None):
        c=64
        ring=[(-w/2+c,-d/2),(w/2-c,-d/2),(w/2,-d/2+c),(w/2,d/2-c),
              (w/2-c,d/2),(-w/2+c,d/2),(-w/2,d/2-c),(-w/2,-d/2+c)]
        for i,a in enumerate(ring):wall(a,ring[(i+1)%8],bottom,top,front=i==0,wall_key=wall_key)
        projected([(x,y,top) for x,y in ring],'t14a05b')
        projected([(x,y,bottom) for x,y in reversed(ring)],'t14a05b')
        return ring

    def tower(cx,cy,radius,top):
        ring=[(round(cx+radius*math.cos(i*math.pi/4)),round(cy+radius*math.sin(i*math.pi/4))) for i in range(8)]
        for i,a in enumerate(ring):
            b=ring[(i+1)%8]
            wall(a,b,floor-64,top,wall_key='t14c01b',windows=False)
            projected([(a[0],a[1],top),(b[0],b[1],top),(cx,cy,top+192)],'t14a05b' if form=='turret_house' else 't14b05')

    # Foundation is shallow; the facade's masonry/plaster split is already painted into its bitmap.
    if form in ['hipped','turret_house']:
        chamfered_body(floor-64,z,wall_key='t14c01b')
    elif form=='manor':
        volume(-1024,-d/2,1024,d/2,floor-64,z,wall_key='t14c01b',windows=False)
        for x0,x1 in [(-w/2,-1024),(1024,w/2)]:
            volume(x0,-d/2+256,x1,d/2,floor-64,z,wall_key='t14c01b',windows=False)
    else:
        volume(-w/2,-d/2,w/2,d/2,floor-64,z,wall_key='t14c01b',windows=False)
    if form=='courtyard':
        inner=128
        for x0,x1 in [(-w/2,-inner),(inner,w/2)]:
            volume(x0,-d/2,x1,d/2,z,z+256,front=True)
            roof(x0-24,-d/2-24,x1+24,d/2+24,z+256,z+448)
        volume(-inner,d/2-384,inner,d/2,z,z+256)
        roof(-inner-24,d/2-408,inner+24,d/2+24,z+256,z+448)
    elif form=='manor':
        # Central hall projects ahead of lower wings; two rear towers frame the uphill silhouette.
        volume(-1024,-d/2,1024,d/2,z,z+768,front=True)
        roof(-1072,-d/2-48,1072,d/2+48,z+768,z+1152)
        for x0,x1 in [(-w/2,-1024),(1024,w/2)]:
            volume(x0,-d/2+256,x1,d/2,z,z+512)
            roof(x0-32,-d/2+224,x1+32,d/2+32,z+512,z+800)
        for tx in [-w/2+384,w/2-384]:tower(tx,d/2-384,384,z+1408)
    elif form in ['inn','civic']:
        volume(-w/2,-d/2,w/2,d/2,z,z+512,front=True)
        roof(-w/2-32,-d/2-32,w/2+32,d/2+32,z+512,z+736)
        if form=='civic':
            tower(w/2-160,d/2-160,160,z+896)
        else:
            # Small upper rear pavilion changes the long roof silhouette without enlarging the entrance.
            volume(-w/2,d/2-384,-w/2+512,d/2,z+512,z+768)
            roof(-w/2-32,d/2-416,-w/2+544,d/2+32,z+768,z+928)
    elif form=='chapel':
        volume(-w/2,-d/2,w/2,d/2,z,z+512,front=True)
        roof(-w/2-32,-d/2-32,w/2+32,d/2+32,z+512,z+896)
        for tx in [-w/2+160,w/2-160]: tower(tx,d/2-160,192,z+1216)
    else:
        if form in ['hipped','turret_house']:
            ring=chamfered_body(z,z+256)
        else:
            volume(-w/2,-d/2,w/2,d/2,z,z+256,front=True)
        if form in ['flat','turret_house']:
            # Low roof and narrow trim, in the simple flat-roof house vocabulary.
            if form=='turret_house':
                for i,a in enumerate(ring):wall(a,ring[(i+1)%8],z+256,z+288,wall_key='t14d01',windows=False)
                projected([(x,y,z+288) for x,y in ring],'t14a05b')
            else:
                volume(-w/2-16,-d/2-16,w/2+16,d/2+16,z+256,z+288,wall_key='t14d01',windows=False)
            if form=='turret_house':tower(w/2-128,d/2-128,128,z+576)
        elif form == 'shop_bay':
            if building['id'] == 'weapon_shop':
                roof(-w/2-32,-d/2-32,w*1.5+32,d/2+32,z+256,z+448)
        else:
            roof(-w/2-32,-d/2-32,w/2+32,d/2+32,z+256,z+(448 if form=='barn' else 416),form!='gable')
            if form=='barn':
                # Timber roof supports are geometry; a chimney is not part of this kit.
                for tx in [-w/2+64,w/2-64]:
                    volume(tx-24,d/2-160,tx+24,d/2-112,z,z+256,wall_key='t14b06',windows=False)
    if step:
        volume(door_x-96,-d/2-128,door_x+96,-d/2,floor,z,wall_key='t14c01b',windows=False)
    sign=building.get('service_sign')
    if sign:
        # Upper right of the doorway as viewed from outside.
        x0=door_x+80; y=-d/2-2
        panel([(x0,y,z+192),(x0+64,y,z+192),(x0+64,y,z+256),(x0,y,z+256)],sign,[(0,0),(1,0),(1,1),(0,1)])
    door=[(door_x-64,-d/2-3,z),(door_x+64,-d/2-3,z),(door_x+64,-d/2-3,z+256),(door_x-64,-d/2-3,z+256)]
    return dict(panels=panels,uvs=uvs,door=door,door_texture=door_key,door_floor=z,
                reference_policy='128x256 facade door; one native unit per texel; original geometry; no chimneys')
