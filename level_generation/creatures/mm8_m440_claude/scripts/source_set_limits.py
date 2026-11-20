import bpy,math,json,hashlib,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];root=p.parents[2];path=root/'anim_library/humanoid_set/Armed.glb'
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');sc=bpy.context.scene;fps=sc.render.fps/sc.render.fps_base;results={}
for name,clip in [('Death','ArmedDeath1'),('Hit','ArmedGetHitF1'),('Fidget','ArmedIdleAlert1')]:
 a=next(a for a in bpy.data.actions if a.name.split('@')[-1].split('|')[-1]==clip);rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f0,f1=a.frame_range;duration=(f1-f0)/fps
 names=[f'B_{s}_{b}' for s in 'LR' for b in ('UpperArm','Forearm','Hand')];frames={n:[] for n in names};times=np.r_[np.arange(0,duration-1e-10,1/48),duration]
 for t in times:
  f=f0+t*fps;sc.frame_set(math.floor(f),subframe=f-math.floor(f))
  for n in names:frames[n].append((rig.matrix_world@rig.pose.bones[n].matrix).to_quaternion())
 result={}
 for n,qs in frames.items():
  steps=[];vel=[]
  for i,(a,b) in enumerate(zip(qs[:-1],qs[1:])):
   dq=b@a.inverted()
   if dq.w<0:dq.negate()
   axis,angle=dq.to_axis_angle();steps.append(math.degrees(angle));vel.append(np.array(axis)*angle/(times[i+1]-times[i]))
  acc=np.linalg.norm(np.diff(vel,axis=0),axis=1)/np.diff(times)[:-1]*180/math.pi
  result[n]={'max_step_degrees_48hz':max(steps),'max_angular_acceleration_deg_s2':float(acc.max())}
 results[name]={'clip':clip,'duration_s':duration,'bones':result}
report={'file':str(path.relative_to(root)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'clips':results};(p/'work/source_set_limits.json').write_text(json.dumps(report,indent=2));print('SOURCE_LIMITS',json.dumps(report))
