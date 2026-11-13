import sys;sys.path.insert(0,'/home/pjasicek/github/OpenYAMM/output/studio_cal/mm6_hive/tools')
from geom import *
from stations import portals
def dp3(pts,tol,ztol):
    if len(pts)<3: return pts
    a,b=pts[0],pts[-1];dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy) or 1
    md,mi=0,0
    for i in range(1,len(pts)-1):
        t=((pts[i][0]-a[0])*dx+(pts[i][1]-a[1])*dy)/L/L
        d=abs((pts[i][0]-a[0])*dy-(pts[i][1]-a[1])*dx)/L/tol
        dz=abs(pts[i][2]-(a[2]+t*(b[2]-a[2])))/ztol
        d=max(d,dz)
        if d>md: md,mi=d,i
    if md<=1: return [a,b]
    return dp3(pts[:mi+1],tol,ztol)[:-1]+dp3(pts[mi:],tol,ztol)
def centre(si,frm,to,tol=70,ztol=30):
    P={o:(c,z) for o,c,n,z in portals(si)}
    fl=[i for i in S[si]['floor_faces'] if nrm(i)[2]>0.9]
    cs=[]
    for i in fl:
        p=fpts(i);cs.append([sum(q[k] for q in p)/len(p) for k in range(3)])
    a=[P[frm][0][0],P[frm][0][1],P[frm][1]];b=[P[to][0][0],P[to][0][1],P[to][1]]
    chain=[a];cur=a;rest=cs[:]
    while rest:
        j=min(range(len(rest)),key=lambda k:(rest[k][0]-cur[0])**2+(rest[k][1]-cur[1])**2)
        # stop if the end portal is nearer than any remaining and we passed most
        cur=rest.pop(j);chain.append(cur)
    chain.append(b)
    # drop points that go backwards (side-branch stubs): keep those reducing no constraint; simple
    return dp3(chain,tol,ztol)
if __name__=='__main__':
    si=int(sys.argv[1]);frm=int(sys.argv[2]);to=int(sys.argv[3])
    c=centre(si,frm,to)
    print(f"S{si} {frm}->{to}:",[[round(x) for x in p] for p in c])
