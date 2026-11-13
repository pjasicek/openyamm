import json,sys,math,collections
sys.path.insert(0,'/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/91a1fa2b-de0e-45ea-a792-30bbe6bc04d4/scratchpad/py')
from shapely.geometry import Polygon,MultiPolygon
from shapely.ops import unary_union
D='/home/pjasicek/github/OpenYAMM/output/studio_cal/mm6_cd2/'
m=json.load(open(D+'orig.json'))['map']
V=m['vertices'];F=m['faces'];S=m['sectors']
DOORS=json.load(open(D+'doors.json'))
LEAF=set()
for _d in DOORS:
    _mv=set(_d['vertex_ids'])
    for _fi in _d['face_ids']:
        if all(v in _mv for v in F[_fi]['vertices']): LEAF.add(_fi)
for _s in S:
    for _k in ('floor_faces','ceiling_faces','wall_faces'):
        _s[_k]=[fi for fi in _s[_k] if fi not in LEAF]
def fpts(f): return [V[i] for i in f['vertices']]
def nrm(f): return [c/65536 for c in f['plane_normal']]
def area3(p):
    ax=ay=az=0
    for i in range(1,len(p)-1):
        a=[p[i][k]-p[0][k] for k in range(3)];b=[p[i+1][k]-p[0][k] for k in range(3)]
        ax+=a[1]*b[2]-a[2]*b[1];ay+=a[2]*b[0]-a[0]*b[2];az+=a[0]*b[1]-a[1]*b[0]
    return math.sqrt(ax*ax+ay*ay+az*az)/2
def poly2(f):
    p=[(x,y) for x,y,z in fpts(f)]
    try:
        P=Polygon(p)
        if not P.is_valid: P=P.buffer(0)
        return P
    except Exception: return None
def sector_info(si):
    s=S[si]
    info={'id':si,'min':s['min'],'max':s['max']}
    fl=collections.Counter();ce=collections.Counter();tex=collections.Counter();polys=[];slop=0
    for fi in s['floor_faces']:
        f=F[fi];p=fpts(f);a=area3(p);n=nrm(f)
        zs=[q[2] for q in p]
        if max(zs)-min(zs)>2: slop+=a
        fl[round(sum(zs)/len(zs))]+=a;tex['F:'+f['texture']]+=a
        P=poly2(f)
        if P is not None and P.area>0: polys.append(P)
    for fi in s['ceiling_faces']:
        f=F[fi];p=fpts(f);a=area3(p);zs=[q[2] for q in p]
        ce[round(sum(zs)/len(zs))]+=a;tex['C:'+f['texture']]+=a
    for fi in s['wall_faces']:
        f=F[fi];tex['W:'+f['texture']]+=area3(fpts(f))
    info['floors']=fl;info['ceils']=ce;info['tex']=tex;info['sloped']=slop
    info['foot']=unary_union(polys) if polys else None
    por=[]
    for fi in s['portal_faces']:
        f=F[fi];p=fpts(f)
        o=f['room_behind'] if f['room']==si else f['room']
        por.append({'face':fi,'to':o,'min':[min(q[k] for q in p) for k in range(3)],'max':[max(q[k] for q in p) for k in range(3)],'n':nrm(f)})
    info['portals']=por
    return info
