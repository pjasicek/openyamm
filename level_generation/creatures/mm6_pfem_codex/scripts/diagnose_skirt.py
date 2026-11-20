import bpy,sys,json,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/skirt_animated.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;sc=bpy.context.scene
pv=np.array([a.value for a in me.attributes['piece'].data]);co=np.array([v.co[:] for v in me.vertices])
print('MODIFIERS',[(m.name,m.type,getattr(m,'use_deform_preserve_volume',None),str(getattr(m,'object',None))) for m in o.modifiers])
for part in (5,6,8,10,14,15):print('PART',part,co[pv==part].min(0).tolist(),co[pv==part].max(0).tolist())
a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
pos=[]
for f in np.arange(0,60.01,.5):
 sc.frame_set(int(f),subframe=float(f%1));ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();P=np.array([v.co[:] for v in mm.vertices]);ev.to_mesh_clear();pos.append(P)
 if f in (0,5,7.5,30,60):
  print('FRAME',f)
  for s in 'LR':
   print('BONES',s,[(n,tuple(round(x,3) for x in r.pose.bones[f'B_{s}_{n}'].head),tuple(round(x,3) for x in r.pose.bones[f'B_{s}_{n}'].location)) for n in ('Thigh','Calf','Foot')])
  i=int(np.argmin(np.where(pv==100,P[:,2],99)));v=me.vertices[i]
  print('FLOOR',i,P[i].tolist(),co[i].tolist(),[(o.vertex_groups[g.group].name,g.weight) for g in v.groups])
  if f==60:
   for part in (5,6,8,10,14,15):print('POSEDPART',part,P[pv==part].min(0).tolist(),P[pv==part].max(0).tolist())
P=np.array(pos)[::2];A=np.linalg.norm(P[2:]-2*P[1:-1]+P[:-2],axis=2);A[:,pv!=100]=0
i,j=np.unravel_index(A.argmax(),A.shape)
print('WORSTJERK',i+1,j,A[i,j],co[j].tolist(),P[i:i+3,j].tolist(),[(o.vertex_groups[g.group].name,g.weight) for g in me.vertices[j].groups])
