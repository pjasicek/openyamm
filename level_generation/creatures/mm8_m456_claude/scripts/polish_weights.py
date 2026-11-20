"""Smooth only flexible sleeves and the thumb web; rigid plates retain exact segment weights."""
import bpy,numpy as np,json,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilot_gated.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
co=np.array([v.co[:] for v in me.vertices]);pc=np.array([v.value for v in me.attributes['piece'].data]);E=np.array([e.vertices[:] for e in me.edges]);W=np.zeros((len(co),len(body.vertex_groups)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
nb=[[] for _ in co]
for a,b in E:nb[a].append(b);nb[b].append(a)
# Thumb web transitions span multiple triangles rather than one hard phalanx boundary.
for piece,steps in [(6,10),(7,10),(4,5)]:
 ids=np.where(pc==piece)[0]
 for _ in range(steps):
  Q=W.copy()
  for i in ids:
   adj=[j for j in nb[i] if pc[j]==piece]
   if adj:Q[i]=.5*W[i]+.5*W[adj].mean(0)
  W=Q
# Keep only the four actual skin influences the exported mesh uses.
for v in me.vertices:
 for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
 weights=W[v.index];keep=np.argsort(weights)[-4:];total=weights[keep].sum();assert total>.5
 for j in keep:
  if weights[j]>1e-6:body.vertex_groups[int(j)].add([v.index],float(weights[j]/total),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/master_pilot.blend'))
# Inspect exact stretched edges so small slivers cannot hide a visible joint defect.
restlen=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1);report={}
for name,frame in [('Attack',4),('Attack',16),('Running',16)]:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(frame);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();P=np.array([v.co[:] for v in em.vertices]);ev.to_mesh_clear();ratio=np.linalg.norm(P[E[:,0]]-P[E[:,1]],axis=1)/np.maximum(restlen,1e-6)
 order=np.argsort(ratio)[-15:][::-1];report[name+str(frame)]=[{'edge':E[i].tolist(),'pieces':pc[E[i]].tolist(),'rest_mm':float(restlen[i]*1000),'ratio':float(ratio[i]),'coords':co[E[i]].tolist()} for i in order]
 common.workbench_clay(bpy.context.scene);common.render_views(str(p/f'review/polished_{name}_{frame}'),1.2,.70,views=('front','three_quarter','left'),resolution=(700,700))
(p/'review/weight_edges.json').write_text(json.dumps(report,indent=2));print('WEIGHT_WORST',[(k,v[0]) for k,v in report.items()])
