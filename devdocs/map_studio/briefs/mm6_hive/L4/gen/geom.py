import json,math,collections
from PIL import Image,ImageDraw
D=json.load(open('/home/pjasicek/github/OpenYAMM/output/studio_cal/mm6_hive/orig.json'))['map']
V=D['vertices'];F=D['faces'];S=D['sectors']
def fpts(i): return [V[v] for v in F[i]['vertices']]
def nrm(i): return [x/65536 for x in F[i]['plane_normal']]
def dp(pts,tol):
    if len(pts)<3: return pts
    a,b=pts[0],pts[-1];dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy) or 1
    md,mi=0,0
    for i in range(1,len(pts)-1):
        d=abs((pts[i][0]-a[0])*dy-(pts[i][1]-a[1])*dx)/L
        if d>md: md,mi=d,i
    if md<=tol: return [a,b]
    return dp(pts[:mi+1],tol)[:-1]+dp(pts[mi:],tol)
def raster_outline(polys,cell=16,tol=40):
    xs=[p[0] for q in polys for p in q];ys=[p[1] for q in polys for p in q]
    x0,y0=min(xs)-cell*2,min(ys)-cell*2
    w=int((max(xs)-x0)/cell)+4;h=int((max(ys)-y0)/cell)+4
    im=Image.new('1',(w,h),0);dr=ImageDraw.Draw(im)
    for q in polys:
        if len(q)>=3: dr.polygon([((p[0]-x0)/cell,(p[1]-y0)/cell) for p in q],fill=1,outline=1)
    px=im.load()
    # boundary edges of filled cells, directed with fill on the left (ccw in x right,y up)
    nxt=collections.defaultdict(list)
    for y in range(h):
        for x in range(w):
            if not px[x,y]: continue
            if y==0 or not px[x,y-1]: nxt[(x,y)].append((x+1,y))
            if x==w-1 or not px[x+1,y]: nxt[(x+1,y)].append((x+1,y+1))
            if y==h-1 or not px[x,y+1]: nxt[(x+1,y+1)].append((x,y+1))
            if x==0 or not px[x-1,y]: nxt[(x,y+1)].append((x,y))
    loops=[]
    while nxt:
        s=next(iter(nxt));loop=[s];c=s
        while True:
            l=nxt[c];n=l.pop()
            if not l: del nxt[c]
            if n==s: break
            loop.append(n);c=n
        loops.append(loop)
    loops.sort(key=len,reverse=True)
    out=[]
    for loop in loops:
        if len(loop)<8: continue
        pts=[(x0+x*cell,y0+y*cell) for x,y in loop]
        # dp on closed loop: split at farthest pair
        i0=0;i1=max(range(len(pts)),key=lambda i:(pts[i][0]-pts[0][0])**2+(pts[i][1]-pts[0][1])**2)
        a=dp(pts[i0:i1+1],tol);b=dp(pts[i1:]+[pts[0]],tol)
        out.append(a[:-1]+b[:-1])
    return out
def sector_polys(si,kinds=('floor_faces','ceiling_faces')):
    r=[]
    for k in kinds:
        for i in S[si][k]: r.append(fpts(i))
    return r
def area2(p):
    return sum(p[i][0]*p[(i+1)%len(p)][1]-p[(i+1)%len(p)][0]*p[i][1] for i in range(len(p)))/2
