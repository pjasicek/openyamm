import bpy,json,math,sys,os,runpy
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));rig=bpy.data.objects['Rig'];ob=bpy.data.objects['BowAsset'];sc=bpy.context.scene;a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
body=bpy.data.objects['Body'];hand_ids=[v.index for v in body.data.vertices if body.data.attributes['piece'].data[v.index].value in [2,10,12]]
def handfloor():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=min((m.vertices[i].co.copy()for i in hand_ids),key=lambda v:v.z);ev.to_mesh_clear();return v
# Adjust the holding wrist during the fall so the rigid bow stays above the ground.
poses=[]
for f in range(32):
 sc.frame_set(f);poses.append({b.name:(b.rotation_quaternion.copy(),b.location.copy(),b.scale.copy())for b in rig.pose.bones})
rig.animation_data.action=None;report=[]
for f,pose in enumerate(poses):
 for n,(q,l,s)in pose.items():b=rig.pose.bones[n];b.rotation_quaternion=q;b.location=l;b.scale=s
 bpy.context.view_layer.update();pb=rig.pose.bones['B_L_Hand'];original=pb.rotation_quaternion.copy()
 # Flatten the bow plane during the floor-contact part of the fall; blending is spread over eight frames.
 bow=rig.pose.bones['Bow'].matrix.copy();local=pb.matrix.inverted()@bow;z=bow.to_3x3().col[2];z.z=0;z.normalize();x=Vector((0,0,1));y=z.cross(x).normalized();target=Matrix((x,y,z)).transposed()@local.to_3x3().inverted();M=target.to_4x4();M.translation=pb.head;pb.matrix=M;bpy.context.view_layer.update();goal=pb.rotation_quaternion.copy()
 def smooth(v):v=max(0,min(1,v));return v*v*(3-2*v)
 weight=smooth((f-7)/8)*smooth((31-f)/7);pb.rotation_quaternion=original.slerp(goal,weight);bpy.context.view_layer.update()
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=min((x.co.copy()for x in m.vertices),key=lambda v:v.z);ev.to_mesh_clear()
 for _ in range(5):
  v=min(v,handfloor(),key=lambda v:v.z)
  if v.z>=.0002:break
  fore=rig.pose.bones['B_L_Forearm'];oldhand=pb.matrix.copy();d=pb.head-fore.head;target=d+Vector((0,0,.0015-v.z));M=fore.matrix.copy();t=M.translation.copy();M=d.rotation_difference(target).to_matrix().to_4x4()@M;M.translation=t;fore.matrix=M;bpy.context.view_layer.update();oldhand.translation=pb.head;pb.matrix=oldhand;bpy.context.view_layer.update()
  ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=min((x.co.copy()for x in m.vertices),key=lambda v:v.z);ev.to_mesh_clear()
 pose['B_L_Forearm']=(rig.pose.bones['B_L_Forearm'].rotation_quaternion.copy(),rig.pose.bones['B_L_Forearm'].location.copy(),rig.pose.bones['B_L_Forearm'].scale.copy())
 pose['B_L_Hand']=(pb.rotation_quaternion.copy(),pb.location.copy(),pb.scale.copy());report.append({'frame':f,'wrist_adjustment_deg':math.degrees(original.rotation_difference(pb.rotation_quaternion).angle),'bow_floor_m':v.z})
rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
for f,pose in enumerate(poses):
 for n in ['B_L_Hand','B_L_Forearm']:
  b=rig.pose.bones[n];b.rotation_quaternion=pose[n][0];b.keyframe_insert('rotation_quaternion',frame=f)
FA,UA=.6,.5
code=(P/'scripts/twist_bones.py').read_text();exec(code[code.index('def twist_about'):code.index('for act in [a for a in bpy.data.actions')]);bake_twist(a)
(P/'work/bow_floor.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
print('BOW FLOOR correction max degrees',max(x['wrist_adjustment_deg']for x in report))
