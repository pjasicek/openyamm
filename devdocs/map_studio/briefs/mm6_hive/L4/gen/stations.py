import sys;sys.path.insert(0,'/home/pjasicek/github/OpenYAMM/output/studio_cal/mm6_hive/tools')
from geom import *
def stations(si):
    # walkable floor faces
    fl=[i for i in S[si]['floor_faces'] if nrm(i)[2]>0.9]
    cnt=collections.Counter()
    for i in fl:
        vs=F[i]['vertices']
        for a in range(len(vs)):
            e=tuple(sorted((vs[a],vs[(a+1)%len(vs)])));cnt[e]+=1
    be=[e for e,c in cnt.items() if c==1]
    adj=collections.defaultdict(list)
    for a,b in be: adj[a].append(b);adj[b].append(a)
    return fl,be,adj
def portals(si):
    r=[]
    for i in S[si]['portal_faces']:
        p=fpts(i);o=F[i]['room_behind'] if F[i]['room']==si else F[i]['room']
        c=[sum(q[k] for q in p)/len(p) for k in range(3)]
        r.append((o,c,[round(x,2) for x in nrm(i)],min(q[2] for q in p)))
    return r
if __name__=='__main__':
    for a in sys.argv[1:]:
        si=int(a);fl,be,adj=stations(si)
        deg=collections.Counter(len(v) for v in adj.values())
        # floor vertices sorted along principal chain: just list distinct floor verts with z
        vs=sorted(set(v for i in fl for v in F[i]['vertices']))
        print(f"S{si}: {len(fl)} walk faces, {len(vs)} verts, boundary deg {dict(deg)}")
        for o,c,n,z in portals(si): print("   portal->",o,[round(x) for x in c],n,'floor',z)
