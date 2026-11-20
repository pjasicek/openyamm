import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/accepted_master.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];co=np.array([tuple(v.co)for v in body.data.vertices]);piece=np.array([a.value for a in body.data.attributes['piece'].data]);soles={}
for sd in 'LR':
 ids=np.where((piece==1)&(co[:,0]*(1 if sd=='L'else -1)>0)&(co[:,2]<.075))[0];z=co[ids,2].min();ids=ids[co[ids,2]<z+.009];soles[sd]=(ids[co[ids,1]>np.quantile(co[ids,1],.75)],ids[co[ids,1]<np.quantile(co[ids,1],.25)])
sc=bpy.context.scene;report={}
for name in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];Q={n:[]for n in [f'B_{s}_{b}'for s in 'LR'for b in ['UpperArm','Forearm','Hand']]};feet={s:[]for s in 'LR'}
 for f in np.arange(0,a.frame_range[1]+.001,sc.render.fps/48):
  sc.frame_set(int(f),subframe=float(f%1))
  for n,seq in Q.items():
   q=rig.pose.bones[n].matrix.to_quaternion()
   if seq and q.dot(seq[-1])<0:q.negate()
   seq.append(q.copy())
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();cc=np.array([tuple(v.co)for v in me.vertices]);ev.to_mesh_clear()
  for s in 'LR':
   heel,toe=soles[s];d=cc[toe].mean(0)-cc[heel].mean(0);feet[s].append(math.degrees(math.atan2(d[0],-d[1])))
 report[name]={'joints':{},'foot_yaw_range':{s:[min(v),max(v)]for s,v in feet.items()}}
 for n,q in Q.items():
  vel=[]
  for l,r in zip(q,q[1:]):
   axis,angle=(r@l.conjugated()).to_axis_angle();angle=(angle+math.pi)%(2*math.pi)-math.pi;vel.append(np.array(axis)*math.degrees(angle)*48)
  vv=np.array(vel);aa=np.linalg.norm(np.diff(vv,axis=0)*48,axis=1);report[name]['joints'][n]={'max_step_deg':float(np.linalg.norm(vv,axis=1).max()/48),'max_accel_deg_s2':float(aa.max()),'p99_accel_deg_s2':float(np.percentile(aa,99)),'max_accel_seconds':float((np.argmax(aa)+1)/48)}
 print(name,report[name],flush=True)
(P/'review/motion_probe.json').write_text(json.dumps(report,indent=2))
