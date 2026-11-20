import bpy,math,sys,os
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_reach_baseline.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
for f in range(4,20):
 sc.frame_set(f);old=rig.pose.bones['B_R_Finger1'].head.copy();pb=rig.pose.bones['B_R_UpperArm'];m=pb.matrix.copy();t=m.translation.copy();m=Matrix.Rotation(-math.radians(10)*math.sin(math.pi*(f-4)/16)**2,4,'Y')@m;m.translation=t;pb.matrix=m;bpy.context.view_layer.update();delta=rig.pose.bones['B_R_Finger1'].head-old;pb.keyframe_insert('rotation_quaternion',frame=f)
 if f>=12:
  arrow=rig.pose.bones['Arrow'];m=arrow.matrix.copy();m.translation+=delta;arrow.matrix=m;bpy.context.view_layer.update();arrow.keyframe_insert('location',frame=f)
FA,UA=.6,.5;code=(P/'scripts/twist_bones.py').read_text();exec(code[code.index('def twist_about'):code.index('for act in [a for a in bpy.data.actions')]);bake_twist(a)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
