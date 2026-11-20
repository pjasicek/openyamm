"""Keep both hands and the held blade outside the tunic during the backward recoil."""
from pathlib import Path
import bpy,sys,math
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v2c.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
a=bpy.data.actions['Death'];poses=[]
rest=rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()
for f in range(int(a.frame_range[1])+1):
 rig.animation_data.action=a
 if len(a.slots):rig.animation_data.action_slot=a.slots[0]
 sc.frame_set(f);snap={b.name:b.matrix_basis.copy() for b in rig.pose.bones};C=armik.W(rig,'B_Spine2').to_3x3().normalized()@rest
 w=min(1,max(0,(f-8)/12),max(0,(77-f)/14));w=w*w*(3-2*w)
 targets={sd:armik.W(rig,f'B_{sd}_Hand').translation+C@Vector((sign*.11,-.04,0))*w for sd,sign in [('R',-1),('L',1)]}
 rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis=snap[b.name]
 for sd in 'RL':armik.solve(rig,sd,targets[sd])
 poses.append({n:rig.pose.bones[n].rotation_quaternion.copy() for sd in 'RL' for n in [f'B_{sd}_UpperArm',f'B_{sd}_Forearm',f'B_{sd}_Hand']})
rig.animation_data.action=a
for f,pose in enumerate(poses):
 for n,q in pose.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v2c.blend'))
