"""Upright native stance, quiet breath and a small near-face hand gesture."""
from pathlib import Path
import bpy,sys,math
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_fingers.blend'))
rig=bpy.data.objects['Rig'];sc=bpy.context.scene;sc.render.fps=30
rig.animation_data_create();rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix();b.rotation_mode='QUATERNION'
bpy.context.view_layer.update()
for side,sign in [('L',1),('R',-1)]:
 ua,fa,ha=[rig.pose.bones[f'B_{side}_{n}'] for n in ['UpperArm','Forearm','Hand']]
 old=(fa.head-ua.head).normalized();target=Vector((sign*.25,-.04,-1)).normalized()
 m=ua.matrix.copy();q=old.rotation_difference(target);m=armik.rot_world(m,q.to_matrix()@m.to_3x3());armik.set_world(rig,ua.name,m)
 # A slight elbow bend leaves the open hand clear of the breastplate and hip.
 old=(ha.head-fa.head).normalized();target=Vector((sign*.20,-.35,-1)).normalized()
 m=fa.matrix.copy();q=old.rotation_difference(target);m=armik.rot_world(m,q.to_matrix()@m.to_3x3());armik.set_world(rig,fa.name,m)
base={b.name:b.matrix_basis.copy() for b in rig.pose.bones}
for name,n in [('Standing',60),('Fidget',45)]:
 act=bpy.data.actions.new(name);act.use_fake_user=True
 for f in range(n+1):
  rig.animation_data.action=None
  for b in rig.pose.bones:b.matrix_basis=base[b.name]
  phase=2*math.pi*f/n
  rig.pose.bones['B_Spine2'].rotation_quaternion=base['B_Spine2'].to_quaternion()@Quaternion((1,0,0),.006*math.sin(phase))
  bpy.context.view_layer.update()
  if name=='Fidget':
   t=math.sin(math.pi*f/n)**2
   h=armik.W(rig,'B_R_Hand');target=h.translation.lerp(Vector((-.22,-.25,1.40)),t)
   rot=Quaternion((0,1,0),-.95*t).to_matrix()@h.to_3x3()
   armik.solve(rig,'R',target,pole=(-.5,-.18,1.20),hand_rot=rot)
  snap={b.name:b.matrix_basis.copy() for b in rig.pose.bones}
  rig.animation_data.action=act
  if act.slots:rig.animation_data.action_slot=act.slots[0]
  for b in rig.pose.bones:
   b.matrix_basis=snap[b.name];b.keyframe_insert('rotation_quaternion',frame=f)
   if b.name=='B_Pelvis':b.keyframe_insert('location',frame=f)
 act.use_frame_range=True;act.frame_start=0;act.frame_end=n
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/idle.blend'))
