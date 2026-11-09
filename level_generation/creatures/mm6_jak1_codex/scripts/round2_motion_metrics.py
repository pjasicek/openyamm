import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from timing import phase
"""Measure world-space arm acceleration and the actual casting socket at 48 Hz."""
import bpy,json,math,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];names=[f'B_{s}_{b}'for s in 'LR'for b in ['UpperArm','Forearm','Hand']]
def measure(rig,action):
 rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];sc=bpy.context.scene;end=action.frame_range[1]/sc.render.fps;times=np.arange(int(math.floor(end*48+1e-6))+1)/48
 if end-times[-1]>1e-6:times=np.r_[times,end]
 else:times[-1]=end
 samples={n:[]for n in names};staff=[]
 for t in times:
  f=t*sc.render.fps;sc.frame_set(int(f),subframe=float(f-int(f)))
  for n in names:samples[n].append((rig.matrix_world@rig.pose.bones[n].matrix).to_quaternion())
  if action.name=='Cast' and 'StaffTip'in rig.pose.bones:staff.append((np.array((rig.matrix_world@rig.pose.bones['StaffTip'].matrix).translation),-(rig.matrix_world@rig.pose.bones['Staff'].matrix).to_3x3().col[2].normalized().y))
 rows={};dt=np.diff(times)
 for n,qs in samples.items():
  velocity=[]
  for a,b,h in zip(qs,qs[1:],dt):
   q=b@a.inverted()
   if q.w<0:q=-q
   axis,angle=q.to_axis_angle();velocity.append(np.array(axis)*math.degrees(angle)/h)
  accel=np.linalg.norm(np.diff(np.array(velocity),axis=0)/((dt[:-1]+dt[1:])*.5)[:,None],axis=1);k=int(accel.argmax());rows[n]={'max_deg_s2':float(accel[k]),'p99_deg_s2':float(np.percentile(accel,99)),'seconds':float(times[k+1])}
 if staff:
  positions=np.array([v[0]for v in staff]);vel=np.diff(positions,axis=0)/dt[:,None];direction=np.array([v[1]for v in staff[:-1]]);ok=(times[:-1]>=phase('Cast',.3))&(times[:-1]<=phase('Cast',.966666667))&(direction>.5);speed=-vel[:,1];assert ok.any();k=int(np.argmax(np.where(ok,speed,-1e9)));cast={'launch_seconds':float((times[k]+times[k+1])*.5),'socket':'StaffTip','target_dot':float(direction[k]),'forward_speed_mps':float(speed[k]),'tip_speed_mps':float(np.linalg.norm(vel[k]))};assert cast['forward_speed_mps']>0;(P/'review/cast_gate.json').write_text(json.dumps(cast,indent=2));print('CAST',cast,flush=True)
 return rows
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'export/mm6_jak1_runtime_lod0.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');runtime={a.name:measure(rig,a)for a in bpy.data.actions}
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2_sources.blend'));rig=bpy.data.objects['Rig'];source={role:measure(rig,bpy.data.actions[alias])for role,alias in {'Standing':'Standing','Walking':'Walking','Attack':'Staff2','Cast':'Cast1','Hit':'Hit','Death':'StaffFall','Fidget':'Fidget'}.items()}
report={'sample_hz':48,'runtime':runtime,'source':source,'fixed_threshold_deg_s2':20000,'over_threshold':{role:{n:row for n,row in rows.items()if row['max_deg_s2']>20000}for role,rows in runtime.items()}};(P/'review/round2/angular_acceleration.json').write_text(json.dumps(report,indent=2))
print('ACCELERATION',{role:{n:round(row['max_deg_s2'])for n,row in rows.items()}for role,rows in report['over_threshold'].items()if rows},flush=True)
print('SOURCE ACCELERATION',{role:max(round(row['max_deg_s2'])for row in rows.values())for role,rows in source.items()},flush=True)
