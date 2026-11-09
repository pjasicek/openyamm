from pathlib import Path
import json, heapq
import numpy as np
P=Path(__file__).resolve().parents[1]
m=np.load(P/'work/geometry.npz'); co=m['co']; edges=m['edges']; pa=m['parts']
J=json.loads((P/'work/joints_final.json').read_text())['joints']
adj=[[] for _ in co]
for a,b in edges: adj[a].append(int(b));adj[b].append(int(a))
def components(mask):
    unseen=set(np.where(mask)[0]); cs=[]
    while unseen:
        seed=unseen.pop(); q=[seed]; c=[]
        while q:
            v=q.pop();c.append(v)
            for w in adj[v]:
                if w in unseen:unseen.remove(w);q.append(w)
        cs.append(np.array(c))
    return cs
def dist(mask,seeds):
    d=np.full(len(co),1e9); d[seeds]=0;q=[(0,int(i)) for i in seeds];heapq.heapify(q)
    while q:
        dv,v=heapq.heappop(q)
        if dv>d[v]:continue
        for w in adj[v]:
            if not mask[w]:continue
            nd=dv+np.linalg.norm(co[w]-co[v])
            if nd<d[w]:d[w]=nd;heapq.heappush(q,(nd,w))
    return d
out={}
for side in ['L1','L2','L3','R1','R2','R3']:
    wr=np.array(J[side+'_Hand']);el=np.array(J[side+'_Forearm']);axis=wr-el;axis/=np.linalg.norm(axis)
    dep=(co-wr)@axis;mask=np.isin(pa,[0,100,101,102])&(dep>-.035)&(np.linalg.norm(co-wr,axis=1)<.36)
    mask &= (pa==99+int(side[1])) if side.startswith('R') else (pa==0)
    cs=components(mask);main=min(cs,key=lambda c:np.min(np.linalg.norm(co[c]-wr,axis=1)))
    mask[:]=False;mask[main]=True;d=dist(mask,main[np.argsort(dep[main])[:10]])
    levels=[]
    for t in np.arange(.015,.4,.003):
        cs=[c for c in components(mask&(d>t)) if len(c)>=8]
        if cs:levels.append(cs)
    owners=[{int(v):i for i,c in enumerate(cs) for v in c} for cs in levels]
    kids=[[[j for j,c in enumerate(levels[k+1]) if owners[k].get(int(c[0]))==i] for i in range(len(levels[k]))] for k in range(len(levels)-1)]+[[[]for _ in levels[-1]]]
    memo={}
    def chain(k,i):
        if (k,i) not in memo:
            ch=kids[k][i];memo[k,i]=len(ch)<=1 and (not ch or chain(k+1,ch[0]))
        return memo[k,i]
    leaves=[]
    for k,cs in enumerate(levels):
        for i,c in enumerate(cs):
            parent=next((j for j,ch in enumerate(kids[k-1]) if i in ch),None) if k else None
            if chain(k,i) and len(c)>=15 and (k==0 or parent is None or not chain(k-1,parent)):leaves.append(c)
    print(side,'fingers',len(leaves),[(len(c),co[c].mean(0).round(3).tolist())for c in leaves],flush=True)
    assert len(leaves)==5
    # Thumb separates closest to the wrist. Remaining digits sort across the knuckle row.
    leaves.sort(key=lambda c:float(d[c].min()));thumb=leaves[0]
    tc=co[thumb].mean(0);leaves=[thumb]+sorted(leaves[1:],key=lambda c:np.linalg.norm(co[c].mean(0)-tc))
    item={'verts':{},'hand_verts':main.tolist()}
    for name,c in zip(['thumb','index','middle','ring','pinky'],leaves):
        v=co[c];base=v[np.argsort(d[c])[:5]].mean(0);tip=v[np.argsort(d[c])[-5:]].mean(0)
        direct=tip-base;length=np.linalg.norm(direct);direct/=length
        base-=direct*min(.035,length*.35)
        if name=='thumb':base=wr+(base-wr)*.65
        pts=[base,base+(tip-base)*.53,tip]
        item[name]=np.array(pts).tolist();item['verts'][name]=c.tolist()
    out[side]=item
(P/'work/fingers_fit.json').write_text(json.dumps(out,indent=2))
mask=(pa==0)&(co[:,2]<1.16)
seeds=np.where(mask&(co[:,2]>1.12)&(abs(co[:,0])<.3))[0];d=dist(mask,seeds);ids=np.where(d<1e8)[0];tip=ids[np.argmax(d[ids])];dt=dist(mask,[tip]);s=(d-dt)/2;s-=s[ids].min();line=[]
for t in np.linspace(0,s[ids].max(),25):
    q=co[(d<1e8)&(abs(s-t)<.07)];line.append(q.mean(0) if len(q) else line[-1])
line=np.array(line);line[0]=[-.024,.06,1.16]
for _ in range(3):line[1:-1]=.25*line[:-2]+.5*line[1:-1]+.25*line[2:]
arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(line,axis=0),axis=1))];ss=np.linspace(0,arc[-1],21)
line=np.column_stack([np.interp(ss,arc,line[:,k])for k in range(3)])
(P/'work/tail_rest.json').write_text(json.dumps({'joints':line.tolist(),'root_index':int(np.argmin(line[:,2])),'vertices':ids.tolist()},indent=2))
