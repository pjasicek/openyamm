import numpy as np
def garment(me,co,piece):
 eligible=set(np.where((piece==0)&(co[:,2]<1.015))[0].tolist());adj={i:[]for i in eligible}
 for e in me.edges:
  a,b=e.vertices
  if a in eligible and b in eligible:adj[a].append(b);adj[b].append(a)
 components=[]
 while eligible:
  seed=eligible.pop();group=[seed]
  for i in group:
   for j in adj[i]:
    if j in eligible:eligible.remove(j);group.append(j)
  components.append(group)
 print("CLOTH COMPONENTS",[(len(g),co[g].mean(0).tolist())for g in components],flush=True)
 core=max((g for g in components if abs(co[g,0].mean())<.03),key=len);assert abs(co[core,0].mean())<.03 and len(core)>200
 mask=np.zeros(len(co),bool);mask[core]=True;mask|=piece==2
 for i in set(piece.tolist()):
  c=co[piece==i].mean(0)
  if i not in range(16) and c[2]<1.035 and abs(c[0])<.25:mask|=piece==i
 return mask
