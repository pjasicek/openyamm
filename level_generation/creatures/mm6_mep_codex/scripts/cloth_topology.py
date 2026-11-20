import bpy,numpy as np,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/texture_master.blend'));b=bpy.data.objects['Body'];me=b.data;rest=np.array([v.co[:] for v in me.vertices]);pv=np.array([v.value for v in me.attributes['piece'].data]);hd=np.array([v.value for v in me.attributes['head'].data]);sets={}
for sd,sg in [('L',1),('R',-1)]:sets[sd]=[list(f.vertices) for f in me.polygons if all(pv[i]==0 and rest[i,0]*sg>.21 and rest[i,2]>1.08 for i in f.vertices)]
sets['coat']=[list(f.vertices) for f in me.polygons if all(pv[i]==0 and abs(rest[i,0])<.235 and rest[i,2]<1.31 for i in f.vertices)]
report={}
for kind,faces in sets.items():
 edges={}
 for f in faces:
  for a,z in zip(f,f[1:]+f[:1]):edges.setdefault(tuple(sorted((a,z))),[]).append((a,z))
 boundary=[v[0] for v in edges.values() if len(v)==1];loops=[]
 while boundary:
  a,z=boundary.pop();loop=[a,z]
  while loop[-1]!=loop[0]:
   ids=[i for i,e in enumerate(boundary) if e[0]==loop[-1]]
   assert ids,(kind,loop[-1]);loop.append(boundary.pop(ids[0])[1])
  loops.append(loop[:-1])
 report[kind]={'faces':faces,'loops':loops};print(kind,len(faces),[(len(l),rest[l].mean(0).tolist(),rest[l].min(0).tolist(),rest[l].max(0).tolist())for l in loops],flush=True)
(p/'work/cloth_topology.json').write_text(json.dumps(report))
