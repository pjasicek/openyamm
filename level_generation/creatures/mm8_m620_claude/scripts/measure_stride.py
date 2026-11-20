from pathlib import Path
import bpy,json,numpy as np
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_textured_uv.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene;co=np.array([tuple(v.co) for v in b.data.vertices]);pc=np.array([v.value for v in b.data.attributes['piece'].data]);report={}
for role in ['Walking']:
 a=bpy.data.actions[role];r.animation_data.action=a
 if a.slots:r.animation_data.action_slot=a.slots[0]
 points=[];floors=[]
 for f in range(int(a.frame_range[1])+1):
  sc.frame_set(f);points.append([tuple(r.pose.bones['B_'+s+'_Foot'].head) for s in 'LR']);ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();z=np.array([v.co.z for v in m.vertices]);ev.to_mesh_clear();floors.append([float(z[np.isin(pc,[3,4,5,6])&(co[:,0]*sign>0)].min()) for sign in [1,-1]])
 points=np.array(points);floors=np.array(floors);vel=np.diff(points[:,:,1],axis=0)*30;near=(floors[:-1]<np.quantile(floors,.25,axis=0)+.025);samples=vel[near&(vel>.02)];assert len(samples)>3,(role,len(samples));speed=float(np.median(samples));duration=a.frame_range[1]/30
 report[role]={'stride_length_m':speed*duration,'stance_speed_m_s':speed,'samples':len(samples),'method':'Median backward ankle speed during low-foot stance, times cycle duration.'}
(p/'work/strides.json').write_text(json.dumps(report,indent=2)+'\n');print('STRIDES',report)
