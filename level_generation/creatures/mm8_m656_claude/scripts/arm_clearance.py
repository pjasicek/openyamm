import bpy,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_equipped.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
for name,deg in [('Walking',19),('Running',10),('Standing',10),('Hit',10),('Attack',10),('Fidget',10),('Death',19)]:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];rows=[]
 for f in np.arange(0,float(a.frame_range[1])+.001,.25):
  sc.frame_set(int(f),subframe=float(f%1));b=rig.pose.bones['B_L_UpperArm'];m=b.matrix.copy();pivot=m.translation
  axis=rig.pose.bones['B_Spine'].matrix.to_3x3()@rig.data.bones['B_Spine'].matrix_local.to_3x3().inverted()@Vector((0,-1,0))
  b.matrix=Matrix.Translation(pivot)@Matrix.Rotation(math.radians(deg*(max(0,min(1,(70-f)/15)) if name=='Death' else 1)),4,axis)@Matrix.Translation(-pivot)@m
  rows.append((float(f),b.rotation_quaternion.copy()))
 for f,q in rows:
  b=rig.pose.bones['B_L_UpperArm'];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master_equipped.blend'))
