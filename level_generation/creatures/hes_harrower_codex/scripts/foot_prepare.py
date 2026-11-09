"""Retain run ankle paths while fitting the Demon's long feet to stable body-forward headings."""
from pathlib import Path
import bpy,sys,math,numpy as np
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/guard_polished.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
up=Vector((0,0,1));local={}
for sd in 'LR':
 foot=rig.data.bones[f'B_{sd}_Foot'];toe=rig.data.bones[f'B_{sd}_Toe0'];R=foot.matrix_local.to_3x3();d=(R.inverted()@(toe.head_local-foot.head_local)).normalized();z=R.inverted()@up;z=(z-d*z.dot(d)).normalized();local[sd]=Matrix((d,z,d.cross(z))).transposed()
for a in [a for a in bpy.data.actions if a.name.startswith('Harrower_') and not a.name.endswith(('_Death','_Dead'))]:
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];keys={};prev={};n=int(a.frame_range[1])
 for f in range(n+1):
  sc.frame_set(f);lat=armik.W(rig,'B_L_Thigh').translation-armik.W(rig,'B_R_Thigh').translation;lat.z=0;lat.normalize();forward=lat.cross(up)
  for sd in 'LR':
   foot=f'B_{sd}_Foot';toe=f'B_{sd}_Toe0';rig.pose.bones[toe].matrix_basis.identity();bpy.context.view_layer.update()
   if a.name=='Harrower_Running':
    q=rig.pose.bones[foot].rotation_quaternion.copy().slerp(Quaternion(),.8);keys[(f,foot)]=q;continue
   d=(armik.W(rig,toe).translation-armik.W(rig,foot).translation).normalized();pitch=max(math.radians(-30),min(math.radians(20),math.asin(max(-1,min(1,d.z)))))
   target=forward*math.cos(pitch)+up*math.sin(pitch);z=(up-target*up.dot(target)).normalized();R=Matrix((target,z,target.cross(z))).transposed()@local[sd].transposed();M=armik.W(rig,foot);N=R.to_4x4();N.translation=M.translation;armik.set_world(rig,foot,N)
   q=rig.pose.bones[foot].rotation_quaternion.copy()
   if sd in prev and q.dot(prev[sd])<0:q=-q
   prev[sd]=q;keys[(f,foot)]=q
 for (f,name),q in keys.items():rig.pose.bones[name].rotation_quaternion=q;rig.pose.bones[name].keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/feet_prepared.blend'))
