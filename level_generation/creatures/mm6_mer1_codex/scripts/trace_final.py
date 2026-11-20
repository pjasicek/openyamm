"""Compare exported 48 Hz world rotation increments with the actual owned source clips."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];MX=ROOT/'anim_library/mixamo';HS=ROOT/'anim_library/humanoid_set'
groups={'arms':['B_L_UpperArm','B_R_UpperArm','B_L_Forearm','B_R_Forearm'],'hands':['B_L_Hand','B_R_Hand']}
mix={'B_L_UpperArm':'LeftArm','B_R_UpperArm':'RightArm','B_L_Forearm':'LeftForeArm','B_R_Forearm':'RightForeArm','B_L_Hand':'LeftHand','B_R_Hand':'RightHand'}
sources={'Standing':(MX/'Standard Idle.fbx',None),'Walking':(HS/'Armed.glb','ArmedWalk'),'Running':(MX/'Jogging.fbx',None),'Attack':(MX/'Sword And Shield Slash.fbx',None),'Hit':(HS/'Unarmed.glb','UnarmedGetHitF1'),'Death':(MX/'Standing Death Forward 02.fbx',None),'Fidget':(MX/'Standing Idle 03 Examine.fbx',None)}
def trace(rig,action,names):
 rig.animation_data_create();rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];sc=bpy.context.scene;fps=sc.render.fps/sc.render.fps_base;start,end=action.frame_range;worst={g:{'degrees_per_sample':0.,'time':0.,'bone':None,'acceleration_deg_s2':0.,'acceleration_time':0.,'acceleration_bone':None}for g in names};previous=None;previous_velocity={}
 for t in np.arange(start/fps,end/fps+.00001,1/48):
  f=float(t*fps);sc.frame_set(int(f),subframe=f%1);q={n:(rig.matrix_world@rig.pose.bones[n].matrix).to_quaternion()for ns in names.values()for n in ns if n in rig.pose.bones};velocity={}
  if previous is not None:
   for group,ns in names.items():
    for n in ns:
     if n not in q:continue
     dq=previous[n].rotation_difference(q[n])
     if dq.w<0:dq=-dq
     angle=math.degrees(dq.angle);velocity[n]=(previous[n]@dq.axis)*(angle*48)
     if angle>worst[group]['degrees_per_sample']:worst[group].update({'degrees_per_sample':angle,'time':float(t-start/fps),'bone':n})
     if n in previous_velocity:
      acc=(velocity[n]-previous_velocity[n]).length*48
      if acc>worst[group]['acceleration_deg_s2']:worst[group].update({'acceleration_deg_s2':acc,'acceleration_time':float(t-start/fps),'acceleration_bone':n})
  previous=q;previous_velocity=velocity
 return worst
reference={}
for role,(path,clip)in sources.items():
 bpy.ops.wm.read_factory_settings(use_empty=True)
 if path.suffix=='.fbx':bpy.ops.import_scene.fbx(filepath=str(path))
 else:bpy.ops.import_scene.gltf(filepath=str(path))
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');act=next(a for a in bpy.data.actions if clip is None or a.name.split('@')[-1].split('|')[-1].split('|')[-1]==clip)
 if path.suffix=='.fbx':
  prefix=next(b.name for b in rig.data.bones if b.name.endswith('Hips'))[:-4];names={g:[prefix+mix[n]for n in ns]for g,ns in groups.items()}
 else:names=groups
 reference[role]={'file':str(path.relative_to(ROOT)),'clip':act.name,'groups':trace(rig,act,names)}
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'review/viewer/mm6_mer1_a.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
names={**groups,'twist':[b.name for b in rig.data.bones if 'Twist'in b.name],'fingers':[b.name for b in rig.data.bones if 'Finger'in b.name],'club':['Club']};report={}
for a in bpy.data.actions:
 role=a.name.split('@')[-1].split('|')[-1];out=trace(rig,a,names);ref=reference.get(role);fail=[]
 for group,v in out.items():
  kind='arms'if group in ['arms','twist']else'hands';limit=(ref['groups'][kind]['degrees_per_sample']if ref else 0)+10;v['source_limit_plus_10_deg']=limit;v['acceleration_limit_deg_s2']=(ref['groups'][kind]['acceleration_deg_s2']if ref else 0)+10*48**2;v['speed_pass']=v['degrees_per_sample']<=limit;v['acceleration_pass']=v['acceleration_deg_s2']<=v['acceleration_limit_deg_s2'];v['pass']=v['speed_pass']and v['acceleration_pass']
  if not v['pass']:fail.append(group)
 report[role]={'source':ref,'exported':out,'failed_groups':fail};print('SOURCE TRACE',role,[(g,round(v['degrees_per_sample'],2),round(v['source_limit_plus_10_deg'],2),v['pass'])for g,v in out.items()],flush=True)
(P/'review/final_source_motion_trace.json').write_text(json.dumps({'sample_hz':48,'clips':report,'pass':not any(v['failed_groups']for v in report.values())},indent=2))
