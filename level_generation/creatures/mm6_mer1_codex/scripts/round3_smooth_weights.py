import bpy,sys,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3/before_shoulder_field.blend'));C.reset();o=bpy.data.objects['Body'];pv=np.array([v.value for v in o.data.attributes['piece'].data]);co=np.array([v.co[:]for v in o.data.vertices]);W=np.zeros((len(co),len(o.vertex_groups)));adj=[[]for _ in co]
for v in o.data.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
for e in o.data.edges:
 a,b=e.vertices
 if pv[a]==pv[b]==1:adj[a].append(b);adj[b].append(a)
ids=[i for i,nb in enumerate(adj)if nb and co[i,2]>1.07 and not(co[i,2]>1.37 and abs(co[i,0])<.18)]
weights={i:1/np.maximum(np.linalg.norm(co[adj[i]]-co[i],axis=1),.004)**2 for i in ids}
for _ in range(60):
 old=W.copy()
 for i in ids:
  w=weights[i];W[i]=.45*old[i]+.55*(old[adj[i]]*w[:,None]).sum(0)/w.sum()
for i in ids:
 v=o.data.vertices[i]
 for g in list(v.groups):o.vertex_groups[g.group].remove([i])
 keep=np.argsort(W[i])[-4:];total=W[i,keep].sum()
 for j in keep:
  if W[i,j]>1e-8:o.vertex_groups[int(j)].add([i],float(W[i,j]/total),'REPLACE')
# Relax compressed rest-pose armpit creases before the clothing-only rebake.
for _ in range(3):
 old=co.copy()
 for i in ids:
  if .16<abs(co[i,0])<.30 and 1.10<co[i,2]<1.28:co[i]=old[i]*.8+old[adj[i]].mean(0)*.2
for i in ids:o.data.vertices[i].co=co[i]
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round3/master.blend'))
