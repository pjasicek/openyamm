"""Fit five digit chains from connected mesh slices, following the Claude humanoid finger split-tree method."""
from pathlib import Path
import json
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
P=Path(__file__).resolve().parents[1]
a=np.load(P/'work/geometry_v1.npz');v=a['vertices'];f=a['faces']
e=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]])
adj=[set() for _ in v]
for x,y in e: adj[x].add(int(y));adj[y].add(int(x))

def components(mask):
    todo=set(np.flatnonzero(mask));out=[]
    while todo:
        seed=todo.pop();stack=[seed];ids=[seed]
        while stack:
            ns=adj[stack.pop()] & todo;todo.difference_update(ns);stack.extend(ns);ids.extend(ns)
        if len(ids)>=7: out.append(np.array(ids))
    return out

out={}
for side,sign in [('L',1),('R',-1)]:
    wrist=np.array([sign*.958,-1.182,1.61 if sign==1 else 1.625])
    elbow=np.array([sign*.62,-1.05,1.79 if sign==1 else 1.81])
    direction=wrist-elbow;direction/=np.linalg.norm(direction)
    depth=(v-wrist)@direction
    hand=(np.linalg.norm(v-wrist,axis=1)<.29)&(v[:,0]*sign>.92)
    levels=[]
    for cut in np.arange(-.02,.26,.002):
        parts=components(hand&(depth>cut))
        if not parts: break
        levels.append(parts)
    owner=[{int(x):i for i,c in enumerate(cs) for x in c}for cs in levels]
    kids=[[[j for j,c in enumerate(levels[k+1])if owner[k].get(int(c[0]))==i]for i in range(len(levels[k]))]for k in range(len(levels)-1)]+[[[]for _ in levels[-1]]]
    memo={}
    def chain(k,i):
        if (k,i) not in memo:
            ch=kids[k][i];memo[k,i]=len(ch)<=1 and (not ch or chain(k+1,ch[0]))
        return memo[k,i]
    terminal=[]
    for k,cs in enumerate(levels):
        for i,c in enumerate(cs):
            parent=next((j for j,ch in enumerate(kids[k-1])if i in ch),None)if k else None
            if chain(k,i)and len(c)>=14 and(k==0 or parent is None or not chain(k-1,parent)):
                terminal.append(c)
    print(side,'digit components',list(map(len,terminal)))
    assert len(terminal)==5, f'{side}: expected five separate digits, got {len(terminal)}'
    # The thumb separates nearest the wrist; remaining knuckles are ordered by distance from it.
    terminal.sort(key=lambda c:float(depth[c].min()))
    thumb=terminal[0];tc=v[thumb].mean(0)
    terminal=[thumb]+sorted(terminal[1:],key=lambda c:np.linalg.norm(v[c].mean(0)-tc))
    result={'wrist':wrist.tolist(),'elbow':elbow.tolist(),'digits':{}}
    for name,ids in zip(('Thumb','Index','Middle','Ring','Pinky'),terminal):
        pts=v[ids];d=depth[ids];base=pts[d<d.min()+.008].mean(0)
        axis=pts.mean(0)-base;axis/=np.linalg.norm(axis);projection=(pts-base)@axis
        tip=pts[projection>projection.max()-.006].mean(0)
        length=np.linalg.norm(tip-base);base-=(tip-base)/length*min(.024,length*.25)
        result['digits'][name]={'points':[list(base+(tip-base)*t)for t in (0,.45,.75,1)],'vertices':ids.tolist()}
    out[side]=result
(P/'work/hand_fit.json').write_text(json.dumps(out,indent=2)+'\n')
