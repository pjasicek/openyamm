import bpy,numpy as np,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/production_master.blend'));body=bpy.data.objects['Body'];me=body.data;co=np.array([tuple(v.co)for v in me.vertices]);part=np.array([a.value for a in me.attributes['piece'].data]);W=np.zeros((len(co),len(body.vertex_groups)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
adj=[[]for v in co]
for e in me.edges:
 a,b=e.vertices
 if part[a]==0 and part[b]==0:adj[a].append(b);adj[b].append(a)
ids=np.where((part==0)&(abs(co[:,0])>.09)&(abs(co[:,0])<.30)&(co[:,2]>1.14)&(co[:,2]<1.39))[0]
for it in range(8):
 old=W.copy()
 for i in ids:
  if adj[i]:W[i]=.5*old[i]+.5*old[adj[i]].mean(0)
for i in ids:
 w=W[i];js=np.argsort(w)[-4:];total=w[js].sum();assert total>0
 for g in list(me.vertices[i].groups):body.vertex_groups[g.group].remove([int(i)])
 for j in js:
  if w[j]>1e-7:body.vertex_groups[int(j)].add([int(i)],float(w[j]/total),'REPLACE')
(P/'work/shoulder_smoothing.json').write_text(json.dumps({'vertices':len(ids),'iterations':8,'region':'connected shoulder skin; hands, cloth, bone transforms unchanged'},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/gate_master.blend'))
