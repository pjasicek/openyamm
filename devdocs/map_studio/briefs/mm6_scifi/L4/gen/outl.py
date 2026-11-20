import json,sys,collections,math
sys.path.insert(0,'output/studio_cal/mm6_scifi')
from secs import d,V,F,S,area,bb
def loops_of(faces):
    cnt=collections.Counter()
    for fi in faces:
        vs=[tuple(V[i][:2]) for i in F[fi]['vertices']]
        # ensure ccw
        a=sum(vs[i][0]*vs[(i+1)%len(vs)][1]-vs[(i+1)%len(vs)][0]*vs[i][1] for i in range(len(vs)))
        if a<0: vs=vs[::-1]
        for i in range(len(vs)):
            p,q=vs[i],vs[(i+1)%len(vs)]
            if p==q: continue
            cnt[(p,q)]+=1
    nxt=collections.defaultdict(list)
    for (p,q),c in cnt.items():
        if cnt.get((q,p),0)==0: nxt[p].append(q)
    loops=[]
    while nxt:
        s=next(iter(nxt)); lp=[s]; cur=s
        while True:
            if cur not in nxt: break
            n=nxt[cur].pop()
            if not nxt[cur]: del nxt[cur]
            if n==s: break
            lp.append(n); cur=n
        loops.append(lp)
    return loops
def simp(lp,tol=20):
    # drop near-collinear points
    ch=True
    lp=list(lp)
    while ch and len(lp)>3:
        ch=False
        for i in range(len(lp)):
            a,b,c=lp[i-1],lp[i],lp[(i+1)%len(lp)]
            L=math.hypot(c[0]-a[0],c[1]-a[1])
            if L==0: dist=math.hypot(b[0]-a[0],b[1]-a[1])
            else: dist=abs((c[0]-a[0])*(b[1]-a[1])-(c[1]-a[1])*(b[0]-a[0]))/L
            if dist<tol:
                del lp[i]; ch=True; break
    return lp
def parea(lp): return sum(lp[i][0]*lp[(i+1)%len(lp)][1]-lp[(i+1)%len(lp)][0]*lp[i][1] for i in range(len(lp)))/2
if __name__=='__main__':
    tol=20
    sel=[int(x) for x in sys.argv[1:]] or range(len(S))
    for si in sel:
        s=S[si]
        if not s['floor_faces']: continue
        ls=loops_of(s['floor_faces'])
        ls=[simp(l,tol) for l in ls]
        ls.sort(key=lambda l:-abs(parea(l)))
        print(f"S{si}:")
        for l in ls:
            if abs(parea(l))<2000: continue
            print(f"   n{len(l)} area{int(parea(l))}: {[list(p) for p in l]}")
