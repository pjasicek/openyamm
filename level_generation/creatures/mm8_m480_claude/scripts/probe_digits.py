from pathlib import Path
import bpy,numpy as np,json
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/body_v1_parts.blend'));o=bpy.data.objects['P00'];co=np.array([tuple(v.co) for v in o.data.vertices]);edges=np.array([tuple(e.vertices) for e in o.data.edges]);np.savez(P/'work/body_topology.npz',co=co,edges=edges)
for s in [-1,1]:
 for z in [.68,.64,.60,.57,.54,.51,.48,.45]:
  ids=set(np.where((co[:,0]*s>.39)&(co[:,2]<z))[0]);adj={i:[] for i in ids}
  for a,b in edges:
   if a in ids and b in ids:adj[a].append(b);adj[b].append(a)
  seen=set();cs=[]
  for v in ids:
   if v in seen:continue
   stack=[v];comp=[]
   while stack:
    i=stack.pop()
    if i in seen:continue
    seen.add(i);comp.append(i);stack.extend(adj[i])
   if len(comp)>=4:cs.append((len(comp),np.round(co[comp].mean(0),3).tolist()))
  print('CUT',s,z,cs)
