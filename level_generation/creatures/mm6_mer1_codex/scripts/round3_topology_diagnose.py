import bpy,sys,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3/master.blend'));C.reset();o=bpy.data.objects['Body'];me=o.data;co=np.array([v.co[:]for v in me.vertices]);p=np.array([v.value for v in me.attributes['piece'].data]);adj=[[]for v in co]
for e in me.edges:
 a,b=e.vertices;adj[a].append(b);adj[b].append(a)
seen=set();components=[]
for i in range(len(co)):
 if i in seen:continue
 group=[i];seen.add(i)
 for j in group:
  for k in adj[j]:
   if k not in seen:seen.add(k);group.append(k)
 components.append(group)
print('COMPONENTS',[(len(g),np.unique(p[g]).tolist(),co[g].min(0).tolist(),co[g].max(0).tolist())for g in components],flush=True)
for point in [(-.253,.0577,1.1348),(.232,-.011,1.101)]:
 i=int(np.linalg.norm(co-point,axis=1).argmin());v=me.vertices[i];print('POINT',i,'piece',p[i],'component',next(j for j,g in enumerate(components)if i in g),'normal',v.normal[:],flush=True)
