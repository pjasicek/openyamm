"""Keep the native upright support stance for the small flinch and palm cast; fidget is a quiet ready gesture."""
from pathlib import Path
import bpy,sys,math
from mathutils import Matrix,Quaternion,Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v2l.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene

def select(a):
 rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
select(bpy.data.actions['Standing']);sc.frame_set(0)
base={b.name:b.matrix_basis.copy() for b in rig.pose.bones};pelvis=armik.W(rig,'B_Pelvis');legs=[n for n in base if any(k in n for k in ('Thigh','Calf','Foot','Toe'))]
for name in ['Hit','Cast']:
 act=bpy.data.actions[name];poses=[]
 for f in range(int(act.frame_range[1])+1):
  select(act);sc.frame_set(f);snap={b.name:b.matrix_basis.copy() for b in rig.pose.bones};spine=armik.W(rig,'B_Spine');select(None)
  for b in rig.pose.bones:b.matrix_basis=snap[b.name]
  for n in legs:rig.pose.bones[n].matrix_basis=base[n]
  armik.set_world(rig,'B_Pelvis',pelvis)
  spine.translation=armik.W(rig,'B_Spine').translation;armik.set_world(rig,'B_Spine',spine)
  poses.append({n:rig.pose.bones[n].matrix_basis.copy() for n in legs+['B_Pelvis','B_Spine']})
 select(act)
 for f,pose in enumerate(poses):
  for n,m in pose.items():
   pb=rig.pose.bones[n];pb.matrix_basis=m;pb.rotation_mode='QUATERNION';pb.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis':pb.keyframe_insert('location',frame=f)
for name in ['Fidget','FidgetFull']:
 if name in bpy.data.actions:bpy.data.actions.remove(bpy.data.actions[name])
# Derive a subtle stance adjustment from the loop; carry is fitted in the next step.
a=bpy.data.actions['Standing'].copy();a.name='Fidget';a.use_fake_user=True;select(a)
for layer in a.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for key in fc.keyframe_points:key.co.x*=.875/3;key.handle_left.x*=.875/3;key.handle_right.x*=.875/3
for f in range(28):
 sc.frame_set(f);u=min(1,f/26.25);w=math.sin(math.pi*u)**2
 for n,axis,angle in [('B_Head',(1,0,0),-5),('B_L_Clavicle',(0,0,1),-3)]:
  pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=base[n].to_quaternion()@Quaternion(axis,math.radians(angle)*w);pb.keyframe_insert('rotation_quaternion',frame=f)
a.use_frame_range=True;a.frame_start=0;a.frame_end=26.25
select(None);bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v2p.blend'))
