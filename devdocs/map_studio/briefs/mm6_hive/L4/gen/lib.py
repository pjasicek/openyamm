"""Helpers that turn a measured description of the Hive into project files (rooms.yml and the rest).
Everything here only writes vocabulary of the studio: outlines, paths, slopes, openings."""
import math,json,yaml
BASE='/home/pjasicek/github/OpenYAMM/'
TEX=json.load(open(BASE+'output/studio_cal/mm6_hive/tex.json'))
EXTRA_SIZES={'swfloor2b':[128,128],'hvdorc':[256,256],'hvdord':[256,256],'hvdorg':[128,256],'hvflorh':[128,128],'hvflorf':[128,128],'ch1frntb':[64,64],'hvtrim4':[32,32],'hvwl3':[128,128],'hvwl5':[128,128],'hvwl4':[128,128]}
OVERRIDE={36:('hvceilb','hvflori','hvceilb'),35:('hvwl5a','hvflori','hvceilb'),76:('hvwl3a','hvflore','hvceilb'),62:('hvwl5a','hvflori','hvceilb'),5:('hvwl4a','hvflora','hvwl4a'),6:('hvwl4a','hvflorb','hvwl4a'),7:('hvwl4a','hvflorb','hvwl4a'),8:('hvwl4a','hvflora','hvwl4a'),77:('hvdorf','swflorb','hvdore'),80:('hvwl5a','hvflorb','hvdore'),73:('hvflord','hvflorb','hvflora'),74:('hvwl2a','hvflori','hvflora')}
import os
SMOOTH=json.load(open(BASE+'output/studio_cal/mm6_hive/tools/smooth.json')) if os.path.exists(BASE+'output/studio_cal/mm6_hive/tools/smooth.json') else {}
def rnd(x): return int(math.floor(abs(x)+0.5))*(1 if x>=0 else -1)
def gcd(a,b): return math.gcd(abs(int(a)),abs(int(b)))
class Proj:
    def __init__(s):
        s.rooms=[];s.openings=[];s.themes={};s.polys={};s.meta={}
    def surf(s,name):
        size=TEX['sizes'].get(name) or EXTRA_SIZES[name]
        return {'texture':name,'size':size}
    def theme(s,wall,floor,ceil):
        key=f"theme:{wall}_{floor}_{ceil}"
        if key not in s.themes:
            s.themes[key]={'id':key,'wall':s.surf(wall),'floor':s.surf(floor),'ceiling':s.surf(ceil)}
        return key
    def theme_of(s,si,wall=None,floor=None,ceil=None):
        w,f,c=TEX['dom'][str(si)]
        w,f,c=OVERRIDE.get(si,(w,f,c))
        w=w or c
        return s.theme(wall or w or 'hvwl1a',floor or f or 'hvflora',ceil or c or f or 'hvflora')
    def room(s,rid,sector,floor,ceiling,outline=None,path=None,width=None,smooth=None,slope=None,rough=None,poly=None,theme=None,**kw):
        r={'id':'room:'+rid}
        if outline is not None: r['outline']=[[int(x),int(y)] for x,y in outline]
        if path is not None:
            r['path']=[[int(x),int(y)] for x,y in path];r['width']=width
            if smooth: r['smooth']=smooth
        r['floor']=floor
        if slope: r['slope']=slope
        if rough: r['rough']=rough
        r['ceiling']=ceiling
        r['theme']=theme or s.theme_of(sector)
        r.update(kw)
        s.rooms.append(r)
        s.polys[r['id']]=[tuple(p) for p in (outline if outline is not None else poly)]
        zs=[floor]+([slope['to']] if slope else [])
        s.meta[r['id']]={'sector':sector,'zmin':min(zs),'zmax':max(zs),'ceiling':ceiling}
        return r
    def open(s,a,b,width='full',height='full',**kw):
        o={'id':f"open:{a}__{b}",'from':'room:'+a,'to':'room:'+b,'width':width,'height':height}
        o.update(kw);s.openings.append(o);return o['id']
    # ---- tunnels
    def tunnel(s,name,sector,st,width=224,height=256,leg=128,rough=None,theme=None,smooth=2,maxdrop=80):
        """st: stations [x,y,z] (optional 4th: leg). A straight sloping piece between stations, a flat smoothed
        bend at every inner station. Returns the ids in order and the two end edges."""
        n=len(st);P=[(int(p[0]),int(p[1])) for p in st];Z=[p[2] for p in st]
        legs=[0]*n;turn=[0]*n
        segl=[math.hypot(P[i+1][0]-P[i][0],P[i+1][1]-P[i][1]) for i in range(n-1)]
        for j in range(1,n-1):
            a1=math.atan2(P[j][1]-P[j-1][1],P[j][0]-P[j-1][0]);a2=math.atan2(P[j+1][1]-P[j][1],P[j+1][0]-P[j][0])
            th=abs((a2-a1+math.pi)%(2*math.pi)-math.pi);turn[j]=th
            need=width/2*math.tan(th/2)
            legs[j]=st[j][3] if len(st[j])>3 else max(2.2*need+40,min(leg,96))
        for i in range(n-1):
            tot=legs[i]+legs[i+1]
            if tot>0.88*segl[i]:
                k=0.88*segl[i]/tot
                print(f"note: tunnel {name} segment {i} ({P[i]} to {P[i+1]}, {segl[i]:.0f} long) is short for its bends (legs {legs[i]:.0f}+{legs[i+1]:.0f})")
                legs[i]*=k;legs[i+1]*=k
        A=[];B=[]
        for i in range(n-1):
            vx,vy=P[i+1][0]-P[i][0],P[i+1][1]-P[i][1];g=gcd(vx,vy);gx,gy=vx//g,vy//g;gl=math.hypot(gx,gy)
            ma=max(1,round(legs[i]/gl)) if legs[i] else 0
            mb=max(1,round(legs[i+1]/gl)) if legs[i+1] else 0
            if ma+mb>=g: raise Exception(f"tunnel {name} segment {i}: stations too close or off-grid (gcd {g})")
            A.append((P[i][0]+ma*gx,P[i][1]+ma*gy));B.append((P[i+1][0]-mb*gx,P[i+1][1]-mb*gy))
        ids=[]
        def rect(a,b):
            dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy);ox,oy=rnd(-dy/L*width/2),rnd(dx/L*width/2)
            return [(a[0]-ox,a[1]-oy),(b[0]-ox,b[1]-oy),(b[0]+ox,b[1]+oy),(a[0]+ox,a[1]+oy)]
        for i in range(n-1):
            if i>0:
                rid=f"{name}_b{i}"
                need=width/2*math.tan(turn[i]/2);sm=2 if legs[i]>=2.2*need+39 else (1 if legs[i]>=1.6*need+30 else 0)
                sm=SMOOTH.get('room:'+rid,sm)
                s.room(rid,sector,Z[i],Z[i]+height,path=[B[i-1],P[i],A[i]],width=width,smooth=sm,rough=rough,
                       poly=rect(B[i-1],P[i])[:2]+rect(P[i],A[i])[1:3]+rect(B[i-1],P[i])[3:],theme=theme)
                s.open(ids[-1],rid);ids.append(rid)
            z0,z1=Z[i],Z[i+1]
            if abs(z1-z0)<6:
                rid=f"{name}_s{i}"
                s.room(rid,sector,z0,max(z0,z1)+height,path=[A[i],B[i]],width=width,poly=rect(A[i],B[i]),rough=rough,theme=theme)
                if i>0: s.open(ids[-1],rid)
                ids.append(rid)
            else:
                # a ramp; long drops are cut into pieces so the flat ceiling of each piece stays near the floor
                vx,vy=B[i][0]-A[i][0],B[i][1]-A[i][1];g=gcd(vx,vy);run=math.hypot(vx,vy)
                k=min(max(1,math.ceil(abs(z1-z0)/maxdrop)),max(1,int(run//160)),g)
                cuts=[(A[i][0]+vx//g*round(g*j/k),A[i][1]+vy//g*round(g*j/k)) for j in range(k+1)]
                for j in range(k):
                    rid=f"{name}_s{i}"+('' if k==1 else 'abcdefgh'[j])
                    za=round(z0+(z1-z0)*j/k);zb=round(z0+(z1-z0)*(j+1)/k)
                    s.room(rid,sector,za,max(za,zb)+height,path=[cuts[j],cuts[j+1]],width=width,slope={'to':zb,'toward':1},poly=rect(cuts[j],cuts[j+1]),theme=theme)
                    if ids: s.open(ids[-1],rid)
                    ids.append(rid)
        def edge(p,q,start):
            dx,dy=q[0]-p[0],q[1]-p[1];L=math.hypot(dx,dy);ox,oy=rnd(-dy/L*width/2),rnd(dx/L*width/2)
            # corner points in the order a counter-clockwise chamber outline needs them
            if start: return [(p[0]-ox,p[1]-oy),(p[0]+ox,p[1]+oy)]
            return [(q[0]+ox,q[1]+oy),(q[0]-ox,q[1]-oy)]
        return {'ids':ids,'first':ids[0],'last':ids[-1],'m0':edge(P[0],P[1],True),'m1':edge(P[-2],P[-1],False)}
    def jrect(s,name,sector,C,u,halflen,hw,floor,ceiling,theme=None,**kw):
        """A short straight flat piece of tunnel where a side passage leaves: centre C, direction u (whole numbers)."""
        L=math.hypot(*u);k=max(1,round(halflen/L));ax,ay=u[0]*k,u[1]*k
        ox,oy=rnd(-u[1]/L*hw),rnd(u[0]/L*hw)   # left of u
        Pin=(C[0]-ax,C[1]-ay);Pout=(C[0]+ax,C[1]+ay)
        out=[(Pin[0]-ox,Pin[1]-oy),(Pout[0]-ox,Pout[1]-oy),(Pout[0]+ox,Pout[1]+oy),(Pin[0]+ox,Pin[1]+oy)]
        s.room(name,sector,floor,ceiling,outline=out,theme=theme,**kw)
        def side(which,centre_steps,half_steps):
            """two points on a side wall ('left' or 'right' of u), measured in steps of u from the centre."""
            sg=1 if which=='left' else -1
            c=(C[0]+sg*ox,C[1]+sg*oy)
            a=(c[0]+u[0]*(centre_steps-half_steps),c[1]+u[1]*(centre_steps-half_steps))
            b=(c[0]+u[0]*(centre_steps+half_steps),c[1]+u[1]*(centre_steps+half_steps))
            return [a,b] if which=='left' else [b,a]   # order for a ccw room lying on that side
        return {'in':Pin,'out':Pout,'side':side,'id':name}
    def write(s,folder):
        doc={'format':0,'themes':sorted(s.themes.values(),key=lambda t:t['id']),
             'defaults':{'theme':sorted(s.themes)[0],'ambient':18},'rooms':s.rooms,'openings':s.openings}
        yaml.safe_dump(doc,open(folder+'/rooms.yml','w'),default_flow_style=None,sort_keys=False,width=100000)
        json.dump({'polys':s.polys,'meta':s.meta},open(BASE+'output/studio_cal/mm6_hive/rebuilt_polys.json','w'))

    # ---- placing things
    def inside(s,poly,x,y):
        c=False;n=len(poly)
        for i in range(n):
            x1,y1=poly[i];x2,y2=poly[(i+1)%n]
            if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1: c=not c
        return c
    def room_at(s,x,y,z):
        best=None
        for rid,poly in s.polys.items():
            m=s.meta[rid]
            if s.inside(poly,x,y):
                d=0 if m['zmin']-40<=z<=m['ceiling'] else min(abs(z-m['zmin']),abs(z-m['ceiling']))
                if best is None or d<best[0]: best=(d,rid)
        if best and best[0]<200: return best[1]
        # nearest room by its corner average, at a fitting height
        cand=[]
        for rid,poly in s.polys.items():
            m=s.meta[rid]
            if m['zmin']-200<=z<=m['ceiling']+100:
                cx=sum(q[0] for q in poly)/len(poly);cy=sum(q[1] for q in poly)/len(poly)
                cand.append((math.hypot(cx-x,cy-y),rid))
        if not cand:
            for rid,poly in s.polys.items():
                cx=sum(q[0] for q in poly)/len(poly);cy=sum(q[1] for q in poly)/len(poly);cand.append((math.hypot(cx-x,cy-y),rid))
        return min(cand)[1]
    def wall_at(s,rid,x,y):
        poly=s.polys['room:'+rid if not rid.startswith('room:') else rid];best=None
        for i in range(len(poly)):
            a=poly[i];b=poly[(i+1)%len(poly)];dx,dy=b[0]-a[0],b[1]-a[1];L2=dx*dx+dy*dy
            t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/L2));d=math.hypot(a[0]+t*dx-x,a[1]+t*dy-y)
            if best is None or d<best[0]: best=(d,i,round(t,3))
        return best[1],best[2]
