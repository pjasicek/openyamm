import bpy,math,json,hashlib,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];root=p.parents[2];path=root/'anim_library/mixamo/Standing Melee Attack Downward.fbx'
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(path));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');a=rig.animation_data.action;sc=bpy.context.scene;fps=sc.render.fps/sc.render.fps_base;f0,f1=a.frame_range;duration=(f1-f0)/fps
names=[n for n in rig.pose.bones.keys() if n.endswith(('LeftArm','LeftForeArm','LeftHand','RightArm','RightForeArm','RightHand'))];frames={n:[] for n in names};times=np.linspace(0,duration,int(round(duration*48))+1)
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
report={'file':str(path.relative_to(root)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'duration_s':duration,'bones':result};(p/'work/source_attack_limits.json').write_text(json.dumps(report,indent=2));print('SOURCE_LIMITS',json.dumps(report))
