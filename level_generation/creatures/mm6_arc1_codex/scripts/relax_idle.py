import bpy,math,sys,os,json
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_idle_baseline.blend'));rig=bpy.data.objects['Rig'];a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
for f in range(int(a.frame_range[1])+1):
 bpy.context.scene.frame_set(f)
 for name,target in [('B_R_Forearm',(-.15,-.28,-1)),('B_R_Hand',(-.08,-.12,-1))]:
  pb=rig.pose.bones[name];m=pb.matrix.copy();q=(pb.tail-pb.head).normalized().rotation_difference(Vector(target).normalized());pos=m.translation.copy();m=q.to_matrix().to_4x4()@m;m.translation=pos;pb.matrix=m;bpy.context.view_layer.update();pb.keyframe_insert('rotation_quaternion',frame=f)
FA,UA=.6,.5;code=(P/'scripts/twist_bones.py').read_text();exec(code[code.index('def twist_about'):code.index('for act in [a for a in bpy.data.actions')]);bake_twist(a)
for layer in a.layers:
 for strip in layer.strips:
  for cb in strip.channelbags:
   for fc in cb.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
