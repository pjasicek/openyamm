"""Smooth abrupt shoulder/collar weight boundaries before overhead library motion."""
import json

def repair_shoulders(body):
 me=body.data;groups=body.vertex_groups
 key='round2_shoulder_original'
 if key not in body:body[key]=json.dumps([{groups[g.group].name:g.weight for g in v.groups} for v in me.vertices])
 weights=json.loads(body[key]);adj=[set() for v in me.vertices]
 for edge in me.edges:
  a,b=edge.vertices;adj[a].add(b);adj[b].add(a)
 masks=[]
 for v in me.vertices:
  x,y,z=v.co
  masks.append(max(0,min(1,(abs(x)-.065)/.065,(.48-abs(x))/.08,(z-1.20)/.09,(1.53-z)/.065)))
 for _ in range(28):
  old=weights;weights=[dict(w) for w in old]
  for i,amount in enumerate(masks):
   if not amount or not adj[i]:continue
   amount*=.65;w={n:value*(1-amount) for n,value in old[i].items()}
   for j in adj[i]:
    for n,value in old[j].items():w[n]=w.get(n,0)+amount*value/len(adj[i])
   w=dict(sorted(w.items(),key=lambda item:item[1],reverse=True)[:8]);total=sum(w.values());weights[i]={n:v/total for n,v in w.items()}
 for i,amount in enumerate(masks):
  if not amount:continue
  for g in list(me.vertices[i].groups):groups[g.group].remove([i])
  for n,w in weights[i].items():groups[n].add([i],w,'REPLACE')
 assert all(abs(sum(g.weight for g in v.groups)-1)<1e-5 for v,amount in zip(me.vertices,masks) if amount)
