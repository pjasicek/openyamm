import bpy,json,math
from pathlib import Path
from mathutils import Vector
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/rig_review_01/upright_audit');OUT.mkdir(exist_ok=True)
s=bpy.data.scenes['Goblin - Posture Alignment v2'];bpy.context.window.scene=s;arm=bpy.data.objects['MM6_Goblin_Upright_Rig'];mesh=max((o for o in s.objects if o.type=='MESH'),key=lambda o:len(o.data.vertices));prevaction=arm.animation_data.action;prevframe=s.frame_current;prevsub=s.frame_subframe
report={'scene':s.name,'frame':prevframe,'active_action':prevaction.name if prevaction else None,'rest_bones':{},'clips':{}}
for b in arm.data.bones:
 if b.name.split(':')[-1] in ['Hips','Spine','Spine1','Spine2','Neck','Head','LeftArm','RightArm','LeftForeArm','RightForeArm','LeftHand','RightHand','LeftUpLeg','RightUpLeg','LeftLeg','RightLeg','LeftFoot','RightFoot']:
  report['rest_bones'][b.name]=list(arm.matrix_world@b.head_local)
for key in ['Idle_3','Walking','Running','Right_Hand_Sword_Slash']:
 a=bpy.data.actions['Goblin_Upright_'+key];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];samples=[]
 for i in range(48):
  frame=a.frame_range[0]+(a.frame_range[1]-a.frame_range[0])*i/48;s.frame_set(int(frame),subframe=frame-int(frame));points={n:list(arm.matrix_world@arm.pose.bones['mixamorig:'+n].head) for n in ['Hips','Spine','Spine1','Spine2','Neck','Head','LeftArm','RightArm','LeftFoot','RightFoot']};delta=Vector(points['Head'])-Vector(points['Hips']);chest=Vector(points['Spine2'])-Vector(points['Hips']);bd=arm.pose.bones['mixamorig:Hips'].matrix@arm.data.bones['mixamorig:Hips'].matrix_local.inverted();right=bd.to_quaternion()@Vector((1,0,0));right.z=0;right.normalize();forward=Vector((right.y,-right.x,0))
  samples.append({'frame':frame,'points':points,'head_hip_x':delta.x,'head_hip_lateral':delta.dot(right),'head_hip_forward':delta.dot(forward),'front_lean_deg':math.degrees(math.atan2(delta.x,delta.z)),'lateral_lean_deg':math.degrees(math.atan2(delta.dot(right),delta.z)),'shoulder_height_difference':points['LeftArm'][2]-points['RightArm'][2]})
 fields=['head_hip_x','head_hip_lateral','head_hip_forward','front_lean_deg','lateral_lean_deg','shoulder_height_difference'];stats={k:{'mean':sum(x[k] for x in samples)/len(samples),'min':min(x[k] for x in samples),'max':max(x[k] for x in samples)} for k in fields};report['clips'][key]={'stats':stats,'samples':samples}
arm.animation_data.action=prevaction
if prevaction:arm.animation_data.action_slot=prevaction.slots[0]
s.frame_set(prevframe,subframe=prevsub);(OUT/'posture_v2_report.json').write_text(json.dumps(report,indent=2));print(json.dumps({key:value['stats'] for key,value in report['clips'].items()}))
