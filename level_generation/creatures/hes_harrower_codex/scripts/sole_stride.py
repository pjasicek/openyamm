"""Stride from moving sole vertices in contact, rather than an ankle lifted by digitigrade foot roll."""
from pathlib import Path
import bpy,numpy as np,json
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/final.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
names={g.index:g.name for g in body.vertex_groups};dom=[names[max(v.groups,key=lambda x:x.weight).group] for v in body.data.vertices];report={}
for role in ('Walking','Running'):
 a=bpy.data.actions['Harrower_'+role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];n=float(a.frame_range[1]);T=n/30;frames=np.arange(0,n+.001,.25);points=[]
 for f in frames:
  sc.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();points.append(np.array([list(body.matrix_world@v.co) for v in m.vertices]));ev.to_mesh_clear()
 A=np.array(points);v=np.gradient(A,frames/30,axis=0);sides={}
 for side in 'LR':
  ids=np.where([x in ('B_'+side+'_Foot','B_'+side+'_Toe0') for x in dom])[0];z=A[:,ids,2];low=z.min(1);vel=[]
  for i in range(1,len(frames)-1):
   if low[i]<.012:
    contact=z[i]<low[i]+.004;vel.append(float(np.median(v[i,ids[contact],1])))
  sides[side]={'contact_samples':len(vel),'median_speed_mps':float(np.median(vel)) if vel else None,'speed_p25_p75':np.percentile(vel,[25,75]).tolist() if vel else None}
 speed=float(np.mean([x['median_speed_mps'] for x in sides.values()]));report[role]={'duration':T,'stride_m':speed*T,'sides':sides};print('SOLE_STRIDE',role,report[role],flush=True)
(P/'review/sole_stride.json').write_text(json.dumps(report,indent=2)+'\n')
