import sys,collections
sys.path.insert(0,'/home/pjasicek/github/OpenYAMM/output/studio_cal/mm8_d05')
from an import *
def loops(faces):
    E=collections.Counter()
    for fi in faces:
        vs=[tuple(V[v][:2]) for v in F[fi]['vertices']]
        # orientation normalize ccw
        a=sum(vs[i][0]*vs[(i+1)%len(vs)][1]-vs[(i+1)%len(vs)][0]*vs[i][1] for i in range(len(vs)))
        if a<0: vs=vs[::-1]
        for i in range(len(vs)):
            p,q=vs[i],vs[(i+1)%len(vs)]
            if p==q: continue
            if E[(q,p)]>0: E[(q,p)]-=1
            else: E[(p,q)]+=1
    nxt=collections.defaultdict(list)
    for (p,q),c in E.items():
        for _ in range(c): nxt[p].append(q)
    out=[]
    while any(nxt.values()):
        s=next(p for p,v in nxt.items() if v)
        loop=[s];cur=s
        while True:
            if not nxt[cur]: break
            n=nxt[cur].pop()
            if n==s: break
            loop.append(n);cur=n
        # simplify collinear
        ch=True
        while ch and len(loop)>3:
            ch=False
            for i in range(len(loop)):
                a,b,c=loop[i-1],loop[i],loop[(i+1)%len(loop)]
                if (b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0])==0:
                    del loop[i];ch=True;break
        out.append(loop)
    return out
def larea(l): return sum(l[i][0]*l[(i+1)%len(l)][1]-l[(i+1)%len(l)][0]*l[i][1] for i in range(len(l)))/2
if __name__=='__main__':
    which=[int(a) for a in sys.argv[1:]] or range(1,33)
    for i in which:
        s=SE[i]
        print(f'== S{i}')
        byz=collections.defaultdict(list)
        for fi in s['floor_faces']:
            zs=[V[v][2] for v in F[fi]['vertices']]
            if zs: byz[(min(zs),max(zs))].append(fi)
        print(' ALL floor:')
        for l in loops([f for f in s['floor_faces'] if F[f]['vertices']]):
            print('   ',round(larea(l)),len(l),[list(p) for p in l] if len(l)<=40 else str([list(p) for p in l[:40]])+'...')
        for z,fs in sorted(byz.items()):
            ls=loops(fs)
            print(f'  z{z}:',' | '.join(f"{round(larea(l))}:{[list(p) for p in l]}" if len(l)<=12 else f"{round(larea(l))}:n{len(l)}" for l in ls)[:1500])
