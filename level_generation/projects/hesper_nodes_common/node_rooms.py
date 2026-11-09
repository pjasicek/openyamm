"""Shared Lattice node rooms, furniture and event surfaces. Import from a node's Blender author script."""
import math

import blv_kit as kit
from blv_kit import Wall, banded, box, ceiling, floor, flight, plaque, prism, pipe, rect_minus

ROLES = dict(wall='hnwall', conduit='hnconduit', resin='hnresin', trim='hntrim', floor='hnfloor',
             grate='hngrate', ceiling='hnceil', capacitor='hncapac', dead='hncapacx', blast='hnblast',
             terminal='hnterm', terminal_off='hntermx', coupling='hncoupl', coupling_off='hncouplo',
             coupling_blown='hncouplx', strip='hnstrip', shield='hnshield', cool='hncool', motor='hnmach',
             tunnel='httunnel', rib='htrib', tunnel_floor='htfloor', crown='htcrown', track='httrack',
             glyph='hkglyph', pylon='hkpylon', pylon_off='hkpylonx', rack='harack', service='hcdoor',
             scorch='hcscorch', marker='hnwall')
COMMON_SPLITS = {'guard': ('x', [4800]), 'galleries': ('x', [3800, 6000]),
                 'core': ('xy', [4800, 7616]), 'tunnel': ('y', [10880])}
COMMON_ROOMS = ('vestibule', 'guard', 'ramp', 'galleries', 't1', 't3', 'core', 'vault', 'tunnel')
DOORS = dict(inner=1, west=2, east=3, t3=4, vault=5, service=6)


