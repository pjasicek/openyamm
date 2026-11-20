import json,sys,collections
d=json.load(open('output/studio_cal/mm6_6d18/orig.json'))['map']
V=d['vertices'];F=d['faces']
def parea(p):
    return sum(p[i][0]*p[(i+1)%len(p)][1]-p[(i+1)%len(p)][0]*p[i][1] for i in range(len(p)))/2
def boundary(polys):
    # polys: lists of (x,y); returns loops
    E=collections.Counter()
    for p in polys:
        if parea(p)<0: p=p[::-1]
        for i in range(len(p)):
            a,b=p[i],p[(i+1)%len(p)]
            if a==b: continue
            if E[(b,a)]>0: E[(b,a)]-=1
            else: E[(a,b)]+=1
    nxt=collections.defaultdict(list)
    for (a,b),c in E.items():
        for _ in range(c): nxt[a].append(b)
    loops=[]
    while any(nxt.values()):
        s=next(k for k,v in nxt.items() if v); loop=[s]; cur=s
        while True:
            if not nxt[cur]: break
            b=nxt[cur].pop(); 
            if b==s: break
            loop.append(b); cur=b
        # drop collinear
        out=[]
        n=len(loop)
        for i in range(n):
            a,b,c=loop[i-1],loop[i],loop[(i+1)%n]
            if (b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0])!=0: out.append(b)
        loops.append(out)
    return loops
def floors(si,minarea=3000):
    s=d['sectors'][si]
    by=collections.defaultdict(list)
    for fi in s['floor_faces']:
        f=F[fi]; zs=[V[i][2] for i in f['vertices']]
        p=[(V[i][0],V[i][1]) for i in f['vertices']]
        by[(min(zs),max(zs),f['texture'],f['cog_triggered'])].append(p)
    return by
if __name__=='__main__':
  want=[int(a) for a in sys.argv[1:]] or range(1,48)
  for si in want:
    s=d['sectors'][si]
    print('=== sector',si,s['min'],s['max'])
    by=floors(si)
    for k in sorted(by):
        A=sum(abs(parea(p)) for p in by[k])
        if A<3000:
            xs=[q[0] for p in by[k] for q in p];ys=[q[1] for p in by[k] for q in p]
            print('  floor',k,'small',int(A),min(xs),min(ys),max(xs),max(ys)); continue
        print('  floor',k,'area',int(A))
        for l in boundary(by[k]): print('     loop',int(parea(l)),l)
    cy=collections.defaultdict(list)
    for fi in s['ceiling_faces']:
        f=F[fi]; zs=[V[i][2] for i in f['vertices']]
        p=[(V[i][0],V[i][1]) for i in f['vertices']]
        cy[(min(zs),max(zs),f['texture'])].append(p)
    for k in sorted(cy):
        A=sum(abs(parea(p)) for p in cy[k])
        if A<3000: continue
        xs=[q[0] for p in cy[k] for q in p];ys=[q[1] for p in cy[k] for q in p]
        print('  ceil',k,'area',int(A),min(xs),min(ys),max(xs),max(ys))
    for fi in s['portal_faces']:
        f=F[fi]; p=[V[i] for i in f['vertices']]
        lo=[min(q[k] for q in p) for k in range(3)];hi=[max(q[k] for q in p) for k in range(3)]
        print('  portal',fi,'rooms',f['room'],f['room_behind'],lo,hi)
