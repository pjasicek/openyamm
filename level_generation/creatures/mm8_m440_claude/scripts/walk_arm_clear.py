from pathlib import Path
import bpy,sys
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik,action_curves
bpy.ops.wm.open_mainfile(filepath=str(p/'work/full_repaired.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;a=bpy.data.actions['Walking'];N=int(a.frame_range[1]);frames=[]
for i in range(N*2+1):
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f=i/2;sc.frame_set(int(f),subframe=f-int(f));x={b.name:b.matrix_basis.copy() for b in rig.pose.bones};rig.animation_data.action=None
 for n,m in x.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update();H=armik.W(rig,'B_R_Hand');armik.solve(rig,'R',H.translation+Vector((-.03,-.08,.03)),hand_rot=H.to_3x3());frames.append({n:rig.pose.bones[n].rotation_quaternion.copy() for n in ('B_R_UpperArm','B_R_Forearm','B_R_Hand')})
frames[-1]=frames[0];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];action_curves.remove_rotations(a,list(frames[0]));previous={}
for i,qs in enumerate(frames):
 for n,q in qs.items():
  if n in previous and q.dot(previous[n])<0:q=-q
  previous[n]=q.copy();rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=i/2)
rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/full_repaired.blend'))
