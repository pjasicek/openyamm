import sys, glob, os, struct, math, statistics as st, json
from pathlib import Path
from collections import defaultdict
ROOT=Path('/home/pjasicek/github/OpenYAMM'); sys.path.insert(0,str(ROOT/'util')); sys.path.insert(0,str(ROOT/'tools/mm9_import_discovery'))
os.chdir(ROOT)
import yaml
from map_export import parse_blv_file, parse_odm_file
import inventory_mm9_rework as inv
by_number, by_picture = inv.load_engine_monsters(); ms=inv.load_map_stats()
def area_xy(pts):
    a=0
    for i in range(len(pts)):
        x1,y1=pts[i]; x2,y2=pts[(i+1)%len(pts)]; a+=x1*y2-x2*y1
    return abs(a)/2
def raster(polys, cell):
    # polys: list of [(x,y,z),...]; unique (cx,cy,zlayer) cells whose centre lies inside a floor polygon
    cells=defaultdict(list)
    for P in polys:
        xs=[p[0] for p in P]; ys=[p[1] for p in P]; z=sum(p[2] for p in P)/len(P)
        x0=int(min(xs)//cell); x1=int(max(xs)//cell); y0=int(min(ys)//cell); y1=int(max(ys)//cell)
        n=len(P)
        for cx in range(x0,x1+1):
            px=(cx+0.5)*cell
            for cy in range(y0,y1+1):
                py=(cy+0.5)*cell; inside=False; j=n-1
                for i in range(n):
                    xi,yi=P[i][0],P[i][1]; xj,yj=P[j][0],P[j][1]
                    if (yi>py)!=(yj>py) and px < (xj-xi)*(py-yi)/(yj-yi+1e-12)+xi: inside=not inside
                    j=i
                if inside: cells[(cx,cy)].append(z)
    layers=0
    for zs in cells.values():
        zs.sort(); layers+=1
        for a,b in zip(zs,zs[1:]):
            if b-a>320: layers+=1
    return layers*cell*cell
def cluster(points, link=1200):
    # points: list of (x,y,z,weight); single linkage in 3D (z weighted 2x)
    n=len(points); par=list(range(n))
    def f(i):
        while par[i]!=i: par[i]=par[par[i]]; i=par[i]
        return i
    for i in range(n):
        for j in range(i+1,n):
            dx=points[i][0]-points[j][0]; dy=points[i][1]-points[j][1]; dz=(points[i][2]-points[j][2])*2
            if dx*dx+dy*dy+dz*dz<=link*link: par[f(i)]=f(j)
    sizes=defaultdict(float); cen=defaultdict(lambda:[0,0,0,0])
    for i in range(n):
        r=f(i); sizes[r]+=points[i][3]; c=cen[r]; c[0]+=points[i][0]; c[1]+=points[i][1]; c[2]+=points[i][2]; c[3]+=1
    C=[(c[0]/c[3],c[1]/c[3],c[2]/c[3]) for c in cen.values()]
    global LAST_NN
    nn=[]
    for i,a in enumerate(C):
        d=min((math.dist(a,b) for j,b in enumerate(C) if j!=i), default=0); nn.append(d)
    LAST_NN=st.median(nn) if nn else 0
    return list(sizes.values())
def mm68(world, stem, kind):
    scene=yaml.load(open(f'assets_dev/worlds/{world}/maps/{stem}.scene.yml'),Loader=yaml.CSafeLoader)
    fn=stem+('.blv' if kind=='blv' else '.odm')
    name,enc=ms.get(fn.lower(),(fn,[]))
    pts=[]
    for sp in scene.get('spawns') or []:
        if sp.get('type_id')!=3: continue
        idx=int(sp.get('index',0))
        slot = idx if 1<=idx<=3 else ((idx-4)%3+1 if 4<=idx<=12 else 0)
        if not slot or slot>len(enc) or not enc[slot-1].picture or enc[slot-1].picture=='0': continue
        e=enc[slot-1]; c=(e.count_low+e.count_high)/2
        p=sp.get('position') or [sp.get('x',0),sp.get('y',0),sp.get('z',0)]
        if isinstance(p,dict): p=[p['x'],p['y'],p['z']]
        pts.append((p[0],p[1],p[2],c))
    for a in (scene.get('initial_state') or {}).get('actors') or []:
        m=by_number.get(int(a.get('monster_info_id',0)))
        if not m or 'peasant' in m.picture.lower(): continue
        p=a.get('position') or [0,0,0]
        if isinstance(p,dict): p=[p['x'],p['y'],p['z']]
        pts.append((p[0],p[1],p[2],1))
    if kind=='blv':
        q=parse_blv_file(Path(f'assets_dev/worlds/{world}/maps/{fn}'))['payload']
        V=q['vertices']; area=raster([[(V[i]['x'],V[i]['y'],V[i]['z']) for i in f['vertex_indices']] for f in q['faces'] if f['facet_type'] in (3,4) and not f['is_portal']],128)
    else:
        area=88*512*88*512  # playable ODM approx (88 of 128 tiles each way)
    return name, area, pts
def kind_hint(stem):
    return 'indoor' if 'enclosed' in open(f'assets_dev/worlds/mm9/maps/{stem}.scene.yml').read(3000) else 'outdoor'
def mm9(stem):
    scene=yaml.load(open(f'assets_dev/worlds/mm9/maps/{stem}.scene.yml'),Loader=yaml.CSafeLoader)
    pts=[]
    for a in (scene.get('initial_state') or {}).get('actors') or []:
        mid=int(a.get('monster_info_id',0))
        if a.get('mm9_civilian') or a.get('npc_id') or a.get('hostility_type',4)==0: continue
        p=a.get('position')
        if isinstance(p,dict): p=[p['x'],p['y'],p['z']]
        if not p: continue
        pts.append((p[0],p[1],p[2],1))
    odm=parse_odm_file(Path(f'assets_dev/worlds/mm9/maps/{stem}.odm'))['payload']
    nav=Path(f'assets_dev/worlds/mm9/maps/{stem}.nav').read_bytes()
    count=struct.unpack_from('<I',nav,40)[0]
    polys=[]
    for r in range(count):
        sk,bi,fi,mech,kind,flags,ml=struct.unpack_from('<QIIIBBH',nav,48+24*r)
        if kind!=1: continue
        b=odm['bmodels'][bi]; f=b['faces'][fi]; Vs=b['vertices']
        polys.append([(Vs[i]['x'],Vs[i]['y'],Vs[i]['z']) if isinstance(Vs[i],dict) else tuple(Vs[i]) for i in f['vertex_indices']])
    area=raster(polys, 128 if kind_hint(stem)=='indoor' else 512)
    return stem, area, pts
rows=[]
for world in ('mm6','mm7','mm8'):
    for p in sorted(glob.glob(f'assets_dev/worlds/{world}/maps/*.blv')):
        stem=Path(p).stem
        if not os.path.exists(f'assets_dev/worlds/{world}/maps/{stem}.scene.yml'): continue
        try: name,area,pts=mm68(world,stem,'blv')
        except Exception as e: print('skip',world,stem,e,file=sys.stderr); continue
        rows.append((world,'indoor',stem,name,area,pts))
    for p in sorted(glob.glob(f'assets_dev/worlds/{world}/maps/*.odm')):
        stem=Path(p).stem
        if not os.path.exists(f'assets_dev/worlds/{world}/maps/{stem}.scene.yml'): continue
        name,area,pts=mm68(world,stem,'odm'); rows.append((world,'outdoor',stem,name,area,pts))
for p in sorted(glob.glob('assets_dev/worlds/mm9/maps/*.odm')):
    stem=Path(p).stem
    sc=open(f'assets_dev/worlds/mm9/maps/{stem}.scene.yml').read(3000)
    kind='indoor' if 'enclosed' in sc else 'outdoor'
    try: name,area,pts=mm9(stem)
    except Exception as e: print('skip mm9',stem,repr(e)[:200]); continue
    rows.append(('mm9',kind,stem,name,area,pts)) if kind=='outdoor' else None
R='output/mm9_rework/assets_dev/worlds/mm9/maps/'
for p in sorted(glob.glob(R+'*.blv')):
    stem=Path(p).stem
    try:
        scene=yaml.load(open(R+stem+'.scene.yml'),Loader=yaml.CSafeLoader)
        pts=[]
        for a in (scene.get('initial_state') or {}).get('actors') or []:
            if a.get('mm9_civilian') or a.get('npc_id') or a.get('hostility_type',4)==0: continue
            pp=a.get('position')
            if isinstance(pp,dict): pp=[pp['x'],pp['y'],pp['z']]
            if pp: pts.append((pp[0],pp[1],pp[2],1))
        q=parse_blv_file(Path(p))['payload']; V=q['vertices']
        area=raster([[(V[i]['x'],V[i]['y'],V[i]['z']) for i in f['vertex_indices']] for f in q['faces'] if f['facet_type'] in (3,4) and not f['is_portal']],128)
        xs=sorted(v['x'] for v in V); ys=sorted(v['y'] for v in V)
        rows.append(('mm9r','indoor',stem,stem,area,pts))
        print('bbox',stem,round((xs[-1]-xs[0])*(ys[-1]-ys[0])/1e6),'floor',round(area/1e6),'sectors',q['sector_count'],'mon',len(pts))
    except Exception as e: print('skip mm9r',stem,repr(e)[:150])
out=[]
for w,k,stem,name,area,pts in rows:
    n=sum(p[3] for p in pts)
    if n<5: continue
    packs=cluster(pts)
    out.append(dict(world=w,kind=k,map=stem,name=name,area_m=area/1e6,monsters=n,packs=len(packs),pack_size=n/len(packs) if packs else 0,
                    per_1m=n/(area/1e6) if area else 0, nn=LAST_NN, area_per_pack=(area/1e6)/len(packs) if packs else 0))
json.dump(out,open('/home/pjasicek/github/OpenYAMM/output/mm9_balance/density.json','w'),indent=1)
for w in ('mm6','mm7','mm8','mm9','mm9r'):
    for k in ('indoor','outdoor'):
        xs=[o for o in out if o['world']==w and o['kind']==k]
        if not xs: continue
        md=lambda key: st.median(o[key] for o in xs)
        print(f"{w} {k:7s} maps={len(xs):3d}  floor(M u²) med {md('area_m'):7.1f}  monsters med {md('monsters'):5.0f}  per 1M u² med {md('per_1m'):6.2f}  packs med {md('packs'):4.0f}  pack size med {md('pack_size'):4.1f}  area/pack (M u²) med {md('area_per_pack'):5.2f}  pack spacing med {md('nn'):5.0f}")
