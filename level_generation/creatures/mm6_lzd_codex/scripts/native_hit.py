"""Native hit is a small recoil, without the source clip's overhead shoulder shrug."""
import bpy,math,sys
from pathlib import Path
from mathutils import Matrix, Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_reduced.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene;st=bpy.data.actions['Standing'];poses=[]
def aim(name, child, target):
 pb=rig.pose.bones[name];m=pb.matrix.copy();q=(rig.pose.bones[child].head-pb.head).rotation_difference(target-pb.head);t=m.translation.copy();m=q.to_matrix().to_4x4()@m;m.translation=t;pb.matrix=m;bpy.context.view_layer.update()
def plant(side,target,rotation):
 th,ca,ft=[f'B_{side}_{x}'for x in ('Thigh','Calf','Foot')];H=rig.pose.bones[th].head.copy();K=rig.pose.bones[ca].head.copy();A=rig.pose.bones[ft].head.copy();a=(K-H).length;b=(A-K).length;u=(target-H).normalized();d=min((target-H).length,(a+b)*.9999);v=Vector((0,-1,0));v=(v-u*v.dot(u)).normalized();c=max(-1,min(1,(a*a+d*d-b*b)/(2*a*d)));aim(th,ca,H+a*(u*c+v*math.sqrt(1-c*c)));aim(ca,ft,target);m=rotation.to_matrix().to_4x4();m.translation=rig.pose.bones[ft].head;rig.pose.bones[ft].matrix=m;bpy.context.view_layer.update()
for f in range(16):
 rig.animation_data.action=st;rig.animation_data.action_slot=st.slots[0];scene.frame_set(0);pose={b.name:(b.rotation_quaternion.copy(),b.location.copy(),b.scale.copy())for b in rig.pose.bones};rig.animation_data.action=None
 for n,(q,l,s)in pose.items():pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.scale=s
 bpy.context.view_layer.update();u=math.sin(math.pi*f/15)**2
 feet={s:(rig.pose.bones[f'B_{s}_Foot'].head.copy(),rig.pose.bones[f'B_{s}_Foot'].matrix.to_quaternion())for s in 'LR'}
 pb=rig.pose.bones['B_Pelvis'];m=pb.matrix.copy();m.translation.z-=.015*u;pb.matrix=m;bpy.context.view_layer.update()
 for side in 'LR':plant(side,*feet[side])
 for n,degrees in [('B_Spine',-7),('B_Head',3)]:
  pb=rig.pose.bones[n];M=pb.matrix.copy();t=M.translation.copy();M=Matrix.Rotation(math.radians(degrees)*u,4,'X')@M;M.translation=t;pb.matrix=M;bpy.context.view_layer.update()
 poses.append({b.name:(b.rotation_quaternion.copy(),b.location.copy(),b.scale.copy())for b in rig.pose.bones})
bpy.data.actions.remove(bpy.data.actions['Hit']);act=bpy.data.actions.new('Hit');act.use_fake_user=True;rig.animation_data.action=act
for f,pose in enumerate(poses):
 for n,(q,l,s)in pose.items():
  pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.scale=s
  for channel in ['rotation_quaternion','location','scale']:pb.keyframe_insert(channel,frame=f)
act.use_frame_range=True;act.frame_start=0;act.frame_end=15
# A native stance adjustment: planted knee flex, torso/arms/bow sway and a head scan.
poses=[]
for f in range(31):
 rig.animation_data.action=st;rig.animation_data.action_slot=st.slots[0];scene.frame_set(f);p={b.name:(b.rotation_quaternion.copy(),b.location.copy(),b.scale.copy())for b in rig.pose.bones};rig.animation_data.action=None
 for n,(q,l,s)in p.items():pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.scale=s
 bpy.context.view_layer.update();u=math.sin(2*math.pi*f/30);feet={s:(rig.pose.bones[f'B_{s}_Foot'].head.copy(),rig.pose.bones[f'B_{s}_Foot'].matrix.to_quaternion())for s in 'LR'}
 pb=rig.pose.bones['B_Pelvis'];m=pb.matrix.copy();m.translation.z-=.008*u*u;pb.matrix=m;bpy.context.view_layer.update()
 for side in 'LR':plant(side,*feet[side])
 for n,axis,degrees in [('B_Spine','Y',2),('B_Head','Z',12),('B_L_UpperArm','X',-3),('B_R_UpperArm','X',3)]:
  pb=rig.pose.bones[n];m=pb.matrix.copy();t=m.translation.copy();m=Matrix.Rotation(math.radians(degrees)*u,4,axis)@m;m.translation=t;pb.matrix=m;bpy.context.view_layer.update()
 poses.append({b.name:(b.rotation_quaternion.copy(),b.location.copy(),b.scale.copy())for b in rig.pose.bones})
bpy.data.actions.remove(bpy.data.actions['Fidget']);act=bpy.data.actions.new('Fidget');act.use_fake_user=True;rig.animation_data.action=act
for f,p in enumerate(poses):
 for n,(q,l,s)in p.items():
  pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.scale=s
  for channel in ['rotation_quaternion','location','scale']:pb.keyframe_insert(channel,frame=f)
act.use_frame_range=True;act.frame_start=0;act.frame_end=30;rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_reduced.blend'))
