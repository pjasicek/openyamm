import bpy,sys,json,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/skirt_animated.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];sc=bpy.context.scene;pv=np.array([a.value for a in o.data.attributes['piece'].data]);rest=np.array([v.co[:] for v in o.data.vertices]);names=[b.name for b in r.data.bones if b.name.startswith('Skirt_')]
a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
P=[];B=[];floor=[]
for f in range(61):
 sc.frame_set(f);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();pts=np.array([v.co[:] for v in mm.vertices]);ev.to_mesh_clear();P.append(pts);B.append([r.pose.bones[n].tail[:] for n in names])
 floor.append((f,float(pts[(pv!=100)|(rest[:,2]>1.02),2].min()),float(pts[:,2].min())))
P=np.array(P);B=np.array(B)
for label,Q in [('skin',P[:,pv==100]),('bones',B)]:
 A=np.linalg.norm(Q[2:]-2*Q[1:-1]+Q[:-2],axis=2);idx=np.unravel_index(A.argmax(),A.shape);f,k=idx
 if label=='skin':
  vi=np.flatnonzero(pv==100)[k];extra=[(o.vertex_groups[g.group].name,round(g.weight,3)) for g in o.data.vertices[vi].groups]
 else:extra=names[k]
 print(label,'WORST',f+1,extra,'jerk',A[f,k],'positions',Q[f:f+3,k].tolist())
print('FLOOR',floor)