class NodeRooms:
    """Thick-wall room shell from a node plan; common contents are added separately from its own middle.

    Extra doors map a plan link label to (name, id, event). Extra splits use the same format as COMMON_SPLITS.
    Floor cuts are (x0,x1,y0,y1); use them for pressure plates so no coincident floor covers the trigger.
    """
    def __init__(self, builder, plan, *, splits, doors, floor_cuts, accent='conduit',
                 middle_walls=None, middle_floors=None, ambient=None, wall_roles=None):
        self.b, self.plan, self.accent = builder, plan, accent
        self.parents = {r['id']: dict(r) for r in plan.rooms if r['sectors']}
        self.parts, self.open_sides, self.holes, self.openings, self.leaves, self.exits = {}, {}, {}, [], [], []
        self.floor_cuts = {'vestibule':[(4300,5300,640,800)], 'guard':[(3944,5656,2724,3224)],
                           'galleries':[(m['x']-128,m['x']+128,4992,5952) for m in plan.marks
                                        if m['kind']=='trap' and m['label'].startswith('Arc ')],
                           'core':[(4100,5500,6916,8316)]}
        for base,cuts in floor_cuts.items(): self.floor_cuts.setdefault(base,[]).extend(cuts)
        self.middle_walls, self.middle_floors = middle_walls or {}, middle_floors or {}
        self.wall_roles = wall_roles or {}
        self.ambient = {'core':20,'galleries':24,'tunnel':24, **(ambient or {})}
        split_table = {**COMMON_SPLITS, **splits}
        for name, r in self.parents.items():
            x, y, w, h = (r[k] for k in ('x', 'y', 'w', 'h'))
            axis, cuts = split_table.get(name, ('x', []))
            xs = [x] + (cuts[:1] if axis == 'xy' else cuts if axis == 'x' else []) + [x+w]
            ys = [y] + (cuts[1:] if axis == 'xy' else cuts if axis == 'y' else []) + [y+h]
            for j, (y0, y1) in enumerate(zip(ys, ys[1:])):
                for i, (x0, x1) in enumerate(zip(xs, xs[1:])):
                    rid = name if len(xs)*len(ys) == 4 else name+'_'+str(j*(len(xs)-1)+i)
                    self.parts[rid] = dict(r, base=name, x=x0, y=y0, w=x1-x0, h=y1-y0)
                    self.open_sides[rid] = [s for s, v in [('west', i>0), ('east', i<len(xs)-2),
                                                         ('south', j>0), ('north', j<len(ys)-2)] if v]
            assert (len(xs)-1)*(len(ys)-1) == r['sectors'], (name, r['sectors'])
        # The three nodes retain their shared machine plan, with corners outside every original door mouth.
        self.chamfers = {'vestibule': 160, 'guard': 240, 't1': {'sw': 128, 'se': 64, 'ne': 128, 'nw': 128},
                         't2': 160, 't3': {'se': 128, 'ne': 128, 'nw': 128},
                         'core': {'sw': 512, 'se': 512, 'ne': 512, 'nw': 96}}
        self.hips = {'vestibule', 'guard', 't1', 't2', 't3', 'core'}
        self.door_links = {'inner blast': ('inner', 1, 51), 'west door': ('west', 2, 52),
                           'east door': ('east', 3, 53), 'T3 from': ('t3', 4, 54),
                           'Loot Vault:': ('vault', 5, 55), 'service door:': ('service', 6, 56), **doors}
        for link in plan.links:
            self._link(link)

    def at(self, x, y, base=None):
        return next(n for n, r in self.parts.items() if (base is None or r['base'] == base)
                    and r['x'] <= x <= r['x']+r['w'] and r['y'] <= y <= r['y']+r['h'])

    def _link(self, link):
        edges = []
        for name, r in self.parents.items():
            x, y, w, h = (r[k] for k in ('x', 'y', 'w', 'h'))
            for side, axis, plane, lo, hi in [('west','x',x,y,y+h), ('east','x',x+w,y,y+h),
                                             ('south','y',y,x,x+w), ('north','y',y+h,x,x+w)]:
                along = link['y'] if axis == 'x' else link['x']
                if abs(plane-link[axis]) <= 32 and lo <= along <= hi:
                    edges.append((name, side, axis, plane))
        assert len(edges) in (1,2), (link, edges)
        name, side, axis, plane = edges[0]
        along = link['y'] if axis == 'x' else link['x']
        a0, a1 = along-link['width']/2, along+link['width']/2
        z = self.plan.floors[link['floor']]
        door = next((v for k,v in self.door_links.items() if k in link['label']), None)
        height = 512 if name in ('vestibule','ramp') or 'ramp' in link['label'] else 384
        if door and door[0] == 'vault': height = 448
        if len(edges) == 1:
            height = 384
            self.exits.append((name, side, axis, plane, along, z, link['width'], height,
                               50 if name == 'vestibule' else 57))
        elif link['kind'] == 'open' and all(self.parents[e[0]]['ceiling']>=512 for e in edges): height = 512
        for base, s, ax, p in edges:
            for rid, r in self.parts.items():
                if r['base'] != base: continue
                boundary = r[ax] + (r['w' if ax=='x' else 'h'] if s in ('north','east') else 0)
                lo = r['y' if ax=='x' else 'x']; hi = lo+r['h' if ax=='x' else 'w']
                if boundary == p and min(hi,a1)>max(lo,a0):
                    self.holes.setdefault(rid,{}).setdefault(s,[]).append((max(lo,a0),min(hi,a1),z,z+height))
        if len(edges) == 2:
            edges.sort(key=lambda e:e[3])
            first, second = edges
            cuts = {a0,a1}
            for r in self.parts.values():
                if r['base'] in (first[0],second[0]):
                    lo = r['y' if axis=='x' else 'x']; hi=lo+r['h' if axis=='x' else 'w']
                    cuts.update(v for v in (lo,hi) if a0<v<a1)
            cuts=sorted(cuts)
            for lo,hi in zip(cuts,cuts[1:]):
                def owner(edge):
                    p=edge[3]+(-1 if edge[1] in ('north','east') else 1)
                    return self.at(p,(lo+hi)/2,edge[0]) if axis=='x' else self.at((lo+hi)/2,p,edge[0])
                self.openings.append((owner(first),owner(second),axis,first[3],lo,hi,z,z+height))
            if door:
                self.leaves.append((*door, self.openings[-1][0], axis, link[axis], a0,a1,z,z+height))

    def shell(self):
        b=self.b
        for rid,r in self.parts.items():
            base=r['base']; x,y,w,h,z,clear=(r[k] for k in ('x','y','w','h','z','ceiling'))
            b.room(rid,(x,y,x+w,y+h,-513 if base=='ramp' else z-1,z+clear),
                   self.ambient.get(base,22))
            if base=='ramp':
                # Plan z is the upper landing; the ceiling follows the falling floor, 640 above it.
                for dz,role,normal in [(0,'grate',(0,0,1)),(clear,'ceiling',(0,0,-1))]:
                    b.rooms[rid].append(([(x,y,dz),(x+w,y,dz),(x+w,y+h,-512+dz),(x,y+h,-512+dz)],role,normal))
                for xx,n in [(x,(1,0,0)),(x+w,(-1,0,0))]:
                    b.rooms[rid].append(([(xx,y,0),(xx,y+h,-512),(xx,y+h,128),(xx,y,640)],'conduit',n))
                continue
            cuts=list(self.floor_cuts.get(base,[]))
            if base=='tunnel': cuts.append((3360,3488,y,y+h))
            for a0,a1,c0,c1 in rect_minus(x,x+w,y,y+h,cuts):
                b.rooms[rid]+=floor(a0,c0,a1,c1,z,self.middle_floors.get(base,'tunnel_floor' if base=='tunnel' else 'floor'))
            if base=='tunnel': b.rooms[rid]+=floor(3360,y,3488,y+h,z,'track')
            b.rooms[rid]+=ceiling(x,y,x+w,y+h,z+clear,'crown' if base=='tunnel' else 'ceiling')
            for side,wall,lo,hi in [('south',Wall('y',y,(0,1,0)),x,x+w),('north',Wall('y',y+h,(0,-1,0)),x,x+w),
                                    ('west',Wall('x',x,(1,0,0)),y,y+h),('east',Wall('x',x+w,(-1,0,0)),y,y+h)]:
                if side in self.open_sides[rid]: continue
                role='conduit' if base=='galleries' or (base in ('t1','t2','t3') and side=='north') else 'wall'
                if (base=='guard' and side=='north') or (base=='t2' and side=='west'):
                    role=self.accent
                role=self.middle_walls.get(base,role)
                role=self.wall_roles.get((base,side),role)
                if base=='tunnel': role='tunnel'
                lower=min(clear-64,640 if base=='core' else 512 if base=='guard' or base in self.middle_walls else 448)
                bands=[(z,z+lower,role),(z+lower,z+lower+32,'rib' if base=='tunnel' else 'trim'),
                       (z+lower+32,z+clear,'resin' if base!='tunnel' else 'tunnel')]
                b.rooms[rid]+=banded(wall,lo,hi,bands,self.holes.get(rid,{}).get(side,[]))
            parent = self.parents[base]
            px, py, pw, ph = (parent[k] for k in ('x', 'y', 'w', 'h'))
            footprint = kit.chamfer_rect(px, py, px+pw, py+ph, self.chamfers.get(base, 0))
            if base in self.chamfers:
                b.rooms[rid] = kit.clip_to(b.rooms[rid], footprint)
                corners = [p for p in kit.rect_walls(px, py, px+pw, py+ph,
                           [(z, z+clear-64, self.middle_walls.get(base, 'wall')),
                            (z+clear-64, z+clear, 'resin')], chamfer=self.chamfers[base])
                           if p[2][0] and p[2][1]]
                b.rooms[rid] += kit.clip_to(corners, kit.chamfer_rect(x, y, x+w, y+h, 0))
                # room_at must use each sector's part of the shared footprint.
                panel = kit.clip_to(kit.polygon_floor(footprint, z, 'floor'),
                                    kit.chamfer_rect(x, y, x+w, y+h, 0))[0]
                b.footprints[rid] = [(float(v[0]), float(v[1])) for v in panel[0]]
                for side, holes in self.holes.get(rid, {}).items():
                    for a0, a1, _, _ in holes:
                        for a in (a0, a1):
                            xx, yy = ((a, y+(h if side == 'north' else 0)) if side in ('north', 'south')
                                      else (x+(w if side == 'east' else 0), a))
                            assert kit._inside(footprint, xx, yy), (rid, side, a)
            if base in self.hips:
                b.rooms[rid] = [p for p in b.rooms[rid] if p[2][2] >= 0]
                b.rooms[rid] += kit.clip_to(kit.hip_ceiling(footprint, z+clear, z+clear+128, 'ceiling'),
                                          kit.chamfer_rect(x, y, x+w, y+h, 0))
                b.bounds[rid] = (*b.bounds[rid][:5], z+clear+128)
        for a,ra in self.parts.items():
            for c,rc in self.parts.items():
                if a>=c or ra['base']!=rc['base']: continue
                for axis,size,other,extent in [('x','w','y','h'),('y','h','x','w')]:
                    if ra[axis]+ra[size]!=rc[axis]: continue
                    lo,hi=max(ra[other],rc[other]),min(ra[other]+ra[extent],rc[other]+rc[extent])
                    if hi<=lo: continue
                    p=ra[axis]+ra[size]; wall=Wall(axis,p,(1,0,0) if axis=='x' else (0,1,0))
                    z=ra['z']; top=z+ra['ceiling']+(128 if ra['base'] in self.hips else 0)
                    b.portal(a,c,[wall.point(lo,z),wall.point(hi,z),wall.point(hi,top),wall.point(lo,top)])
        for a,c,axis,p,lo,hi,z,top in self.openings:
            before=len(b.rooms[a])
            b.opening(a,c,axis,p,lo,hi,z,top)
            # A portal split is not a physical jamb; only the ends of the complete opening have jambs.
            internal=[v for v in (lo,hi) if any(o[2]==axis and o[3]==p and o[6:]==(z,top)
                       and (o[5]==v if v==lo else o[4]==v) for o in self.openings)]
            along=1 if axis=='x' else 0
            panels=b.rooms[a][before:]
            b.rooms[a][before:]=[face for face in panels
                                if not any(all(abs(pt[along]-v)<.01 for pt in face[0]) for v in internal)]
            assert len(b.rooms[a])-before==len(panels)-len(internal)
        for name,did,event,rid,axis,p,lo,hi,z,top in self.leaves:
            role='service' if name=='service' else 'blast'
            leaf=box((p-8,lo,z),(p+8,hi,top),role,top='trim') if axis=='x' else box((lo,p-8,z),(hi,p+8,top),role,top='trim')
            length=top-z
            seconds=1.2 if did==1 else 2 if did==5 else 1 if did==6 else .8
            # Fit each blast face to its opening; service faces retain their own fitted panel below.
            for i,panel in enumerate(leaf):
                pts,role,n=panel
                if abs(n[0 if axis=='x' else 1])>.5:
                    ww=Wall(axis,pts[0][0 if axis=='x' else 1],n)
                    leaf[i]=(*panel,ww.fit(lo,hi,z,top))
            b.door(name,rid,leaf,did,length,direction=(0,0,-1) if did==5 else (0,0,1),
                   open_speed=length/seconds,close_speed=length/seconds,event=event)
        for base,side,axis,p,along,z,width,height,event in self.exits:
            n={'south':(0,1,0),'north':(0,-1,0),'west':(1,0,0),'east':(-1,0,0)}[side]
            rid=self.at(self.parents[base]['x']+self.parents[base]['w']/2,
                        self.parents[base]['y']+(1 if side=='south' else self.parents[base]['h']-1),base)
            face,jambs=kit.recessed_door(Wall(axis,p,n),along,z,width,height,'blast')
            b.rooms[rid]+=jambs; b.trigger('exit_'+base,rid,face,event)

    def validate_shapes(self):
        """Every door, fixture and event surface stays inside its chamfered parent room."""
        b = self.b
        for base, cut in self.chamfers.items():
            r = self.parents[base]
            x0, y0, x1, y1 = r['x'], r['y'], r['x']+r['w'], r['y']+r['h']
            footprint = kit.chamfer_rect(x0, y0, x1, y1, cut)
            for rid, part in self.parts.items():
                if part['base'] != base: continue
                panels = list(b.rooms[rid])
                for name, owner, faces, *_ in b.triggers + b.mechanisms:
                    if owner == rid: panels += faces
                for panel in panels:
                    for x, y, _ in panel[0]:
                        if x0 <= x <= x1 and y0 <= y <= y1:
                            assert kit._inside(footprint, x, y), (rid, x, y)
            for name, x, y, z, *_ in b.decorations:
                if x0 <= x <= x1 and y0 <= y <= y1 and r['z'] <= z < r['z']+r['ceiling']:
                    assert kit._inside(footprint, x, y), (base, name, x, y)

    def plate(self,name,base,rect,event,z=None,cog=0,role='floor'):
        x0,x1,y0,y1=rect
        z=self.parents[base]['z'] if z is None else z
        for rid,r in self.parts.items():
            if r['base']!=base: continue
            a,c=max(x0,r['x']),max(y0,r['y']); d,e=min(x1,r['x']+r['w']),min(y1,r['y']+r['h'])
            if d>a and e>c: self.b.trigger(name+'_'+rid,rid,floor(a,c,d,e,z,role),event,kind='pressure_plate',cog=cog)

    def terminal(self,base,event):
        b=self.b; r=self.parents[base]
        m=next(m for m in self.plan.marks if m['kind']=='interact' and f'event {event}' in m['label'])
        x,y=m['x'],m['y']; z=r['z']; rid=self.at(x,y,base)
        # The design's 900-high console cannot fit under its 448/512 ceilings. Keep 64 overhead.
        top=z+r['ceiling']-64
        b.rooms[rid]+=box((x-300,y-234,z),(x+300,y+66,top),'conduit',top='trim',skip=('north',))
        b.trigger('terminal_'+base,rid,plaque(Wall('y',y-234,(0,-1,0)),x,z+128,256,192,'terminal',out=4),event,cog=event)

    def common_contents(self,design,*,coupling_radius,coupling_geometry=True):
        b=self.b
        # Capacitor cover and a low dais; side stairs preserve a level approach to the down ramp.
        for x in (3900,5700):
            for y in (1700,2600):
                b.rooms[self.at(x,y,'guard')]+=box((x-200,y-200,0),(x+200,y+200,512),'capacitor',top='trim')
        for rid,x0,x1 in [('guard_0',4200,4800),('guard_1',4800,5400)]:
            b.rooms[rid]+=box((x0,2724,0),(x1,2968,128),'trim',top='grate',skip=('east' if x1==4800 else 'west',))
            b.rooms[rid]+=flight(x0,2968,x1,3224,0,8,'south',tread='grate',rise=16)
        for x0,x1,direction in [(3944,4200,'east'),(5400,5656,'west')]:
            b.rooms[self.at((x0+x1)/2,2900,'guard')]+=flight(x0,2724,x1,3224,0,8,direction,tread='grate',rise=16)
            rid = self.at((x0+x1)/2,2900,'guard')
            b.rooms[rid] += Wall('y',2724,(0,-1,0)).quad(x0,x1,0,160,'trim')
            edge = 4200 if direction == 'east' else 5400
            b.rooms[rid] += Wall('x',edge,(1,0,0) if direction == 'east' else (-1,0,0)).quad(
                2968,3224,0,160,'trim')
        p=next(m for m in self.plan.marks if 'event 70'  in m['label'])
        b.decoration('hes_alarm_pylon',p['x'],p['y'],0,90,event=70,cog=70)
        b.trigger('pylon_niche','guard_0',plaque(Wall('x',3200,(1,0,0)),1500,48,320,384,'pylon',out=8),70,cog=70)
        # Readable plates are attached to the named room fixtures, not scattered room dressing.
        for name,base,w,a,z,event in [('duty','guard',Wall('y',3224,(0,-1,0)),4100,200,10),
                                     ('arc_warning','galleries',Wall('x',1600,(1,0,0)),5472,-288,11),
                                     ('heart_plate','core',Wall('y',6016,(0,1,0)),5200,-288,12)]:
            point=w.point(a,z); rid=self.at(point.x+ w.inward[0],point.y+w.inward[1],base)
            b.trigger(name,rid,plaque(w,a,z,256,160,'glyph'),event)
        self.plate('inner_approach','vestibule',(4300,5300,640,800),51)
        for k,x in enumerate(design.ARC_X):
            rid=self.at(x,5472,'galleries')
            for y in (5112,5832):
                b.rooms[rid]+=box((x-160,y-120,-512),(x+160,y+120,128),'capacitor',top='trim')
            b.rooms[rid]+=plaque(Wall('y',5952,(0,-1,0)),x,-464,256,192,'scorch',out=4)
            self.plate('arc_'+str(k),'galleries',(x-128,x+128,4992,5952),71+k,cog=71+k,role='strip')
        for rid,r in self.parts.items():
            if r['base']=='galleries':
                for z in (-392,-132): b.rooms[rid]+=pipe((r['x'],5890,z),(r['x']+r['w'],5890,z),60,'resin')
        for base,event in [('t1',80),('t3',82)]: self.terminal(base,event)
        cx,cy=design.CORE_CENTRE
        # Divide the central pillar and its annulus across all four owning sectors.
        for quarter in range(4):
            theta=quarter*math.pi/2
            rid=self.at(cx+math.cos(theta+.5)*10,cy+math.sin(theta+.5)*10,'core')
            panels=[]; skirt=[]
            for k in range(4):
                a=theta+k*math.pi/8; c=a+math.pi/8
                points=lambda r,z:[(cx+r*math.cos(v),cy+r*math.sin(v),z) for v in (a,c)]
                p0,p1=points(400,-512); p2,p3=points(700,-512)
                b.rooms[rid].append(([p0,p2,p3,p1],'grate',(0,0,1)))
                outer=[(cx+700*math.cos(v)/max(abs(math.cos(v)),abs(math.sin(v))),
                        cy+700*math.sin(v)/max(abs(math.cos(v)),abs(math.sin(v))),-512) for v in (a,c)]
                b.rooms[rid].append(([p2,outer[0],outer[1],p3],'floor',(0,0,1)))
                for z0,z1 in [(-512,-352),(-352,-96),(-96,160),(160,416),(416,640)]:
                    lo=points(400,z0); hi=points(400,z1)
                    panel=([lo[0],lo[1],hi[1],hi[0]],'resin' if z0==-512 else 'capacitor',
                           (math.cos((a+c)/2),math.sin((a+c)/2),0))
                    (skirt if z0==-512 else panels).append(panel)
            b.trigger('heart_'+str(quarter),rid,panels,90,cog=90)
            b.trigger('heart_skirt_'+str(quarter),rid,skirt,90)
        for k,(x,y) in enumerate(design.couplings(coupling_radius)):
            rid=self.at(x,y,'core')
            if coupling_geometry:
                b.trigger('coupling_'+str(k),rid,prism(x,y,140,-512,128,'coupling',top='trim'),85+k,cog=85+k)
                b.rooms[rid]+=prism(x,y,50,128,256,'resin',sides=8)
            # Axis-aligned elbows meet the heart at the specified 768-unit cable height.
            b.rooms[rid]+=pipe((x,y,256),(cx,y,256),50,'resin') if x!=cx else []
            b.rooms[rid]+=pipe((cx,y,256),(cx,cy,256),50,'resin')
        for x,y,w,h in [(4264,9440,160,640),(5176,9440,160,640),(4440,10080,280,160),(4880,10080,280,160)]:
            b.rooms['vault']+=box((x,y,-512),(x+w,y+h,-192),'rack',top='trim')
        for y in range(9280,12481,1200):
            rid=self.at(3424,min(y+1,12479),'tunnel')
            for x in (3200,3616): b.rooms[rid]+=box((x,y,-512),(x+32,y+48,0),'rib',top='rib')
        for base,label,event in [('t1','T1 locker',30),('galleries',"Galleries' end",31),('vault','Loot Vault',33)]:
            m=next(m for m in self.plan.marks if m['label'].startswith(label))
            b.decoration('hes_colonial_locker',m['x'],m['y'],-512,0,event=event)
        for base,label,width in [('t1','Breach Charge cache',300),('t3','Cache before the core',600)]:
            m=next(m for m in self.plan.marks if m['label'].startswith(label))
            x,y=m['x'],m['y']; rid=self.at(x,y,base)
            b.rooms[rid]+=box((x-width/2,y-80,-384),(x+width/2,y+80,-352),'rack',top='trim',bottom='trim')
            for dx in (-width/2+24,width/2-24): b.rooms[rid]+=box((x+dx-12,y-60,-512),(x+dx+12,y+60,-384),'trim')
