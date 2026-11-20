import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/before_feedback_v1/textured_uv.blend'))
ob=bpy.data.objects['Body'];me=ob.data;rig=bpy.data.objects['Rig'];pc=np.array([x.value for x in me.attributes['piece'].data]);co=np.array([v.co[:] for v in me.vertices]);report={}
for part in [0,1,2,4,5]:
 ids=set(np.where(pc==part)[0]);adj={i:set() for i in ids}
 for e in me.edges:
  a,b=e.vertices
  if a in ids and b in ids:adj[a].add(b);adj[b].add(a)
 comps=[]
 while ids:
  seen=set();todo=[next(iter(ids))]
  while todo:
   i=todo.pop()
   if i in seen:continue
   seen.add(i);todo.extend(adj[i]-seen)
  ids-=seen;pts=co[sorted(seen)];comps.append({'ids':list(map(int,sorted(seen))),'vertices':len(seen),'min':pts.min(0).tolist(),'max':pts.max(0).tolist()})
 report[str(part)]=comps
print('COMPONENTS',json.dumps({k:[{n:v for n,v in c.items() if n!='ids'} for c in cs] for k,cs in report.items()}),flush=True)
for side in ['L','R']:
 sh=np.array(rig.data.bones[f'B_{side}_UpperArm'].head_local);el=np.array(rig.data.bones[f'B_{side}_Forearm'].head_local);ax=(el-sh)/np.linalg.norm(el-sh);dist=(co-sh)@ax
 print('ARM',side,'shoulder',sh.tolist(),'elbow',el.tolist(),'length',np.linalg.norm(el-sh))
 for lo in np.arange(.08,.31,.025):
  print('RING',lo,[(p,int(m.sum()),float(np.percentile(np.linalg.norm(co[m]-sh-np.outer(dist[m],ax),axis=1),95)) if m.any() else None) for p in [0,4 if side=='L' else 5] for m in [(pc==p)&(co[:,0]*sh[0]>0)&(dist>lo)&(dist<lo+.025)]])
(P/'work/feedback_components.json').write_text(json.dumps(report,indent=2))
# Export all hair vertex/face data for finding the lower sheet and its shared boundary.
head={'co':co.tolist(),'pieces':pc.tolist(),'faces':[list(f.vertices) for f in me.polygons]}
(P/'work/feedback_mesh.json').write_text(json.dumps(head))
